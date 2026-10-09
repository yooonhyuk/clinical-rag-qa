from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import ContainerDep, SessionDep, resolve_allowed_path
from app.models import Document, DocumentStatus
from app.schemas.documents import (
    CorpusListResponse,
    CorpusOut,
    DocumentListResponse,
    DocumentOut,
    IndexableFolderOut,
    IndexRequest,
    IndexResponse,
)
from app.services.llm_guardrail import (
    ExternalLLMNotAllowedError,
    allows_external,
    corpus_classification,
    corpus_name,
    ensure_corpus_allows_external,
)

router = APIRouter(prefix="/api", tags=["documents"])


@router.get("/documents", response_model=DocumentListResponse, response_model_by_alias=True)
async def list_documents(session: SessionDep) -> DocumentListResponse:
    rows = (await session.scalars(select(Document).order_by(Document.file_name))).all()
    return DocumentListResponse(documents=[DocumentOut.model_validate(d) for d in rows])


@router.get("/corpora", response_model=CorpusListResponse, response_model_by_alias=True)
async def list_corpora(container: ContainerDep, session: SessionDep) -> CorpusListResponse:
    """Indexed corpora (for the UI's corpus selector) and the folders that can be indexed."""
    settings = container.settings
    rows = (
        await session.execute(
            select(
                Document.corpus,
                Document.classification,
                func.count(),
                func.coalesce(func.sum(Document.chunk_count), 0),
            )
            .where(Document.status == DocumentStatus.INDEXED)
            .group_by(Document.corpus, Document.classification)
            .order_by(Document.corpus)
        )
    ).all()
    corpora = [
        CorpusOut(
            name=name,
            classification=classification,
            documents=docs,
            chunks=int(chunks),
            external_allowed=allows_external(classification),
        )
        for name, classification, docs, chunks in rows
    ]
    candidates: list[Path] = [settings.samples_path / "documents", settings.corpora_path / "public"]
    if settings.private_corpus_path is not None:
        candidates.append(settings.private_corpus_path.expanduser())
    marker = settings.corpus_marker_file
    folders = [
        IndexableFolderOut(
            name=corpus_name(folder, marker),
            path=str(folder),
            classification=corpus_classification(folder, marker),
            external_allowed=allows_external(corpus_classification(folder, marker)),
        )
        for folder in candidates
        if folder.is_dir()
    ]
    return CorpusListResponse(
        corpora=corpora, folders=folders, llm_provider=container.generator.provider
    )


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
