import uuid
from datetime import date

from pydantic import Field

from app.schemas.common import CamelModel


class QuestionRequest(CamelModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    file_type: str | None = Field(default=None, pattern="^(md|txt|pdf|xml|html|docx|xlsx)$")
    # Restrict retrieval to one corpus (documents.corpus, e.g. "toy" / "public"). None = all.
    corpus: str | None = Field(default=None, max_length=100)
    # Search reads only the latest edition of each document by default (documents.is_latest);
    # True also searches editions a newer one replaced (SEARCH_LATEST_ONLY=false does it for all).
    include_superseded: bool = False


class SourceOut(CamelModel):
    chunk_id: uuid.UUID
    file_name: str
    page_number: int | None
    section_title: str | None
    chunk_index: int
    score: float
    rerank_score: float | None = None
    version_label: str | None = None
    version_date: date | None = None
    is_latest: bool = True


class LatencyOut(CamelModel):
    retrieval: int
    generation: int


class LLMUsageOut(CamelModel):
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None


class AskResponse(CamelModel):
    answer: str
    sources: list[SourceOut]
    refused: bool
    refusal_reason: str | None
    # answered from part of the evidence (docs/issues/007): show `caveat` next to the answer
    partial: bool = False
    caveat: str | None = None
    # old editions were searched and one of them is cited: names them (UI shows it under the answer)
    superseded_warning: str | None = None
    citation_mode: str
    latency_ms: LatencyOut
    llm: LLMUsageOut | None = None


class RetrievedChunkOut(CamelModel):
    chunk_id: uuid.UUID
    text: str
    file_name: str
    score: float
    metadata: dict[str, object]


class RetrieveResponse(CamelModel):
    chunks: list[RetrievedChunkOut]
    retrieval_ms: int
