from typing import Any

from sqlalchemy import CHAR, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class DicomFile(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "dicom_files"

    file_name: Mapped[str] = mapped_column(Text)
    file_path: Mapped[str] = mapped_column(Text)
    checksum: Mapped[str] = mapped_column(CHAR(64))
    status: Mapped[str] = mapped_column(Text)  # ANALYZED / FAILED
    tags: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    privacy_warnings: Mapped[list[str]] = mapped_column(JSONB, default=list)
    missing_required_tags: Mapped[list[str]] = mapped_column(JSONB, default=list)
