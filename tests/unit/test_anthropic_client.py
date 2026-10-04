"""The Anthropic SDK client is mocked: these tests never call the real Claude API."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import anthropic
import httpx2
import pytest

from app.services.anthropic_client import AnthropicGenerationClient
from app.services.llm_types import (
    GROUNDED_ANSWER_SCHEMA,
    LLMError,
    ModelRefusalError,
    StructuredOutputError,
)


def fake_response(text: str, *, stop_reason: str = "end_turn", **kw) -> SimpleNamespace:
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        stop_reason=stop_reason,
        stop_details=kw.get("stop_details"),
        model=kw.get("model", "claude-opus-5-5"),
        usage=SimpleNamespace(input_tokens=120, output_tokens=30),
        _request_id="req_test",
    )


def make_client(
    response=None, side_effect=None, **kw
) -> tuple[AnthropicGenerationClient, AsyncMock]:
    create = AsyncMock(return_value=response, side_effect=side_effect)
    sdk = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create)))
    return AnthropicGenerationClient(sdk, model="claude-opus-5-5", **kw), create  # type: ignore[arg-type]


async def test_generate_answer_uses_json_schema_output_and_reports_usage() -> None:
    body = {"answer": "확인 [1]", "cited_context_ids": [1], "insufficient_evidence": False}
    client, create = make_client(fake_response(json.dumps(body, ensure_ascii=False)))
    answer, usage = await client.generate_answer("prompt", system="sys")

    assert answer.cited_context_ids == [1]
    assert (usage.provider, usage.model, usage.input_tokens, usage.output_tokens) == (
        "anthropic",
        "claude-opus-5-5",
        120,
        30,
    )
    kwargs = create.call_args.kwargs
    assert kwargs["model"] == "claude-opus-5-5"
    assert kwargs["system"] == "sys"
    assert kwargs["output_config"] == {
        "effort": "medium",
        "format": {"type": "json_schema", "schema": GROUNDED_ANSWER_SCHEMA},
    }
    assert kwargs["fallbacks"] == "default"
    assert kwargs["betas"] == ["server-side-fallback-2026-07-01"]


async def test_plain_generate_has_no_schema_and_fallback_can_be_disabled() -> None:
    client, create = make_client(fake_response("설명"), refusal_fallback=False)
    result = await client.generate("p")
    assert result.text == "설명"
    kwargs = create.call_args.kwargs
    assert "format" not in kwargs["output_config"]
    assert "fallbacks" not in kwargs and "betas" not in kwargs


async def test_refusal_stop_reason_raises_model_refusal() -> None:
    details = SimpleNamespace(category="bio", explanation="...")
    client, _ = make_client(fake_response("", stop_reason="refusal", stop_details=details))
    with pytest.raises(ModelRefusalError) as err:
        await client.generate_answer("p")
    assert err.value.usage.output_tokens == 30


async def test_max_tokens_and_bad_json() -> None:
    client, _ = make_client(fake_response("{", stop_reason="max_tokens"))
    with pytest.raises(LLMError) as err:
        await client.generate_answer("p")
    assert err.value.error_type == "ANTHROPIC_MAX_TOKENS"

    client, _ = make_client(fake_response("not json"))
    with pytest.raises(StructuredOutputError):
        await client.generate_answer("p")


_REQ = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


@pytest.mark.parametrize(
    ("exc", "error_type"),
    [
        (anthropic.APITimeoutError(request=_REQ), "ANTHROPIC_TIMEOUT"),
        (anthropic.APIConnectionError(request=_REQ), "ANTHROPIC_UNAVAILABLE"),
        (
            anthropic.RateLimitError(
                "rate", response=httpx2.Response(429, request=_REQ), body=None
            ),
            "ANTHROPIC_RATE_LIMIT",
        ),
        (
            anthropic.InternalServerError(
                "boom", response=httpx2.Response(529, request=_REQ), body=None
            ),
            "ANTHROPIC_SERVER_ERROR",
        ),
        (
            anthropic.BadRequestError(
                "bad", response=httpx2.Response(400, request=_REQ), body=None
            ),
            "ANTHROPIC_BAD_REQUEST",
        ),
    ],
)
async def test_sdk_errors_map_to_llm_errors(exc: Exception, error_type: str) -> None:
    client, _ = make_client(side_effect=exc)
    with pytest.raises(LLMError) as err:
        await client.generate_answer("p")
    assert err.value.error_type == error_type


def test_create_configures_sdk_timeout_and_retries() -> None:
    client = AnthropicGenerationClient.create(
        api_key="sk-ant-test",
        model="claude-opus-5-5",
        timeout_sec=12,
        max_retries=4,
        max_tokens=16000,
        effort="low",
        refusal_fallback=True,
    )
    sdk = client._client
    assert sdk.max_retries == 4
    assert sdk.timeout == 12
