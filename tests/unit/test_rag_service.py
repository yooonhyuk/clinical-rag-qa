import uuid

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
    PARTIAL_CAVEAT,
    REFUSAL_MESSAGE,
    RagService,
    RefusalReason,
    extract_citations,
    is_out_of_scope,
)
from app.services.reranker import rerank_chunks
from app.services.vector_search_service import rrf_fuse
from tests.fakes import DIM, FakeOllama, FakeSession, make_chunk


def _service(llm: FakeOllama, chunks: list, min_score: float = 0.5) -> RagService:
    async def search(session, vector, *, top_k, file_type, **_):
        return chunks[:top_k]

    embeddings = EmbeddingService(llm, dimension=DIM)
    return RagService(embeddings, llm, system_prompt="sys", min_score=min_score, search=search)


@pytest.mark.parametrize(
    "question",
    [
        "이 환자의 CT에서 폐결절이 있나요?",
        "이 영상 판독해줘",
        "이 MR 영상 판독 결과를 알려줘.",
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


def test_rrf_fuse_rewards_items_ranked_by_both_channels() -> None:
    a, b, c, d = (uuid.uuid4() for _ in range(4))
    fused = rrf_fuse([[a, b, c], [c, d, a]], k=60)
    assert fused[:2] == [a, c]  # in both rankings
    assert set(fused) == {a, b, c, d}


async def test_hybrid_flag_controls_query_text_passed_to_search() -> None:
    seen: list[str | None] = []

    async def search(session, vector, *, top_k, file_type, query_text=None, rrf_k=60, **_):
        seen.append(query_text)
        return []

    for hybrid in (True, False):
        rag = RagService(
            EmbeddingService(FakeOllama(), dimension=DIM),
            FakeOllama(),
            system_prompt="sys",
            min_score=0.5,
            hybrid=hybrid,
            search=search,
        )
        await rag.retrieve(FakeSession(), "업로드 용량", top_k=3)
    assert seen == ["업로드 용량", None]


# --- partial answers (docs/issues/007) -------------------------------------------------------


def _flagged(answer: str, cited: list[int]) -> FakeOllama:
    return FakeOllama(
        answer=GroundedAnswer(answer=answer, cited_context_ids=cited, insufficient_evidence=True)
    )


async def test_flagged_answer_with_citations_is_a_partial_answer_not_a_refusal() -> None:
    chunks = [make_chunk("a.md"), make_chunk("b.md")]
    llm = _flagged("직접 비교는 없습니다. 다만 최소 2주기 이상 투여합니다 [2].", [2])
    result = await _service(llm, chunks).ask(FakeSession(), "q", top_k=5)
    assert not result.refused and result.refusal_reason is None
    assert result.partial and result.caveat == PARTIAL_CAVEAT
    assert [s.file_name for s in result.sources] == ["b.md"]


async def test_flagged_answer_with_only_text_citations_is_partial() -> None:
    llm = _flagged("구체적 정의는 없지만 2배 이상 증가로 봅니다 [1].", [])
    result = await _service(llm, [make_chunk()]).ask(FakeSession(), "q", top_k=5)
    assert result.partial and result.citation_mode == "parsed"


@pytest.mark.parametrize(
    ("answer", "cited"),
    [
        ("관련 내용이 없습니다.", []),  # flagged, no citation at all
        (REFUSAL_MESSAGE, [1]),  # explicit refusal sentence, ids only in the structured field
        ("근거 없음 [7]", [9]),  # citations that point outside the context are not citations
    ],
)
async def test_flagged_answer_without_valid_citations_is_still_refused(
    answer: str, cited: list[int]
) -> None:
    result = await _service(_flagged(answer, cited), [make_chunk()]).ask(
        FakeSession(), "q", top_k=5
    )
    assert result.refused and result.refusal_reason == RefusalReason.MODEL_REFUSED
    assert not result.partial and result.sources == []


async def test_partial_answers_off_restores_mvp1_refusal() -> None:
    async def search(session, vector, *, top_k, **_):
        return [make_chunk()]

    rag = RagService(
        EmbeddingService(FakeOllama(), dimension=DIM),
        _flagged("일부만 확인됩니다 [1].", [1]),
        system_prompt="sys",
        min_score=0.5,
        search=search,
        partial_answers=False,
    )
    result = await rag.ask(FakeSession(), "q", top_k=5)
    assert result.refused and not result.partial


async def test_normal_answer_is_not_partial_and_records_schema_validity() -> None:
    result = await _service(FakeOllama(), [make_chunk()]).ask(FakeSession(), "q", top_k=5)
    assert not result.partial and result.caveat is None
    assert result.meta["schemaValid"] is True


# --- cross-encoder reranker (B7) -------------------------------------------------------------


class FakeReranker:
    model = "fake-reranker"

    def __init__(self, scores: dict[str, float]) -> None:
        self.scores = scores
        self.calls: list[tuple[str, int]] = []

    async def score(self, query: str, texts: list[str]) -> list[float]:
        self.calls.append((query, len(texts)))
        return [self.scores.get(t, 0.0) for t in texts]


def _reranked_service(
    llm: FakeOllama,
    chunks: list,
    reranker: FakeReranker,
    *,
    min_score: float = 0.45,
    rerank_min_score: float = 0.2,
) -> tuple[RagService, list[int]]:
    asked: list[int] = []

    async def search(session, vector, *, top_k, **_):
        asked.append(top_k)
        return chunks[:top_k]

    rag = RagService(
        EmbeddingService(llm, dimension=DIM),
        llm,
        system_prompt="sys",
        min_score=min_score,
        search=search,
        reranker=reranker,
        rerank_candidates=4,
        rerank_min_score=rerank_min_score,
    )
    return rag, asked


def _texts(n: int) -> list:
    return [make_chunk(f"{i}.md", 0.9 - i * 0.05, text=f"t{i}") for i in range(n)]


async def test_reranker_fetches_candidates_and_keeps_best_top_k() -> None:
    reranker = FakeReranker({"t3": 0.9, "t0": 0.5, "t2": 0.1})
    rag, asked = _reranked_service(FakeOllama(), _texts(6), reranker)
    chunks, _ = await rag.retrieve(FakeSession(), "q", top_k=2)
    assert asked == [4] and reranker.calls == [("q", 4)]
    assert [c.file_name for c in chunks] == ["3.md", "0.md"]
    assert [c.rerank_score for c in chunks] == [0.9, 0.5]


async def test_rerank_gate_refuses_without_llm_when_best_rerank_is_low() -> None:
    llm = FakeOllama()
    rag, _ = _reranked_service(llm, _texts(4), FakeReranker({"t1": 0.1}))
    result = await rag.ask(FakeSession(), "q", top_k=2)
    assert result.refused and result.refusal_reason == RefusalReason.NO_EVIDENCE
    assert llm.generate_calls == []
    assert result.meta["gate"] == {"bestCosine": pytest.approx(0.9), "topRerank": 0.1}


async def test_cosine_gate_still_applies_with_reranker() -> None:
    llm = FakeOllama()
    chunks = [make_chunk("a.md", 0.3, text="a")]
    rag, _ = _reranked_service(llm, chunks, FakeReranker({"a": 0.99}), min_score=0.45)
    result = await rag.ask(FakeSession(), "q", top_k=2)
    assert result.refusal_reason == RefusalReason.NO_EVIDENCE and llm.generate_calls == []


async def test_reranked_top_k_all_go_into_the_prompt_in_rerank_order() -> None:
    llm = FakeOllama()
    rag, _ = _reranked_service(llm, _texts(4), FakeReranker({"t2": 0.8, "t1": 0.01}))
    result = await rag.ask(FakeSession(), "q", top_k=2)
    assert not result.refused
    prompt = llm.generate_calls[0]
    assert prompt.index("2.md") < prompt.index("1.md")  # low rerank score still in context


def test_rerank_chunks_rejects_mismatched_scores() -> None:
    with pytest.raises(ValueError):
        rerank_chunks([make_chunk()], [0.1, 0.2], top_k=1)


def test_no_reranker_by_default() -> None:
    from app.config import Settings
    from app.container import build_reranker

    assert build_reranker(Settings(_env_file=None)) is None


class _SystemRecordingLlm(FakeOllama):
    def __init__(self) -> None:
        super().__init__()
        self.systems: list[str | None] = []

    async def generate_answer(self, prompt: str, *, system: str | None = None):
        self.systems.append(system)
        return await super().generate_answer(prompt, system=system)


async def test_default_prompt_sends_instructions_as_system() -> None:
    llm = _SystemRecordingLlm()
    await _service(llm, [make_chunk()]).ask(FakeSession(), "질문", top_k=5)
    assert llm.systems == ["sys"] and "sys" not in llm.generate_calls[0]


async def test_inline_prompt_variant_puts_instructions_in_the_user_turn() -> None:
    llm = _SystemRecordingLlm()

    async def search(session, vector, *, top_k, file_type, **_):
        return [make_chunk(text="chunk text")]

    rag = RagService(
        EmbeddingService(llm, dimension=DIM),
        llm,
        system_prompt="INSTRUCTIONS",
        min_score=0.5,
        search=search,
        inline_instructions=True,
    )
    result = await rag.ask(FakeSession(), "the question?", top_k=5)
    prompt = llm.generate_calls[0]
    assert llm.systems == [None] and not result.refused
    assert prompt.startswith("INSTRUCTIONS")
    assert prompt.index("[1] Source:") < prompt.index("Question: the question?")


def test_prompt_variant_defaults_to_the_tuned_prompt() -> None:
    from app.config import Settings

    assert Settings(_env_file=None).rag_prompt_variant == "default"
