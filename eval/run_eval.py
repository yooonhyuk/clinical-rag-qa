"""RAG evaluation runner (`make eval`).

Runs every question in `eval/questions.yaml` through the real RAG service (in-process, real
PostgreSQL + pgvector + Ollama embeddings) once per generation provider and writes a Markdown
report to `eval/reports/<date>-<provider>.md` (+ a side-by-side table when several providers
are given).

    uv run --project backend python eval/run_eval.py             # ollama only
    uv run --project backend python eval/run_eval.py --reindex   # index RAW_DOCS_PATH first
    uv run --project backend python eval/run_eval.py --provider ollama --provider anthropic

The anthropic provider only runs when ANTHROPIC_API_KEY is set and the external-LLM guardrail
passes (ALLOW_EXTERNAL_LLM=true + marked sample corpus); otherwise it is reported as skipped.
No numbers are ever fabricated: a provider that did not run has no column values.
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from eval_metrics import EvalOutcome, EvalQuestion, failed_questions, summarize  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.container import AppContainer, build_container  # noqa: E402
from app.services.llm_guardrail import ExternalLLMNotAllowedError  # noqa: E402

REPORTS = ROOT / "eval" / "reports"
METRIC_LABELS = {
    "hit_at_k": "Retrieval hit@k",
    "section_hit_at_k": "Section hit@k",
    "citation_correctness": "Citation correctness",
    "keyword_coverage": "Keyword coverage",
    "refusal_correctness": "Refusal correctness",
    "false_refusal_rate": "False refusal rate (answerable)",
    "retrieval_ms_p50": "Retrieval p50 (ms)",
    "retrieval_ms_p95": "Retrieval p95 (ms)",
    "generation_ms_p50": "Generation p50 (ms)",
    "generation_ms_p95": "Generation p95 (ms)",
    "total_ms_p50": "Total p50 (ms)",
    "total_ms_p95": "Total p95 (ms)",
    "input_tokens_total": "Input tokens (total)",
    "output_tokens_total": "Output tokens (total)",
}


def load_questions(path: Path) -> list[EvalQuestion]:
    return [EvalQuestion.from_dict(q) for q in yaml.safe_load(path.read_text(encoding="utf-8"))]


async def run_question(container: AppContainer, q: EvalQuestion, top_k: int) -> EvalOutcome:
    try:
        async with container.session_factory() as session:
            r = await container.rag.ask(session, q.question, top_k=top_k)
        retrieved = r.retrieved
        if not retrieved:  # OUT_OF_SCOPE skips retrieval; measure the cosine anyway
            async with container.session_factory() as session:
                retrieved, _ = await container.rag.retrieve(session, q.question, top_k=top_k)
    except Exception as exc:  # recorded per question, the run continues
        return EvalOutcome(q, [], [], [], "", False, None, 0, 0, error=repr(exc))
    return EvalOutcome(
        question=q,
        retrieved_files=[c.file_name for c in r.retrieved],
        retrieved_sections=[c.section_title for c in r.retrieved],
        cited_files=[c.file_name for c in r.sources],
        answer=r.answer,
        refused=r.refused,
        refusal_reason=r.refusal_reason,
        retrieval_ms=r.retrieval_ms,
        generation_ms=r.generation_ms,
        input_tokens=r.usage.input_tokens if r.usage else None,
        output_tokens=r.usage.output_tokens if r.usage else None,
        extra={
            "citationMode": r.citation_mode,
            # what the NO_EVIDENCE threshold compares against: best cosine among retrieved
            "maxCosine": max((c.score for c in retrieved), default=None),
        },
    )


async def run_provider(
    provider: str, questions: list[EvalQuestion], top_k: int, reindex: bool
) -> tuple[list[EvalOutcome], dict[str, Any]]:
    settings = get_settings().model_copy(update={"llm_provider": provider})
    container = build_container(settings)  # raises ExternalLLMNotAllowedError if not allowed
    try:
        if reindex:
            job = await container.pipeline.run(settings.raw_docs_path)
            print(f"[index] indexed={job.indexed} failed={job.failed} dup={job.skipped_duplicate}")
        outcomes = [await run_question(container, q, top_k) for q in questions]
        model = settings.anthropic_model if provider == "anthropic" else settings.ollama_llm_model
        config = {
            "provider": provider,
            "model": model,
            "embedding_model": settings.ollama_embedding_model,
            "embedding_dim": settings.embedding_dimension,
            "top_k": top_k,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "min_relevance_score": settings.min_relevance_score,
            "hybrid_search": settings.hybrid_search,
        }
        return outcomes, config
    finally:
        await container.aclose()


def _question_row(o: EvalOutcome) -> dict[str, Any]:
    """Per-question record (used to inspect cosine distributions / refusal thresholds)."""
    return {
        "id": o.question.id,
        "answerable": o.question.answerable,
        "refused": o.refused,
        "refusalReason": o.refusal_reason,
        "hit": o.hit if o.question.answerable else None,
        "sectionHit": o.section_hit if o.question.answerable else None,
        "maxCosine": o.extra.get("maxCosine"),
        "retrievedFiles": o.retrieved_files,
        "citedFiles": o.cited_files,
        "error": o.error,
    }


def _fmt(key: str, value: Any) -> str:
    if value is None:
        return "-"
    if key.endswith(("_ms_p50", "_ms_p95")) or key.endswith("_total"):
        return f"{value:,.0f}"
    return f"{value:.1%}"


def render_report(config: dict[str, Any], outcomes: list[EvalOutcome], run_at: str) -> str:
    summary = summarize(outcomes)
    lines = [
        f"# RAG Eval Report — {config['provider']} ({run_at})",
        "",
        "## Config",
        "",
        *(f"- {k}: `{v}`" for k, v in config.items()),
        "",
        "## Metrics",
        "",
        *(
            [f"> INCOMPLETE: {summary['errors']} question(s) errored; metrics cover the rest", ""]
            if summary["errors"]
            else []
        ),
        "| Metric | Value |",
        "|---|---|",
        *(f"| {label} | {_fmt(key, summary[key])} |" for key, label in METRIC_LABELS.items()),
        f"| Questions / errors | {summary['questions']} / {summary['errors']} |",
        "",
        "## Failed questions",
        "",
    ]
    failures = failed_questions(outcomes)
    lines += [f"- **{qid}**: {reason}" for qid, reason in failures] or ["- (none)"]
    lines += ["", "## Per-question", "", "| id | refused | hit | cited | answer (first 80 chars) |"]
    lines += ["|---|---|---|---|---|"]
    for o in outcomes:
        answer = o.answer.replace("\n", " ").replace("|", "/")[:80]
        cited = ", ".join(sorted(set(o.cited_files))) or "-"
        hit = "-" if not o.question.answerable else ("Y" if o.hit else "N")
        lines.append(
            f"| {o.question.id} | {o.refusal_reason or '-'} | {hit} | {cited} | {answer} |"
        )
    return "\n".join(lines) + "\n"


def render_comparison(results: dict[str, dict[str, Any] | str], run_at: str) -> str:
    providers = list(results)
    lines = [
        f"# RAG Eval — provider comparison ({run_at})",
        "",
        "| Metric | " + " | ".join(providers) + " |",
        "|---|" + "---|" * len(providers),
    ]
    for key, label in METRIC_LABELS.items():
        cells = [_fmt(key, r[key]) if isinstance(r, dict) else "skipped" for r in results.values()]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    notes = [f"- {p}: {r}" for p, r in results.items() if isinstance(r, str)]
    return "\n".join(lines + ([""] + notes if notes else [])) + "\n"


async def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--provider", action="append", choices=["ollama", "anthropic"], help="repeatable"
    )
    parser.add_argument("--questions", type=Path, default=ROOT / "eval" / "questions.yaml")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--reindex", action="store_true", help="index RAW_DOCS_PATH first")
    args = parser.parse_args()

    providers = args.provider or ["ollama"]
    questions = load_questions(args.questions)
    top_k = args.top_k or get_settings().top_k
    run_at = datetime.now().strftime("%Y-%m-%d_%H%M")
    REPORTS.mkdir(parents=True, exist_ok=True)

    results: dict[str, dict[str, Any] | str] = {}
    for i, provider in enumerate(providers):
        if provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
            results[provider] = "skipped: ANTHROPIC_API_KEY not set (no numbers reported)"
            print(f"[{provider}] {results[provider]}")
            continue
        try:
            outcomes, config = await run_provider(
                provider, questions, top_k, reindex=args.reindex and i == 0
            )
        except ExternalLLMNotAllowedError as exc:
            results[provider] = f"skipped: guardrail — {exc}"
            print(f"[{provider}] {results[provider]}")
            continue
        report = render_report(config, outcomes, run_at)
        path = REPORTS / f"{run_at}-{provider}.md"
        path.write_text(report, encoding="utf-8")
        (REPORTS / f"{run_at}-{provider}.json").write_text(
            json.dumps(summarize(outcomes), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (REPORTS / f"{run_at}-{provider}-questions.json").write_text(
            json.dumps(
                {"config": config, "questions": [_question_row(o) for o in outcomes]},
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        results[provider] = summarize(outcomes)
        print(report)
        print(f"[{provider}] report written to {path.relative_to(ROOT)}")

    if len(providers) > 1:
        path = REPORTS / f"{run_at}-comparison.md"
        path.write_text(render_comparison(results, run_at), encoding="utf-8")
        print(path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
