"""samples/office (synthetic docx / xlsx / permission-only AES PDF) index end to end."""

from pathlib import Path

import pytest
from sqlalchemy import select

from app.models import Chunk, Document, DocumentStatus
from app.services.embedding_service import EmbeddingService
from app.services.indexing_pipeline import IndexingPipeline
from tests.fakes import DIM, FakeOllama

pytestmark = pytest.mark.integration
OFFICE = Path(__file__).resolve().parents[2] / "samples" / "office"


async def test_office_samples_are_indexed_with_type_and_section_titles(session_factory) -> None:
    embeddings = EmbeddingService(FakeOllama(), dimension=DIM, concurrency=2, batch_size=4)
    pipeline = IndexingPipeline(
        session_factory, embeddings, parse_concurrency=2, chunk_size=500, chunk_overlap=80
    )
    job = await pipeline.run(OFFICE)
    assert (job.status, job.total, job.indexed, job.failed) == ("COMPLETED", 3, 3, 0)

    async with session_factory() as s:
        docs = {d.file_name: d for d in (await s.scalars(select(Document))).all()}
        assert {d.status for d in docs.values()} == {DocumentStatus.INDEXED}
        chunks = (await s.scalars(select(Chunk).join(Document))).all()
        by_doc = {name: [c for c in chunks if c.document_id == d.id] for name, d in docs.items()}

    docx = by_doc["demo-imaging-charter.docx"]
    assert {c.file_type for c in docx} == {"docx"}
    assert "2. 판독 절차 > 2.1 판독자 구성" in {c.section_title for c in docx}
    assert all(c.page_number is None for c in docx)
    assert not any("DO-NOT-INDEX" in c.text for c in docx)

    xlsx = by_doc["demo-imaging-schedule.xlsx"]
    assert {c.file_type for c in xlsx} == {"xlsx"}
    assert {c.section_title for c in xlsx} == {"촬영 일정", "메모"}

    pdf = by_doc["demo-signed-protocol.pdf"]
    assert {c.file_type for c in pdf} == {"pdf"}
    assert {c.page_number for c in pdf} == {1}
