"""Document editions against a real PostgreSQL + pgvector: is_latest after indexing, the search
filter on both channels, migration 0007 and the API fields."""

import asyncio
from datetime import date
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select, text

from app.config import Settings
from app.container import build_container
from app.main import create_app
from app.models import Document
from app.services.embedding_service import EmbeddingService
from app.services.indexing_pipeline import IndexingPipeline
from app.services.vector_search_service import search_chunks
from tests.fakes import DIM, FakeOllama, hash_embedding

pytestmark = pytest.mark.integration
BACKEND = Path(__file__).resolve().parents[2] / "backend"
TOPIC = "Subject ID mapping error E103 upload validation"


def _pipeline(factory) -> IndexingPipeline:
    embeddings = EmbeddingService(FakeOllama(), dimension=DIM, batch_size=4)
    return IndexingPipeline(factory, embeddings, chunk_size=500, chunk_overlap=80)


def _write(root: Path, name: str, extra: str = "") -> None:
    root.mkdir(exist_ok=True)
    (root / name).write_text(f"# Guide\n{TOPIC}. Edition note: {name} {extra}\n", encoding="utf-8")


async def _flags(factory) -> dict[str, bool]:
    async with factory() as s:
        return {d.file_name: d.is_latest for d in (await s.scalars(select(Document))).all()}


async def _names(factory, *, latest_only: bool, hybrid: bool = False) -> set[str]:
    async with factory() as s:
        hits = await search_chunks(
            s,
            hash_embedding(TOPIC),
            top_k=10,
            query_text=TOPIC if hybrid else None,
            latest_only=latest_only,
        )
    return {h.file_name for h in hits}


async def test_two_editions_default_search_skips_the_old_one(session_factory, tmp_path) -> None:
    root = tmp_path / "docs"
    _write(root, "sample guide v1.md")
    _write(root, "sample guide v2.md")
    _write(root, "standalone notes.md")
    job = await _pipeline(session_factory).run(root)
    assert job.indexed == 3
    assert await _flags(session_factory) == {
        "sample guide v1.md": False,
        "sample guide v2.md": True,
        "standalone notes.md": True,
    }
    everything = {"sample guide v1.md", "sample guide v2.md", "standalone notes.md"}
    for hybrid in (False, True):  # the lexical (pg_trgm) channel gets the same filter
        assert await _names(session_factory, latest_only=False, hybrid=hybrid) == everything
        assert await _names(session_factory, latest_only=True, hybrid=hybrid) == everything - {
            "sample guide v1.md"
        }
    async with session_factory() as s:
        doc = await s.scalar(select(Document).where(Document.file_name == "sample guide v2.md"))
        assert (doc.doc_family, doc.version_label, doc.version_source) == (
            "sample guide",
            "v2",
            "filename",
        )


async def test_indexing_a_newer_edition_demotes_the_previous_latest(
    session_factory, tmp_path
) -> None:
    root = tmp_path / "docs"
    _write(root, "sample guide v1.md")
    await _pipeline(session_factory).run(root)
    assert await _flags(session_factory) == {"sample guide v1.md": True}
    _write(root, "sample guide v2.md")
    await _pipeline(session_factory).run(root)
    assert await _flags(session_factory) == {
        "sample guide v1.md": False,
        "sample guide v2.md": True,
    }
    _write(root, "sample guide v10.md")  # numeric, not textual, order
    await _pipeline(session_factory).run(root)
    assert await _flags(session_factory) == {
        "sample guide v1.md": False,
        "sample guide v2.md": False,
        "sample guide v10.md": True,
    }


async def test_failed_new_edition_does_not_hide_the_old_one(session_factory, tmp_path) -> None:
    root = tmp_path / "docs"
    _write(root, "sample guide v1.md")
    (root / "sample guide v2.md").write_text("  \n", encoding="utf-8")  # EMPTY_DOCUMENT
    job = await _pipeline(session_factory).run(root)
    assert (job.indexed, job.failed) == (1, 1)
    assert (await _flags(session_factory))["sample guide v1.md"] is True


async def test_manifest_overrides_the_filename_and_applies_to_rows_indexed_before(
    session_factory, tmp_path
) -> None:
    root = tmp_path / "docs"
    _write(root, "02_gcp_2025.md")
    _write(root, "05_gcp_ko.md")
    _write(root, "10_other_v3.md")
    await _pipeline(session_factory).run(root)
    assert set((await _flags(session_factory)).values()) == {True}  # no tokens, no manifest

    (root / ".corpus.yaml").write_text(
        "name: docs\n"
        "versions:\n"
        "  - {match: '02_gcp_2025.md', family: GCP, version: R3, date: 2025-01-06}\n"
        "  - {match: '05_*.md', family: GCP, version: R2, superseded: true}\n",
        encoding="utf-8",
    )
    job = await _pipeline(session_factory).run(root)  # same files: skipped as duplicates
    assert job.skipped_duplicate == 3 and job.indexed == 0
    assert await _flags(session_factory) == {
        "02_gcp_2025.md": True,
        "05_gcp_ko.md": False,
        "10_other_v3.md": True,
    }
    async with session_factory() as s:
        new = await s.scalar(select(Document).where(Document.file_name == "02_gcp_2025.md"))
        assert (new.version_label, new.version_date, new.version_source) == (
            "R3",
            date(2025, 1, 6),
            "manifest",
        )
    assert await _names(session_factory, latest_only=True) == {
        "02_gcp_2025.md",
        "10_other_v3.md",
    }


async def test_editions_in_different_corpora_do_not_compete(session_factory, tmp_path) -> None:
    a, b = tmp_path / "a", tmp_path / "b"
    _write(a, "sample guide v1.md")
    _write(b, "sample guide v2.md")
    await _pipeline(session_factory).run(a)
    await _pipeline(session_factory).run(b)
    assert set((await _flags(session_factory)).values()) == {True}


async def test_same_file_name_in_other_folders_does_not_hide_a_study(
    session_factory, tmp_path
) -> None:
    root = tmp_path / "docs"
    for folder, name in (
        ("studyA", "Protocol_v2.0.md"),
        ("studyB", "Protocol_v3.0.md"),
    ):
        (root / folder).mkdir(parents=True)
        _write(root / folder, name)
    await _pipeline(session_factory).run(root)
    assert await _flags(session_factory) == {
        "Protocol_v2.0.md": True,
        "Protocol_v3.0.md": True,
    }
    assert await _names(session_factory, latest_only=True) == {
        "Protocol_v2.0.md",
        "Protocol_v3.0.md",
    }
    _write(root / "studyA", "Protocol_v4.0.md")  # same folder: the real newer edition competes
    await _pipeline(session_factory).run(root)
    assert await _flags(session_factory) == {
        "Protocol_v2.0.md": False,
        "Protocol_v3.0.md": True,
        "Protocol_v4.0.md": True,
    }


async def _alembic(url: str, action: str, revision: str) -> None:
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    await asyncio.to_thread(getattr(command, action), cfg, revision)  # env.py has its own loop


_VERSION_COLUMNS = {
    "doc_family",
    "version_label",
    "version_date",
    "version_source",
    "version_superseded",
    "is_latest",
}


async def _columns(factory) -> set[str]:
    async with factory() as s:
        rows = await s.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name='documents'")
        )
        return {r[0] for r in rows}


async def test_migration_0007_up_down_keeps_rows_and_fills_defaults(
    session_factory, database_url
) -> None:
    insert = text(
        "INSERT INTO documents (id, file_name, file_path, file_type, checksum, status, chunk_count)"
        " VALUES (gen_random_uuid(), 'old row.pdf', '/x/old row.pdf', 'pdf', :sum, 'INDEXED', 0)"
    )
    try:
        await _alembic(database_url, "downgrade", "0006")
        assert not _VERSION_COLUMNS & await _columns(session_factory)
        async with session_factory() as s:
            await s.execute(insert, {"sum": "a" * 64})  # a row from before 0007
            await s.commit()
        await _alembic(database_url, "upgrade", "head")
        assert _VERSION_COLUMNS <= await _columns(session_factory)
        async with session_factory() as s:
            row = (
                await s.execute(
                    text(
                        "SELECT doc_family, version_label, version_date, version_source,"
                        " version_superseded, is_latest FROM documents"
                        " WHERE file_name='old row.pdf'"
                    )
                )
            ).one()
        assert tuple(row) == (None, None, None, "none", False, True)  # nothing hidden
        await _alembic(database_url, "downgrade", "0006")  # down again, data intact
        assert not _VERSION_COLUMNS & await _columns(session_factory)
        async with session_factory() as s:
            assert await s.scalar(text("SELECT count(*) FROM documents")) == 1
    finally:
        await _alembic(database_url, "upgrade", "head")


async def test_api_exposes_the_edition_and_include_superseded(session_factory, tmp_path) -> None:
    root = tmp_path / "docs"
    _write(root, "sample guide v1.md")
    _write(root, "sample guide v2.md")
    settings = Settings(
        _env_file=None,
        raw_docs_path=root,
        dicom_path=tmp_path,
        samples_path=tmp_path,
        min_relevance_score=0.1,
        embedding_query_prefix="",
        embedding_document_prefix="",
    )
    container = build_container(settings, ollama=FakeOllama(), session_factory=session_factory)  # type: ignore[arg-type]
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(container)), base_url="http://t"
    ) as c:
        assert (await c.post("/api/index", json={})).json()["indexed"] == 2
        body = {"question": TOPIC, "topK": 5}

        latest = (await c.post("/api/retrieve", json=body)).json()["chunks"]
        assert {h["fileName"] for h in latest} == {"sample guide v2.md"}
        assert latest[0]["metadata"]["versionLabel"] == "v2"
        assert latest[0]["metadata"]["isLatest"] is True

        both = (await c.post("/api/retrieve", json={**body, "includeSuperseded": True})).json()
        assert {h["fileName"] for h in both["chunks"]} == {
            "sample guide v1.md",
            "sample guide v2.md",
        }
        old = next(h for h in both["chunks"] if h["fileName"] == "sample guide v1.md")
        assert old["metadata"]["isLatest"] is False

        answer = (await c.post("/api/ask", json=body)).json()
        assert answer["refused"] is False and answer["supersededWarning"] is None
        assert [s["fileName"] for s in answer["sources"]] == ["sample guide v2.md"]
        assert answer["sources"][0]["versionLabel"] == "v2"
        assert answer["sources"][0]["isLatest"] is True
        assert "versionDate" in answer["sources"][0]

        # file type filter now knows docx / xlsx (no such documents here: empty, not a 422)
        res = await c.post("/api/retrieve", json={**body, "fileType": "docx"})
        assert res.status_code == 200 and res.json()["chunks"] == []


async def test_versions_yaml_states_dates_and_removing_it_restores_both_as_latest(
    session_factory, tmp_path
) -> None:
    root = tmp_path / "docs"
    _write(root, "sample form v1.0 a.md")
    _write(root, "sample form v1.0 b.md")
    await _pipeline(session_factory).run(root)
    assert set((await _flags(session_factory)).values()) == {True}  # same edition, no dates

    (root / ".versions.yaml").write_text(
        "versions:\n"
        "  - {match: 'sample form v1.0 a.md', family: form, version: v1.0, date: 2025-01-01}\n"
        "  - {match: 'sample form v1.0 b.md', family: form, version: v1.0, date: 2025-03-01}\n",
        encoding="utf-8",
    )
    await _pipeline(session_factory).run(root)
    assert await _flags(session_factory) == {
        "sample form v1.0 a.md": False,
        "sample form v1.0 b.md": True,
    }
    assert await _names(session_factory, latest_only=True) == {"sample form v1.0 b.md"}

    (root / ".versions.yaml").unlink()
    await _pipeline(session_factory).run(root)
    assert set((await _flags(session_factory)).values()) == {True}


async def test_corpus_yaml_entry_wins_over_versions_yaml(session_factory, tmp_path) -> None:
    root = tmp_path / "docs"
    _write(root, "guide a.md")
    _write(root, "guide b.md")
    (root / ".corpus.yaml").write_text(
        "name: docs\nversions:\n  - {match: 'guide a.md', family: G, version: v2}\n",
        encoding="utf-8",
    )
    (root / ".versions.yaml").write_text(
        "versions:\n"
        "  - {match: 'guide a.md', family: G, version: v1}\n"  # shadowed by .corpus.yaml
        "  - {match: 'guide b.md', family: G, version: v1}\n",
        encoding="utf-8",
    )
    await _pipeline(session_factory).run(root)
    assert await _flags(session_factory) == {"guide a.md": True, "guide b.md": False}


@pytest.mark.parametrize(
    "broken",
    [
        "versions: [unclosed\n",
        "- just\n- a list\n",
        "versions: not-a-list\n",
        "versions:\n  - {match: 'sample guide v1.md', family: g, date: 2025-02-30}\n",
        "versions:\n  - {match: 'sample guide v1.md', family: g, date: 2025-13-01}\n",
        "versions:\n  - {match: 'sample guide v1.md', family: g, date: !!timestamp nope}\n",
        "versions:\n  - {match: 'sample guide v1.md', family: g, date: !!bool maybe}\n",
    ],
)
async def test_broken_versions_yaml_warns_and_falls_back_to_filenames(
    session_factory, tmp_path, caplog, broken
) -> None:
    root = tmp_path / "docs"
    _write(root, "sample guide v1.md")
    _write(root, "sample guide v2.md")
    (root / ".versions.yaml").write_text(broken, encoding="utf-8")
    with caplog.at_level("WARNING"):
        job = await _pipeline(session_factory).run(root)
    assert job.status == "COMPLETED" and job.indexed == 2
    assert any(".versions.yaml ignored" in r.getMessage() for r in caplog.records)
    assert await _flags(session_factory) == {
        "sample guide v1.md": False,
        "sample guide v2.md": True,
    }


async def test_versions_yaml_is_not_indexed_as_a_document(session_factory, tmp_path) -> None:
    root = tmp_path / "docs"
    _write(root, "only doc.md")
    (root / ".versions.yaml").write_text("versions: []\n", encoding="utf-8")
    job = await _pipeline(session_factory).run(root)
    assert job.total == 1
    assert set(await _flags(session_factory)) == {"only doc.md"}
