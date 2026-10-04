import pytest

from app.models import AskLog
from app.services.embedding_service import EmbeddingService
from app.services.llm_types import (
    GroundedAnswer,
    LLMUsage,
    ModelRefusalError,
    StructuredOutputError,
)
from app.services.rag_service import (
    REFUSAL_MESSAGE,
    RagService,
    RefusalReason,
    extract_citations,
    is_out_of_scope,
)
from tests.fakes import FakeOllama, FakeSession, make_chunk


def _service(llm: FakeOllama, chunks: list, min_score: float = 0.5) -> RagService:
    async def search(session, vector, *, top_k, file_type):
        return chunks[:top_k]

    embeddings = EmbeddingService(llm, dimension=768)
    return RagService(embeddings, llm, system_prompt="sys", min_score=min_score, search=search)


@pytest.mark.parametrize(
    "question",
    [
        "이 환자의 CT에서 폐결절이 있나요?",
        "이 영상 판독해줘",
        "어떤 약을 처방해야 하나요?",
        "암인지 알려줘",
    ],
)
def test_out_of_scope_questions(question: str) -> None:
    assert is_out_of_scope(question)


@pytest.mark.parametrize(
    "question",
    [
        "DICOM 분석 기능이 영상 판독을 수행하나요?",
        "암호화된 PDF는 어떻게 처리되나요?",
        "E101 오류 의미는?",
    ],
)
def test_in_scope_questions(question: str) -> None:
    assert not is_out_of_scope(question)


def test_extract_citations_dedupes_and_ignores_unknown_ids() -> None:
    assert extract_citations("a [2] b [1] c [2] d [9]", n_chunks=3) == [1, 0]


async def test_out_of_scope_refuses_without_calling_models() -> None:
    llm = FakeOllama()
    session = FakeSession()
    result = await _service(llm, [make_chunk()]).ask(session, "폐결절이 있나요?", top_k=5)
    assert result.refused and result.refusal_reason == RefusalReason.OUT_OF_SCOPE
    assert llm.embed_calls == 0 and llm.generate_calls == []
    assert isinstance(session.added[0], AskLog)


async def test_low_score_refuses_without_llm() -> None:
    llm = FakeOllama()
    result = await _service(llm, [make_chunk(score=0.2)]).ask(FakeSession(), "질문", top_k=5)
    assert result.refused and result.refusal_reason == RefusalReason.NO_EVIDENCE
    assert result.answer == REFUSAL_MESSAGE and result.sources == []
    assert llm.generate_calls == []


async def test_structured_citations_select_sources_and_log_usage() -> None:
    chunks = [make_chunk("a.md", 0.9), make_chunk("b.md", 0.8), make_chunk("c.md", 0.1)]
    llm = FakeOllama(
        answer=GroundedAnswer(answer="답 [2]", cited_context_ids=[2], insufficient_evidence=False)
    )
    session = FakeSession()
    result = await _service(llm, chunks).ask(session, "질문", top_k=5)
    assert not result.refused
    assert [s.file_name for s in result.sources] == ["b.md"]
    assert result.citation_mode == "structured"
    # only evidence above min_score goes into the prompt
    assert "c.md" not in llm.generate_calls[0]
    log = session.added[0]
    assert (log.llm_provider, log.input_tokens, log.output_tokens) == ("ollama", 10, 5)
    assert len(log.retrieved_chunk_ids) == 3


async def test_falls_back_to_parsed_then_retrieved_citations() -> None:
    chunks = [make_chunk("a.md"), make_chunk("b.md")]
    parsed = FakeOllama(
        answer=GroundedAnswer(answer="답 [2]", cited_context_ids=[], insufficient_evidence=False)
    )
    result = await _service(parsed, chunks).ask(FakeSession(), "q", top_k=5)
    assert result.citation_mode == "parsed" and [s.file_name for s in result.sources] == ["b.md"]

    uncited = FakeOllama(
        answer=GroundedAnswer(answer="답", cited_context_ids=[], insufficient_evidence=False)
    )
    result = await _service(uncited, chunks).ask(FakeSession(), "q", top_k=5)
    assert result.citation_mode == "retrieved" and len(result.sources) == 2


async def test_model_reported_insufficient_evidence_is_a_refusal() -> None:
    llm = FakeOllama(
        answer=GroundedAnswer(
            answer=REFUSAL_MESSAGE, cited_context_ids=[], insufficient_evidence=True
        )
    )
    result = await _service(llm, [make_chunk()]).ask(FakeSession(), "q", top_k=5)
    assert result.refused and result.refusal_reason == RefusalReason.MODEL_REFUSED
    assert result.sources == []


async def test_schema_violation_keeps_text_answer() -> None:
    class Sloppy(FakeOllama):
        async def generate_answer(self, prompt, *, system=None):
            usage = LLMUsage("ollama", "m", 1)
            raise StructuredOutputError("bad", raw_text="자유 텍스트 답변 [1]", usage=usage)

    result = await _service(Sloppy(), [make_chunk()]).ask(FakeSession(), "q", top_k=5)
    assert not result.refused
    assert result.answer == "자유 텍스트 답변 [1]" and result.citation_mode == "parsed"


async def test_provider_refusal_is_a_refusal() -> None:
    class Declines(FakeOllama):
        async def generate_answer(self, prompt, *, system=None):
            raise ModelRefusalError("declined", usage=LLMUsage("anthropic", "m", 1, 5, 0))

    result = await _service(Declines(), [make_chunk()]).ask(FakeSession(), "q", top_k=5)
    assert result.refused and result.refusal_reason == RefusalReason.MODEL_REFUSED
    assert result.usage is not None and result.usage.provider == "anthropic"
