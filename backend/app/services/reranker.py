"""Optional cross-encoder reranking stage (B7).

Retrieval returns `RERANK_CANDIDATES` chunks by cosine, a cross-encoder scores every
(question, chunk) pair jointly, and the best `top_k` by that score go to the prompt. The
cross-encoder score (sigmoid of the relevance logit, 0..1) also drives the answerability gate
(`RERANK_MIN_SCORE`) instead of the bi-encoder cosine, see docs/decisions/0004-reranker.md.

The model is BAAI/bge-reranker-v2-m3 (XLM-RoBERTa large, Apache-2.0), run in-process with
PyTorch on Apple MPS when available, else CPU. torch/transformers are an optional extra
(`uv sync --extra rerank`) so the default api image stays small; they are imported lazily and
the model is only loaded from a local folder or Hugging Face cache (never downloaded at runtime:
`local_files_only=True`).
"""

import asyncio
import math
import threading
from dataclasses import replace
from pathlib import Path
from typing import Any, Protocol

from app.services.vector_search_service import RetrievedChunk

BGE_RERANKER_V2_M3 = "BAAI/bge-reranker-v2-m3"
# Exact Hugging Face revision measured in eval/results (pin it; `main` can move).
BGE_RERANKER_V2_M3_REVISION = "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"


class RerankerUnavailableError(RuntimeError):
    """The optional extra is not installed or the model files are not available locally."""


class Reranker(Protocol):
    model: str

    async def score(self, query: str, texts: list[str]) -> list[float]: ...


def rerank_chunks(
    chunks: list[RetrievedChunk], scores: list[float], top_k: int
) -> list[RetrievedChunk]:
    """Attach `rerank_score` and keep the `top_k` best (stable for ties: cosine order wins)."""
    if len(scores) != len(chunks):
        raise ValueError(f"reranker returned {len(scores)} scores for {len(chunks)} chunks")
    scored = [replace(c, rerank_score=float(s)) for c, s in zip(chunks, scores, strict=True)]
    order = sorted(range(len(scored)), key=lambda i: -scored[i].rerank_score)  # type: ignore[operator]
    return [scored[i] for i in order[:top_k]]


def _pick_device(requested: str) -> str:
    import torch

    if requested != "auto":
        return requested
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


class CrossEncoderReranker:
    """bge-reranker-v2-m3 via transformers. Thread-safe; inference runs in a worker thread."""

    def __init__(
        self,
        model: str = BGE_RERANKER_V2_M3,
        *,
        revision: str | None = BGE_RERANKER_V2_M3_REVISION,
        device: str = "auto",
        batch_size: int = 16,
        max_length: int = 512,
    ) -> None:
        self.model = model
        self.revision = revision
        self._requested_device = device
        self.device: str | None = None
        self._batch_size = batch_size
        self._max_length = max_length
        self._tokenizer: Any = None
        self._net: Any = None
        self._lock = threading.Lock()

    def load(self) -> None:
        """Load once (blocking). Raises RerankerUnavailableError instead of downloading."""
        if self._net is not None:
            return
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except ImportError as exc:  # pragma: no cover - depends on the optional extra
            raise RerankerUnavailableError(
                "reranker needs the optional extra: uv sync --extra rerank"
            ) from exc
        source = self.model
        revision = None if Path(source).is_dir() else self.revision
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                source, revision=revision, local_files_only=True
            )
            net = AutoModelForSequenceClassification.from_pretrained(
                source, revision=revision, local_files_only=True, dtype=torch.float32
            )
        except OSError as exc:
            raise RerankerUnavailableError(
                f"reranker model {source}@{revision} is not available locally: {exc}"
            ) from exc
        device = _pick_device(self._requested_device)
        net.eval().to(device)
        self._tokenizer, self._net, self.device = tokenizer, net, device

    def score_sync(self, query: str, texts: list[str]) -> list[float]:
        import torch

        with self._lock:
            self.load()
            scores: list[float] = []
            for i in range(0, len(texts), self._batch_size):
                batch = texts[i : i + self._batch_size]
                inputs = self._tokenizer(
                    [query] * len(batch),
                    batch,
                    padding=True,
                    truncation="only_second",
                    max_length=self._max_length,
                    return_tensors="pt",
                ).to(self.device)
                with torch.inference_mode():
                    logits = self._net(**inputs).logits.view(-1).float().cpu().tolist()
                scores.extend(1.0 / (1.0 + math.exp(-x)) for x in logits)
            return scores

    async def score(self, query: str, texts: list[str]) -> list[float]:
        if not texts:
            return []
        return await asyncio.to_thread(self.score_sync, query, texts)
