"""Tune the cosine answerability gate (MIN_RELEVANCE_SCORE) for one embedding model, dev only.

Input: result folders of runs made with `--min-relevance-score -1` (gate off), so every question
records its best cosine `maxCosine` and what the generator did. The gate only removes questions
before generation (NO_EVIDENCE) and the prompt does not depend on the threshold, so any
threshold can be replayed exactly from one run:

    refused(t) = refused in the run  or  maxCosine < t

Split: the same as eval/tune_gate.py (dev = every toy question + public questions at even
positions per type sorted by id). The held-out half is never read here.

Objective (v1, pre-registered 2026-10-10 in the packet report before any EmbeddingGemma run):
maximize refusal accuracy (must-refuse) - false refusal rate (answerable) on dev, partial
answers counted as answered. Ties -> the middle of the tied interval (largest margin).

    uv run --project backend python eval/tune_cosine_gate.py \
        --run eval/results/<toy gate-off run> --run eval/results/<public gate-off run> \
        --out eval/results/<date>_cosine-gate_<model>
"""

import argparse
import json
from pathlib import Path
from typing import Any

from tune_gate import load, split


def replay(rows: list[dict[str, Any]], t: float) -> dict[str, Any]:
    answerable = [r for r in rows if r["answerable"]]
    refuse = [r for r in rows if not r["answerable"]]

    def refused(r: dict[str, Any]) -> bool:
        cos = r.get("maxCosine")
        return bool(r["refused"]) or (cos is not None and cos < t)

    fr = sum(refused(r) for r in answerable)
    ok = sum(refused(r) for r in refuse)
    return {
        "threshold": t,
        "answerable": len(answerable),
        "must_refuse": len(refuse),
        "false_refusals": fr,
        "false_refusal_rate": fr / len(answerable) if answerable else None,
        "refused_correctly": ok,
        "refusal_accuracy": ok / len(refuse) if refuse else None,
    }


def objective(m: dict[str, Any]) -> float:
    return (m["refusal_accuracy"] or 0.0) - (m["false_refusal_rate"] or 0.0)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--run", action="append", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    dev: list[dict[str, Any]] = []
    n_test = 0
    for run in args.run:
        corpus, rows = load(run)
        assignment = split(corpus, rows)
        dev += [{**r, "corpus": corpus} for r in rows if assignment[r["id"]] == "dev"]
        n_test += sum(1 for r in rows if assignment[r["id"]] == "test")  # counted, never read

    cosines = sorted({round(r["maxCosine"], 4) for r in dev if r.get("maxCosine") is not None})
    mids = [round((a + b) / 2, 5) for a, b in zip(cosines, cosines[1:], strict=False)]
    grid = sorted({-1.0, *mids, *(round(x * 0.01, 2) for x in range(-100, 101))})
    curve = [replay(dev, t) for t in grid]
    top = max(round(objective(m), 9) for m in curve)
    tied = [m["threshold"] for m in curve if round(objective(m), 9) == top]
    # the tied thresholds can form several runs; use the widest contiguous run on the grid
    runs: list[list[float]] = []
    for t in grid:
        if t in tied:
            if runs and grid.index(t) == grid.index(runs[-1][-1]) + 1:
                runs[-1].append(t)
            else:
                runs.append([t])
    widest = max(runs, key=lambda r: r[-1] - r[0])
    chosen = round((widest[0] + widest[-1]) / 2, 3)
    result = {
        "objective": "dev: refusal accuracy - false refusal rate (v1, pre-registered)",
        "dev_questions": len(dev),
        "test_questions_not_read": n_test,
        "chosen_threshold": chosen,
        "objective_value": top,
        "tied_interval": [widest[0], widest[-1]],
        "dev_at_chosen": replay(dev, chosen),
        "dev_no_gate": replay(dev, -1.0),
        "dev_curve": [m for m in curve if round(m["threshold"] * 100) % 5 == 0],
        "runs": [str(r) for r in args.run],
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    a, n = result["dev_at_chosen"], result["dev_no_gate"]
    lines = [
        "# Cosine gate tuning (MIN_RELEVANCE_SCORE)",
        "",
        f"Runs: {', '.join(f'`{r.name}`' for r in args.run)}",
        f"Dev: {len(dev)} questions. Held-out half ({n_test}) not read.",
        "",
        f"Objective v1 (pre-registered): refusal accuracy - false refusal rate -> value {top:.4f}, "
        f"tied interval {widest[0]}..{widest[-1]} -> **{chosen}**",
        "",
        "| gate | refusal accuracy | false refusal |",
        "|---|---|---|",
        f"| none (-1) | {n['refused_correctly']}/{n['must_refuse']} | "
        f"{n['false_refusals']}/{n['answerable']} |",
        f"| {chosen} | {a['refused_correctly']}/{a['must_refuse']} | "
        f"{a['false_refusals']}/{a['answerable']} |",
        "",
    ]
    (args.out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
