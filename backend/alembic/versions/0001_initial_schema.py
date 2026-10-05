"""initial schema: documents, chunks(pgvector), dicom_files, index_jobs, ask_logs

Revision ID: 0001
Revises:
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# nomic-embed-text = 768 (the original default). Since 0004 the dimension follows the configured
# embedding model (bge-m3 = 1024); see app.services.embedding_schema.
EMBEDDING_DIM = 768


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_type", sa.Text(), nullable=False),
        sa.Column("checksum", sa.CHAR(64), nullable=False, unique=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_type", sa.Text()),
        sa.Column("error_message", sa.Text()),
        _created_at(),
        sa.Column("indexed_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "chunks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "document_id",
            sa.Uuid(),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("file_type", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer()),
        sa.Column("section_title", sa.Text()),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        _created_at(),
    )
    op.create_index(
        "chunks_embedding_hnsw",
        "chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index("chunks_document_id_idx", "chunks", ["document_id"])
    op.create_index("chunks_file_type_idx", "chunks", ["file_type"])

    op.create_table(
        "dicom_files",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("checksum", sa.CHAR(64), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("tags", postgresql.JSONB(), nullable=False),
        sa.Column("privacy_warnings", postgresql.JSONB(), nullable=False),
        sa.Column("missing_required_tags", postgresql.JSONB(), nullable=False),
        _created_at(),
    )

    op.create_table(
        "index_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("indexed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_duplicate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("details", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "ask_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("retrieved_chunk_ids", postgresql.ARRAY(sa.Uuid()), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("sources", postgresql.JSONB(), nullable=False),
        sa.Column("retrieval_ms", sa.Integer(), nullable=False),
        sa.Column("generation_ms", sa.Integer(), nullable=False),
        _created_at(),
    )


def downgrade() -> None:
    op.drop_table("ask_logs")
    op.drop_table("index_jobs")
    op.drop_table("dicom_files")
    op.drop_index("chunks_file_type_idx", table_name="chunks")
    op.drop_index("chunks_document_id_idx", table_name="chunks")
    op.drop_index("chunks_embedding_hnsw", table_name="chunks")
    op.drop_table("chunks")
    op.drop_table("documents")
