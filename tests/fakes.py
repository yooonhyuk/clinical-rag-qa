"""Test doubles: no test talks to a real Ollama or Claude API."""

import hashlib
import math
import re
import uuid
from typing import Any

from app.services.llm_types import GenerationResult, GroundedAnswer, LLMUsage
from app.services.vector_search_service import RetrievedChunk

DIM = 768
_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]+")


def hash_embedding(text: str, dim: int = DIM) -> list[float]:
    """Deterministic bag-of-ngrams embedding so retrieval behaves sensibly in tests."""
    vec = [0.0] * dim
    for token in _TOKEN_RE.findall(text.lower()):
        grams = [token] + [token[i : i + 2] for i in range(len(token) - 1)]
        for gram in grams:
            h = int(hashlib.md5(gram.encode()).hexdigest(), 16)
            vec[h % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class FakeOllama:
    """Implements EmbeddingClient + GenerationClient + list_models."""

    provider = "ollama"

    def __init__(
        self,
        *,
        answer: GroundedAnswer | None = None,
        text: str = "fake explanation",
        dim: int = DIM,
        fail_embed_after: int | None = None,
    ) -> None:
        self.model = "fake-gemma"
        self.answer = answer or GroundedAnswer(
            answer="파일 형식과 필수 태그를 확인합니다 [1].",
            cited_context_ids=[1],
            insufficient_evidence=False,
        )
        self.text = text
        self.dim = dim
        self.fail_embed_after = fail_embed_after
        self.embed_calls = 0
        self.generate_calls: list[str] = []

    async def embed(self, texts: list[str]) -> list[list[float]]:
        from app.services.ollama_client import OllamaError

        self.embed_calls += 1
        if self.fail_embed_after is not None and self.embed_calls > self.fail_embed_after:
            raise OllamaError("boom", error_type="OLLAMA_UNAVAILABLE")
        return [hash_embedding(t, self.dim) for t in texts]

    def _usage(self) -> LLMUsage:
        return LLMUsage(self.provider, self.model, latency_ms=1, input_tokens=10, output_tokens=5)

    async def generate(self, prompt: str, *, system: str | None = None) -> GenerationResult:
        self.generate_calls.append(prompt)
        return GenerationResult(text=self.text, usage=self._usage())

    async def generate_answer(
        self, prompt: str, *, system: str | None = None
    ) -> tuple[GroundedAnswer, LLMUsage]:
        self.generate_calls.append(prompt)
        return self.answer, self._usage()

    async def list_models(self) -> list[str]:
        return ["fake-gemma:latest", "nomic-embed-text:latest"]


def make_chunk(
    file_name: str = "dicom-upload-guide.md", score: float = 0.8, **kw: Any
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=kw.get("chunk_id", uuid.uuid4()),
        document_id=kw.get("document_id", uuid.uuid4()),
        file_name=file_name,
        file_type=kw.get("file_type", "md"),
        chunk_index=kw.get("chunk_index", 0),
        page_number=kw.get("page_number"),
        section_title=kw.get("section_title", "Upload Validation"),
        text=kw.get("text", "파일 형식, 필수 태그, Subject ID 매핑을 확인한다."),
        score=score,
    )


class FakeSession:
    """Minimal AsyncSession stand-in that records added objects."""

    def __init__(self) -> None:
        self.added: list[Any] = []
        self.commits = 0

    async def __aenter__(self) -> "FakeSession":
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        return None

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        return None

    async def scalar(self, *args: Any, **kwargs: Any) -> Any:
        return "0.8.0"

    async def scalars(self, *args: Any, **kwargs: Any) -> Any:
        class _Result:
            def all(self) -> list[Any]:
                return []

        return _Result()


class FakeSessionFactory:
    def __init__(self) -> None:
        self.sessions: list[FakeSession] = []

    def __call__(self) -> FakeSession:
        session = FakeSession()
        self.sessions.append(session)
        return session

    @property
    def added(self) -> list[Any]:
        return [obj for s in self.sessions for obj in s.added]
