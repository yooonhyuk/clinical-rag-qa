"""Retrieval-augmented question answering with source citations and a refusal policy.

Refusal policy (checked in this order, the first two never call the LLM):
1. OUT_OF_SCOPE      - the question asks for image reading / diagnosis / treatment.
2. NO_EVIDENCE       - nothing retrieved, or the best cosine score < `min_score`.
3. MODEL_REFUSED     - the LLM reports `insufficient_evidence` (structured output), answers
                       "문서에서 확인할 수 없습니다" without citations, or the provider declines.

Both generation providers (Ollama, Claude API) return the same `GroundedAnswer` structure.
"""

import re
import time
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass, field
from enum import StrEnum

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
from app.services.prompt_builder import build_rag_prompt
from app.services.vector_search_service import RetrievedChunk, search_chunks

REFUSAL_MESSAGE = "문서에서 확인할 수 없습니다."
OUT_OF_SCOPE_MESSAGE = (
    "이 시스템은 영상 판독, 질병 진단, 치료·처방 조언을 하지 않습니다. "
    "문서·업로드·QA 운영 관련 질문만 답변할 수 있습니다."
)

# Heuristic guard for clinical-judgement requests. Deliberately narrow: it should catch
# "is there a nodule in this CT?" but not "does the analyzer perform image reading?".
_OUT_OF_SCOPE_RE = re.compile(
    r"(결절|병변|종양|암\s*(이|인지|일까|여부)|악성|양성인지|"
    r"진단(해|을\s*내려|명)|판독(해|해줘|결과를\s*알려)|소견(을|이)\s*(알려|뭐)|"
    r"처방|투약|복용|용량을|치료\s*(방법|법|해야)|어떤\s*약)"
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
    meta: dict[str, object] = field(default_factory=dict)


SearchFn = Callable[..., Awaitable[list[RetrievedChunk]]]


def is_out_of_scope(question: str) -> bool:
    return bool(_OUT_OF_SCOPE_RE.search(question))


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
        search: SearchFn = search_chunks,
    ) -> None:
        self._embeddings = embeddings
        self._llm = llm
        self._system_prompt = system_prompt
        self._min_score = min_score
        self._search = search

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
    ) -> tuple[list[RetrievedChunk], int]:
        start = time.perf_counter()
        query_vector = await self._embeddings.embed_query(question)
        chunks = await self._search(session, query_vector, top_k=top_k, file_type=file_type)
        return chunks, _elapsed_ms(start)

    async def ask(
        self,
        session: AsyncSession,
        question: str,
        *,
        top_k: int,
        file_type: str | None = None,
    ) -> AskResult:
        if is_out_of_scope(question):
            result = self._refusal(
                OUT_OF_SCOPE_MESSAGE, RefusalReason.OUT_OF_SCOPE, retrieved=[], retrieval_ms=0
            )
            await self._log(session, question, result)
            return result

        retrieved, retrieval_ms = await self.retrieve(
            session, question, top_k=top_k, file_type=file_type
        )
        evidence = [c for c in retrieved if c.score >= self._min_score]
        if not evidence:
            result = self._refusal(
                REFUSAL_MESSAGE,
                RefusalReason.NO_EVIDENCE,
                retrieved=retrieved,
                retrieval_ms=retrieval_ms,
            )
            result.meta["topScore"] = retrieved[0].score if retrieved else None
            await self._log(session, question, result)
            return result

        result = await self._generate(question, evidence, retrieved, retrieval_ms)
        await self._log(session, question, result)
        return result

    async def _generate(
        self,
        question: str,
        evidence: list[RetrievedChunk],
        retrieved: list[RetrievedChunk],
        retrieval_ms: int,
    ) -> AskResult:
        prompt = build_rag_prompt(question, evidence)
        start = time.perf_counter()
        try:
            answer, usage = await self._llm.generate_answer(prompt, system=self._system_prompt)
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
        generation_ms = _elapsed_ms(start)

        if answer.insufficient_evidence or is_model_refusal(answer.answer):
            result = self._refusal(
                answer.answer or REFUSAL_MESSAGE,
                RefusalReason.MODEL_REFUSED,
                retrieved=retrieved,
                retrieval_ms=retrieval_ms,
            )
            result.generation_ms = generation_ms
            result.usage = usage
            return result

        cited = _valid_ids(answer.cited_context_ids, len(evidence))
        mode = "structured"
        if not cited:
            cited, mode = extract_citations(answer.answer, len(evidence)), "parsed"
        sources = [evidence[i] for i in cited] if cited else evidence
        return AskResult(
            answer=answer.answer,
            sources=sources,
            retrieved=retrieved,
            retrieval_ms=retrieval_ms,
            generation_ms=generation_ms,
            citation_mode=mode if cited else "retrieved",
            usage=usage,
        )

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
