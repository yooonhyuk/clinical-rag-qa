"""embedding model tracking + configurable vector dimension (default bge-m3, 1024)

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-06

- `chunks.embedding_model` (NOT NULL), `documents.embedding_model`, `index_jobs.embedding_model`
  record which Ollama model produced the vectors, so mixed-model state is detectable
  (/api/health) and the pipeline re-embeds documents of another model.
- `chunks.embedding` is resized to the configured dimension (EMBEDDING_DIM, or the known
  dimension of OLLAMA_EMBEDDING_MODEL: bge-m3 = 1024). Vectors cannot be converted between
  models, so when the dimension changes ALL chunks are deleted, the HNSW index is recreated and
  documents are marked FAILED / REINDEX_REQUIRED -> run `/api/index` (or `make eval
  EVAL_ARGS=--reindex`) afterwards. Later model switches use `make reset-embeddings`, which runs
  the same `reset_embedding_column`.
- If the dimension already matches, existing chunks are kept but labelled `unknown` (the model
  that produced them was never recorded); health reports them and the next index re-embeds.

Downgrade restores vector(768) (revision 0001) and also clears every embedding.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.config import get_settings
from app.services.embedding_schema import column_dimension, reset_embedding_column

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = ("chunks", "documents", "index_jobs")
_PRE_0004_DIM = 768
UNKNOWN_MODEL = "unknown"


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(table, sa.Column("embedding_model", sa.Text(), nullable=True))

    bind = op.get_bind()
    dim = get_settings().embedding_dimension
    if column_dimension(bind) != dim:
        reset_embedding_column(bind, dim)
    else:
        backfill = sa.text("UPDATE chunks SET embedding_model = :m WHERE embedding_model IS NULL")
        op.execute(backfill.bindparams(m=UNKNOWN_MODEL))
    op.alter_column("chunks", "embedding_model", nullable=False)


def downgrade() -> None:
    bind = op.get_bind()
    if column_dimension(bind) != _PRE_0004_DIM:
        reset_embedding_column(bind, _PRE_0004_DIM)
    for table in reversed(_TABLES):
        op.drop_column(table, "embedding_model")
