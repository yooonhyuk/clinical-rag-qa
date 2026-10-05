"""Check whether an Ollama embedding model can represent Korean (docs/issues/001).

    uv run --project backend python scripts/diagnose_embedding.py nomic-embed-text bge-m3

1. Tokenizer vocabulary: reads the model's GGUF file from the local Ollama store
   (OLLAMA_MODELS or ~/.ollama/models) and counts tokens containing Hangul syllables.
2. Embedding probe: cosine similarity of unrelated Korean texts via the Ollama API
   (OLLAMA_BASE_URL, default http://localhost:11434). ~1.0 means the texts collapse to the
   same token sequence ([UNK] ...).
"""

import json
import math
import os
import re
import struct
import sys
from pathlib import Path
from typing import Any, BinaryIO

import httpx

STORE = Path(os.getenv("OLLAMA_MODELS", Path.home() / ".ollama" / "models"))
OLLAMA = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
PREFIX = {"nomic-embed-text": "search_query: "}
PAIRS = [
    ("업로드", "태그"),
    ("헬프데스크 운영 시간은 언제인가요?", "이 CT에 폐결절이 있나요?"),
    ("upload", "tag"),
]
_SCALARS = dict(zip((0, 1, 2, 3, 4, 5, 6, 7, 10, 11, 12), "BbHhIif?Qqd", strict=True))


def _gguf_metadata(path: Path) -> dict[str, Any]:
    def unpack(f: BinaryIO, fmt: str) -> Any:
        return struct.unpack("<" + fmt, f.read(struct.calcsize("<" + fmt)))[0]

    def string(f: BinaryIO) -> str:
        return f.read(unpack(f, "Q")).decode("utf-8", "replace")

    def value(f: BinaryIO, kind: int) -> Any:
        if kind == 8:
            return string(f)
        if kind == 9:
            item_kind, n = unpack(f, "I"), unpack(f, "Q")
            return [value(f, item_kind) for _ in range(n)]
        return unpack(f, _SCALARS[kind])

    with path.open("rb") as f:
        if f.read(4) != b"GGUF":
            raise ValueError(f"{path} is not a GGUF file")
        _version, _tensors, n_kv = unpack(f, "I"), unpack(f, "Q"), unpack(f, "Q")
        meta = {}
        for _ in range(n_kv):
            key = string(f)
            meta[key] = value(f, unpack(f, "I"))
        return meta


def _model_blob(model: str) -> Path:
    name, _, tag = model.partition(":")
    manifest = STORE / "manifests" / "registry.ollama.ai" / "library" / name / (tag or "latest")
    layers = json.loads(manifest.read_text())["layers"]
    digest = next(x["digest"] for x in layers if x["mediaType"].endswith(".model"))
    return STORE / "blobs" / digest.replace(":", "-")


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    return dot / math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))


def main(models: list[str]) -> None:
    for model in models:
        meta = _gguf_metadata(_model_blob(model))
        tokens = meta["tokenizer.ggml.tokens"]
        hangul = [t for t in tokens if re.search("[가-힣]", t)]
        unk = meta.get("tokenizer.ggml.unknown_token_id")
        dim = next((v for k, v in meta.items() if k.endswith(".embedding_length")), None)
        print(f"## {model}")
        print(f"tokenizer={meta.get('tokenizer.ggml.model')} vocab={len(tokens)} dim={dim}")
        print(f"tokens with Hangul syllables: {len(hangul)} {hangul[:5]}")
        print(f"unknown token: id={unk} {tokens[unk]!r}" if unk is not None else "unknown token: -")
        prefix = PREFIX.get(model.split(":")[0], "")
        for a, b in PAIRS:
            r = httpx.post(
                f"{OLLAMA}/api/embed",
                json={"model": model, "input": [prefix + a, prefix + b]},
                timeout=120,
            )
            r.raise_for_status()
            ea, eb = r.json()["embeddings"]
            print(f"cos({a!r}, {b!r}) = {_cos(ea, eb):.4f}")
        print()


if __name__ == "__main__":
    main(sys.argv[1:] or ["nomic-embed-text", "bge-m3"])
