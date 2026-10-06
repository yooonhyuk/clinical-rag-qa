"""Section-aware character chunking with overlap (~1000 chars, ~150 overlap).

Extractors already split documents at headings (Markdown `#`, numbered PDF headings such as
"4.2.1" / "Ⅳ." / "제3장", JATS `<sec>`, HTML `<h1..6>`, one section per table), and a chunk
never spans two sections. Inside a section, cuts prefer paragraph/line/sentence boundaries, so
table rows (one row per line) are not cut in half unless a single row exceeds the size.
For sections that cross pages, each chunk cites the page where it starts.
"""

from dataclasses import dataclass

from app.services.document_types import Section


@dataclass(frozen=True, slots=True)
class ChunkData:
    chunk_index: int
    text: str
    page_number: int | None
    section_title: str | None


_BREAK_CHARS = ("\n\n", "\n", ". ", "다. ", " ")


def _split(text: str, size: int, overlap: int) -> list[tuple[int, str]]:
    """(start offset, piece) pairs."""
    if len(text) <= size:
        return [(0, text)]
    pieces: list[tuple[int, str]] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            # Prefer to cut at a natural boundary in the last 20% of the window.
            window_floor = start + int(size * 0.8)
            for brk in _BREAK_CHARS:
                pos = text.rfind(brk, window_floor, end)
                if pos != -1:
                    end = pos + len(brk)
                    break
        raw = text[start:end]
        piece = raw.strip()
        if piece:
            pieces.append((start + len(raw) - len(raw.lstrip()), piece))
        if end >= len(text):
            break
        start = max(_overlap_start(text, end - overlap, end), start + 1)
    return pieces


def _overlap_start(text: str, floor: int, end: int) -> int:
    """Start the overlap at a line (or word) boundary so a table row is not cut mid-cell."""
    floor = max(floor, 0)
    if (pos := text.find("\n", floor, end)) != -1 and pos + 1 < end:
        return pos + 1
    if (pos := text.find(" ", floor, end)) != -1 and pos + 1 < end:
        return pos + 1
    return floor


def chunk_sections(
    sections: list[Section], *, size: int = 1000, overlap: int = 150
) -> list[ChunkData]:
    """Chunk each section independently so a chunk never spans two headings.

    The section title (heading path) is prepended to the chunk text so it also contributes to
    the embedding. `page_number` is the page where the chunk starts.
    """
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    chunks: list[ChunkData] = []
    for section in sections:
        for offset, piece in _split(section.text, size, overlap):
            text = f"[{section.section_title}]\n{piece}" if section.section_title else piece
            chunks.append(
                ChunkData(
                    chunk_index=len(chunks),
                    text=text,
                    page_number=section.page_at(offset),
                    section_title=section.section_title,
                )
            )
    return chunks
