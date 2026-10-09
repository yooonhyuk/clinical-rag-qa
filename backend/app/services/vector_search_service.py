"""Chunk search: pgvector cosine search, optionally fused with a pg_trgm lexical channel.

Hybrid mode was added as a mitigation for nomic-embed-text, whose English WordPiece vocabulary
maps every Hangul word to `[UNK]`, so Korean questions embed to almost the same vector and
cosine ranking alone degenerates (docs/issues/001). The default model is now the multilingual
bge-m3 and hybrid is opt-in (HYBRID_SEARCH=true). `word_similarity` (pg_trgm) works on Hangul
character trigrams, and the two rankings are merged with Reciprocal Rank Fusion.
`score` always stays the cosine similarity (it drives the NO_EVIDENCE threshold).

With `embedding_model` set, only chunks embedded by that model are searched: vectors of
different models are not comparable (see embedding_schema).

Approximate vs exact (docs/issues/009): the HNSW index returns `hnsw.ef_search` (default 40)
candidates and only then applies the WHERE filters (corpus, model, classification). When the
filtered corpus is a minority of the table, fewer than top_k - or different - chunks survive.
`exact=True` disables index scans for this transaction (sequential scan, exact cosine order);
`iterative_scan` turns on pgvector 0.8 iterative index scans, which keep scanning the graph
until enough rows pass the filter; `ef_search` widens the HNSW candidate list (recall).

Whether the index is used at all is the planner's choice: measured on 2026-10-09, a corpus
filter that keeps a minority of a ~10k-chunk table gives a sequential scan + sort (exact),
while a DB holding (almost) only that corpus gives an HNSW index scan (approximate), whose
top-k then depends on the graph, i.e. on insertion order (docs/issues/009).
"""

import uuid
from collections.abc import Collection
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import Select, func, select, text
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
    rerank_score: float | None = None  # cross-encoder relevance (0..1), reranker only


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
    embedding_model: str | None = None,
    corpus: str | None = None,
    classifications: Collection[str] | None = None,
    exact: bool = False,
    iterative_scan: Literal["off", "relaxed_order", "strict_order"] = "off",
    ef_search: int | None = None,
) -> list[RetrievedChunk]:
    """Vector-only search, or hybrid (vector + pg_trgm, RRF) when `query_text` is given.

    `classifications` (external-LLM mode) keeps only documents with one of these corpus
    classifications; documents without one are excluded.
    """
    if exact:
        await session.execute(text("SET LOCAL enable_indexscan = off"))
    elif iterative_scan != "off":
        if iterative_scan not in ("relaxed_order", "strict_order"):
            raise ValueError(f"invalid hnsw.iterative_scan: {iterative_scan!r}")
        await session.execute(text(f"SET LOCAL hnsw.iterative_scan = {iterative_scan}"))
    if ef_search is not None and not exact:
        await session.execute(text(f"SET LOCAL hnsw.ef_search = {int(ef_search)}"))
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
    if embedding_model is not None:
        stmt = stmt.where(Chunk.embedding_model == embedding_model)
    if corpus is not None:
        stmt = stmt.where(Document.corpus == corpus)
    if classifications is not None:
        stmt = stmt.where(Document.classification.in_(sorted(classifications)))

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
