"""Text-PDF extraction with pypdf (BSD-3-Clause). See docs/decisions/0001-pdf-library.md.

Steps (blocking, run via `asyncio.to_thread`):
1. extract text per page (pypdf `extract_text`), normalise Unicode (NFC; the Hangul jamo
   "araea" U+119E and U+318D that MFDS PDFs use as a middle dot become "·")
2. drop running headers/footers: lines in the first/last 3 lines of a page that repeat (digits
   ignored) on at least 40% of pages, plus bare page numbers ("13", "- 7 -", "Page 3/43")
3. drop table-of-contents lines (dot leaders)
4. find heading candidates (`headings.detect_heading`: numbered, appendix, table captions) and
   keep only numbered headings that form a consistent chain (`headings.consistent_headings`:
   section numbers quoted in an amendment table or a cross-reference are body text)
5. split into sections at the kept headings; a section keeps the pages it spans as
   (char offset -> page number) so every chunk can cite its page
"""

import logging
import re
import unicodedata
from collections import Counter
from dataclasses import replace
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import DependencyError, FileNotDecryptedError, PdfReadError

from app.services.document_types import ExtractionError, Section
from app.services.headings import (
    Heading,
    SectionPath,
    consistent_headings,
    detect_heading,
    heading_continuation,
    is_toc_line,
)

logging.getLogger("pypdf").setLevel(logging.ERROR)  # "Ignoring wrong pointing object" noise


def _register_korean_unicode_cmaps() -> None:
    """pypdf 6.x knows the UTF-16 CMaps of the CNS/GB/JIS collections but not Korea1.

    UniKS-UTF16-H/V are Unicode CMaps whose character codes *are* UTF-16BE (Adobe TN #5094), so
    they decode exactly like UniCNS-UTF16-H. PDFs written with a non-embedded Korean CID font
    (e.g. the toy protocol made by scripts/generate_sample_pdf.py) use them.
    """
    try:
        from pypdf import _cmap
    except ImportError:  # pragma: no cover - pypdf layout changed; extraction degrades only
        return
    table = getattr(_cmap, "_predefined_cmap", None)
    if isinstance(table, dict):
        for name in ("/UniKS-UTF16-H", "/UniKS-UTF16-V"):
            table.setdefault(name, "utf-16-be")


_register_korean_unicode_cmaps()

_EDGE_LINES = 3
_REPEAT_RATIO = 0.4
_PAGE_NUMBER_RE = re.compile(
    r"^\s*(?:[-–—]\s*\d{1,4}\s*[-–—]|\d{1,4}|page\s+\d+(?:\s*(?:/|of)\s*\d+)?|\d+\s*/\s*\d+)\s*$",
    re.IGNORECASE,
)
_DIGITS_RE = re.compile(r"\d+")
# NUL bytes occur in some sponsor PDFs' text layer (an SAP of the private corpus); PostgreSQL
# text columns reject them ("invalid byte sequence for encoding UTF8: 0x00").
_CHAR_FIXES = str.maketrans({"ᆞ": "·", "ㆍ": "·", " ": " ", "\x00": None})


def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFC", text).translate(_CHAR_FIXES)


def _edge_key(line: str) -> str:
    return _DIGITS_RE.sub("#", " ".join(line.split()).lower())


def strip_running_lines(pages: list[list[str]]) -> list[list[str]]:
    """Remove repeated header/footer lines and bare page numbers from each page's lines."""
    counts: Counter[str] = Counter()
    for lines in pages:
        content = [ln for ln in lines if ln.strip()]
        edges = {_edge_key(ln) for ln in content[:_EDGE_LINES] + content[-_EDGE_LINES:]}
        counts.update(edges)
    threshold = max(3, int(len(pages) * _REPEAT_RATIO))
    repeated = {key for key, n in counts.items() if n >= threshold and key.strip()}

    cleaned: list[list[str]] = []
    for lines in pages:
        content = [ln for ln in lines if ln.strip()]
        n = len(content)

        def at_edge(i: int, n: int = n) -> bool:
            return i < _EDGE_LINES or i >= n - _EDGE_LINES

        cleaned.append(
            [
                ln
                for i, ln in enumerate(content)
                if not _PAGE_NUMBER_RE.match(ln) and not (at_edge(i) and _edge_key(ln) in repeated)
            ]
        )
    return cleaned


def read_pdf_pages(path: Path) -> list[str]:
    try:
        reader = PdfReader(path)
    except (DependencyError, FileNotDecryptedError) as exc:
        # pypdf tries the empty password while opening; AES needs the optional `cryptography`
        # package, which we do not ship: an AES-encrypted PDF is reported as encrypted.
        raise ExtractionError("ENCRYPTED_PDF", "PDF is encrypted") from exc
    except (PdfReadError, OSError, ValueError) as exc:
        raise ExtractionError("CORRUPTED_FILE", f"Cannot open PDF: {exc}") from exc
    if reader.is_encrypted:
        try:
            if not reader.decrypt(""):
                raise ExtractionError("ENCRYPTED_PDF", "PDF is encrypted")
        except (FileNotDecryptedError, DependencyError, NotImplementedError) as exc:
            raise ExtractionError("ENCRYPTED_PDF", "PDF is encrypted") from exc
    try:
        return [normalize_text(page.extract_text() or "") for page in reader.pages]
    except (FileNotDecryptedError, DependencyError) as exc:
        raise ExtractionError("ENCRYPTED_PDF", "PDF is encrypted") from exc
    except Exception as exc:  # pypdf raises many types on damaged content streams
        raise ExtractionError("CORRUPTED_FILE", f"Cannot read PDF: {exc}") from exc


_TOC_PAGE_MIN_LINES = 3


def sections_from_pages(pages: list[str]) -> list[Section]:
    """Heading-aware sections over the cleaned pages; each keeps its page offsets."""
    page_lines = strip_running_lines([p.splitlines() for p in pages])
    # Contents pages: drop the whole page, not only the dot-leader lines (wrapped TOC entries
    # without a leader would otherwise become bogus headings).
    page_lines = [
        [] if sum(is_toc_line(ln) for ln in lines) >= _TOC_PAGE_MIN_LINES else lines
        for lines in page_lines
    ]
    flat = [(page_no, ln) for page_no, lines in enumerate(page_lines, start=1) for ln in lines]

    # Pass 1: heading candidates (a wrapped heading consumes its continuation line).
    candidates: list[tuple[int, int, Heading]] = []  # (first line, lines consumed, heading)
    i = 0
    while i < len(flat):
        line = flat[i][1]
        if is_toc_line(line):
            i += 1
            continue
        next_line = flat[i + 1][1] if i + 1 < len(flat) else None
        heading = detect_heading(line, next_line)
        if heading is None:
            i += 1
            continue
        consumed = 1
        if next_line is not None and (extra := heading_continuation(heading, next_line)):
            heading = replace(heading, text=f"{heading.text} {extra}")
            consumed = 2
        candidates.append((i, consumed, heading))
        i += consumed
    # Pass 2: section numbers quoted in tables / cross-references are not headings.
    keep = consistent_headings([h for _, _, h in candidates])
    headings_at = {
        start: (consumed, h)
        for (start, consumed, h), kept in zip(candidates, keep, strict=True)
        if kept
    }

    path = SectionPath()
    sections: list[Section] = []
    buffer: list[str] = []
    spans: list[tuple[int, int]] = []
    size = 0

    def flush() -> None:
        nonlocal size
        joined = "\n".join(buffer)
        text = joined.strip()
        if text:
            lead = len(joined) - len(joined.lstrip())
            shifted = tuple((max(0, off - lead), page) for off, page in spans)
            sections.append(
                Section(
                    text=text,
                    page_number=shifted[0][1],
                    section_title=path.title(),
                    page_spans=shifted,
                )
            )
        buffer.clear()
        spans.clear()
        size = 0

    i = 0
    while i < len(flat):
        page_no, line = flat[i]
        if i in headings_at:
            consumed, heading = headings_at[i]
            i += consumed
            flush()
            path.push(heading)
            continue
        i += 1
        if is_toc_line(line):
            continue
        if not spans or spans[-1][1] != page_no:
            spans.append((size, page_no))
        buffer.append(line.rstrip())
        size += len(line.rstrip()) + 1
    flush()
    return sections


def extract_pdf(path: Path) -> list[Section]:
    pages = read_pdf_pages(path)
    if not any(p.strip() for p in pages):
        raise ExtractionError(
            "NO_EXTRACTABLE_TEXT", "PDF has no text layer (scanned PDF / OCR is out of scope)"
        )
    return sections_from_pages(pages)
