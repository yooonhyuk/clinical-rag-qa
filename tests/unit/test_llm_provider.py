"""Provider switching, external-LLM guardrail and response-model parity."""

import json
from pathlib import Path

import httpx
import pytest
import respx
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
from tests.fakes import FakeOllama, FakeSession, FakeSessionFactory, make_chunk
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


def test_anthropic_allowed_when_all_conditions_hold(settings: Settings) -> None:
    _mark(settings.raw_docs_path, "non-sensitive")
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


# --- parity ------------------------------------------------------------------------------


async def _ask(generator) -> object:
    chunks = [make_chunk("dicom-upload-guide.md", 0.9), make_chunk("error-code-guide.md", 0.8)]

    async def search(session, vector, *, top_k, file_type, **_):
        return chunks

    rag = RagService(
        EmbeddingService(FakeOllama(), dimension=768),
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
