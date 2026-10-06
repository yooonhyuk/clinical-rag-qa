"""documents.corpus: which corpus (toy / public / private / ...) a document belongs to

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-07

Nullable, no backfill: rows indexed before 0005 keep corpus = NULL and are still searched when
no corpus filter is given (the API default), so existing deployments behave exactly as before.
The indexer fills it from the folder's `.corpus.yaml` `name:` (or the folder name).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("corpus", sa.Text(), nullable=True))
    op.create_index("documents_corpus_idx", "documents", ["corpus"])


def downgrade() -> None:
    op.drop_index("documents_corpus_idx", table_name="documents")
    op.drop_column("documents", "corpus")
