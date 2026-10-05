"""Resize chunks.embedding for the configured embedding model and clear every vector.

    OLLAMA_EMBEDDING_MODEL=bge-m3 uv run --project backend python scripts/reset_embeddings.py
    make reset-embeddings                      # same, inside the Makefile's eval env

Run after changing OLLAMA_EMBEDDING_MODEL / EMBEDDING_DIM to a model with another dimension,
then reindex (`/api/index` or `make eval EVAL_ARGS=--reindex`). Embeddings of different models
are not comparable, so nothing is converted: all chunks are deleted and documents are marked
FAILED / REINDEX_REQUIRED. Without --force it does nothing when the dimension already matches
(a same-dimension model switch is handled by the indexing pipeline, which re-embeds documents
whose `embedding_model` differs).
"""

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.services.embedding_schema import column_dimension, reset_embedding_column  # noqa: E402


async def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--force", action="store_true", help="reset even if the dimension matches")
    args = parser.parse_args()

    settings = get_settings()
    dim = settings.embedding_dimension
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.begin() as conn:
            current = await conn.run_sync(column_dimension)
            if current == dim and not args.force:
                print(f"chunks.embedding is already vector({dim}); nothing to do (use --force)")
                return 0
            pending = await conn.run_sync(reset_embedding_column, dim)
    finally:
        await engine.dispose()
    print(
        f"chunks.embedding: vector({current}) -> vector({dim}) "
        f"for {settings.ollama_embedding_model}; all chunks deleted, "
        f"{pending} document(s) marked REINDEX_REQUIRED -> reindex now"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
