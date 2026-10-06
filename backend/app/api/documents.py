from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import ContainerDep, SessionDep, resolve_allowed_path
from app.models import Document
from app.schemas.documents import DocumentListResponse, DocumentOut, IndexRequest, IndexResponse
from app.services.llm_guardrail import ExternalLLMNotAllowedError, ensure_corpus_allows_external

router = APIRouter(prefix="/api", tags=["documents"])


@router.get("/documents", response_model=DocumentListResponse, response_model_by_alias=True)
async def list_documents(session: SessionDep) -> DocumentListResponse:
    rows = (await session.scalars(select(Document).order_by(Document.file_name))).all()
    return DocumentListResponse(documents=[DocumentOut.model_validate(d) for d in rows])


@router.post("/index", response_model=IndexResponse, response_model_by_alias=True)
async def run_index(container: ContainerDep, body: IndexRequest | None = None) -> IndexResponse:
    settings = container.settings
    raw_path = (body.path if body else None) or str(settings.raw_docs_path)
    root = resolve_allowed_path(raw_path, settings.allowed_roots)
    if settings.llm_provider != "ollama":
        # External generation: every indexed folder must carry the sample/non-sensitive marker.
        try:
            ensure_corpus_allows_external(root, settings.corpus_marker_file)
        except ExternalLLMNotAllowedError as exc:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    job = await container.pipeline.run(root, corpus=body.corpus if body else None)
    return IndexResponse(
        job_id=job.id,
        status=job.status,
        total=job.total,
        indexed=job.indexed,
        failed=job.failed,
        skipped_duplicate=job.skipped_duplicate,
        details=job.details,
    )
