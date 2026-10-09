"""Index one corpus folder in-process and report chunks per document and wall time.

    DATABASE_URL=... uv run --project backend python scripts/index_corpus.py ~/clinical-rag-private
    ... --json out.json      # also write the report (file names, counts, seconds; no text)

Uses the same IndexingPipeline as /api/index (marker name / classification / include globs).
Run it against a throwaway database when evaluating: re-indexing is idempotent by checksum,
but the HNSW graph depends on insertion order (docs/issues/009).
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import select  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.container import build_container  # noqa: E402
from app.models import Document  # noqa: E402


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--json", type=Path, help="write the report as JSON")
    args = parser.parse_args()
    root = args.folder.expanduser().resolve()

    container = build_container(get_settings())
    try:
        start = time.perf_counter()
        job = await container.pipeline.run(root)
        seconds = time.perf_counter() - start
        async with container.session_factory() as session:
            paths = {d["filePath"] for d in job.details}
            docs = (
                await session.scalars(select(Document).where(Document.file_path.in_(paths)))
            ).all()
        rows = sorted(
            (
                {
                    "file": d.file_name,
                    "corpus": d.corpus,
                    "classification": d.classification,
                    "status": d.status,
                    "chunks": d.chunk_count,
                    "error": d.error_type,
                }
                for d in docs
            ),
            key=lambda r: r["file"],
        )
    finally:
        await container.aclose()

    for r in rows:
        print(f"{r['file']:45s} {r['status']:10s} {r['chunks']:6d} {r['error'] or ''}")
    report = {
        "folder": root.name,
        "embedding_model": container.settings.ollama_embedding_model,
        "indexed": job.indexed,
        "failed": job.failed,
        "skipped_duplicate": job.skipped_duplicate,
        "chunks": sum(r["chunks"] for r in rows),
        "seconds": round(seconds, 1),
        "documents": rows,
    }
    print(
        f"indexed={job.indexed} failed={job.failed} dup={job.skipped_duplicate} "
        f"chunks={report['chunks']} in {seconds:.1f}s"
    )
    if args.json:
        args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if job.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
