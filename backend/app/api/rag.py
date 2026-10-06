from fastapi import APIRouter

from app.api.deps import ContainerDep, SessionDep
from app.schemas.rag import (
    AskResponse,
    LatencyOut,
    LLMUsageOut,
    QuestionRequest,
    RetrievedChunkOut,
    RetrieveResponse,
    SourceOut,
)
from app.services.vector_search_service import RetrievedChunk

router = APIRouter(prefix="/api", tags=["rag"])


def _source(chunk: RetrievedChunk) -> SourceOut:
    return SourceOut(
        chunk_id=chunk.chunk_id,
        file_name=chunk.file_name,
        page_number=chunk.page_number,
        section_title=chunk.section_title,
        chunk_index=chunk.chunk_index,
        score=round(chunk.score, 4),
        rerank_score=None if chunk.rerank_score is None else round(chunk.rerank_score, 4),
    )


@router.post("/ask", response_model=AskResponse, response_model_by_alias=True)
async def ask(body: QuestionRequest, container: ContainerDep, session: SessionDep) -> AskResponse:
    result = await container.rag.ask(
        session,
        body.question,
        top_k=body.top_k or container.settings.top_k,
        file_type=body.file_type,
        corpus=body.corpus,
    )
    return AskResponse(
        answer=result.answer,
        sources=[_source(c) for c in result.sources],
        refused=result.refused,
        refusal_reason=result.refusal_reason,
        partial=result.partial,
        caveat=result.caveat,
        citation_mode=result.citation_mode,
        latency_ms=LatencyOut(retrieval=result.retrieval_ms, generation=result.generation_ms),
        llm=(
            LLMUsageOut(
                provider=result.usage.provider,
                model=result.usage.model,
                input_tokens=result.usage.input_tokens,
                output_tokens=result.usage.output_tokens,
            )
            if result.usage
            else None
        ),
    )


@router.post("/retrieve", response_model=RetrieveResponse, response_model_by_alias=True)
async def retrieve(
    body: QuestionRequest, container: ContainerDep, session: SessionDep
) -> RetrieveResponse:
    chunks, retrieval_ms = await container.rag.retrieve(
        session,
        body.question,
        top_k=body.top_k or container.settings.top_k,
        file_type=body.file_type,
        corpus=body.corpus,
    )
    return RetrieveResponse(
        chunks=[
            RetrievedChunkOut(
                chunk_id=c.chunk_id,
                text=c.text,
                file_name=c.file_name,
                score=round(c.score, 4),
                metadata={
                    "fileType": c.file_type,
                    "chunkIndex": c.chunk_index,
                    "pageNumber": c.page_number,
                    "sectionTitle": c.section_title,
                    "rerankScore": c.rerank_score,
                },
            )
            for c in chunks
        ],
        retrieval_ms=retrieval_ms,
    )
