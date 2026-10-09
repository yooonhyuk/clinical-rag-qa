"""Local-only corpora: the repo copy of an eval run is aggregate only (no answers, no text)."""

import json
from pathlib import Path

from eval_metrics import EvalOutcome, EvalQuestion, refusal_reasons, summarize, summarize_by
from run_eval import _inside_git_work_tree, render_report, write_results

SECRET_ANSWER = "Scans every 6 weeks per section 8.1.1 [1]"


def _outcomes() -> list[EvalOutcome]:
    q = EvalQuestion.from_dict(
        {
            "id": "r01",
            "type": "imaging_schedule",
            "question": "스캔 주기는?",
            "expected_sources": [{"file": "NCT0_Prot_000.pdf", "section": "8.1.1", "pages": [9]}],
        }
    )
    return [
        EvalOutcome(
            question=q,
            retrieved_files=["NCT0_Prot_000.pdf"],
            retrieved_sections=["8.1.1 RECIST"],
            cited_files=["NCT0_Prot_000.pdf"],
            answer=SECRET_ANSWER,
            refused=False,
            refusal_reason=None,
            retrieval_ms=100,
            generation_ms=900,
        )
    ]


def test_aggregate_results_carry_no_answers_or_questions(tmp_path: Path) -> None:
    outcomes = _outcomes()
    summary = {
        "overall": summarize(outcomes),
        "by_type": summarize_by(outcomes, lambda o: o.question.qtype),
        "by_lang": summarize_by(outcomes, lambda o: o.question.lang),
        "refusal_reasons": refusal_reasons(outcomes),
    }
    config = {"corpus": "private", "label": "x", "run_at": "2026-10-09T00:00:00"}
    report = render_report(config, summary, outcomes, per_question=False)
    write_results(tmp_path / "agg", config, summary, None, report)

    written = {p.name: p.read_text(encoding="utf-8") for p in (tmp_path / "agg").iterdir()}
    assert sorted(written) == ["config.json", "report.md", "summary.json"]
    blob = "\n".join(written.values())
    assert SECRET_ANSWER not in blob and "스캔 주기" not in blob
    assert json.loads(written["summary.json"])["by_type"]["imaging_schedule"]["hit_at_k"] == 1.0

    full = render_report(config, summary, outcomes)  # the local-only copy keeps the table
    assert "## Per-question" in full


def test_private_results_must_live_outside_git(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    assert _inside_git_work_tree(root / "eval" / "results" / "new-folder")
    assert not _inside_git_work_tree(tmp_path / "results")
