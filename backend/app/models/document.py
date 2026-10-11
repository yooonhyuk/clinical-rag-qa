import enum
from datetime import date, datetime

from sqlalchemy import CHAR, Boolean, Date, DateTime, Index, Integer, Text, false, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class DocumentStatus(enum.StrEnum):
    DISCOVERED = "DISCOVERED"
    EXTRACTED = "EXTRACTED"
    CHUNKED = "CHUNKED"
    EMBEDDED = "EMBEDDED"
    INDEXED = "INDEXED"
    FAILED = "FAILED"
    SKIPPED_DUPLICATE = "SKIPPED_DUPLICATE"


class Document(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (Index("documents_corpus_idx", "corpus"),)

    file_name: Mapped[str] = mapped_column(Text)
    file_path: Mapped[str] = mapped_column(Text)
    file_type: Mapped[str] = mapped_column(Text)
    checksum: Mapped[str] = mapped_column(CHAR(64), unique=True)
    status: Mapped[str] = mapped_column(Text, default=DocumentStatus.DISCOVERED)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    error_type: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Embedding model of the current chunks; a different configured model triggers re-embedding.
    embedding_model: Mapped[str | None] = mapped_column(Text)
    # Corpus name (`.corpus.yaml` name:, else folder name): toy / public / private ...
    # NULL for rows indexed before Alembic 0005. Search can be restricted to one corpus.
    corpus: Mapped[str | None] = mapped_column(Text)
    # `.corpus.yaml` classification at index time (synthetic-sample / public-regulatory /
    # licensed-local-only ...). With an external LLM provider only allowed classes are searched;
    # NULL (no marker, or indexed before Alembic 0006) counts as local-only.
    classification: Mapped[str | None] = mapped_column(Text)
    # Edition (services/doc_versions.py, Alembic 0007). `doc_family` groups the editions of one
    # document inside a corpus; `is_latest` is recomputed per corpus after every index run and
    # search reads only latest editions by default. `version_source`: manifest | filename | none.
    doc_family: Mapped[str | None] = mapped_column(Text)
    version_label: Mapped[str | None] = mapped_column(Text)
    version_date: Mapped[date | None] = mapped_column(Date)
    version_source: Mapped[str] = mapped_column(Text, default="none", server_default="none")
    version_superseded: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    chunks: Mapped[list["Chunk"]] = relationship(  # noqa: F821
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )
