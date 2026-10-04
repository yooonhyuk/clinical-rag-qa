"""ask_logs: refusal reason, LLM provider/model and token usage

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = (
    ("refusal_reason", sa.Text()),
    ("llm_provider", sa.Text()),
    ("llm_model", sa.Text()),
    ("input_tokens", sa.Integer()),
    ("output_tokens", sa.Integer()),
)


def upgrade() -> None:
    for name, type_ in _COLUMNS:
        op.add_column("ask_logs", sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    for name, _ in reversed(_COLUMNS):
        op.drop_column("ask_logs", name)
