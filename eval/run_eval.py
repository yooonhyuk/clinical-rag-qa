"""RAG evaluation runner (`make eval`).

Runs every question of an eval set through the real RAG service (in-process, real PostgreSQL +
pgvector + local Ollama) once per generation provider, restricted to one corpus, and writes

    eval/results/<date>_<corpus>_<label>_<corpus-hash>/
        config.json       run configuration (models, retrieval, corpus hash, git commit)
        summary.json      overall metrics + by question type + by language + refusal reasons
        questions.jsonl   one record per question (retrieved/cited chunks, answer, latency)
        report.md         human-readable report

Examples:

    uv run --project backend python eval/run_eval.py --corpus toy --reindex
    uv run --project backend python eval/run_eval.py --corpus public --hybrid off --label vector
    uv run --project backend python eval/run_eval.py --corpus ~/clinical-rag-private/originals \
        --questions my_private_questions.yaml          # local only; never commit the results

`--corpus` is `toy` (samples/documents), `public` (corpus/public) or a folder path. The corpus
name used to filter retrieval comes from the folder's .corpus.yaml `name:` (else the folder
name). Without `--corpus` the runner behaves like MVP-1: RAW_DOCS_PATH, no corpus filter.

`--generator-model` swaps the Ollama LLM (e.g. medgemma:4b). `--reranker bge-reranker-v2-m3`
adds the cross-encoder stage (`uv sync --extra rerank`, model in the local HF cache);
`--rerank-min-score 0` records every question's rerank score without gating, so a gate can be
tuned offline on the dev split (eval/tune_gate.py). `--partial-answers off` scores with the
MVP-1 policy (cited-but-flagged answers are refusals). The anthropic provider
only runs when ANTHROPIC_API_KEY is set and the external-LLM guardrail passes; otherwise it is
reported as skipped. No numbers are ever fabricated: a provider that did not run has none.
"""

import argparse
import asyncio
import hashlib
import json
import os
import resource
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from eval_metrics import (  # noqa: E402
    EvalOutcome,
    EvalQuestion,
    failed_questions,
    refusal_reasons,
    summarize,
    summarize_by,
)

from app.config import get_settings  # noqa: E402
from app.container import AppContainer, build_container  # noqa: E402
from app.services.document_loader import scan_documents  # noqa: E402
from app.services.llm_guardrail import ExternalLLMNotAllowedError, corpus_name  # noqa: E402

RESULTS = ROOT / "eval" / "results"
CORPORA = {"toy": ROOT / "samples" / "documents", "public": ROOT / "corpus" / "public"}
DEFAULT_QUESTIONS = {
    "toy": ROOT / "eval" / "questions.yaml",
    "public": ROOT / "eval" / "public_questions.yaml",
}
METRIC_LABELS = {
    "hit_at_k": "Retrieval hit@k (file)",
    "section_hit_at_k": "Section/page hit@k",
    "citation_correctness": "Citation accuracy (cited files ⊆ gold)",
    "citation_location": "Citation location (a cited chunk in gold section/page)",
    "keyword_coverage": "Keyword coverage",
    "refusal_correctness": "Refusal accuracy (must-refuse)",
    "false_refusal_rate": "False refusal rate (answerable)",
    "partial_answer_rate": "Partial answers with caveat (answerable)",
    "legacy_false_refusal_rate": "False refusal if partial = refusal (MVP-1 policy)",
    "legacy_refusal_correctness": "Refusal accuracy if partial = refusal (MVP-1 policy)",
    "korean_answer_rate": "Answers in Korean (answered)",
    "schema_valid_rate": "JSON schema-valid generations",
    "retrieval_ms_p50": "Retrieval p50 (ms)",
    "retrieval_ms_p95": "Retrieval p95 (ms)",
    "generation_ms_p50": "Generation p50 (ms)",
    "generation_ms_p95": "Generation p95 (ms)",
    "total_ms_p50": "Total p50 (ms)",
    "total_ms_p95": "Total p95 (ms)",
    "input_tokens_total": "Input tokens (total)",
    "output_tokens_total": "Output tokens (total)",
}
GROUP_METRICS = (
    "hit_at_k",
    "section_hit_at_k",
    "citation_correctness",
    "keyword_coverage",
    "refusal_correctness",
    "false_refusal_rate",
    "partial_answer_rate",
    "total_ms_p50",
)


def load_questions(path: Path) -> list[EvalQuestion]:
    return [EvalQuestion.from_dict(q) for q in yaml.safe_load(path.read_text(encoding="utf-8"))]


def corpus_hash(root: Path) -> str:
    """sha256 over (relative path, content sha256) of every supported file, sorted."""
    digest = hashlib.sha256()
    for f in scan_documents(root):
        if f.supported:
            digest.update(f"{f.path.relative_to(root)}:{f.checksum}\n".encode())
    return digest.hexdigest()


def resolve_corpus(value: str | None) -> tuple[Path | None, str | None]:
    if value is None:
        return None, None
    root = CORPORA.get(value) or Path(value).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"corpus folder not found: {root}")
    return root, corpus_name(root, get_settings().corpus_marker_file)


def _round(value: float | None) -> float | None:
    return None if value is None else round(value, 4)


async def run_question(
    container: AppContainer, q: EvalQuestion, top_k: int, corpus: str | None
) -> EvalOutcome:
    try:
        async with container.session_factory() as session:
            r = await container.rag.ask(session, q.question, top_k=top_k, corpus=corpus)
        retrieved = r.retrieved
        if not retrieved:  # OUT_OF_SCOPE skips retrieval; measure the cosine anyway
            async with container.session_factory() as session:
                retrieved, _ = await container.rag.retrieve(
                    session, q.question, top_k=top_k, corpus=corpus
                )
    except Exception as exc:  # recorded per question, the run continues
        return EvalOutcome(q, [], [], [], "", False, None, 0, 0, error=repr(exc))
    return EvalOutcome(
        question=q,
        retrieved_files=[c.file_name for c in r.retrieved],
        retrieved_sections=[c.section_title for c in r.retrieved],
        retrieved_pages=[c.page_number for c in r.retrieved],
        cited_files=[c.file_name for c in r.sources],
        cited_sections=[c.section_title for c in r.sources],
        cited_pages=[c.page_number for c in r.sources],
        answer=r.answer,
        refused=r.refused,
        refusal_reason=r.refusal_reason,
        retrieval_ms=r.retrieval_ms,
        generation_ms=r.generation_ms,
        input_tokens=r.usage.input_tokens if r.usage else None,
        output_tokens=r.usage.output_tokens if r.usage else None,
        partial=r.partial,
        schema_valid=r.meta.get("schemaValid"),  # type: ignore[arg-type]
        extra={
            "citationMode": r.citation_mode,
            "gate": r.meta.get("gate"),
            "retrievedScores": [
                {"cosine": round(c.score, 4), "rerank": _round(c.rerank_score)} for c in r.retrieved
            ],
            # what the NO_EVIDENCE threshold compares against: best cosine among retrieved
            "maxCosine": max((c.score for c in retrieved), default=None),
            "topRerank": retrieved[0].rerank_score if retrieved else None,
            "scope": r.meta.get("scope"),
            # what retrieval would have returned (also for OUT_OF_SCOPE refusals)
            "probe": [
                {"file": c.file_name, "section": c.section_title, "page": c.page_number}
                for c in retrieved
            ],
        },
    )


async def run_provider(
    provider: str,
    questions: list[EvalQuestion],
    *,
    top_k: int,
    root: Path,
    corpus: str | None,
    reindex: bool,
    overrides: dict[str, Any],
) -> tuple[list[EvalOutcome], dict[str, Any]]:
    settings = get_settings().model_copy(update={"llm_provider": provider, **overrides})
    container = build_container(settings)  # raises ExternalLLMNotAllowedError if not allowed
    try:
        if reindex:
            job = await container.pipeline.run(root, corpus=corpus)
            print(f"[index] indexed={job.indexed} failed={job.failed} dup={job.skipped_duplicate}")
        outcomes = []
        for i, q in enumerate(questions, start=1):
            outcomes.append(await run_question(container, q, top_k, corpus))
            o = outcomes[-1]
            print(f"  [{i}/{len(questions)}] {q.id} {o.refusal_reason or 'ANSWERED'}", flush=True)
        model = settings.anthropic_model if provider == "anthropic" else settings.ollama_llm_model
        config = {
            "provider": provider,
            "generator_model": model,
            "reranker": settings.reranker,
            **(
                {
                    "reranker_model": settings.reranker_model,
                    "reranker_revision": settings.reranker_revision,
                    "reranker_device": getattr(container.rag._reranker, "device", None),
                    "rerank_candidates": settings.rerank_candidates,
                    "rerank_min_score": settings.rerank_min_score,
                }
                if settings.reranker != "none"
                else {}
            ),
            "partial_answers": settings.partial_answers,
            "rag_prompt_variant": settings.rag_prompt_variant,
            # eval process (incl. an in-process reranker); Ollama runs in its own process
            "eval_process_max_rss_mb": round(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
            ),
            "embedding_model": settings.ollama_embedding_model,
            "embedding_dim": settings.embedding_dimension,
            "hybrid_search": settings.hybrid_search,
            "top_k": top_k,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "min_relevance_score": settings.min_relevance_score,
            "scope_classifier": settings.scope_classifier,
            "scope_margin": settings.scope_margin,
        }
        return outcomes, config
    finally:
        await container.aclose()


def question_record(o: EvalOutcome) -> dict[str, Any]:
    q = o.question
    return {
        "id": q.id,
        "type": q.qtype,
        "lang": q.lang,
        "question": q.question,
        "answerable": q.answerable,
        "refused": o.refused,
        "refusalReason": o.refusal_reason,
        "partial": o.partial,
        "schemaValid": o.schema_valid,
        "hit": o.hit if q.answerable else None,
        "sectionHit": o.section_hit if q.answerable else None,
        "citationCorrect": o.citation_correct if q.answerable and not o.refused else None,
        "citationLocated": o.citation_located if q.answerable and not o.refused else None,
        "maxCosine": o.extra.get("maxCosine"),
        "topRerank": o.extra.get("topRerank"),
        "gate": o.extra.get("gate"),
        "retrievedScores": o.extra.get("retrievedScores"),
        "scope": o.extra.get("scope"),
        "retrieved": [
            {"file": f, "section": s, "page": p}
            for f, s, p in zip(
                o.retrieved_files,
                o.retrieved_sections,
                o.retrieved_pages or [None] * len(o.retrieved_files),
                strict=False,
            )
        ],
        "probe": o.extra.get("probe"),
        "cited": [
            {"file": f, "section": s, "page": p}
            for f, s, p in zip(
                o.cited_files,
                o.cited_sections or [None] * len(o.cited_files),
                o.cited_pages or [None] * len(o.cited_files),
                strict=False,
            )
        ],
        "answer": o.answer,
        "answerKey": q.answer_key,
        "retrievalMs": o.retrieval_ms,
        "generationMs": o.generation_ms,
        "error": o.error,
    }


def _result(o: EvalOutcome) -> str:
    return (
        str(o.refusal_reason)
        if o.refusal_reason
        else ("ANSWERED_PARTIAL" if o.partial else "ANSWERED")
    )


def _fmt(key: str, value: Any) -> str:
    if value is None:
        return "-"
    if key.endswith(("_ms_p50", "_ms_p95")) or key.endswith("_total"):
        return f"{value:,.0f}"
    return f"{value:.1%}"


def _group_table(title: str, groups: dict[str, dict[str, Any]]) -> list[str]:
    lines = [f"## {title}", "", "| group | n | " + " | ".join(GROUP_METRICS) + " |"]
    lines.append("|---|---|" + "---|" * len(GROUP_METRICS))
    for name, s in groups.items():
        cells = [_fmt(k, s[k]) for k in GROUP_METRICS]
        lines.append(f"| {name} | {s['questions']} | " + " | ".join(cells) + " |")
    return [*lines, ""]


def render_report(
    config: dict[str, Any], summary: dict[str, Any], outcomes: list[EvalOutcome]
) -> str:
    overall = summary["overall"]
    lines = [
        f"# RAG Eval Report — {config['corpus']} / {config['label']} ({config['run_at']})",
        "",
        "## Config",
        "",
        *(f"- {k}: `{v}`" for k, v in config.items()),
        "",
        "## Metrics",
        "",
        *(
            [f"> INCOMPLETE: {overall['errors']} question(s) errored; metrics cover the rest", ""]
            if overall["errors"]
            else []
        ),
        "| Metric | Value |",
        "|---|---|",
        *(f"| {label} | {_fmt(key, overall[key])} |" for key, label in METRIC_LABELS.items()),
        f"| Questions (answerable / must-refuse) / errors | {overall['questions']} "
        f"({overall['answerable']} / {overall['unanswerable']}) / {overall['errors']} |",
        f"| Must-refuse questions answered partially | {overall['must_refuse_partial']} |",
        "",
        f"Refusal reasons: {summary['refusal_reasons']}",
        "",
        *_group_table("By question type", summary["by_type"]),
        *_group_table("By language", summary["by_lang"]),
        "## Failed questions",
        "",
    ]
    failures = failed_questions(outcomes)
    lines += [f"- **{qid}**: {reason}" for qid, reason in failures] or ["- (none)"]
    lines += ["", "## Per-question", ""]
    lines += ["| id | type | lang | result | hit | sec | cited | answer |"]
    lines += ["|---|---|---|---|---|---|---|---|"]
    for o in outcomes:
        q = o.question
        answer = o.answer.replace("\n", " ").replace("|", "/")[:80]
        cited = ", ".join(sorted({f"{f}" for f in o.cited_files})) or "-"
        hit = "-" if not q.answerable else ("Y" if o.hit else "N")
        sec = "-" if not q.answerable else ("Y" if o.section_hit else "N")
        lines.append(
            f"| {q.id} | {q.qtype} | {q.lang} | {_result(o)} | {hit} | {sec} | {cited} | {answer} |"
        )
    return "\n".join(lines) + "\n"


def _git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


async def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--provider", action="append", choices=["ollama", "anthropic"], help="repeatable"
    )
    parser.add_argument("--corpus", help="toy | public | <folder path>")
    parser.add_argument("--questions", type=Path, default=None)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--reindex", action="store_true", help="index the corpus folder first")
    parser.add_argument("--hybrid", choices=["on", "off"], help="override HYBRID_SEARCH")
    parser.add_argument("--generator-model", help="override OLLAMA_LLM_MODEL (e.g. medgemma:4b)")
    parser.add_argument("--reranker", choices=["none", "bge-reranker-v2-m3"])
    parser.add_argument("--rerank-candidates", type=int, help="override RERANK_CANDIDATES")
    parser.add_argument("--rerank-min-score", type=float, help="override RERANK_MIN_SCORE")
    parser.add_argument("--min-relevance-score", type=float, help="override MIN_RELEVANCE_SCORE")
    parser.add_argument("--partial-answers", choices=["on", "off"])
    parser.add_argument(
        "--prompt-variant",
        choices=["default", "inline-en"],
        help="override RAG_PROMPT_VARIANT (inline-en: eval-only probe, docs/analysis)",
    )
    parser.add_argument("--scope-classifier", choices=["embedding", "regex", "mvp1"])
    parser.add_argument("--label", help="config label used in the result folder name")
    parser.add_argument("--out", type=Path, default=RESULTS, help="results root")
    args = parser.parse_args()

    root, corpus = resolve_corpus(args.corpus)
    settings = get_settings()
    root = root or settings.raw_docs_path
    questions_path = args.questions or DEFAULT_QUESTIONS.get(
        args.corpus or "toy", ROOT / "eval" / "questions.yaml"
    )
    questions = load_questions(questions_path)
    top_k = args.top_k or settings.top_k
    overrides: dict[str, Any] = {}
    if args.hybrid:
        overrides["hybrid_search"] = args.hybrid == "on"
    if args.generator_model:
        overrides["ollama_llm_model"] = args.generator_model
    if args.prompt_variant:
        overrides["rag_prompt_variant"] = args.prompt_variant
    if args.scope_classifier:
        overrides["scope_classifier"] = args.scope_classifier
    if args.reranker:
        overrides["reranker"] = args.reranker
    if args.rerank_candidates is not None:
        overrides["rerank_candidates"] = args.rerank_candidates
    if args.rerank_min_score is not None:
        overrides["rerank_min_score"] = args.rerank_min_score
    if args.min_relevance_score is not None:
        overrides["min_relevance_score"] = args.min_relevance_score
    if args.partial_answers:
        overrides["partial_answers"] = args.partial_answers == "on"
    providers = args.provider or ["ollama"]
    run_at = datetime.now()
    c_hash = corpus_hash(root)

    for i, provider in enumerate(providers):
        if provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
            print(f"[{provider}] skipped: ANTHROPIC_API_KEY not set (no numbers reported)")
            continue
        try:
            outcomes, config = await run_provider(
                provider,
                questions,
                top_k=top_k,
                root=root,
                corpus=corpus,
                reindex=args.reindex and i == 0,
                overrides=overrides,
            )
        except ExternalLLMNotAllowedError as exc:
            print(f"[{provider}] skipped: guardrail — {exc}")
            continue
        hybrid = "hybrid" if config["hybrid_search"] else "vector"
        if config["reranker"] != "none":
            hybrid += "-rerank"
        label = args.label or f"{config['embedding_model']}-{hybrid}-{config['generator_model']}"
        label = label.replace(":", "-").replace("/", "-")
        config = {
            "run_at": run_at.isoformat(timespec="seconds"),
            "label": label,
            "corpus": corpus or "(all, RAW_DOCS_PATH)",
            "corpus_root": str(root.relative_to(ROOT)) if root.is_relative_to(ROOT) else "local",
            "corpus_sha256": c_hash,
            "questions_file": questions_path.name,
            "questions_sha256": hashlib.sha256(questions_path.read_bytes()).hexdigest(),
            "git_commit": _git_commit(),
            **config,
        }
        summary = {
            "overall": summarize(outcomes),
            "by_type": summarize_by(outcomes, lambda o: o.question.qtype),
            "by_lang": summarize_by(outcomes, lambda o: o.question.lang),
            "refusal_reasons": refusal_reasons(outcomes),
        }
        stem = f"{run_at:%Y-%m-%d}_{corpus or 'raw'}_{label}_{c_hash[:8]}"
        out = args.out / stem
        out.mkdir(parents=True, exist_ok=True)
        report = render_report(config, summary, outcomes)
        (out / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
        (out / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        with (out / "questions.jsonl").open("w", encoding="utf-8") as fh:
            for o in outcomes:
                fh.write(json.dumps(question_record(o), ensure_ascii=False) + "\n")
        (out / "report.md").write_text(report, encoding="utf-8")
        print(report)
        print(f"[{provider}] results written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
