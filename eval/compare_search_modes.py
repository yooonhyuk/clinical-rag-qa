"""Retrieval-only check of docs/issues/009: HNSW vs exact (vs iterative scan) top-k.

For every question of a set, embed it once and retrieve the top-k chunks of one corpus in
several ways in the SAME database: the default plan (HNSW if the planner picks the index),
exact (index scans off), HNSW with pgvector 0.8 iterative scan, and HNSW with a wider candidate
list (ef_search 100 / 200; pgvector default 40). Reports how many questions get a different
top-k than exact search (chunk ids and file sets), file hit@k and median SQL time per mode, and
how many searches returned fewer than k rows (the filter ate the candidates). No document text
is written. EXPLAIN the query to see whether the index is used at all (docs/issues/009).

    DATABASE_URL=... uv run --project backend python eval/compare_search_modes.py \\
        --corpus public --questions eval/public_questions.yaml --out result.json
"""

import argparse
import asyncio
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from eval_metrics import EvalQuestion  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.container import build_container  # noqa: E402
from app.services.vector_search_service import search_chunks  # noqa: E402

MODES: dict[str, dict[str, Any]] = {
    "hnsw": {},
    "exact": {"exact": True},
    "hnsw_iterative": {"iterative_scan": "relaxed_order"},
    "hnsw_ef100": {"ef_search": 100},
    "hnsw_ef200": {"ef_search": 200},
}


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True, help="corpus name stored in documents.corpus")
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--reranker",
        action="store_true",
        help="add a mode: exact top-30 reranked by bge-reranker-v2-m3 (rerank extra + HF cache)",
    )
    args = parser.parse_args()

    raw = yaml.safe_load(args.questions.expanduser().read_text(encoding="utf-8"))
    questions = [EvalQuestion.from_dict(q) for q in raw]
    container = build_container(get_settings())
    model = container.embeddings.model
    reranker = None
    if args.reranker:
        from app.container import build_reranker
        from app.services.reranker import rerank_chunks

        reranker = build_reranker(
            get_settings().model_copy(update={"reranker": "bge-reranker-v2-m3"})
        )
    modes = [*MODES, *(["exact_rerank"] if reranker else [])]
    per_mode: dict[str, list[list[tuple[str, str, str | None, int | None]]]] = {
        m: [] for m in modes
    }
    timings: dict[str, list[float]] = {m: [] for m in modes}
    try:
        for q in questions:
            vector = await container.embeddings.embed_query(q.question)
            for mode, options in MODES.items():
                start = time.perf_counter()
                async with container.session_factory() as session:
                    chunks = await search_chunks(
                        session,
                        vector,
                        top_k=args.top_k,
                        embedding_model=model,
                        corpus=args.corpus,
                        **options,
                    )
                timings[mode].append((time.perf_counter() - start) * 1000)
                per_mode[mode].append(
                    [(str(c.chunk_id), c.file_name, c.section_title, c.page_number) for c in chunks]
                )
            if reranker is not None:
                start = time.perf_counter()
                async with container.session_factory() as session:
                    pool = await search_chunks(
                        session,
                        vector,
                        top_k=30,
                        embedding_model=model,
                        corpus=args.corpus,
                        exact=True,
                    )
                scores = await reranker.score(q.question, [c.text for c in pool])
                chunks = rerank_chunks(pool, scores, args.top_k)
                timings["exact_rerank"].append((time.perf_counter() - start) * 1000)
                per_mode["exact_rerank"].append(
                    [(str(c.chunk_id), c.file_name, c.section_title, c.page_number) for c in chunks]
                )
    finally:
        await container.aclose()

    exact = per_mode["exact"]
    answerable = [i for i, q in enumerate(questions) if q.answerable]
    report: dict[str, Any] = {
        "corpus": args.corpus,
        "questions": len(questions),
        "top_k": args.top_k,
        "modes": {},
    }
    for mode, results in per_mode.items():
        ids_diff = [
            questions[i].id
            for i in range(len(questions))
            if [r[0] for r in results[i]] != [r[0] for r in exact[i]]
        ]
        files_diff = [
            questions[i].id
            for i in range(len(questions))
            if {r[1] for r in results[i]} != {r[1] for r in exact[i]}
        ]
        hits = sum(
            bool(questions[i].expected_files & {r[1] for r in results[i]}) for i in answerable
        )
        located = sum(
            any(s.matches(r[1], r[2], r[3]) for r in results[i] for s in questions[i].sources)
            for i in answerable
        )
        report["modes"][mode] = {
            "topk_differs_from_exact": len(ids_diff),
            "file_set_differs_from_exact": len(files_diff),
            "questions_with_file_diff": files_diff,
            "short_results": sum(len(r) < args.top_k for r in results),
            "hit_at_k": round(hits / len(answerable), 4) if answerable else None,
            "section_hit_at_k": round(located / len(answerable), 4) if answerable else None,
            "search_ms_p50": round(statistics.median(timings[mode]), 1),
        }
    print(json.dumps(report, indent=2))
    if args.out:
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
