import asyncio

import pytest

from app.services.embedding_service import EmbeddingDimensionError, EmbeddingService


class SlowEmbedder:
    def __init__(self, dim: int = 4) -> None:
        self.dim = dim
        self.in_flight = 0
        self.max_in_flight = 0
        self.seen: list[str] = []

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        await asyncio.sleep(0.01)
        self.in_flight -= 1
        self.seen.extend(texts)
        return [[float(len(t))] * self.dim for t in texts]


async def test_concurrency_is_bounded_by_semaphore_and_order_preserved() -> None:
    client = SlowEmbedder()
    service = EmbeddingService(client, dimension=4, concurrency=3, batch_size=8)
    texts = ["x" * i for i in range(1, 30)]
    vectors = await service.embed_documents(texts)
    assert client.max_in_flight == 3
    assert [v[0] for v in vectors] == [float(len(t)) for t in texts]


async def test_shared_semaphore_bounds_concurrent_callers() -> None:
    client = SlowEmbedder()
    service = EmbeddingService(client, dimension=4, concurrency=2, batch_size=16)
    await asyncio.gather(service.embed_documents(["a"] * 10), service.embed_documents(["b"] * 10))
    assert client.max_in_flight == 2


async def test_prefixes_are_applied() -> None:
    client = SlowEmbedder()
    service = EmbeddingService(
        client, dimension=4, query_prefix="search_query: ", document_prefix="search_document: "
    )
    await service.embed_query("q")
    await service.embed_documents(["d"])
    assert client.seen == ["search_query: q", "search_document: d"]


async def test_dimension_mismatch_is_a_typed_error() -> None:
    service = EmbeddingService(SlowEmbedder(dim=3), dimension=768)
    with pytest.raises(EmbeddingDimensionError) as err:
        await service.embed_query("q")
    assert err.value.error_type == "EMBEDDING_DIM_MISMATCH"
