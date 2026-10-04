"""Optional Claude API generation provider (explicit opt-in, see `llm_guardrail.py`).

Only *generation* goes to the Claude API; embeddings always stay on local Ollama.
Retries with exponential backoff on 408/409/429/5xx and connection errors, plus request
timeouts, are handled by the official SDK (`max_retries`, `timeout`); this module maps the
final failures onto the app's `LLMError` types.
"""

import json
import logging
import time
from typing import Any

import anthropic
from pydantic import ValidationError

from app.services.llm_types import (
    GROUNDED_ANSWER_SCHEMA,
    GenerationResult,
    GroundedAnswer,
    LLMError,
    LLMUsage,
    ModelRefusalError,
    StructuredOutputError,
)

logger = logging.getLogger(__name__)

# Server-side refusal fallback: on a safety decline the API re-runs the request on a
# fallback model inside the same call ("default" routes by refusal category).
_FALLBACK_BETA = "server-side-fallback-2026-07-01"


class AnthropicGenerationClient:
    provider = "anthropic"

    def __init__(
        self,
        client: anthropic.AsyncAnthropic,
        *,
        model: str,
        max_tokens: int = 16000,
        effort: str = "medium",
        refusal_fallback: bool = True,
    ) -> None:
        self._client = client
        self.model = model
        self._max_tokens = max_tokens
        self._effort = effort
        self._refusal_fallback = refusal_fallback

    @classmethod
    def create(
        cls,
        *,
        api_key: str,
        model: str,
        timeout_sec: float,
        max_retries: int,
        max_tokens: int,
        effort: str,
        refusal_fallback: bool,
    ) -> "AnthropicGenerationClient":
        client = anthropic.AsyncAnthropic(
            api_key=api_key, timeout=timeout_sec, max_retries=max_retries
        )
        return cls(
            client,
            model=model,
            max_tokens=max_tokens,
            effort=effort,
            refusal_fallback=refusal_fallback,
        )

    async def aclose(self) -> None:
        await self._client.close()

    async def generate(self, prompt: str, *, system: str | None = None) -> GenerationResult:
        text, usage = await self._create(prompt, system=system, schema=None)
        return GenerationResult(text=text, usage=usage)

    async def generate_answer(
        self, prompt: str, *, system: str | None = None
    ) -> tuple[GroundedAnswer, LLMUsage]:
        text, usage = await self._create(prompt, system=system, schema=GROUNDED_ANSWER_SCHEMA)
        try:
            return GroundedAnswer.model_validate(json.loads(text)), usage
        except (json.JSONDecodeError, ValidationError) as exc:
            raise StructuredOutputError(
                f"Claude returned non-schema output: {exc}", raw_text=text, usage=usage
            ) from exc

    async def _create(
        self, prompt: str, *, system: str | None, schema: dict[str, Any] | None
    ) -> tuple[str, LLMUsage]:
        output_config: dict[str, Any] = {"effort": self._effort}
        if schema is not None:
            output_config["format"] = {"type": "json_schema", "schema": schema}
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self._max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "output_config": output_config,
        }
        if system:
            kwargs["system"] = system
        if self._refusal_fallback:
            kwargs["betas"] = [_FALLBACK_BETA]
            kwargs["fallbacks"] = "default"

        start = time.perf_counter()
        try:
            response = await self._client.beta.messages.create(**kwargs)
        except anthropic.APITimeoutError as exc:
            raise LLMError(f"Claude API timeout: {exc}", error_type="ANTHROPIC_TIMEOUT") from exc
        except anthropic.APIConnectionError as exc:
            raise LLMError(
                f"Claude API connection error: {exc}", error_type="ANTHROPIC_UNAVAILABLE"
            ) from exc
        except anthropic.AuthenticationError as exc:
            raise LLMError("Claude API authentication failed", error_type="ANTHROPIC_AUTH") from exc
        except anthropic.RateLimitError as exc:
            raise LLMError(
                "Claude API rate limit (retries exhausted)", error_type="ANTHROPIC_RATE_LIMIT"
            ) from exc
        except anthropic.APIStatusError as exc:
            error_type = (
                "ANTHROPIC_SERVER_ERROR" if exc.status_code >= 500 else "ANTHROPIC_BAD_REQUEST"
            )
            raise LLMError(
                f"Claude API error {exc.status_code}: {exc.message}", error_type=error_type
            ) from exc

        usage = LLMUsage(
            provider=self.provider,
            model=getattr(response, "model", None) or self.model,
            latency_ms=int((time.perf_counter() - start) * 1000),
            input_tokens=getattr(response.usage, "input_tokens", None),
            output_tokens=getattr(response.usage, "output_tokens", None),
        )
        logger.info(
            "claude request_id=%s model=%s in=%s out=%s stop=%s",
            getattr(response, "_request_id", None),
            usage.model,
            usage.input_tokens,
            usage.output_tokens,
            response.stop_reason,
        )
        if response.stop_reason == "refusal":
            category = getattr(getattr(response, "stop_details", None), "category", None)
            raise ModelRefusalError(f"Claude declined the request ({category})", usage=usage)
        if response.stop_reason == "max_tokens":
            raise LLMError("Claude output hit max_tokens", error_type="ANTHROPIC_MAX_TOKENS")

        text = "".join(block.text for block in response.content if block.type == "text").strip()
        return text, usage
