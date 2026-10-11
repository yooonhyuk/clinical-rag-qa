"""Edition-aware retrieval wiring: filter flag, prompt header, citation fields, warning."""

from dataclasses import replace
from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.rag import QuestionRequest
from app.services.embedding_service import EmbeddingService
from app.services.llm_types import GroundedAnswer
from app.services.prompt_builder import build_rag_prompt, format_source_label
from app.services.rag_service import RagService, superseded_warning
from tests.fakes import DIM, FakeOllama, FakeSession
from tests.fakes import make_chunk as _make_chunk


def make_chunk(file_name="dicom-upload-guide.md", score=0.8, **kw):
    """fakes.make_chunk plus the edition fields."""
    edition = {k: kw.pop(k) for k in ("version_label", "version_date", "is_latest") if k in kw}
    return replace(_make_chunk(file_name, score, **kw), **edition)


def _service(chunks, calls: list[dict], *, latest_only: bool = True, llm=None) -> RagService:
    async def search(session, vector, *, top_k, file_type, **options):
        calls.append(options)
        return chunks[:top_k]

    llm = llm or FakeOllama()
    return RagService(
        EmbeddingService(llm, dimension=DIM),
        llm,
        system_prompt="sys",
        min_score=0.5,
        search=search,
        latest_only=latest_only,
    )


def _old(**kw):
    return make_chunk("gcp-r2.pdf", 0.9, version_label="R2", is_latest=False, **kw)


async def test_default_searches_latest_only_and_include_superseded_lifts_it() -> None:
    calls: list[dict] = []
    service = _service([make_chunk()], calls)
    await service.ask(FakeSession(), "질문", top_k=3)
    await service.retrieve(FakeSession(), "질문", top_k=3)
    await service.ask(FakeSession(), "질문", top_k=3, include_superseded=True)
    await service.retrieve(FakeSession(), "질문", top_k=3, include_superseded=True)
    assert [c.get("latest_only") for c in calls] == [True, True, None, None]


async def test_setting_off_turns_the_filter_off_everywhere() -> None:
    calls: list[dict] = []
    await _service([make_chunk()], calls, latest_only=False).ask(FakeSession(), "질문", top_k=3)
    assert "latest_only" not in calls[0]


def test_prompt_header_carries_the_edition_without_touching_unversioned_sources() -> None:
    plain = make_chunk("a.md", section_title=None)
    assert format_source_label(plain) == "a.md"
    labelled = make_chunk("gcp-r3.pdf", page_number=10, section_title=None, version_label="R3")
    assert format_source_label(labelled) == "gcp-r3.pdf · R3 / p.10"
    dated = make_chunk("w.xlsx", section_title=None, version_date=date(2025, 9, 15))
    assert format_source_label(dated) == "w.xlsx · 2025-09-15"
    prompt = build_rag_prompt("Q?", [labelled])
    assert "[1] 출처: gcp-r3.pdf · R3 / p.10\n" in prompt


async def test_old_edition_cited_gives_a_warning_and_latest_only_does_not() -> None:
    calls: list[dict] = []
    llm = FakeOllama(
        answer=GroundedAnswer(
            answer="예외가 있다 [1].",
            cited_context_ids=[1],
            insufficient_evidence=False,
        )
    )
    result = await _service([_old()], calls, llm=llm).ask(
        FakeSession(), "질문", top_k=3, include_superseded=True
    )
    assert result.superseded_warning == (
        "옛 판(gcp-r2.pdf R2) 내용 포함: 최신판이 아닌 문서를 근거로 한 답변입니다."
    )
    fresh = await _service([make_chunk("gcp-r3.pdf", 0.9, version_label="R3")], calls).ask(
        FakeSession(), "질문", top_k=3
    )
    assert fresh.superseded_warning is None


def test_superseded_warning_lists_each_old_edition_once() -> None:
    chunks = [_old(chunk_index=1), _old(chunk_index=2), make_chunk("gcp-r3.pdf")]
    assert superseded_warning(chunks).count("gcp-r2.pdf R2") == 1
    assert superseded_warning([make_chunk()]) is None


def test_request_accepts_office_file_types_and_defaults_to_latest() -> None:
    for file_type in ("docx", "xlsx", "pdf"):
        assert QuestionRequest(question="q", file_type=file_type).file_type == file_type
    assert QuestionRequest(question="q").include_superseded is False
    assert QuestionRequest.model_validate(
        {"question": "q", "includeSuperseded": True}
    ).include_superseded
    with pytest.raises(ValidationError):
        QuestionRequest(question="q", file_type="pptx")
