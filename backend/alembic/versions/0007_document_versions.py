"""documents: edition metadata (doc_family, version_*, is_latest)

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-11

Existing rows are filled with the defaults (no family, source 'none', is_latest = true): nothing
is hidden and no re-indexing is needed. The next index run of a corpus derives the editions
(`.corpus.yaml` `versions:` or the file name) and recomputes `is_latest` per corpus.
`version_superseded` keeps the manifest's `superseded: true` so that recomputation does not need
the manifest again.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("doc_family", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("version_label", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("version_date", sa.Date(), nullable=True))
    op.add_column(
        "documents",
        sa.Column("version_source", sa.Text(), nullable=False, server_default="none"),
    )
    op.add_column(
        "documents",
        sa.Column("version_superseded", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "documents",
        sa.Column("is_latest", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    for column in (
        "is_latest",
        "version_superseded",
        "version_source",
        "version_date",
        "version_label",
        "doc_family",
    ):
        op.drop_column("documents", column)
