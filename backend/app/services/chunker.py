"""Fixed-size character chunking with overlap (MVP-1 policy: ~1000 chars, ~150 overlap)."""

from dataclasses import dataclass

from app.services.text_extractor import Section


@dataclass(frozen=True, slots=True)
class ChunkData:
    chunk_index: int
    text: str
    page_number: int | None
    section_title: str | None


_BREAK_CHARS = ("\n\n", "\n", ". ", "다. ", " ")


def _split(text: str, size: int, overlap: int) -> list[str]:
    if len(text) <= size:
        return [text]
    pieces: list[str] = []
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
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return pieces


def chunk_sections(
    sections: list[Section], *, size: int = 1000, overlap: int = 150
) -> list[ChunkData]:
    """Chunk each section independently so a chunk never spans two pages / headings.

    The section title is prepended to the chunk text so it also contributes to the embedding.
    """
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    chunks: list[ChunkData] = []
    for section in sections:
        for piece in _split(section.text, size, overlap):
            text = f"[{section.section_title}]\n{piece}" if section.section_title else piece
            chunks.append(
                ChunkData(
                    chunk_index=len(chunks),
                    text=text,
                    page_number=section.page_number,
                    section_title=section.section_title,
                )
            )
    return chunks
