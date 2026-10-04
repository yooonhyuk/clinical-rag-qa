import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import get_settings
from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

# The column dimension must match the embedding model. Changing it requires a migration.
EMBEDDING_DIM = get_settings().embedding_dim


class Chunk(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "chunks"
    __table_args__ = (
        Index(
            "chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("chunks_document_id_idx", "document_id"),
        Index("chunks_file_type_idx", "file_type"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    file_type: Mapped[str] = mapped_column(Text)
    page_number: Mapped[int | None] = mapped_column(Integer)
    section_title: Mapped[str | None] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))

    document: Mapped["Document"] = relationship(back_populates="chunks")  # noqa: F821
