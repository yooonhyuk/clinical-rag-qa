import uuid
from typing import Any

from sqlalchemy import Integer, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class AskLog(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "ask_logs"

    question: Mapped[str] = mapped_column(Text)
    retrieved_chunk_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    answer: Mapped[str] = mapped_column(Text)
    sources: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    retrieval_ms: Mapped[int] = mapped_column(Integer)
    generation_ms: Mapped[int] = mapped_column(Integer)
