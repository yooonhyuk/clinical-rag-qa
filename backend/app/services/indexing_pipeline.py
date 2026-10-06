"""Async document indexing pipeline.

    scan (to_thread) -> per document, at most PARSE_CONCURRENCY in flight:
        extract (to_thread) -> chunk -> embed (EmbeddingService: batch gather + Semaphore)
        -> one transaction: insert chunks + status INDEXED

A failure anywhere rolls back that document's chunks and leaves only `status=FAILED` with a
typed `error_type`, so search never sees a half-indexed document.
"""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import Chunk, Document, DocumentStatus, IndexJob
from app.models.base import utcnow
from app.services.chunker import chunk_sections
from app.services.document_loader import DiscoveredFile, scan_documents
from app.services.embedding_service import EmbeddingService
from app.services.llm_guardrail import corpus_name
from app.services.llm_types import LLMError
from app.services.text_extractor import ExtractionError, extract

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class FileOutcome:
    file_name: str
    file_path: str
    status: str
    chunk_count: int = 0
    error_type: str | None = None
    error_message: str | None = None
    duplicate_of: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "fileName": self.file_name,
            "filePath": self.file_path,
            "status": self.status,
            "chunkCount": self.chunk_count,
            "errorType": self.error_type,
            "errorMessage": self.error_message,
            "duplicateOf": self.duplicate_of,
        }


class _DocumentFailure(Exception):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type


class IndexingPipeline:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        embeddings: EmbeddingService,
        *,
        parse_concurrency: int = 2,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        marker_file: str = ".corpus.yaml",
    ) -> None:
        self._session_factory = session_factory
        self._embeddings = embeddings
        self._parse_concurrency = parse_concurrency
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._marker_file = marker_file

    async def run(self, root: Path, *, corpus: str | None = None) -> IndexJob:
        """Index every file under `root`, tagging documents with `corpus` (default: the
        `.corpus.yaml` name, else the folder name)."""
        files = await asyncio.to_thread(scan_documents, root)
        corpus = corpus or corpus_name(root, self._marker_file)

        async with self._session_factory() as session:
            job = IndexJob(
                status="RUNNING", total=len(files), embedding_model=self._embeddings.model
            )
            session.add(job)
            await session.commit()

        outcomes: list[FileOutcome] = []
        unique: list[DiscoveredFile] = []
        first_seen: dict[str, DiscoveredFile] = {}
        for f in files:
            if original := first_seen.get(f.checksum):
                outcomes.append(_duplicate(f, original.file_name))
            else:
                first_seen[f.checksum] = f
                unique.append(f)

        limiter = asyncio.Semaphore(self._parse_concurrency)

        async def bounded(f: DiscoveredFile) -> FileOutcome:
            async with limiter:
                return await self._process(f, corpus)

        status = "COMPLETED"
        try:
            outcomes.extend(await asyncio.gather(*(bounded(f) for f in unique)))
        except Exception:  # defensive: _process converts per-file errors into outcomes
            logger.exception("Indexing job crashed")
            status = "FAILED"

        async with self._session_factory() as session:
            job = await session.get_one(IndexJob, job.id)
            job.status = status
            job.indexed = sum(o.status == DocumentStatus.INDEXED for o in outcomes)
            job.failed = sum(o.status == DocumentStatus.FAILED for o in outcomes)
            job.skipped_duplicate = sum(
                o.status == DocumentStatus.SKIPPED_DUPLICATE for o in outcomes
            )
            job.details = [o.as_dict() for o in sorted(outcomes, key=lambda o: o.file_path)]
            job.finished_at = utcnow()
            await session.commit()
            return job

    async def _process(self, f: DiscoveredFile, corpus: str | None = None) -> FileOutcome:
        async with self._session_factory() as session:
            doc, duplicate_of = await self._register(session, f, corpus)
            if doc is None:
                return _duplicate(f, duplicate_of)
            try:
                count = await self._index_document(session, doc, f)
                return FileOutcome(f.file_name, str(f.path), DocumentStatus.INDEXED, count)
            except Exception as exc:
                await session.rollback()
                error_type, message = _classify(exc)
                logger.warning("Indexing failed for %s: %s %s", f.path, error_type, message)
                doc.status = DocumentStatus.FAILED
                doc.error_type = error_type
                doc.error_message = message[:2000]
                doc.chunk_count = 0
                await session.commit()
                return FileOutcome(
                    f.file_name, str(f.path), DocumentStatus.FAILED, 0, error_type, message
                )

    async def _register(
        self, session: AsyncSession, f: DiscoveredFile, corpus: str | None = None
    ) -> tuple[Document | None, str | None]:
        """Create (or reuse a FAILED / other-model) document row. (None, name) on duplicate.

        A document indexed with a different embedding model is re-embedded: its old vectors
        are not comparable with the configured model's query vectors.
        """
        existing = await session.scalar(select(Document).where(Document.checksum == f.checksum))
        if (
            existing is not None
            and existing.status != DocumentStatus.FAILED
            and existing.embedding_model == self._embeddings.model
        ):
            if corpus is not None and existing.corpus != corpus:
                existing.corpus = corpus  # e.g. a row indexed before Alembic 0005
                await session.commit()
            return None, existing.file_name

        doc = existing or Document(checksum=f.checksum)
        doc.file_name = f.file_name
        doc.file_path = str(f.path)
        doc.file_type = f.file_type
        doc.corpus = corpus
        doc.status = DocumentStatus.DISCOVERED
        doc.error_type = None
        doc.error_message = None
        session.add(doc)
        try:
            await session.commit()
        except IntegrityError:  # concurrent insert of identical content
            await session.rollback()
            return None, None
        return doc, None

    async def _set_status(self, session: AsyncSession, doc: Document, status: str) -> None:
        doc.status = status
        await session.commit()

    async def _index_document(self, session: AsyncSession, doc: Document, f: DiscoveredFile) -> int:
        if not f.supported:
            raise ExtractionError("UNSUPPORTED_FILE_TYPE", f"Unsupported file type: .{f.file_type}")

        # CPU-bound parsing runs in a worker thread so the event loop keeps serving requests.
        sections = await asyncio.to_thread(extract, f.path, f.file_type)
        await self._set_status(session, doc, DocumentStatus.EXTRACTED)

        chunks = chunk_sections(sections, size=self._chunk_size, overlap=self._chunk_overlap)
        if not chunks:
            raise ExtractionError("EMPTY_DOCUMENT", "No chunks produced")
        await self._set_status(session, doc, DocumentStatus.CHUNKED)

        vectors = await self._embeddings.embed_documents([c.text for c in chunks])
        await self._set_status(session, doc, DocumentStatus.EMBEDDED)

        # Single transaction: replace chunks + mark INDEXED. Rolled back as a unit on failure.
        await session.execute(delete(Chunk).where(Chunk.document_id == doc.id))
        session.add_all(
            Chunk(
                document_id=doc.id,
                chunk_index=c.chunk_index,
                file_type=f.file_type,
                page_number=c.page_number,
                section_title=c.section_title,
                text=c.text,
                embedding=vector,
                embedding_model=self._embeddings.model,
            )
            for c, vector in zip(chunks, vectors, strict=True)
        )
        doc.status = DocumentStatus.INDEXED
        doc.chunk_count = len(chunks)
        doc.embedding_model = self._embeddings.model
        doc.indexed_at = utcnow()
        await session.commit()
        return len(chunks)


def _duplicate(f: DiscoveredFile, duplicate_of: str | None) -> FileOutcome:
    return FileOutcome(
        f.file_name, str(f.path), DocumentStatus.SKIPPED_DUPLICATE, duplicate_of=duplicate_of
    )


def _classify(exc: Exception) -> tuple[str, str]:
    if isinstance(exc, ExtractionError | LLMError):
        return exc.error_type, str(exc)
    if isinstance(exc, SQLAlchemyError):
        return "DB_ERROR", str(exc).splitlines()[0]
    return "UNEXPECTED_ERROR", repr(exc)
