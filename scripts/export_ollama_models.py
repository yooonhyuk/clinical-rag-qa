"""Export selected models from an existing Ollama model store into a tar archive.

Used by offline-bundle/build-bundle.sh so the bundle reuses models already on the build machine
instead of downloading them again. Only the manifests and blobs of the requested models are
copied. The archive layout is `models/manifests/...` and `models/blobs/...`, i.e. it extracts
into an Ollama home directory (`/root/.ollama` in the ollama image).

    python scripts/export_ollama_models.py --store ~/.ollama/models --out models.tar \\
        gemma4:e4b bge-m3

Weights are already compressed (GGUF), so the archive is an uncompressed tar.
"""

from __future__ import annotations

import argparse
import json
import sys
import tarfile
from pathlib import Path

REGISTRY = "registry.ollama.ai"


def manifest_path(store: Path, model: str) -> Path:
    """`name[:tag]` or `namespace/name[:tag]` -> manifest file inside the store."""
    name, _, tag = model.partition(":")
    if "/" not in name:
        name = f"library/{name}"
    return store / "manifests" / REGISTRY / name / (tag or "latest")


def blob_paths(store: Path, manifest_file: Path) -> list[Path]:
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    digests = [manifest["config"]["digest"], *(layer["digest"] for layer in manifest["layers"])]
    return [store / "blobs" / digest.replace(":", "-") for digest in digests]


def collect(store: Path, models: list[str]) -> list[Path]:
    """All files (manifests + blobs) needed for `models`; raises if any is missing."""
    files: list[Path] = []
    missing: list[str] = []
    for model in models:
        manifest = manifest_path(store, model)
        if not manifest.is_file():
            missing.append(f"{model}: manifest {manifest}")
            continue
        files.append(manifest)
        for blob in blob_paths(store, manifest):
            if blob.is_file():
                files.append(blob)
            else:
                missing.append(f"{model}: blob {blob.name}")
    if missing:
        raise FileNotFoundError("missing in Ollama store:\n  " + "\n  ".join(missing))
    return list(dict.fromkeys(files))  # shared blobs once, order kept


def export(store: Path, models: list[str], out: Path) -> int:
    files = collect(store, models)
    with tarfile.open(out, "w") as tar:
        for path in files:
            tar.add(path, arcname=str(Path("models") / path.relative_to(store)))
    return sum(p.stat().st_size for p in files)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--store", type=Path, default=Path.home() / ".ollama" / "models")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("models", nargs="+")
    args = parser.parse_args(argv)
    try:
        size = export(args.store.expanduser(), args.models, args.out)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"exported {', '.join(args.models)} ({size / 1e9:.2f} GB) -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
