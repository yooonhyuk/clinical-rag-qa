"""HTTP API tests (httpx AsyncClient + ASGI). DB, Ollama and Claude are faked."""

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import httpx
import pytest
from pydantic import SecretStr

from app.config import Settings
from app.container import build_container
from app.main import create_app
from app.models import DicomFile
from app.services.llm_types import GroundedAnswer
from tests.fakes import FakeOllama, FakeSessionFactory, make_chunk


class FakePipeline:
    def __init__(self) -> None:
        self.roots: list = []

    async def run(self, root):
        self.roots.append(root)
        return SimpleNamespace(
            id=uuid.uuid4(),
            status="COMPLETED",
            total=3,
            indexed=1,
            failed=1,
            skipped_duplicate=1,
            details=[{"fileName": "a.md", "status": "INDEXED"}],
            started_at=datetime.now(UTC),
        )


@pytest.fixture
def factory() -> FakeSessionFactory:
    return FakeSessionFactory()


def _client(settings: Settings, factory: FakeSessionFactory, llm: FakeOllama | None = None):
    container = build_container(settings, ollama=llm or FakeOllama(), session_factory=factory)  # type: ignore[arg-type]
    chunks = [make_chunk("dicom-upload-guide.md", 0.9, page_number=None, chunk_index=3)]

    async def search(session, vector, *, top_k, file_type):
        return chunks

    container.rag._search = search
    container.pipeline = FakePipeline()  # type: ignore[assignment]
    app = create_app(container)
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ), container


async def test_ask_returns_answer_sources_latency_and_usage(settings, factory) -> None:
    client, _ = _client(settings, factory)
    async with client:
        res = await client.post(
            "/api/ask", json={"question": "업로드 실패 시 확인 항목은?", "topK": 3}
        )
    assert res.status_code == 200
    body = res.json()
    assert body["refused"] is False
    assert body["sources"][0]["fileName"] == "dicom-upload-guide.md"
    assert body["sources"][0]["chunkIndex"] == 3
    assert set(body["latencyMs"]) == {"retrieval", "generation"}
    assert body["llm"] == {
        "provider": "ollama",
        "model": "fake-gemma",
        "inputTokens": 10,
        "outputTokens": 5,
    }


async def test_ask_refuses_diagnosis(settings, factory) -> None:
    client, _ = _client(settings, factory)
    async with client:
        body = (await client.post("/api/ask", json={"question": "이 CT에 폐결절이 있나요?"})).json()
    assert body["refused"] is True and body["refusalReason"] == "OUT_OF_SCOPE"
    assert body["sources"] == []


async def test_ask_validates_input(settings, factory) -> None:
    client, _ = _client(settings, factory)
    async with client:
        res = await client.post("/api/ask", json={"question": "", "topK": 999})
    assert res.status_code == 422


async def test_retrieve_returns_chunks_with_metadata(settings, factory) -> None:
    client, _ = _client(settings, factory)
    async with client:
        body = (await client.post("/api/retrieve", json={"question": "업로드 실패 원인"})).json()
    assert body["chunks"][0]["metadata"]["sectionTitle"] == "Upload Validation"
    assert body["chunks"][0]["score"] == 0.9


async def test_dicom_analyze_returns_rule_results_and_persists(
    settings, factory, sample_dicom
) -> None:
    client, _ = _client(settings, factory)
    async with client:
        res = await client.post("/api/dicom/analyze", json={"filePath": sample_dicom.name})
    assert res.status_code == 200
    body = res.json()
    assert body["tagSummary"]["Modality"] == "CT"
    assert "PatientName exists" in body["privacyWarnings"]
    assert body["missingRequiredTags"] == []
    assert "영상 판독은 수행하지 않습니다" in body["summary"]
    assert body["ruleSource"] == "rules/required_tags.yaml, rules/privacy_tags.yaml"
    saved = [o for o in factory.added if isinstance(o, DicomFile)]
    assert saved and saved[0].status == "ANALYZED"


async def test_dicom_analyze_rejects_paths_outside_allowed_roots(settings, factory) -> None:
    client, _ = _client(settings, factory)
    async with client:
        res = await client.post("/api/dicom/analyze", json={"filePath": "/etc/passwd"})
    assert res.status_code == 403


async def test_dicom_analyze_non_dicom_is_422(settings, factory) -> None:
    bad = settings.dicom_path / "broken.dcm"
    bad.write_bytes(b"jpeg bytes")
    client, _ = _client(settings, factory)
    async with client:
        res = await client.post("/api/dicom/analyze", json={"filePath": str(bad)})
    assert res.status_code == 422
    assert any(isinstance(o, DicomFile) and o.status == "FAILED" for o in factory.added)


async def test_index_uses_default_folder(settings, factory) -> None:
    client, container = _client(settings, factory)
    async with client:
        body = (await client.post("/api/index", json={})).json()
    assert body["skippedDuplicate"] == 1 and body["indexed"] == 1
    assert container.pipeline.roots == [settings.raw_docs_path.resolve()]


async def test_index_rejects_unmarked_folder_in_anthropic_mode(settings, factory) -> None:
    (settings.raw_docs_path / ".corpus.yaml").write_text("classification: synthetic-sample")
    other = settings.raw_docs_path / "unmarked"
    other.mkdir()
    ext = settings.model_copy(
        update={
            "llm_provider": "anthropic",
            "allow_external_llm": True,
            "anthropic_api_key": SecretStr("sk-ant-test"),
        }
    )
    client, _ = _client(ext, factory)
    async with client:
        ok = await client.post("/api/index", json={"path": str(settings.raw_docs_path)})
        denied = await client.post("/api/index", json={"path": str(other)})
    assert ok.status_code == 200
    assert denied.status_code == 403


async def test_health_reports_components(settings, factory) -> None:
    client, _ = _client(settings, factory, FakeOllama())
    async with client:
        body = (await client.get("/api/health")).json()
    assert body["database"]["ok"] and body["pgvector"]["ok"]
    assert body["llmProvider"] == "ollama"
    assert body["embeddingModel"]["ok"] is True
    assert body["llmModel"]["ok"] is False  # fake model name "gemma4:e4b" not in fake list


async def test_llm_errors_become_503(settings, factory) -> None:
    from app.services.llm_types import LLMError

    class Down(FakeOllama):
        async def embed(self, texts):
            raise LLMError("ollama down", error_type="OLLAMA_UNAVAILABLE")

    client, _ = _client(settings, factory, Down())
    async with client:
        res = await client.post("/api/retrieve", json={"question": "q"})
    assert res.status_code == 503 and res.json()["errorType"] == "OLLAMA_UNAVAILABLE"


def test_grounded_answer_schema_matches_model() -> None:
    from app.services.llm_types import GROUNDED_ANSWER_SCHEMA

    assert set(GROUNDED_ANSWER_SCHEMA["properties"]) == set(GroundedAnswer.model_fields)
