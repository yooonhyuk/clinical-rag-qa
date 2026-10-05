"""Embedding model switches against a real PostgreSQL + pgvector: migration 0004 resize path,
mixed-model detection and automatic re-embedding."""

import asyncio
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select, text

from app.models import Chunk, Document, DocumentStatus
from app.services.embedding_schema import (
    REINDEX_REQUIRED,
    column_dimension,
    evaluate_embedding_index,
    inspect_embedding_index,
)
from app.services.embedding_service import EmbeddingService
from app.services.indexing_pipeline import IndexingPipeline
from app.services.vector_search_service import search_chunks
from tests.fakes import DIM, FakeOllama

pytestmark = pytest.mark.integration
BACKEND = Path(__file__).resolve().parents[2] / "backend"


def _pipeline(factory, model: str) -> IndexingPipeline:
    embeddings = EmbeddingService(FakeOllama(), dimension=DIM, model=model, batch_size=4)
    return IndexingPipeline(factory, embeddings, chunk_size=500, chunk_overlap=80)


async def _alembic(url: str, action: str, revision: str) -> None:
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    # env.py runs its own event loop -> keep it off this test's loop
    await asyncio.to_thread(getattr(command, action), cfg, revision)


async def test_other_model_chunks_are_excluded_flagged_and_reembedded(
    session_factory, sample_docs_dir
) -> None:
    first = await _pipeline(session_factory, "nomic-embed-text").run(sample_docs_dir)
    assert first.indexed == 6 and first.embedding_model == "nomic-embed-text"
    query = FakeOllama().dim * [0.0]
    query[0] = 1.0

    async with session_factory() as s:
        assert await search_chunks(s, query, top_k=3, embedding_model="bge-m3") == []
        assert await search_chunks(s, query, top_k=3, embedding_model="nomic-embed-text")
        ok, detail = evaluate_embedding_index(
            await inspect_embedding_index(s), model="bge-m3", dim=DIM
        )
    assert not ok and "nomic-embed-text" in detail

    # Same dimension, different model: the pipeline re-embeds instead of skipping as duplicate.
    second = await _pipeline(session_factory, "bge-m3").run(sample_docs_dir)
    assert (second.indexed, second.skipped_duplicate) == (6, 0)
    async with session_factory() as s:
        models = (await s.scalars(select(Chunk.embedding_model).distinct())).all()
        assert models == ["bge-m3"]
        assert await s.scalar(select(func.count()).select_from(Document)) == 6
        assert evaluate_embedding_index(await inspect_embedding_index(s), model="bge-m3", dim=DIM)[
            0
        ]
    third = await _pipeline(session_factory, "bge-m3").run(sample_docs_dir)
    assert (third.indexed, third.skipped_duplicate) == (0, 6)


async def test_migration_resizes_column_clears_vectors_and_requires_reindex(
    session_factory, database_url, sample_docs_dir
) -> None:
    await _pipeline(session_factory, "bge-m3").run(sample_docs_dir)
    try:
        # 0004 downgrade -> vector(768); upgrade -> configured bge-m3 vector(1024)
        await _alembic(database_url, "downgrade", "0003")
        async with session_factory() as s:
            assert await (await s.connection()).run_sync(column_dimension) == 768
        await _alembic(database_url, "upgrade", "head")
    finally:
        await _alembic(database_url, "upgrade", "head")

    async with session_factory() as s:
        dim = await (await s.connection()).run_sync(column_dimension)
        assert dim == DIM
        assert await s.scalar(select(func.count()).select_from(Chunk)) == 0
        docs = (await s.scalars(select(Document))).all()
        assert docs and {(d.status, d.error_type) for d in docs} == {
            (DocumentStatus.FAILED, REINDEX_REQUIRED)
        }
        state = await inspect_embedding_index(s)
        assert state.reindex_pending == 6
        assert await s.scalar(text("SELECT to_regclass('chunks_embedding_hnsw') IS NOT NULL"))

    job = await _pipeline(session_factory, "bge-m3").run(sample_docs_dir)
    assert job.indexed == 6
    async with session_factory() as s:
        state = await inspect_embedding_index(s)
    assert (state.reindex_pending, list(state.chunk_models)) == (0, ["bge-m3"])
