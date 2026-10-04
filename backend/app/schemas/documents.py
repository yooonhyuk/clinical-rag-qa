import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.common import CamelModel


class DocumentOut(CamelModel):
    id: uuid.UUID
    file_name: str
    file_path: str
    file_type: str
    status: str
    chunk_count: int
    error_type: str | None = None
    error_message: str | None = None
    created_at: datetime
    indexed_at: datetime | None = None


class DocumentListResponse(CamelModel):
    documents: list[DocumentOut]


class IndexRequest(CamelModel):
    path: str | None = Field(default=None, description="Folder to index. Defaults to RAW_DOCS_PATH")


class IndexResponse(CamelModel):
    job_id: uuid.UUID
    status: str
    total: int
    indexed: int
    failed: int
    skipped_duplicate: int
    details: list[dict[str, Any]]
