"""PostgreSQL + pgvector for integration tests.

Order of preference:
1. TEST_DATABASE_URL (e.g. a CI service container or a local pgvector instance)
2. testcontainers `pgvector/pgvector:pg16` (needs a running Docker daemon)
3. otherwise every integration test is skipped cleanly.
"""

import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

BACKEND = Path(__file__).resolve().parents[2] / "backend"


def _docker_available() -> bool:
    try:
        import docker

        docker.from_env().ping()
        return True
    except Exception:
        return False


def _migrate(url: str) -> None:
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    if url := os.getenv("TEST_DATABASE_URL"):
        _migrate(url)
        yield url
        return
    if not _docker_available():
        pytest.skip("Docker is not available and TEST_DATABASE_URL is not set")
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("pgvector/pgvector:pg16", driver="asyncpg") as pg:
        url = pg.get_connection_url()
        _migrate(url)
        yield url


@pytest.fixture
async def session_factory(database_url: str) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        await conn.execute(
            text("TRUNCATE ask_logs, chunks, documents, dicom_files, index_jobs CASCADE")
        )
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()
