"""Small probes for docs/analysis/medgemma-vs-gemma4.md (host Ollama only, no downloads).

1. closed-book: eval/probes/closed_book_items.yaml (22 self-authored MCQs), asked WITHOUT
   retrieval in two option orders (as written, and rotated so the gold letters are spread over
   A-D). Scored by exact letter match. Small, low statistical power.
2. image (anecdotal): pydicom's bundled test file CT_small.dcm, only if it is already installed
   locally (never downloaded), rendered to PNG and described by each model. Not scored.

    uv run --project backend python eval/probes/run_model_probes.py \
        --models gemma4:e4b medgemma:4b --out eval/results/2026-10-07_model-probes
"""

import argparse
import base64
import io
import json
import re
import time
from pathlib import Path
from typing import Any

import httpx
import yaml

HERE = Path(__file__).resolve().parent
LETTERS = "ABCD"
MCQ_INSTRUCTION = (
    "Answer the multiple-choice question. Reply with only the letter (A, B, C or D) of the "
    "correct option."
)
IMAGE_QUESTION = (
    "This is a medical image. Which imaging modality is it, which body region is shown, and in "
    "which anatomical plane? Answer in at most three sentences."
)
_LETTER_RE = re.compile(r"\b([ABCD])\b")


def rotate(item: dict[str, Any], target: str) -> tuple[dict[str, str], str]:
    """Reorder the options so the gold option sits at `target` (others keep their order)."""
    gold = item["options"][item["answer"]]
    others = [v for k, v in sorted(item["options"].items()) if k != item["answer"]]
    order = others[:]
    order.insert(LETTERS.index(target), gold)
    return dict(zip(LETTERS, order, strict=True)), target


def mcq_prompt(question: str, options: dict[str, str]) -> str:
    opts = "\n".join(f"{k}. {v}" for k, v in options.items())
    return f"{MCQ_INSTRUCTION}\n\nQuestion: {question}\n{opts}\nAnswer:"


def parse_letter(text: str) -> str | None:
    match = _LETTER_RE.search(text.strip())
    return match.group(1) if match else None


def generate(http: httpx.Client, model: str, prompt: str, images: list[str] | None = None) -> dict:
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 1024},
    }
    if images:
        payload["images"] = images
    start = time.perf_counter()
    data = http.post("/api/generate", json=payload).json()
    data["latency_ms"] = int((time.perf_counter() - start) * 1000)
    return data


def closed_book(http: httpx.Client, model: str, items: list[dict]) -> list[dict]:
    rows = []
    for i, item in enumerate(items):
        variants = {
            "as_written": (item["options"], item["answer"]),
            "rotated": rotate(item, LETTERS[i % 4]),
        }
        for order, (options, gold) in variants.items():
            data = generate(http, model, mcq_prompt(item["question"], options))
            text = str(data.get("response", ""))
            got = parse_letter(text)
            rows.append(
                {
                    "id": item["id"],
                    "lang": item["lang"],
                    "topic": item["topic"],
                    "order": order,
                    "gold": gold,
                    "got": got,
                    "correct": got == gold,
                    "raw": text[:300],
                    "thinking_chars": len(str(data.get("thinking") or "")),
                    "latency_ms": data["latency_ms"],
                }
            )
            print(f"  {model} {item['id']} {order}: {got} (gold {gold})", flush=True)
    return rows


def ct_small_png() -> str | None:
    """CT_small.dcm from pydicom's bundled test data, if installed; never downloads."""
    try:
        import numpy as np
        import pydicom
        from PIL import Image
    except ImportError:
        return None
    path = Path(pydicom.__file__).parent / "data" / "test_files" / "CT_small.dcm"
    if not path.is_file():
        return None
    ds = pydicom.dcmread(path)
    hu = ds.pixel_array.astype(float) * float(ds.RescaleSlope) + float(ds.RescaleIntercept)
    level, width = 40.0, 400.0  # soft-tissue window
    img = np.clip((hu - (level - width / 2)) / width, 0, 1) * 255
    png = Image.fromarray(img.astype("uint8")).resize((512, 512), Image.Resampling.BICUBIC)
    buf = io.BytesIO()
    png.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", default=["gemma4:e4b", "medgemma:4b"])
    parser.add_argument("--ollama", default="http://localhost:11434")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    items = yaml.safe_load((HERE / "closed_book_items.yaml").read_text(encoding="utf-8"))
    args.out.mkdir(parents=True, exist_ok=True)
    image = ct_small_png()
    if image:
        (args.out / "ct_small_soft_tissue.png").write_bytes(base64.b64decode(image))
    summary: dict[str, Any] = {"items": len(items), "models": {}}
    with httpx.Client(base_url=args.ollama, timeout=300) as http:
        for model in args.models:
            rows = closed_book(http, model, items)
            with (args.out / f"closed_book_{model.replace(':', '-')}.jsonl").open("w") as fh:
                for r in rows:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            by_order = {
                o: sum(r["correct"] for r in rows if r["order"] == o)
                for o in ("as_written", "rotated")
            }
            ids = {r["id"] for r in rows}
            both = sum(all(r["correct"] for r in rows if r["id"] == i) for i in ids)
            unparsed = sum(r["got"] is None for r in rows)
            entry: dict[str, Any] = {
                "correct_as_written": by_order["as_written"],
                "correct_rotated": by_order["rotated"],
                "correct_in_both_orders": both,
                "unparsed": unparsed,
            }
            if image:
                data = generate(http, model, IMAGE_QUESTION, images=[image])
                entry["image_ct_small"] = str(data.get("response", "")).strip()
            summary["models"][model] = entry
            print(json.dumps({model: entry}, ensure_ascii=False, indent=2), flush=True)
    summary["image_probe"] = "CT_small.dcm (pydicom bundled)" if image else "skipped: not installed"
    (args.out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
