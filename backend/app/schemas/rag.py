import uuid

from pydantic import Field

from app.schemas.common import CamelModel


class QuestionRequest(CamelModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    file_type: str | None = Field(default=None, pattern="^(md|txt|pdf|xml|html)$")
    # Restrict retrieval to one corpus (documents.corpus, e.g. "toy" / "public"). None = all.
    corpus: str | None = Field(default=None, max_length=100)


class SourceOut(CamelModel):
    chunk_id: uuid.UUID
    file_name: str
    page_number: int | None
    section_title: str | None
    chunk_index: int
    score: float
    rerank_score: float | None = None


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
