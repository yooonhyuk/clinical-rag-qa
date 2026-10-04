"""Provider-neutral LLM types.

Generation is pluggable (local Ollama by default, Claude API as an explicit opt-in), while
embeddings always stay on the local Ollama server. Both generation providers return the same
`GroundedAnswer` structure, so the RAG layer does not care which one produced it.
"""

from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel, Field


class LLMError(RuntimeError):
    """Raised when an LLM provider cannot fulfil a request (after retries)."""

    def __init__(self, message: str, *, error_type: str = "LLM_ERROR") -> None:
        super().__init__(message)
        self.error_type = error_type


class StructuredOutputError(LLMError):
    """The model answered, but not with JSON matching the schema. `raw_text` keeps the answer."""

    def __init__(self, message: str, *, raw_text: str, usage: "LLMUsage") -> None:
        super().__init__(message, error_type="LLM_BAD_OUTPUT")
        self.raw_text = raw_text
        self.usage = usage


class ModelRefusalError(LLMError):
    """The provider declined the request (e.g. Claude `stop_reason == "refusal"`)."""

    def __init__(self, message: str, *, usage: "LLMUsage") -> None:
        super().__init__(message, error_type="LLM_REFUSAL")
        self.usage = usage


@dataclass(frozen=True, slots=True)
class LLMUsage:
    provider: str
    model: str
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class GenerationResult:
    text: str
    usage: LLMUsage


class GroundedAnswer(BaseModel):
    """Structured RAG answer returned by every generation provider."""

    answer: str = Field(description="Answer in Korean, with [n] markers for the context used")
    cited_context_ids: list[int] = Field(description="1-based ids of the context blocks used")
    insufficient_evidence: bool = Field(description="True if the context does not answer it")


# Hand-written so it satisfies strict JSON-schema rules on both providers
# (every property required, additionalProperties: false, no titles/defaults).
GROUNDED_ANSWER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "cited_context_ids": {"type": "array", "items": {"type": "integer"}},
        "insufficient_evidence": {"type": "boolean"},
    },
    "required": ["answer", "cited_context_ids", "insufficient_evidence"],
    "additionalProperties": False,
}


class EmbeddingClient(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class GenerationClient(Protocol):
    provider: str
    model: str

    async def generate(self, prompt: str, *, system: str | None = None) -> GenerationResult: ...

    async def generate_answer(
        self, prompt: str, *, system: str | None = None
    ) -> tuple[GroundedAnswer, LLMUsage]: ...
