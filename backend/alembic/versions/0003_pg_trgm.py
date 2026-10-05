"""pg_trgm extension for the hybrid (vector + lexical) retrieval channel

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-06

No trigram index is created: `word_similarity` ordering over the MVP corpus (< 100 documents)
is a cheap sequential scan. Add a GiST `gist_trgm_ops` index if the corpus grows.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
