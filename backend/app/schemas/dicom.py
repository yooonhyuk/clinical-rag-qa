from typing import Any

from pydantic import Field

from app.schemas.common import CamelModel


class DicomAnalyzeRequest(CamelModel):
    file_path: str = Field(min_length=1)
    explain: bool = Field(default=True, description="Generate the LLM explanation")


class QAResult(CamelModel):
    passed: list[str]
    warnings: list[str]
    missing: list[str]


class DicomAnalyzeResponse(CamelModel):
    file_name: str
    summary: str
    summary_source: str
    tag_summary: dict[str, Any]
    privacy_warnings: list[str]
    missing_required_tags: list[str]
    qa_result: QAResult
    rule_source: str
    disclaimer: str


class DicomFileListResponse(CamelModel):
    files: list[str]
