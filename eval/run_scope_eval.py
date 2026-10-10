"""B6: measure OUT_OF_SCOPE (clinical-judgement request) detection on a held-out set.

    uv run --project backend python eval/run_scope_eval.py          # needs host Ollama (bge-m3)

1. embeds the exemplars (backend/app/rules/scope_exemplars.yaml) and the held-out questions
   (eval/scope_heldout.yaml) with the configured embedding model (local Ollama only)
2. tunes the kNN margin on the EXEMPLARS ONLY (leave-one-out, max Youden J) - the held-out set
   never influences the threshold
3. reports precision / recall / F1 / confusion matrix on the held-out set for:
   mvp1 regex (old) | request regex | embedding kNN | regex + embedding (shipped)
4. writes eval/results/<date>_scope-b6_<model>_<sethash>/{summary.json,report.md}

The positive class is "refuse" (a diagnosis / treatment / reading request).
"""

import argparse
import asyncio
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings  # noqa: E402
from app.services.embedding_service import EmbeddingService  # noqa: E402
from app.services.ollama_client import OllamaClient  # noqa: E402
from app.services.scope_classifier import (  # noqa: E402
    ScopeExemplars,
    margin_score,
    mvp1_regex,
    request_regex,
)

sys.path.insert(0, str(ROOT / "eval"))
from run_eval import ollama_version  # noqa: E402

HELDOUT = ROOT / "eval" / "scope_heldout.yaml"
RESULTS = ROOT / "eval" / "results"


@dataclass
class Confusion:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0

    def add(self, predicted: bool, actual: bool) -> None:
        if predicted and actual:
            self.tp += 1
        elif predicted:
            self.fp += 1
        elif actual:
            self.fn += 1
        else:
            self.tn += 1

    def metrics(self) -> dict[str, Any]:
        p = self.tp / (self.tp + self.fp) if self.tp + self.fp else None
        r = self.tp / (self.tp + self.fn) if self.tp + self.fn else None
        f1 = 2 * p * r / (p + r) if p and r else None
        n = self.tp + self.fp + self.fn + self.tn
        return {
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "tn": self.tn,
            "precision": p,
            "recall": r,
            "f1": f1,
            "accuracy": (self.tp + self.tn) / n if n else None,
            "false_refusal_rate": self.fp / (self.fp + self.tn) if self.fp + self.tn else None,
        }


def tune_margin(pos: list[list[float]], neg: list[list[float]], k: int) -> dict[str, Any]:
    """Leave-one-out scores on the exemplars; threshold with max Youden J (TPR - FPR)."""
    scores: list[tuple[float, bool]] = []
    for i, v in enumerate(pos):
        scores.append((margin_score(v, pos[:i] + pos[i + 1 :], neg, k), True))
    for i, v in enumerate(neg):
        scores.append((margin_score(v, pos, neg[:i] + neg[i + 1 :], k), False))
    n_pos = sum(1 for _, y in scores if y)
    n_neg = len(scores) - n_pos
    best = (-1.0, 0.0)
    candidates = sorted({s for s, _ in scores})
    for a, b in zip(candidates, candidates[1:], strict=False):
        t = (a + b) / 2
        tpr = sum(1 for s, y in scores if y and s >= t) / n_pos
        fpr = sum(1 for s, y in scores if not y and s >= t) / n_neg
        if tpr - fpr > best[0]:
            best = (tpr - fpr, t)
    return {"margin": round(best[1], 4), "youden_j": round(best[0], 4), "loo_scores": scores}


def _fmt(v: Any) -> str:
    return "-" if v is None else (f"{v:.1%}" if isinstance(v, float) else str(v))


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=int, default=None)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    k = args.k or settings.scope_top_k
    exemplars = ScopeExemplars.load(settings.rules_path / "scope_exemplars.yaml")
    heldout = yaml.safe_load(HELDOUT.read_text(encoding="utf-8"))
    client = OllamaClient.create(
        settings.ollama_base_url,
        llm_model=settings.ollama_llm_model,
        embedding_model=settings.ollama_embedding_model,
        embedding_truncate_dim=settings.embedding_truncate_dim,
        timeout_sec=settings.ollama_timeout_sec,
        max_retries=settings.ollama_max_retries,
    )
    embeddings = EmbeddingService(
        client,
        dimension=settings.embedding_dimension,
        model=settings.ollama_embedding_model,
        query_prefix=settings.embedding_query_prefix or "",
    )
    try:
        pos = await embeddings.embed_queries(exemplars.out_of_scope)
        neg = await embeddings.embed_queries(exemplars.in_scope)
        qvecs = await embeddings.embed_queries([h["q"] for h in heldout])
    finally:
        await client.aclose()

    tuned = tune_margin(pos, neg, k)
    margin = tuned["margin"]
    methods = {
        "mvp1_regex": lambda h, s: mvp1_regex(h["q"]),
        "request_regex": lambda h, s: request_regex(h["q"]),
        "embedding_knn": lambda h, s: s >= margin,
        "regex+embedding": lambda h, s: request_regex(h["q"]) or s >= margin,
    }
    rows = []
    for h, v in zip(heldout, qvecs, strict=True):
        score = margin_score(v, pos, neg, k)
        rows.append({**h, "score": round(score, 4)})

    summary: dict[str, Any] = {
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "embedding_model": settings.ollama_embedding_model,
        "embedding_dim": settings.embedding_dimension,
        "embedding_truncate_dim": settings.embedding_truncate_dim,
        "ollama_version": ollama_version(settings.ollama_base_url),
        "k": k,
        "exemplars": {"out_of_scope": len(pos), "in_scope": len(neg)},
        "heldout": {
            "n": len(heldout),
            "refuse": sum(h["label"] == "refuse" for h in heldout),
            "allow": sum(h["label"] == "allow" for h in heldout),
            "sha256": hashlib.sha256(HELDOUT.read_bytes()).hexdigest()[:12],
        },
        "tuned_margin": margin,
        "loo_youden_j": tuned["youden_j"],
        "methods": {},
        "by_group": {},
        "errors": {},
    }
    for name, fn in methods.items():
        cm = Confusion()
        groups: dict[str, Confusion] = {}
        errors = []
        for r in rows:
            pred = bool(fn(r, r["score"]))
            actual = r["label"] == "refuse"
            cm.add(pred, actual)
            for g in (f"lang={r['lang']}", f"kind={r['kind']}"):
                groups.setdefault(g, Confusion()).add(pred, actual)
            if pred != actual:
                errors.append({"q": r["q"], "label": r["label"], "score": r["score"]})
        summary["methods"][name] = cm.metrics()
        summary["by_group"][name] = {g: c.metrics() for g, c in sorted(groups.items())}
        summary["errors"][name] = errors
    summary["heldout_scores"] = rows
    summary["sweep_for_reference_only"] = [
        {
            "margin": t,
            **Confusion_from(rows, lambda r, t=t: request_regex(r["q"]) or r["score"] >= t),
        }
        for t in (-0.04, -0.02, 0.0, 0.02, 0.04, 0.06)
    ]

    report = render(summary)
    print(report)
    if not args.no_write:
        stamp = datetime.now().strftime("%Y-%m-%d")
        model = settings.ollama_embedding_model.replace(":", "-")
        if settings.embedding_truncate_dim:
            model += f"-{settings.embedding_truncate_dim}d"
        out = RESULTS / f"{stamp}_scope-b6_{model}_{summary['heldout']['sha256']}"
        out.mkdir(parents=True, exist_ok=True)
        (out / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (out / "report.md").write_text(report, encoding="utf-8")
        print(f"written to {out.relative_to(ROOT)}")
    return 0


def Confusion_from(rows: list[dict[str, Any]], fn) -> dict[str, Any]:  # noqa: N802
    cm = Confusion()
    for r in rows:
        cm.add(bool(fn(r)), r["label"] == "refuse")
    m = cm.metrics()
    return {k: m[k] for k in ("precision", "recall", "false_refusal_rate")}


def render(s: dict[str, Any]) -> str:
    h = s["heldout"]
    lines = [
        f"# B6 OUT_OF_SCOPE detection — held-out evaluation ({s['run_at']})",
        "",
        f"- embedding model: `{s['embedding_model']}`, k={s['k']}, exemplars "
        f"{s['exemplars']['out_of_scope']} refuse / {s['exemplars']['in_scope']} allow",
        f"- held-out: {h['n']} questions ({h['refuse']} refuse / {h['allow']} allow), "
        f"sha256 {h['sha256']}",
        f"- margin tuned on exemplars only (leave-one-out, Youden J={s['loo_youden_j']}): "
        f"**{s['tuned_margin']}**",
        "",
        "| method | precision | recall | F1 | false-refusal (allow→refuse) | TP | FP | FN | TN |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for name, m in s["methods"].items():
        lines.append(
            f"| {name} | {_fmt(m['precision'])} | {_fmt(m['recall'])} | {_fmt(m['f1'])} | "
            f"{_fmt(m['false_refusal_rate'])} | {m['tp']} | {m['fp']} | {m['fn']} | {m['tn']} |"
        )
    lines += ["", "## Confusion matrix (regex+embedding, shipped)", ""]
    m = s["methods"]["regex+embedding"]
    lines += [
        "| | predicted refuse | predicted allow |",
        "|---|---|---|",
        f"| actual refuse | {m['tp']} | {m['fn']} |",
        f"| actual allow | {m['fp']} | {m['tn']} |",
        "",
        "## By group (R = recall on refuse items, FR = false-refusal rate on allow items)",
        "",
        "| group | " + " | ".join(s["methods"]) + " |",
        "|---|" + "---|" * len(s["methods"]),
    ]
    groups = sorted(next(iter(s["by_group"].values())))
    for g in groups:
        cells = []
        for name in s["methods"]:
            gm = s["by_group"][name][g]
            parts = []
            if gm["tp"] + gm["fn"]:
                parts.append(f"R {_fmt(gm['recall'])}")
            if gm["fp"] + gm["tn"]:
                parts.append(f"FR {_fmt(gm['false_refusal_rate'])}")
            cells.append(" / ".join(parts))
        lines.append(f"| {g} | " + " | ".join(cells) + " |")
    lines += ["", "## Errors (regex+embedding)", ""]
    for e in s["errors"]["regex+embedding"] or [{"q": "(none)", "label": "", "score": ""}]:
        lines.append(f"- [{e['label']}] score={e['score']} — {e['q']}")
    lines += ["", "## Margin sweep on held-out (reference only; NOT used to pick the margin)", ""]
    lines += ["| margin | precision | recall | false-refusal |", "|---|---|---|---|"]
    for row in s["sweep_for_reference_only"]:
        lines.append(
            f"| {row['margin']} | {_fmt(row['precision'])} | {_fmt(row['recall'])} | "
            f"{_fmt(row['false_refusal_rate'])} |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
