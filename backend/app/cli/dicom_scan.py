"""Run the DICOM analyzer (Layer 1 + quantitation readiness + Layer 2) over a folder.

    uv run --project backend python -m app.cli.dicom_scan <folder> [--json out.jsonl]
    make dicom-scan DIR=<folder>

- Reads headers only (stop_before_pixels); no LLM, no database, no network.
- Every file under the folder is tried; non-DICOM files are counted and skipped.
- Output contains finding codes, standard keywords, counts and citations - never attribute
  values. File paths are printed as given (use --redact-paths if the names themselves may
  contain identifiers).
"""

import argparse
import json
import sys
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from app.config import Settings
from app.services.dicom_rules import load_rules
from app.services.dicom_service import DicomReadError, evaluate, read_dataset

DEFAULT_RULES = Path(__file__).resolve().parents[1] / "rules"


def iter_files(paths: list[Path]) -> Iterator[Path]:
    for path in paths:
        if path.is_dir():
            yield from sorted(p for p in path.rglob("*") if p.is_file())
        elif path.is_file():
            yield path


def _fmt(counts: dict[str, int]) -> str:
    return f"{counts['error']}/{counts['warning']}/{counts['info']}"


def scan(paths: list[Path], rules_dir: Path) -> Iterator[tuple[Path, dict[str, Any] | None]]:
    rules = load_rules(rules_dir)
    for path in iter_files(paths):
        try:
            yield path, evaluate(read_dataset(path), rules)
        except DicomReadError:
            yield path, None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="+", type=Path, help="folders and/or files")
    parser.add_argument("--json", type=Path, help="write one JSON result per file (JSONL)")
    parser.add_argument("--rules", type=Path, default=None, help="rules directory")
    parser.add_argument("--redact-paths", action="store_true", help="print #n instead of paths")
    parser.add_argument(
        "--fail-on",
        choices=("error", "warning", "never"),
        default="never",
        help="exit 1 if any file has a Layer 1/2 finding of this severity (CI use)",
    )
    args = parser.parse_args(argv)
    rules_dir = args.rules or Settings(_env_file=None, database_url="x://unused").rules_path

    totals: Counter[str] = Counter()
    codes: Counter[str] = Counter()
    iods: Counter[str] = Counter()
    worst = {"error": 0, "warning": 0}
    out = args.json.open("w", encoding="utf-8") if args.json else None
    print(f"{'file':<48} {'IOD':<34} {'L1 e/w/i':>9} {'QR':>5} {'L2 e/w/i':>9}")
    try:
        for i, (path, result) in enumerate(scan(args.paths, rules_dir), start=1):
            name = f"#{i}" if args.redact_paths else str(path)
            if result is None:
                totals["not_dicom"] += 1
                continue
            totals["dicom"] += 1
            c = result["counts"]
            for layer in ("layer1", "layer2"):
                for severity in worst:
                    worst[severity] += c[layer][severity]
            qr = result["quantitation_readiness"]
            qr_text = "-" if not qr["applicable"] else ("ok" if qr["ready"] else "WARN")
            iod = result["layer1"]["iod"]["name"] or "(unknown)"
            iods[iod] += 1
            for layer in ("layer1", "layer2"):
                for f in result[layer]["findings"]:
                    if f["severity"] != "info":
                        codes[f"{f['code']} {f.get('attribute') or ''}".strip()] += 1
            print(
                f"{name[-48:]:<48} {iod[:34]:<34} {_fmt(c['layer1']):>9} {qr_text:>5} "
                f"{_fmt(c['layer2']):>9}"
            )
            if out:
                record = {"file": name, **{k: v for k, v in result.items()}}
                out.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    finally:
        if out:
            out.close()

    print(f"\nDICOM files: {totals['dicom']}  skipped (not DICOM): {totals['not_dicom']}")
    print("IODs: " + ", ".join(f"{k} x{v}" for k, v in iods.most_common()) if iods else "IODs: -")
    print(f"Layer 1+2 errors: {worst['error']}  warnings: {worst['warning']}")
    if codes:
        print("Most frequent error/warning findings:")
        for code, n in codes.most_common(15):
            print(f"  {n:>5}  {code}")
    if args.fail_on != "never":
        levels = ("error",) if args.fail_on == "error" else ("error", "warning")
        if any(worst[level] for level in levels):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
