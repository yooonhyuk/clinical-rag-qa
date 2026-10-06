"""Text extraction dispatch: Markdown / TXT / text-PDF / JATS XML / HTML.

All functions are blocking (run via `asyncio.to_thread`). Format-specific extractors live in
pdf_extractor (pypdf), jats_extractor and html_extractor (standard library only).
"""

import re
from pathlib import Path

from app.services.document_types import ExtractionError, Section
from app.services.html_extractor import extract_html
from app.services.jats_extractor import extract_jats
from app.services.pdf_extractor import extract_pdf

__all__ = ["ExtractionError", "Section", "extract", "extract_markdown", "extract_text"]

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
        case "xml":
            sections = extract_jats(path)
        case "html":
            sections = extract_html(path)
        case _:
            raise ExtractionError("UNSUPPORTED_FILE_TYPE", f"Unsupported file type: {file_type}")
    if not sections:
        raise ExtractionError("EMPTY_DOCUMENT", "Document contains no text")
    return sections
