"""Thin async client for a local Ollama server (embeddings + local generation).

One `httpx.AsyncClient` is created per application lifetime (connection pooling) and reused for
every call. Transient failures (connection errors, timeouts, 429/5xx) are retried with
exponential backoff.
"""

import asyncio
import json
import logging
import time
from typing import Any

import httpx
from pydantic import ValidationError

from app.services.llm_types import (
    GROUNDED_ANSWER_SCHEMA,
    GenerationResult,
    GroundedAnswer,
    LLMError,
    LLMUsage,
    StructuredOutputError,
)

logger = logging.getLogger(__name__)


class OllamaError(LLMError):
    def __init__(self, message: str, *, error_type: str = "OLLAMA_ERROR") -> None:
        super().__init__(message, error_type=error_type)


_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class _RetryableStatus(Exception):
    def __init__(self, response: httpx.Response) -> None:
        super().__init__(f"HTTP {response.status_code}")
        self.response = response


class OllamaClient:
    provider = "ollama"

    def __init__(
        self,
        http: httpx.AsyncClient,
        *,
        llm_model: str,
        embedding_model: str,
        max_retries: int = 3,
        backoff_base_sec: float = 0.5,
    ) -> None:
        self._http = http
        self.model = llm_model
        self.embedding_model = embedding_model
        self._max_retries = max_retries
        self._backoff_base_sec = backoff_base_sec

    @classmethod
    def create(
        cls,
        base_url: str,
        *,
        llm_model: str,
        embedding_model: str,
        timeout_sec: float,
        max_retries: int,
    ) -> "OllamaClient":
        http = httpx.AsyncClient(base_url=base_url, timeout=httpx.Timeout(timeout_sec))
        return cls(
            http, llm_model=llm_model, embedding_model=embedding_model, max_retries=max_retries
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        payload = {"model": self.embedding_model, "input": texts}
        data = await self._request("POST", "/api/embed", json=payload)
        embeddings = data.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise OllamaError("Unexpected /api/embed response shape", error_type="EMBEDDING_FAILED")
        return embeddings

    async def generate(self, prompt: str, *, system: str | None = None) -> GenerationResult:
        data, usage = await self._generate(prompt, system=system)
        return GenerationResult(text=str(data.get("response", "")).strip(), usage=usage)

    async def generate_answer(
        self, prompt: str, *, system: str | None = None
    ) -> tuple[GroundedAnswer, LLMUsage]:
        # Ollama >= 0.5 constrains decoding to a JSON schema via `format`.
        data, usage = await self._generate(prompt, system=system, fmt=GROUNDED_ANSWER_SCHEMA)
        raw = str(data.get("response", "")).strip()
        try:
            return GroundedAnswer.model_validate(json.loads(raw)), usage
        except (json.JSONDecodeError, ValidationError) as exc:
            raise StructuredOutputError(
                f"Ollama returned non-schema output: {exc}", raw_text=raw, usage=usage
            ) from exc

    async def list_models(self) -> list[str]:
        data = await self._request("GET", "/api/tags")
        return [m.get("name", "") for m in data.get("models", [])]

    async def _generate(
        self, prompt: str, *, system: str | None, fmt: dict[str, Any] | None = None
    ) -> tuple[dict[str, Any], LLMUsage]:
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            # Low temperature: answers should stick to the retrieved context.
            "options": {"temperature": 0.1},
        }
        if system:
            payload["system"] = system
        if fmt is not None:
            payload["format"] = fmt
        start = time.perf_counter()
        data = await self._request("POST", "/api/generate", json=payload)
        usage = LLMUsage(
            provider=self.provider,
            model=self.model,
            latency_ms=int((time.perf_counter() - start) * 1000),
            input_tokens=data.get("prompt_eval_count"),
            output_tokens=data.get("eval_count"),
        )
        return data, usage

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        attempt = 0
        while True:
            try:
                response = await self._http.request(method, path, **kwargs)
                if response.status_code in _RETRYABLE_STATUS:
                    raise _RetryableStatus(response)
                if response.is_error:
                    raise OllamaError(
                        f"Ollama {method} {path} failed: {response.status_code} {response.text}",
                        error_type="OLLAMA_BAD_REQUEST",
                    )
                return response.json()
            except (httpx.TransportError, _RetryableStatus) as exc:
                if attempt >= self._max_retries:
                    error_type = (
                        "OLLAMA_TIMEOUT"
                        if isinstance(exc, httpx.TimeoutException)
                        else "OLLAMA_UNAVAILABLE"
                    )
                    raise OllamaError(
                        f"Ollama {method} {path} failed after {attempt + 1} attempts: {exc!r}",
                        error_type=error_type,
                    ) from exc
                delay = self._backoff_base_sec * (2**attempt)
                logger.warning("Ollama %s %s failed (%r); retry in %.1fs", method, path, exc, delay)
                attempt += 1
                await asyncio.sleep(delay)
