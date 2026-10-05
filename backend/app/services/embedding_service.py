"""Concurrency-bounded embedding generation.

Chunks are processed in batches of `batch_size`; within a batch every chunk becomes one
`embed` call and the calls are awaited with `asyncio.gather`. A single `asyncio.Semaphore`
(shared by the whole app) caps how many requests are in flight to Ollama at any time, which
gives natural backpressure: when Ollama is slow, producers wait on the semaphore instead of
piling up requests (and memory) in front of it.
"""

import asyncio
from collections.abc import Sequence

from app.services.llm_types import EmbeddingClient, LLMError


class EmbeddingDimensionError(LLMError):
    def __init__(self, expected: int, actual: int) -> None:
        super().__init__(
            f"Embedding dimension mismatch: expected {expected}, got {actual}. "
            "Check OLLAMA_EMBEDDING_MODEL / EMBEDDING_DIM and the chunks.embedding column.",
            error_type="EMBEDDING_DIM_MISMATCH",
        )


class EmbeddingService:
    def __init__(
        self,
        client: EmbeddingClient,
        *,
        dimension: int,
        model: str = "unknown",
        concurrency: int = 4,
        batch_size: int = 16,
        query_prefix: str = "",
        document_prefix: str = "",
    ) -> None:
        self._client = client
        self._dimension = dimension
        self.model = model  # recorded on every chunk; vectors of different models never mix
        self._semaphore = asyncio.Semaphore(concurrency)
        self._batch_size = batch_size
        self._query_prefix = query_prefix
        self._document_prefix = document_prefix

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_query(self, text: str) -> list[float]:
        return await self._embed_one(self._query_prefix + text)

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            vectors.extend(
                await asyncio.gather(*(self._embed_one(self._document_prefix + t) for t in batch))
            )
        return vectors

    async def _embed_one(self, text: str) -> list[float]:
        async with self._semaphore:
            (vector,) = await self._client.embed([text])
        if len(vector) != self._dimension:
            raise EmbeddingDimensionError(self._dimension, len(vector))
        return vector
