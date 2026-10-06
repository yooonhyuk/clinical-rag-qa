"""Tune the reranker answerability gate (RERANK_MIN_SCORE) on a dev split only.

Input: result folders of runs made with `--reranker bge-reranker-v2-m3 --rerank-min-score 0`
(the gate is off, so every question records its best rerank score `gate.topRerank` and what the
generator did). The gate only removes questions before generation (NO_EVIDENCE), and the prompt
does not depend on the threshold, so any threshold can be replayed exactly from one run:

    refused(t) = refused in the run  or  topRerank < t

Split (fixed, written down before looking at the scores):
    dev  = every toy question  +  public questions at even positions (0, 2, 4, ...) when each
           question type is sorted by id
    test = public questions at odd positions (held out; never used to pick the threshold)

Objective on dev (v1, pre-registered): maximize refusal accuracy (must-refuse) - false
refusal rate (answerable), partial answers counted as answered; ties -> the lowest threshold.
On the 2026-10-07 dev split v1 is saturated (the generator already refused every dev must-refuse
question, so every threshold <= 0.2 ties and v1 picks 0 = no gate). The gate exists to refuse
*before* the generator (which can turn a must-refuse question into a partial answer), so the
threshold is chosen with
v2: maximize gate recall (must-refuse questions that reach the gate, i.e. not OUT_OF_SCOPE,
    with topRerank < t) - false refusal rate (answerable); ties -> the middle of the tied
    interval (largest margin on both sides). v2 was written after looking at dev scores only.

Outcome 2026-10-07 (both reported in the result folder): v2 picked 0.56 (it buys one toy
must-refuse question, q25 at 0.53, for one dev false refusal) and on the held-out half it doubled
the false refusal rate with no refusal gain. The adopted value is the pre-registered v1 result,
RERANK_MIN_SCORE=0 (no rerank gate; the cosine gate stays). Changing the rule again after seeing
the held-out numbers would be tuning on the test split, so this script does not do that.

    uv run --project backend python eval/tune_gate.py \
        --run eval/results/<toy no-gate run> --run eval/results/<public no-gate run> \
        --out eval/results/<date>_gate-tuning
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load(run: Path) -> tuple[str, list[dict[str, Any]]]:
    config = json.loads((run / "config.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in (run / "questions.jsonl").open(encoding="utf-8")]
    return config["corpus"], rows


def split(corpus: str, rows: list[dict[str, Any]]) -> dict[str, str]:
    """question id -> 'dev' | 'test' (see module docstring)."""
    if corpus != "public":
        return {r["id"]: "dev" for r in rows}
    by_type: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        by_type[r["type"]].append(r["id"])
    out = {}
    for ids in by_type.values():
        for i, qid in enumerate(sorted(ids)):
            out[qid] = "dev" if i % 2 == 0 else "test"
    return out


def top_rerank(r: dict[str, Any]) -> float | None:
    gate = r.get("gate") or {}
    return gate.get("topRerank", r.get("topRerank"))


def replay(rows: list[dict[str, Any]], t: float) -> dict[str, Any]:
    answerable = [r for r in rows if r["answerable"]]
    refuse = [r for r in rows if not r["answerable"]]

    def gated(r: dict[str, Any]) -> bool:
        score = top_rerank(r)
        return score is not None and score < t

    def refused(r: dict[str, Any]) -> bool:
        return bool(r["refused"]) or gated(r)

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
        "gate_refused_ids": sorted(r["id"] for r in rows if not r["refused"] and gated(r)),
    }


def objective(m: dict[str, Any]) -> float:
    """v1: end-to-end refusal accuracy - false refusal rate."""
    return (m["refusal_accuracy"] or 0.0) - (m["false_refusal_rate"] or 0.0)


def gate_objective(rows: list[dict[str, Any]], t: float) -> float:
    """v2: share of gate-reachable must-refuse questions the gate alone refuses - false refusal."""
    reachable = [
        r
        for r in rows
        if not r["answerable"]
        and r.get("refusalReason") != "OUT_OF_SCOPE"
        and top_rerank(r) is not None
    ]
    caught = sum(top_rerank(r) < t for r in reachable)  # type: ignore[operator]
    recall = caught / len(reachable) if reachable else 0.0
    return recall - (replay(rows, t)["false_refusal_rate"] or 0.0)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--run", action="append", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    tagged: list[dict[str, Any]] = []
    for run in args.run:
        corpus, rows = load(run)
        assignment = split(corpus, rows)
        for r in rows:
            tagged.append({**r, "corpus": corpus, "split": assignment[r["id"]]})
    dev = [r for r in tagged if r["split"] == "dev"]
    test = [r for r in tagged if r["split"] == "test"]

    scores = sorted({round(s, 4) for r in dev if (s := top_rerank(r)) is not None})
    candidates = [0.0, *scores, *(round(x * 0.01, 2) for x in range(1, 100))]
    grid = sorted({c for c in candidates if 0.0 <= c <= 0.99})
    curve = [replay(dev, t) for t in grid]
    v1 = max(curve, key=lambda m: (round(objective(m), 9), -m["threshold"]))["threshold"]
    v2_scores = {t: round(gate_objective(dev, t), 9) for t in grid}
    top = max(v2_scores.values())
    tied = [t for t, v in v2_scores.items() if v == top]
    middle = (min(tied) + max(tied)) / 2
    # a readable 2-decimal value inside the tied interval
    chosen = round(middle, 2)
    if not min(tied) <= chosen <= max(tied) or round(gate_objective(dev, chosen), 9) < top:
        chosen = middle

    result = {
        "split": {
            "dev": sorted(f"{r['corpus']}:{r['id']}" for r in dev),
            "test": sorted(f"{r['corpus']}:{r['id']}" for r in test),
        },
        "adopted_threshold": v1,
        "v2_threshold": chosen,
        "objective_v1_threshold": v1,
        "objective_v2_tied_interval": [min(tied), max(tied)],
        "objective_v2_value": top,
        "dev": {"no_gate": replay(dev, 0.0), "v2": replay(dev, chosen)},
        "test": {"no_gate": replay(test, 0.0), "v2": replay(test, chosen)},
        "dev_curve": [
            {k: v for k, v in m.items() if k != "gate_refused_ids"}
            for m in curve
            if m["threshold"] in {0.0, chosen} or round(m["threshold"] * 100) % 5 == 0
        ],
        "runs": [str(r) for r in args.run],
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    def row(name: str, m: dict[str, Any]) -> str:
        return (
            f"| {name} | {m['threshold']} | {m['refused_correctly']}/{m['must_refuse']} "
            f"({m['refusal_accuracy']:.1%}) | {m['false_refusals']}/{m['answerable']} "
            f"({m['false_refusal_rate']:.1%}) | {', '.join(m['gate_refused_ids']) or '-'} |"
        )

    lines = [
        "# Reranker gate tuning (RERANK_MIN_SCORE)",
        "",
        f"Runs: {', '.join(f'`{r.name}`' for r in args.run)}",
        "",
        f"Dev: {len(dev)} questions (toy all + public even positions per type). "
        f"Test (held out): {len(test)} public questions (odd positions per type).",
        "",
        f"Objective v1 (pre-registered) -> **{v1}** (adopted). "
        f"Objective v2 (post-hoc, dev only) -> **{chosen}** "
        f"(tied interval {min(tied)}..{max(tied)}). See the module docstring.",
        "",
        "| split / gate | threshold | refusal accuracy | false refusal | refused by the gate |",
        "|---|---|---|---|---|",
        row("dev · no gate", result["dev"]["no_gate"]),
        row("dev · v2", result["dev"]["v2"]),
        row("test · no gate", result["test"]["no_gate"]),
        row("test · v2", result["test"]["v2"]),
        "",
        "## Dev curve (every 0.05)",
        "",
        "| threshold | refusal accuracy | false refusal |",
        "|---|---|---|",
        *(
            f"| {m['threshold']} | {m['refusal_accuracy']:.1%} | {m['false_refusal_rate']:.1%} |"
            for m in result["dev_curve"]
        ),
        "",
    ]
    (args.out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
