"""Indexing pipeline -> pgvector -> search, against a real PostgreSQL + pgvector."""

import shutil
from pathlib import Path

import httpx
import pytest
from sqlalchemy import func, select

from app.config import Settings
from app.container import build_container
from app.main import create_app
from app.models import AskLog, Chunk, Document, DocumentStatus
from app.services.embedding_service import EmbeddingService
from app.services.indexing_pipeline import IndexingPipeline
from app.services.vector_search_service import search_chunks
from tests.fakes import DIM, FakeOllama

pytestmark = pytest.mark.integration
PUBLIC = Path(__file__).resolve().parents[2] / "corpus" / "public"


@pytest.fixture
def corpus(tmp_path: Path, sample_docs_dir: Path) -> Path:
    root = tmp_path / "corpus"
    shutil.copytree(sample_docs_dir, root)
    (root / "empty.md").write_text("  \n", encoding="utf-8")
    (root / "notes.docx").write_bytes(b"PK\x03\x04 not supported in MVP-1")
    shutil.copy(root / "qa-checklist.md", root / "qa-checklist-copy.md")
    return root


def _pipeline(factory, llm: FakeOllama) -> IndexingPipeline:
    embeddings = EmbeddingService(llm, dimension=DIM, concurrency=2, batch_size=4)
    return IndexingPipeline(
        factory, embeddings, parse_concurrency=2, chunk_size=500, chunk_overlap=80
    )


async def test_index_statuses_failures_and_duplicates(session_factory, corpus) -> None:
    job = await _pipeline(session_factory, FakeOllama()).run(corpus)
    assert (job.status, job.total, job.indexed, job.failed, job.skipped_duplicate) == (
        "COMPLETED",
        9,
        6,
        2,
        1,
    )
    async with session_factory() as s:
        docs = {d.file_name: d for d in (await s.scalars(select(Document))).all()}
        assert docs["empty.md"].error_type == "EMPTY_DOCUMENT"
        assert docs["notes.docx"].error_type == "UNSUPPORTED_FILE_TYPE"
        assert docs["dicom-upload-guide.md"].status == DocumentStatus.INDEXED
        # identical content -> only the first file (by path order) gets a row
        pair = {"qa-checklist.md", "qa-checklist-copy.md"}
        assert len(pair & docs.keys()) == 1
        pages = (
            await s.scalars(
                select(Chunk.page_number).join(Document).where(Document.file_type == "pdf")
            )
        ).all()
        assert set(pages) == {1, 2, 3}
        total_chunks = await s.scalar(select(func.count()).select_from(Chunk))
        assert total_chunks == sum(d.chunk_count for d in docs.values())
    dup = next(d for d in job.details if d["status"] == "SKIPPED_DUPLICATE")
    assert {dup["fileName"], dup["duplicateOf"]} == pair

    # Re-running skips everything already indexed and retries the failed ones.
    rerun = await _pipeline(session_factory, FakeOllama()).run(corpus)
    assert (rerun.indexed, rerun.failed, rerun.skipped_duplicate) == (0, 2, 7)


async def test_embedding_failure_rolls_back_document(session_factory, tmp_path) -> None:
    root = tmp_path / "one"
    root.mkdir()
    (root / "big.md").write_text("# T\n" + ("문장입니다. " * 400), encoding="utf-8")
    job = await _pipeline(session_factory, FakeOllama(fail_embed_after=2)).run(root)
    assert job.failed == 1
    async with session_factory() as s:
        doc = await s.scalar(select(Document))
        assert doc.status == DocumentStatus.FAILED
        assert doc.error_type == "OLLAMA_UNAVAILABLE"
        assert await s.scalar(select(func.count()).select_from(Chunk)) == 0


async def test_api_index_then_ask_end_to_end(session_factory, corpus, tmp_path) -> None:
    settings = Settings(
        _env_file=None,
        raw_docs_path=corpus,
        dicom_path=tmp_path,
        samples_path=tmp_path,
        min_relevance_score=0.1,
        embedding_query_prefix="",
        embedding_document_prefix="",
    )
    container = build_container(settings, ollama=FakeOllama(), session_factory=session_factory)  # type: ignore[arg-type]
    app = create_app(container)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        assert (await c.post("/api/index", json={})).json()["indexed"] == 6
        docs = (await c.get("/api/documents")).json()["documents"]
        assert {d["status"] for d in docs} == {"INDEXED", "FAILED"}

        hits = (
            await c.post(
                "/api/retrieve", json={"question": "E103 Subject ID not matched", "topK": 3}
            )
        ).json()["chunks"]
        assert hits[0]["fileName"] == "error-code-guide.md"
        assert hits[0]["score"] >= hits[-1]["score"]

        md_only = (
            await c.post("/api/retrieve", json={"question": "SliceThickness", "fileType": "pdf"})
        ).json()["chunks"]
        assert md_only and all(h["metadata"]["fileType"] == "pdf" for h in md_only)

        answer = (await c.post("/api/ask", json={"question": "E103 오류는 무엇인가요?"})).json()
        assert answer["refused"] is False and answer["sources"]

    async with session_factory() as s:
        log = await s.scalar(select(AskLog))
        assert log.llm_provider == "ollama" and log.input_tokens == 10
        assert log.retrieved_chunk_ids


async def test_hybrid_search_ranks_korean_text_when_embeddings_degenerate(
    session_factory, sample_docs_dir
) -> None:
    """nomic-embed-text maps every Hangul word to [UNK]; simulate that with a constant query
    vector and check that the pg_trgm channel still finds the right chunk.

    With a constant query vector the vector channel is pure noise (all cosines tie), so RRF can
    only promise that the lexical channel's best match is fused in, not that it ends up first:
    a chunk that is mid-ranked in both lists can outscore it. This used to assert rank 1 and
    broke when the toy PDF gained heading sections (28 -> 32 chunks).
    """
    await _pipeline(session_factory, FakeOllama()).run(sample_docs_dir)
    question = "한 번에 업로드할 수 있는 최대 용량은 얼마인가요?"
    constant = [1.0] + [0.0] * (DIM - 1)
    async with session_factory() as s:
        hybrid = await search_chunks(s, constant, top_k=50, query_text=question)
        vector_only = await search_chunks(s, constant, top_k=3)
    best_lexical = max(hybrid, key=lambda c: c.lexical_score or 0.0)
    assert best_lexical.file_name == "dicom-upload-guide.md"
    assert best_lexical.section_title == "Supported File Formats"
    assert best_lexical.lexical_score is not None and best_lexical.lexical_score > 0.5
    assert all(c.lexical_score is None for c in vector_only)


async def test_corpora_are_tagged_and_search_can_be_restricted(
    session_factory, sample_docs_dir, tmp_path
) -> None:
    """toy (marker name) + a second folder without a marker (folder name) in one DB."""
    other = tmp_path / "publicish"
    other.mkdir()
    shutil.copy(PUBLIC / "07_irecist_how_to_2020.xml", other)
    pipeline = _pipeline(session_factory, FakeOllama())
    await pipeline.run(sample_docs_dir)
    await pipeline.run(other)

    async with session_factory() as s:
        corpora = dict((await s.execute(select(Document.file_name, Document.corpus))).all())
    assert corpora["dicom-upload-guide.md"] == "toy"
    assert corpora["07_irecist_how_to_2020.xml"] == "publicish"

    query = FakeOllama()
    vector = (await query.embed(["iRECIST iUPD iCPD confirmation"]))[0]
    async with session_factory() as s:
        everything = await search_chunks(s, vector, top_k=200)
        toy_only = await search_chunks(s, vector, top_k=50, corpus="toy")
        other_only = await search_chunks(s, vector, top_k=50, corpus="publicish")
    assert {c.file_name for c in everything} >= {"07_irecist_how_to_2020.xml", "qa-checklist.md"}
    assert "07_irecist_how_to_2020.xml" not in {c.file_name for c in toy_only}
    assert {c.file_name for c in other_only} == {"07_irecist_how_to_2020.xml"}
    assert all(c.page_number is None for c in other_only)
    assert any("Table" in (c.section_title or "") or c.section_title for c in other_only)


async def test_classification_is_stored_and_filters_external_search(
    session_factory, sample_docs_dir, tmp_path
) -> None:
    """A licensed-local-only folder (marker with include globs) next to the toy corpus."""
    from app.services.llm_guardrail import ALLOWED_CLASSIFICATIONS

    private = tmp_path / "private"
    (private / "protocols").mkdir(parents=True)
    shutil.copy(PUBLIC / "07_irecist_how_to_2020.xml", private / "protocols")
    (private / "protocols" / "manifest.txt").write_text("NCT00000000 Prot_000.pdf\n")
    (private / ".corpus.yaml").write_text(
        "name: private\nclassification: licensed-local-only\ninclude: ['protocols/*.xml']\n"
    )
    pipeline = _pipeline(session_factory, FakeOllama())
    await pipeline.run(sample_docs_dir)
    job = await pipeline.run(private)
    assert job.total == 1  # manifest.txt is outside the include globs

    async with session_factory() as s:
        rows = (await s.execute(select(Document.corpus, Document.classification))).all()
    assert set(rows) == {("toy", "synthetic-sample"), ("private", "licensed-local-only")}

    vector = (await FakeOllama().embed(["iRECIST iUPD iCPD confirmation"]))[0]
    async with session_factory() as s:
        external = await search_chunks(
            s, vector, top_k=200, classifications=ALLOWED_CLASSIFICATIONS
        )
    async with session_factory() as s:
        exact = await search_chunks(s, vector, top_k=200, exact=True)
    async with session_factory() as s:
        iterative = await search_chunks(
            s, vector, top_k=10, corpus="private", iterative_scan="relaxed_order"
        )
    assert "07_irecist_how_to_2020.xml" not in {c.file_name for c in external}
    assert "07_irecist_how_to_2020.xml" in {c.file_name for c in exact}
    assert {c.file_name for c in iterative} == {"07_irecist_how_to_2020.xml"}
