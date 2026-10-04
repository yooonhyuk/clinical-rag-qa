"""Text extraction for Markdown / TXT / text-PDF. All functions are blocking (run via to_thread)."""

import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf


@dataclass(frozen=True, slots=True)
class Section:
    """A contiguous piece of a document with its location metadata."""

    text: str
    page_number: int | None = None
    section_title: str | None = None


class ExtractionError(Exception):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")


def extract_markdown(content: str) -> list[Section]:
    """Split Markdown by headings; each heading becomes the section title of the text below it."""
    sections: list[Section] = []
    title: str | None = None
    buffer: list[str] = []
    in_fence = False

    def flush() -> None:
        text = "\n".join(buffer).strip()
        if text:
            sections.append(Section(text=text, section_title=title))
        buffer.clear()

    for line in content.splitlines():
        if _FENCE_RE.match(line):
            in_fence = not in_fence
        match = None if in_fence else _HEADING_RE.match(line)
        if match:
            flush()
            title = match.group(2).strip()
            continue
        buffer.append(line)
    flush()
    return sections


def extract_text(content: str) -> list[Section]:
    text = content.strip()
    return [Section(text=text)] if text else []


def extract_pdf(path: Path) -> list[Section]:
    try:
        doc = pymupdf.open(path)
    except Exception as exc:  # PyMuPDF raises several exception types for broken files
        raise ExtractionError("CORRUPTED_FILE", f"Cannot open PDF: {exc}") from exc
    with doc:
        if doc.needs_pass:
            raise ExtractionError("ENCRYPTED_PDF", "PDF is encrypted")
        sections = [
            Section(text=text, page_number=index + 1)
            for index, page in enumerate(doc)
            if (text := page.get_text("text").strip())
        ]
    if not sections:
        raise ExtractionError(
            "NO_EXTRACTABLE_TEXT", "PDF has no text layer (scanned PDF / OCR is out of scope)"
        )
    return sections


def _read_text_file(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp949"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ExtractionError("CORRUPTED_FILE", "Cannot decode text file as UTF-8 or CP949")


def extract(path: Path, file_type: str) -> list[Section]:
    """Extract sections from a file. Raises `ExtractionError` with a typed reason on failure."""
    match file_type:
        case "md":
            sections = extract_markdown(_read_text_file(path))
        case "txt":
            sections = extract_text(_read_text_file(path))
        case "pdf":
            sections = extract_pdf(path)
        case _:
            raise ExtractionError("UNSUPPORTED_FILE_TYPE", f"Unsupported file type: {file_type}")
    if not sections:
        raise ExtractionError("EMPTY_DOCUMENT", "Document contains no text")
    return sections
