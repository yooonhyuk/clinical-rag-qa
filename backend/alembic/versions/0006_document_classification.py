"""documents.classification: corpus classification recorded at index time

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-09

Nullable, no backfill. The indexer copies the folder's `.corpus.yaml` `classification:` into
each document row. In external-LLM mode retrieval reads only documents whose classification is
allowed (llm_guardrail.ALLOWED_CLASSIFICATIONS); NULL counts as local-only, so rows indexed
before 0006 are never sent to an external provider until they are re-indexed.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("classification", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "classification")
