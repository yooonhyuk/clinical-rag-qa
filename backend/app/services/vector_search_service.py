"""Chunk search: pgvector cosine search, optionally fused with a pg_trgm lexical channel.

Hybrid mode exists because the default embedding model (nomic-embed-text) has an English
WordPiece vocabulary: every Hangul word becomes `[UNK]`, so Korean questions embed to almost
the same vector and cosine ranking alone degenerates. `word_similarity` (pg_trgm) works on
Hangul character trigrams, and the two rankings are merged with Reciprocal Rank Fusion.
`score` always stays the cosine similarity (it drives the NO_EVIDENCE threshold).
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import Select, func, select
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
    lexical_score: float | None = None  # pg_trgm word_similarity(question, text), hybrid only


def _to_chunk(chunk: Chunk, file_name: str, score: float, lexical: float | None) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk.id,
        document_id=chunk.document_id,
        file_name=file_name,
        file_type=chunk.file_type,
        chunk_index=chunk.chunk_index,
        page_number=chunk.page_number,
        section_title=chunk.section_title,
        text=chunk.text,
        score=float(score),
        lexical_score=None if lexical is None else float(lexical),
    )


def rrf_fuse(rankings: list[list[uuid.UUID]], *, k: int = 60) -> list[uuid.UUID]:
    """Reciprocal Rank Fusion: sum of 1 / (k + rank) over every ranking an id appears in."""
    scores: dict[uuid.UUID, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=lambda item: scores[item], reverse=True)


async def search_chunks(
    session: AsyncSession,
    query_embedding: list[float],
    *,
    top_k: int,
    file_type: str | None = None,
    query_text: str | None = None,
    rrf_k: int = 60,
) -> list[RetrievedChunk]:
    """Vector-only search, or hybrid (vector + pg_trgm, RRF) when `query_text` is given."""
    distance = Chunk.embedding.cosine_distance(query_embedding)
    columns = [Chunk, Document.file_name, (1 - distance).label("score")]
    lexical = func.word_similarity(query_text, Chunk.text) if query_text else None
    if lexical is not None:
        columns.append(lexical.label("lexical"))

    stmt: Select = (
        select(*columns)
        .join(Document, Document.id == Chunk.document_id)
        .where(Document.status == DocumentStatus.INDEXED)
    )
    if file_type is not None:
        stmt = stmt.where(Chunk.file_type == file_type)

    if lexical is None:
        rows = (await session.execute(stmt.order_by(distance).limit(top_k))).all()
        return [_to_chunk(chunk, name, score, None) for chunk, name, score in rows]

    candidates = max(top_k * 4, 20)
    by_vector = (await session.execute(stmt.order_by(distance).limit(candidates))).all()
    by_lexical = (
        await session.execute(stmt.order_by(lexical.desc(), distance).limit(candidates))
    ).all()
    rows_by_id = {row[0].id: row for row in (*by_vector, *by_lexical)}
    fused = rrf_fuse([[row[0].id for row in by_vector], [row[0].id for row in by_lexical]], k=rrf_k)
    return [_to_chunk(*rows_by_id[chunk_id]) for chunk_id in fused[:top_k]]
