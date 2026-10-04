"""pgvector cosine search over indexed chunks, with optional metadata filtering."""

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chunk, Document, DocumentStatus


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    file_name: str
    file_type: str
    chunk_index: int
    page_number: int | None
    section_title: str | None
    text: str
    score: float  # cosine similarity (1 - cosine distance)


async def search_chunks(
    session: AsyncSession,
    query_embedding: list[float],
    *,
    top_k: int,
    file_type: str | None = None,
) -> list[RetrievedChunk]:
    distance = Chunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(Chunk, Document.file_name, (1 - distance).label("score"))
        .join(Document, Document.id == Chunk.document_id)
        .where(Document.status == DocumentStatus.INDEXED)
        .order_by(distance)
        .limit(top_k)
    )
    if file_type is not None:
        stmt = stmt.where(Chunk.file_type == file_type)

    rows = (await session.execute(stmt)).all()
    return [
        RetrievedChunk(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            file_name=file_name,
            file_type=chunk.file_type,
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            section_title=chunk.section_title,
            text=chunk.text,
            score=float(score),
        )
        for chunk, file_name, score in rows
    ]
