"""Embedding model / dimension configuration and model-mismatch detection."""

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.services.embedding_schema import EmbeddingIndexState, evaluate_embedding_index
from tests.fakes import DIM, FakeOllama, FakeSession, FakeSessionFactory


def _settings(**kw) -> Settings:
    return Settings(_env_file=None, **kw)


def test_default_is_bge_m3_1024_without_prefixes() -> None:
    s = _settings()
    assert s.ollama_embedding_model == "bge-m3"
    assert s.embedding_dimension == 1024 == DIM
    assert (s.embedding_query_prefix, s.embedding_document_prefix) == ("", "")


def test_nomic_gets_its_dimension_and_task_prefixes() -> None:
    s = _settings(ollama_embedding_model="nomic-embed-text:latest")
    assert s.embedding_dimension == 768
    assert s.embedding_query_prefix == "search_query: "
    assert s.embedding_document_prefix == "search_document: "


def test_explicit_prefix_overrides_the_model_default() -> None:
    s = _settings(ollama_embedding_model="nomic-embed-text", embedding_query_prefix="")
    assert s.embedding_query_prefix == ""
    assert s.embedding_document_prefix == "search_document: "


def test_dimension_contradicting_a_known_model_is_rejected() -> None:
    with pytest.raises(ValidationError, match="does not match bge-m3"):
        _settings(ollama_embedding_model="bge-m3", embedding_dim=768)


def test_unknown_model_requires_explicit_dimension() -> None:
    with pytest.raises(ValidationError, match="EMBEDDING_DIM is required"):
        _settings(ollama_embedding_model="my-embedder")
    s = _settings(ollama_embedding_model="my-embedder", embedding_dim=384)
    assert s.embedding_dimension == 384
    assert s.embedding_query_prefix == ""


@pytest.mark.parametrize(
    ("state", "ok", "fragment"),
    [
        (EmbeddingIndexState(1024, ["bge-m3"], 0), True, "bge-m3 / vector(1024)"),
        (EmbeddingIndexState(1024, ["bge-m3:latest"], 0), True, "vector(1024)"),
        (EmbeddingIndexState(1024, [], 0), True, "no chunks indexed yet"),
        (EmbeddingIndexState(768, ["nomic-embed-text"], 0), False, "column is vector(768)"),
        (EmbeddingIndexState(1024, ["bge-m3", "unknown"], 0), False, "embedded with unknown"),
        (EmbeddingIndexState(1024, [], 6), False, "6 document(s) need reindex"),
    ],
)
def test_evaluate_embedding_index(state, ok, fragment) -> None:
    got_ok, detail = evaluate_embedding_index(state, model="bge-m3", dim=1024)
    assert got_ok is ok
    assert fragment in detail


async def _health(settings, factory) -> dict:
    import httpx

    from app.container import build_container
    from app.main import create_app

    container = build_container(settings, ollama=FakeOllama(), session_factory=factory)  # type: ignore[arg-type]
    transport = httpx.ASGITransport(app=create_app(container))
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
        return (await client.get("/api/health")).json()


async def test_health_reports_consistent_embedding_index(settings) -> None:
    body = await _health(settings, FakeSessionFactory(chunk_models=["bge-m3"]))
    assert body["embeddingIndex"] == {"ok": True, "detail": "bge-m3 / vector(1024)"}


async def test_health_degrades_on_model_and_dimension_mismatch(settings) -> None:
    body = await _health(
        settings,
        FakeSessionFactory(embedding_dim=768, chunk_models=["nomic-embed-text"], reindex_pending=2),
    )
    assert body["status"] == "degraded"
    detail = body["embeddingIndex"]["detail"]
    assert body["embeddingIndex"]["ok"] is False
    assert "vector(768)" in detail and "nomic-embed-text" in detail and "2 document(s)" in detail


async def test_rag_searches_only_the_configured_models_chunks() -> None:
    from app.services.embedding_service import EmbeddingService
    from app.services.rag_service import RagService

    seen: list[str | None] = []

    async def search(session, vector, *, embedding_model=None, **_):
        seen.append(embedding_model)
        return []

    rag = RagService(
        EmbeddingService(FakeOllama(), dimension=DIM, model="bge-m3"),
        FakeOllama(),
        system_prompt="sys",
        min_score=0.5,
        search=search,
    )
    await rag.retrieve(FakeSession(), "업로드 용량", top_k=3)
    assert seen == ["bge-m3"]


def test_embeddinggemma2_gets_768_dims_and_task_prefixes() -> None:
    for model in ("embeddinggemma-2:270m", "embeddinggemma-2:740m"):
        s = _settings(ollama_embedding_model=model)
        assert s.embedding_dimension == 768
        assert s.embedding_truncate_dim is None
        assert s.embedding_query_prefix == "task: search result | query: "
        assert s.embedding_document_prefix == "title: none | text: "


@pytest.mark.parametrize("dim", [512, 256, 128])
def test_truncate_dim_sets_the_column_dimension(dim) -> None:
    s = _settings(ollama_embedding_model="embeddinggemma-2:270m", embedding_truncate_dim=dim)
    assert s.embedding_dimension == dim
    # the explicit dimension may be given too, as long as it agrees
    s = _settings(
        ollama_embedding_model="embeddinggemma-2:270m",
        embedding_truncate_dim=dim,
        embedding_dim=dim,
    )
    assert s.embedding_dimension == dim


@pytest.mark.parametrize(
    ("kw", "fragment"),
    [
        ({"ollama_embedding_model": "bge-m3", "embedding_truncate_dim": 512}, "not supported"),
        ({"ollama_embedding_model": "nomic-embed-text", "embedding_truncate_dim": 256}, "not supp"),
        ({"ollama_embedding_model": "embeddinggemma-2:270m", "embedding_truncate_dim": 300}, "300"),
        # larger than the model's own size is not a truncation
        (
            {"ollama_embedding_model": "embeddinggemma-2:270m", "embedding_truncate_dim": 1024},
            "1024",
        ),
        (
            {
                "ollama_embedding_model": "embeddinggemma-2:270m",
                "embedding_truncate_dim": 256,
                "embedding_dim": 768,
            },
            "does not match",
        ),
        (
            {
                "ollama_embedding_model": "my-embedder",
                "embedding_dim": 384,
                "embedding_truncate_dim": 128,
            },
            "not supported",
        ),
    ],
)
def test_unsupported_truncate_combinations_are_rejected(kw, fragment) -> None:
    with pytest.raises(ValidationError, match=fragment):
        _settings(**kw)


def test_blank_truncate_dim_means_full_size() -> None:
    s = _settings(ollama_embedding_model="embeddinggemma-2:270m", embedding_truncate_dim="")
    assert s.embedding_truncate_dim is None
    assert s.embedding_dimension == 768
