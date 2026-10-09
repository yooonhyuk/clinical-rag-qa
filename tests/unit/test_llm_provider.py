"""Provider switching, external-LLM guardrail and response-model parity."""

import json
from pathlib import Path

import httpx
import pytest
import respx
import yaml
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import Settings
from app.container import build_container, build_generator
from app.main import create_app
from app.services.anthropic_client import AnthropicGenerationClient
from app.services.embedding_service import EmbeddingService
from app.services.llm_guardrail import ExternalLLMNotAllowedError, validate_provider
from app.services.ollama_client import OllamaClient
from app.services.rag_service import RagService
from tests.fakes import DIM, FakeOllama, FakeSession, FakeSessionFactory, make_chunk
from tests.unit.test_anthropic_client import fake_response, make_client


def _mark(folder: Path, classification: str = "synthetic-sample") -> None:
    (folder / ".corpus.yaml").write_text(f"classification: {classification}\n", encoding="utf-8")


def _anthropic(settings: Settings, **update) -> Settings:
    values = {
        "llm_provider": "anthropic",
        "allow_external_llm": True,
        "anthropic_api_key": SecretStr("sk-ant-test"),
    }
    values.update(update)
    return settings.model_copy(update=values)


# --- guardrail ---------------------------------------------------------------------------


def test_default_provider_is_local_ollama(settings: Settings) -> None:
    assert settings.llm_provider == "ollama"
    validate_provider(settings)  # no error
    generator = build_generator(settings, FakeOllama())  # type: ignore[arg-type]
    assert generator.provider == "ollama"


def test_anthropic_requires_explicit_opt_in(settings: Settings) -> None:
    _mark(settings.raw_docs_path)
    with pytest.raises(ExternalLLMNotAllowedError, match="ALLOW_EXTERNAL_LLM"):
        validate_provider(_anthropic(settings, allow_external_llm=False))


def test_anthropic_requires_marked_corpus(settings: Settings) -> None:
    with pytest.raises(ExternalLLMNotAllowedError, match="not marked"):
        validate_provider(_anthropic(settings))
    _mark(settings.raw_docs_path, "confidential")
    with pytest.raises(ExternalLLMNotAllowedError, match="confidential"):
        validate_provider(_anthropic(settings))


def test_anthropic_requires_api_key(settings: Settings) -> None:
    _mark(settings.raw_docs_path)
    with pytest.raises(ExternalLLMNotAllowedError, match="ANTHROPIC_API_KEY"):
        validate_provider(_anthropic(settings, anthropic_api_key=None))


@pytest.mark.parametrize("classification", ["non-sensitive", "public-regulatory"])
def test_anthropic_allowed_when_all_conditions_hold(
    settings: Settings, classification: str
) -> None:
    _mark(settings.raw_docs_path, classification)
    generator = build_generator(_anthropic(settings), FakeOllama())  # type: ignore[arg-type]
    assert isinstance(generator, AnthropicGenerationClient)
    assert generator.model == "claude-opus-5-5"


def test_container_keeps_embeddings_and_dicom_local_in_anthropic_mode(settings: Settings) -> None:
    _mark(settings.raw_docs_path)
    ollama = FakeOllama()
    container = build_container(
        _anthropic(settings),
        ollama=ollama,
        session_factory=FakeSessionFactory(),  # type: ignore[arg-type]
    )
    assert container.rag.provider == "anthropic"
    assert container.embeddings._client is ollama  # embeddings never leave the machine
    assert container.dicom._llm is None  # DICOM explanation uses the local template


def test_app_refuses_to_start_when_guardrail_fails(settings: Settings, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.main.get_settings", lambda: _anthropic(settings, allow_external_llm=False)
    )
    with pytest.raises(ExternalLLMNotAllowedError), TestClient(create_app()):
        pass


def test_repo_corpora_are_marked() -> None:
    from app.services.llm_guardrail import corpus_classification

    root = Path(__file__).resolve().parents[2]
    assert corpus_classification(root / "samples" / "documents", ".corpus.yaml") == (
        "synthetic-sample"
    )
    assert corpus_classification(root / "corpus" / "public", ".corpus.yaml") == (
        "public-regulatory"
    )


# --- parity ------------------------------------------------------------------------------


async def _ask(generator) -> object:
    chunks = [make_chunk("dicom-upload-guide.md", 0.9), make_chunk("error-code-guide.md", 0.8)]

    async def search(session, vector, *, top_k, file_type, **_):
        return chunks

    rag = RagService(
        EmbeddingService(FakeOllama(), dimension=DIM),
        generator,
        system_prompt="sys",
        min_score=0.5,
        search=search,
    )
    return await rag.ask(FakeSession(), "업로드 실패 시 확인 항목은?", top_k=5)


@respx.mock
async def test_both_providers_produce_the_same_response_model() -> None:
    body = {
        "answer": "파일 형식과 필수 태그를 확인합니다 [1]. 오류 코드는 E102입니다 [2].",
        "cited_context_ids": [1, 2],
        "insufficient_evidence": False,
    }
    respx.post("http://ollama.test/api/generate").respond(
        json={
            "response": json.dumps(body, ensure_ascii=False),
            "prompt_eval_count": 50,
            "eval_count": 20,
        }
    )
    async with httpx.AsyncClient(base_url="http://ollama.test") as http:
        ollama = OllamaClient(http, llm_model="gemma4:e4b", embedding_model="nomic-embed-text")
        local = await _ask(ollama)
    claude, _ = make_client(fake_response(json.dumps(body, ensure_ascii=False)))
    external = await _ask(claude)

    for field in ("answer", "refused", "refusal_reason", "citation_mode"):
        assert getattr(local, field) == getattr(external, field)
    assert [s.file_name for s in local.sources] == [s.file_name for s in external.sources]
    assert (local.usage.provider, external.usage.provider) == ("ollama", "anthropic")
    assert local.usage.input_tokens == 50 and external.usage.input_tokens == 120


# --- local-only corpora (licensed-local-only) ---------------------------------------------


@pytest.mark.parametrize("classification", ["licensed-local-only", "confidential", None])
def test_local_only_classifications_never_allow_external(
    settings: Settings, classification: str | None
) -> None:
    from app.services.llm_guardrail import LOCAL_ONLY_CLASSIFICATIONS, allows_external

    assert not allows_external(classification)
    if classification is not None:
        assert classification in LOCAL_ONLY_CLASSIFICATIONS
        _mark(settings.raw_docs_path, classification)
        with pytest.raises(ExternalLLMNotAllowedError, match="not marked"):
            validate_provider(_anthropic(settings))


def test_private_corpus_template_is_local_only() -> None:
    from app.services.llm_guardrail import allows_external

    root = Path(__file__).resolve().parents[2]
    marker = yaml.safe_load((root / "corpus" / "private.corpus.yaml.example").read_text())
    assert marker["classification"] == "licensed-local-only"
    assert not allows_external(marker["classification"])
    assert marker["include"] == ["protocols/*.pdf", "originals/*.pdf"]


def _rag(generator, lookup=None, **kwargs) -> tuple[RagService, list[dict]]:
    calls: list[dict] = []

    async def search(session, vector, *, top_k, **options):
        calls.append(options)
        return [make_chunk("a.md", 0.9)]

    rag = RagService(
        EmbeddingService(FakeOllama(), dimension=DIM),
        generator,
        system_prompt="sys",
        min_score=0.5,
        search=search,
        corpus_lookup=lookup,
        **kwargs,
    )
    return rag, calls


async def test_external_generator_only_searches_allowed_classifications() -> None:
    from app.services.llm_guardrail import ALLOWED_CLASSIFICATIONS

    claude, _ = make_client(fake_response('{"answer": "ok [1]", "cited_context_ids": [1]}'))
    rag, calls = _rag(claude)
    await rag.retrieve(FakeSession(), "q", top_k=5)
    assert calls[-1]["classifications"] == ALLOWED_CLASSIFICATIONS

    local, local_calls = _rag(FakeOllama())
    await local.retrieve(FakeSession(), "q", top_k=5)
    assert "classifications" not in local_calls[-1]  # local generation: every corpus


async def test_external_generator_rejects_a_local_only_corpus() -> None:
    async def lookup(session, corpus):
        return {"licensed-local-only"} if corpus == "private" else {"public-regulatory"}

    claude, _ = make_client(fake_response('{"answer": "ok [1]", "cited_context_ids": [1]}'))
    rag, calls = _rag(claude, lookup)
    with pytest.raises(ExternalLLMNotAllowedError, match="local-only"):
        await rag.ask(FakeSession(), "q", top_k=5, corpus="private")
    with pytest.raises(ExternalLLMNotAllowedError):
        await rag.retrieve(FakeSession(), "q", top_k=5, corpus="private")
    assert calls == []  # rejected before retrieval: nothing was read
    await rag.retrieve(FakeSession(), "q", top_k=5, corpus="public")
    assert len(calls) == 1


async def test_ollama_generator_may_use_a_local_only_corpus() -> None:
    async def lookup(session, corpus):  # pragma: no cover - must not be consulted
        raise AssertionError("local generation does not check classifications")

    rag, calls = _rag(FakeOllama(), lookup)
    await rag.retrieve(FakeSession(), "q", top_k=5, corpus="private")
    assert calls[-1]["corpus"] == "private"


async def test_search_mode_options_reach_the_search() -> None:
    rag, calls = _rag(FakeOllama(), exact_search=True)
    await rag.retrieve(FakeSession(), "q", top_k=5)
    assert calls[-1]["exact"] is True and "iterative_scan" not in calls[-1]
    rag, calls = _rag(FakeOllama(), hnsw_iterative_scan="relaxed_order")
    await rag.retrieve(FakeSession(), "q", top_k=5)
    assert calls[-1]["iterative_scan"] == "relaxed_order"


def test_local_only_rejection_is_http_403(settings: Settings) -> None:
    async def lookup(session, corpus):
        return {"licensed-local-only"}

    claude, _ = make_client(fake_response('{"answer": "ok [1]", "cited_context_ids": [1]}'))
    _mark(settings.raw_docs_path, "public-regulatory")
    container = build_container(
        _anthropic(settings),
        ollama=FakeOllama(),  # type: ignore[arg-type]
        generator=claude,
        session_factory=FakeSessionFactory(),  # type: ignore[arg-type]
    )
    container.rag._corpus_lookup = lookup
    with TestClient(create_app(container)) as client:
        res = client.post("/api/ask", json={"question": "스캔 주기는?", "corpus": "private"})
    assert res.status_code == 403
    assert res.json()["errorType"] == "EXTERNAL_LLM_NOT_ALLOWED"
