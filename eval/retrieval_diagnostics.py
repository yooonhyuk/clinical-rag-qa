"""Aggregate retrieval diagnostics of an eval run (no text is written).

Reads a result folder's questions.jsonl (the local-only copy for private corpora) and the
questions file, and reports what the main metrics hide:

- probe hit@k: file / section hit of what retrieval WOULD return for every answerable question,
  including questions that the OUT_OF_SCOPE classifier refused before retrieval (the main
  hit@k counts those as misses)
- other-trial share: fraction of top-k chunks that come from a trial (NCT id prefix of the file
  name, else the file) other than the gold trials - how often one protocol's chunks crowd out
  another's when the chunk text does not say which trial it belongs to
- answerable questions refused per reason

    uv run --project backend python eval/retrieval_diagnostics.py RESULT_DIR QUESTIONS.yaml \\
        [--out diagnostics.json]
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml
from eval_metrics import EvalQuestion

_NCT = re.compile(r"(NCT\d{8})")


def trial_of(file_name: str) -> str:
    match = _NCT.search(file_name)
    return match.group(1) if match else file_name


def diagnose(rows: list[dict[str, Any]], questions: dict[str, EvalQuestion]) -> dict[str, Any]:
    answerable = [r for r in rows if r["answerable"]]
    file_hits = section_hits = other = total = 0
    refused: dict[str, int] = {}
    by_type: dict[str, dict[str, int]] = {}
    for r in answerable:
        q = questions[r["id"]]
        probe = r.get("probe") or []
        files = {p["file"] for p in probe}
        file_hit = bool(q.expected_files & files)
        section_hit = any(
            s.matches(p["file"], p["section"], p["page"]) for p in probe for s in q.sources
        )
        file_hits += file_hit
        section_hits += section_hit
        gold = {trial_of(f) for f in q.expected_files}
        other += sum(trial_of(p["file"]) not in gold for p in probe)
        total += len(probe)
        if r["refused"]:
            refused[r["refusalReason"]] = refused.get(r["refusalReason"], 0) + 1
        group = by_type.setdefault(q.qtype, {"n": 0, "probe_file_hit": 0})
        group["n"] += 1
        group["probe_file_hit"] += file_hit
    n = len(answerable)
    return {
        "answerable": n,
        "probe_file_hit_at_k": round(file_hits / n, 4) if n else None,
        "probe_section_hit_at_k": round(section_hits / n, 4) if n else None,
        "other_trial_chunk_share": round(other / total, 4) if total else None,
        "answerable_refused_by_reason": dict(sorted(refused.items())),
        "probe_file_hit_by_type": {
            t: round(g["probe_file_hit"] / g["n"], 4) for t, g in sorted(by_type.items())
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_dir", type=Path)
    parser.add_argument("questions", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    raw = yaml.safe_load(args.questions.expanduser().read_text(encoding="utf-8"))
    questions = {q["id"]: EvalQuestion.from_dict(q) for q in raw}
    lines = (args.result_dir.expanduser() / "questions.jsonl").read_text(encoding="utf-8")
    report = diagnose([json.loads(line) for line in lines.splitlines() if line], questions)
    print(json.dumps(report, indent=2))
    if args.out:
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
