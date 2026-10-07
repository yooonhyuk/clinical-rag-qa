"""Retrieval-augmented question answering with source citations and a refusal policy.

Refusal policy (checked in this order, the first two never call the LLM):
1. OUT_OF_SCOPE      - the question asks for image reading / diagnosis / treatment
                       (scope_classifier: precise regex, then embedding kNN over exemplars).
2. NO_EVIDENCE       - nothing retrieved, or the best cosine score < `min_score`; with the
                       optional cross-encoder reranker, also the best rerank score <
                       `rerank_min_score` (the reranker reorders `rerank_candidates` chunks and
                       keeps the best `top_k`).
3. MODEL_REFUSED     - the LLM reports `insufficient_evidence` (structured output) without
                       citing any context, answers "문서에서 확인할 수 없습니다" without citations,
                       or the provider declines.

Partial answers (docs/issues/007): when the model flags `insufficient_evidence` but its answer
cites valid context blocks, the answer is returned with `partial=True` and a caveat instead of
being refused (`partial_answers=False` restores the MVP-1 behaviour: refuse).

Both generation providers (Ollama, Claude API) return the same `GroundedAnswer` structure.
"""

import re
import time
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AskLog
from app.services.embedding_service import EmbeddingService
from app.services.llm_types import (
    GenerationClient,
    GroundedAnswer,
    LLMUsage,
    ModelRefusalError,
    StructuredOutputError,
)
from app.services.prompt_builder import build_inline_rag_prompt, build_rag_prompt
from app.services.reranker import Reranker, rerank_chunks
from app.services.scope_classifier import (
    MVP1_OUT_OF_SCOPE_RE,
    RegexScopeClassifier,
    ScopeDecision,
)
from app.services.vector_search_service import RetrievedChunk, search_chunks

REFUSAL_MESSAGE = "문서에서 확인할 수 없습니다."
OUT_OF_SCOPE_MESSAGE = (
    "이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. "
    "문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다."
)

PARTIAL_CAVEAT = (
    "문서에서 질문의 일부에 대한 근거만 확인됩니다. 인용된 출처가 다루는 부분만 참고하고, "
    "나머지는 원문을 확인하세요."
)

_CITATION_RE = re.compile(r"\[(\d{1,2})\]")


class RefusalReason(StrEnum):
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    NO_EVIDENCE = "NO_EVIDENCE"
    MODEL_REFUSED = "MODEL_REFUSED"


@dataclass(slots=True)
class AskResult:
    answer: str
    sources: list[RetrievedChunk]
    retrieved: list[RetrievedChunk]
    retrieval_ms: int
    generation_ms: int
    refused: bool = False
    refusal_reason: RefusalReason | None = None
    # "structured" (cited_context_ids) | "parsed" ([n] in text) | "retrieved" (fallback) | "none"
    citation_mode: str = "structured"
    usage: LLMUsage | None = None
    # answered from part of the evidence: the model flagged insufficient evidence but cited it
    partial: bool = False
    caveat: str | None = None
    meta: dict[str, object] = field(default_factory=dict)


SearchFn = Callable[..., Awaitable[list[RetrievedChunk]]]


class ScopeClassifier(Protocol):
    needs_vector: bool

    def precheck(self, question: str) -> ScopeDecision | None: ...

    async def classify(
        self, question: str, query_vector: list[float] | None = None
    ) -> ScopeDecision: ...


def is_out_of_scope(question: str) -> bool:
    """MVP-1 regex (kept for callers/tests; RagService uses its ScopeClassifier)."""
    return bool(MVP1_OUT_OF_SCOPE_RE.search(question))


def is_model_refusal(answer: str) -> bool:
    return "확인할 수 없습니다" in answer and not _CITATION_RE.search(answer)


def extract_citations(answer: str, n_chunks: int) -> list[int]:
    """Return 0-based chunk indexes cited as [n] in the answer, in first-seen order."""
    return _valid_ids((int(m.group(1)) for m in _CITATION_RE.finditer(answer)), n_chunks)


def _valid_ids(one_based: Iterable[int], n_chunks: int) -> list[int]:
    seen: list[int] = []
    for value in one_based:
        idx = value - 1
        if 0 <= idx < n_chunks and idx not in seen:
            seen.append(idx)
    return seen


def _elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


class RagService:
    def __init__(
        self,
        embeddings: EmbeddingService,
        llm: GenerationClient,
        *,
        system_prompt: str,
        min_score: float,
        hybrid: bool = True,
        rrf_k: int = 60,
        search: SearchFn = search_chunks,
        scope: ScopeClassifier | None = None,
        reranker: Reranker | None = None,
        rerank_candidates: int = 30,
        rerank_min_score: float = 0.0,
        partial_answers: bool = True,
        inline_instructions: bool = False,
    ) -> None:
        self._embeddings = embeddings
        self._llm = llm
        self._system_prompt = system_prompt
        self._min_score = min_score
        self._hybrid = hybrid
        self._rrf_k = rrf_k
        self._search = search
        self._scope: ScopeClassifier = scope or RegexScopeClassifier()
        self._reranker = reranker
        self._rerank_candidates = rerank_candidates
        self._rerank_min_score = rerank_min_score
        self._partial_answers = partial_answers
        # eval-only prompt variant: `system_prompt` goes into the user turn, no system message
        self._inline_instructions = inline_instructions

    @property
    def provider(self) -> str:
        return self._llm.provider

    async def retrieve(
        self,
        session: AsyncSession,
        question: str,
        *,
        top_k: int,
        file_type: str | None = None,
        corpus: str | None = None,
    ) -> tuple[list[RetrievedChunk], int]:
        start = time.perf_counter()
        query_vector = await self._embeddings.embed_query(question)
        chunks, _, retrieval_ms = await self._retrieve_with(
            session, question, query_vector, start, top_k=top_k, file_type=file_type, corpus=corpus
        )
        return chunks, retrieval_ms

    async def _retrieve_with(
        self,
        session: AsyncSession,
        question: str,
        query_vector: list[float],
        start: float,
        *,
        top_k: int,
        file_type: str | None,
        corpus: str | None,
    ) -> tuple[list[RetrievedChunk], float | None, int]:
        """(top_k chunks, best cosine among all candidates, elapsed ms)."""
        n = max(top_k, self._rerank_candidates) if self._reranker else top_k
        chunks = await self._search(
            session,
            query_vector,
            top_k=n,
            file_type=file_type,
            query_text=question if self._hybrid else None,
            rrf_k=self._rrf_k,
            embedding_model=self._embeddings.model,
            corpus=corpus,
        )
        # the cosine gate compares the best candidate's cosine (= vector top-1) in both modes
        best_cosine = max((c.score for c in chunks), default=None)
        if self._reranker is not None and chunks:
            scores = await self._reranker.score(question, [c.text for c in chunks])
            chunks = rerank_chunks(chunks, scores, top_k)
        return chunks, best_cosine, _elapsed_ms(start)

    def _evidence(
        self, retrieved: list[RetrievedChunk], best_cosine: float | None
    ) -> list[RetrievedChunk]:
        """Chunks that go into the prompt; [] means NO_EVIDENCE (no LLM call)."""
        if self._reranker is None:
            return [c for c in retrieved if c.score >= self._min_score]
        if not retrieved or best_cosine is None or best_cosine < self._min_score:
            return []
        if (retrieved[0].rerank_score or 0.0) < self._rerank_min_score:
            return []
        # the cross-encoder already chose and ordered these top_k: all go into the prompt
        return retrieved

    async def ask(
        self,
        session: AsyncSession,
        question: str,
        *,
        top_k: int,
        file_type: str | None = None,
        corpus: str | None = None,
    ) -> AskResult:
        # Layer 1 (precise regex) refuses before any model call.
        if decision := self._scope.precheck(question):
            return await self._out_of_scope(session, question, decision, retrieval_ms=0)

        start = time.perf_counter()
        query_vector = await self._embeddings.embed_query(question)
        # Layer 2 (embedding kNN) reuses the query vector that retrieval needs anyway.
        decision = await self._scope.classify(question, query_vector)
        if decision.out_of_scope:
            return await self._out_of_scope(
                session, question, decision, retrieval_ms=_elapsed_ms(start)
            )

        retrieved, best_cosine, retrieval_ms = await self._retrieve_with(
            session, question, query_vector, start, top_k=top_k, file_type=file_type, corpus=corpus
        )
        evidence = self._evidence(retrieved, best_cosine)
        gate = {
            "bestCosine": best_cosine,
            "topRerank": retrieved[0].rerank_score if retrieved else None,
        }
        if not evidence:
            result = self._refusal(
                REFUSAL_MESSAGE,
                RefusalReason.NO_EVIDENCE,
                retrieved=retrieved,
                retrieval_ms=retrieval_ms,
            )
            result.meta["topScore"] = retrieved[0].score if retrieved else None
            result.meta["gate"] = gate
            result.meta["scope"] = {"method": decision.method, "score": decision.score}
            await self._log(session, question, result)
            return result

        result = await self._generate(question, evidence, retrieved, retrieval_ms)
        result.meta["gate"] = gate
        result.meta["scope"] = {"method": decision.method, "score": decision.score}
        await self._log(session, question, result)
        return result

    async def _out_of_scope(
        self, session: AsyncSession, question: str, decision: ScopeDecision, *, retrieval_ms: int
    ) -> AskResult:
        result = self._refusal(
            OUT_OF_SCOPE_MESSAGE,
            RefusalReason.OUT_OF_SCOPE,
            retrieved=[],
            retrieval_ms=retrieval_ms,
        )
        result.meta["scope"] = {"method": decision.method, "score": decision.score}
        await self._log(session, question, result)
        return result

    async def _generate(
        self,
        question: str,
        evidence: list[RetrievedChunk],
        retrieved: list[RetrievedChunk],
        retrieval_ms: int,
    ) -> AskResult:
        if self._inline_instructions:
            prompt = build_inline_rag_prompt(self._system_prompt, question, evidence)
            system: str | None = None
        else:
            prompt, system = build_rag_prompt(question, evidence), self._system_prompt
        start = time.perf_counter()
        schema_valid = True
        try:
            answer, usage = await self._llm.generate_answer(prompt, system=system)
        except ModelRefusalError as exc:
            result = self._refusal(
                REFUSAL_MESSAGE,
                RefusalReason.MODEL_REFUSED,
                retrieved=retrieved,
                retrieval_ms=retrieval_ms,
            )
            result.generation_ms = _elapsed_ms(start)
            result.usage = exc.usage
            return result
        except StructuredOutputError as exc:
            # Small local models occasionally break the schema: keep the text answer and
            # recover citations from its [n] markers.
            answer = GroundedAnswer(
                answer=exc.raw_text,
                cited_context_ids=[],
                insufficient_evidence=is_model_refusal(exc.raw_text),
            )
            usage = exc.usage
            schema_valid = False
        generation_ms = _elapsed_ms(start)

        cited = _valid_ids(answer.cited_context_ids, len(evidence))
        mode = "structured"
        if not cited:
            cited, mode = extract_citations(answer.answer, len(evidence)), "parsed"
        explicit_refusal = is_model_refusal(answer.answer)
        # Partial answer: flagged insufficient, yet it cites the evidence it did use.
        partial = (
            answer.insufficient_evidence
            and bool(cited)
            and not explicit_refusal
            and self._partial_answers
        )
        if (answer.insufficient_evidence and not partial) or explicit_refusal:
            result = self._refusal(
                answer.answer or REFUSAL_MESSAGE,
                RefusalReason.MODEL_REFUSED,
                retrieved=retrieved,
                retrieval_ms=retrieval_ms,
            )
            result.generation_ms = generation_ms
            result.usage = usage
            result.meta["schemaValid"] = schema_valid
            return result

        sources = [evidence[i] for i in cited] if cited else evidence
        result = AskResult(
            answer=answer.answer,
            sources=sources,
            retrieved=retrieved,
            retrieval_ms=retrieval_ms,
            generation_ms=generation_ms,
            citation_mode=mode if cited else "retrieved",
            usage=usage,
            partial=partial,
            caveat=PARTIAL_CAVEAT if partial else None,
        )
        result.meta["schemaValid"] = schema_valid
        return result

    @staticmethod
    def _refusal(
        message: str,
        reason: RefusalReason,
        *,
        retrieved: list[RetrievedChunk],
        retrieval_ms: int,
    ) -> AskResult:
        return AskResult(
            answer=message,
            sources=[],
            retrieved=retrieved,
            retrieval_ms=retrieval_ms,
            generation_ms=0,
            refused=True,
            refusal_reason=reason,
            citation_mode="none",
        )

    async def _log(self, session: AsyncSession, question: str, result: AskResult) -> None:
        usage = result.usage
        session.add(
            AskLog(
                question=question,
                retrieved_chunk_ids=[c.chunk_id for c in result.retrieved],
                answer=result.answer,
                sources=[
                    {
                        "chunkId": str(c.chunk_id),
                        "fileName": c.file_name,
                        "pageNumber": c.page_number,
                        "sectionTitle": c.section_title,
                        "chunkIndex": c.chunk_index,
                        "score": round(c.score, 4),
                        "rerankScore": (
                            None if c.rerank_score is None else round(c.rerank_score, 4)
                        ),
                    }
                    for c in result.sources
                ],
                retrieval_ms=result.retrieval_ms,
                generation_ms=result.generation_ms,
                refusal_reason=result.refusal_reason,
                llm_provider=usage.provider if usage else None,
                llm_model=usage.model if usage else None,
                input_tokens=usage.input_tokens if usage else None,
                output_tokens=usage.output_tokens if usage else None,
            )
        )
        await session.commit()
