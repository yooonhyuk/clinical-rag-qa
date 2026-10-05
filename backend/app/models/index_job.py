from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin, utcnow


class IndexJob(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "index_jobs"

    status: Mapped[str] = mapped_column(Text, default="RUNNING")  # RUNNING / COMPLETED / FAILED
    total: Mapped[int] = mapped_column(Integer, default=0)
    indexed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    skipped_duplicate: Mapped[int] = mapped_column(Integer, default=0)
    # Per-file outcome (incl. SKIPPED_DUPLICATE and failure reasons). Added on top of the plan's
    # schema because a duplicate cannot get its own `documents` row (checksum is UNIQUE).
    details: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    embedding_model: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
