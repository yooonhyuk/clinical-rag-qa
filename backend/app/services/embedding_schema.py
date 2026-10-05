"""Embedding column management and model/dimension consistency checks.

Vectors produced by different embedding models live in unrelated spaces, even when the
dimensions happen to match. Switching models therefore always means *re-embedding*:

- different dimension -> `reset_embedding_column` (Alembic 0004 or `make reset-embeddings`)
  alters `chunks.embedding` to `vector(<dim>)`, deletes every chunk, recreates the HNSW index
  and marks the documents `FAILED / REINDEX_REQUIRED`, so the next `/api/index` re-embeds them.
- same dimension -> the indexing pipeline re-embeds every document whose `embedding_model`
  differs from the configured one; until then search only reads chunks of the configured model.

`/api/health` reports the column dimension, the models present in `chunks` and the number of
documents waiting for a reindex (`inspect_embedding_index` + `evaluate_embedding_index`).
"""

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import normalize_model_name

REINDEX_REQUIRED = "REINDEX_REQUIRED"
HNSW_INDEX = "chunks_embedding_hnsw"

_INSPECT_SQL = text(
    """
    SELECT
      (SELECT atttypmod FROM pg_attribute
        WHERE attrelid = 'chunks'::regclass AND attname = 'embedding') AS dim,
      (SELECT coalesce(array_agg(DISTINCT embedding_model), ARRAY[]::text[])
         FROM chunks) AS models,
      (SELECT count(*) FROM documents WHERE error_type = :reindex) AS pending
    """
)


@dataclass(frozen=True, slots=True)
class EmbeddingIndexState:
    column_dim: int | None
    chunk_models: Sequence[str]
    reindex_pending: int


def column_dimension(conn: Connection) -> int | None:
    """Declared dimension of chunks.embedding (pgvector stores it as the type modifier)."""
    value = conn.execute(
        text(
            "SELECT atttypmod FROM pg_attribute "
            "WHERE attrelid = 'chunks'::regclass AND attname = 'embedding'"
        )
    ).scalar()
    return None if value is None or value < 0 else int(value)


def reset_embedding_column(conn: Connection, dim: int) -> int:
    """Clear all embeddings and resize chunks.embedding to `dim`. Returns documents to reindex.

    Destructive by design: there is no way to convert vectors between models.
    """
    if dim <= 0:
        raise ValueError(f"invalid embedding dimension: {dim}")
    conn.execute(text(f"DROP INDEX IF EXISTS {HNSW_INDEX}"))
    conn.execute(text("DELETE FROM chunks"))
    pending = conn.execute(
        text(
            "UPDATE documents SET status = 'FAILED', chunk_count = 0, embedding_model = NULL, "
            "indexed_at = NULL, error_type = :reindex, "
            "error_message = 'embedding model/dimension changed: run /api/index to re-embed' "
            "WHERE status <> 'FAILED' OR error_type = :reindex"
        ),
        {"reindex": REINDEX_REQUIRED},
    ).rowcount
    conn.execute(text(f"ALTER TABLE chunks ALTER COLUMN embedding TYPE vector({int(dim)})"))
    conn.execute(
        text(f"CREATE INDEX {HNSW_INDEX} ON chunks USING hnsw (embedding vector_cosine_ops)")
    )
    return int(pending or 0)


async def inspect_embedding_index(session: AsyncSession) -> EmbeddingIndexState:
    row = (await session.execute(_INSPECT_SQL, {"reindex": REINDEX_REQUIRED})).one()
    dim, models, pending = row
    return EmbeddingIndexState(
        column_dim=None if dim is None or dim < 0 else int(dim),
        chunk_models=list(models or []),
        reindex_pending=int(pending or 0),
    )


def evaluate_embedding_index(
    state: EmbeddingIndexState, *, model: str, dim: int
) -> tuple[bool, str]:
    """(ok, detail) for /api/health. Not ok = search results would be wrong or incomplete."""
    problems: list[str] = []
    if state.column_dim != dim:
        problems.append(
            f"column is vector({state.column_dim}) but {model} produces {dim}-dim vectors "
            "-> make reset-embeddings + reindex"
        )
    wanted = normalize_model_name(model)
    foreign = sorted({m for m in state.chunk_models if normalize_model_name(m) != wanted})
    if foreign:
        problems.append(
            f"chunks embedded with {', '.join(foreign)} (configured: {model}; "
            "they are excluded from search) -> reindex"
        )
    if state.reindex_pending:
        problems.append(f"{state.reindex_pending} document(s) need reindex")
    if problems:
        return False, "; ".join(problems)
    if not state.chunk_models:
        return True, f"{model} / vector({dim}), no chunks indexed yet"
    return True, f"{model} / vector({dim})"
