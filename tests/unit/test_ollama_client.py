import json

import httpx
import pytest
import respx

from app.services.llm_types import StructuredOutputError
from app.services.ollama_client import OllamaClient, OllamaError

BASE = "http://ollama.test"


@pytest.fixture
async def client():
    http = httpx.AsyncClient(base_url=BASE, timeout=5)
    yield OllamaClient(
        http, llm_model="gemma", embedding_model="nomic", max_retries=2, backoff_base_sec=0
    )
    await http.aclose()


@respx.mock
async def test_embed(client) -> None:
    route = respx.post(f"{BASE}/api/embed").respond(json={"embeddings": [[0.1, 0.2]]})
    assert await client.embed(["hi"]) == [[0.1, 0.2]]
    assert json.loads(route.calls[0].request.content) == {"model": "nomic", "input": ["hi"]}


@respx.mock
async def test_generate_returns_usage(client) -> None:
    respx.post(f"{BASE}/api/generate").respond(
        json={"response": " 답변 ", "prompt_eval_count": 12, "eval_count": 3}
    )
    result = await client.generate("q", system="sys")
    assert result.text == "답변"
    assert (result.usage.provider, result.usage.input_tokens, result.usage.output_tokens) == (
        "ollama",
        12,
        3,
    )


@respx.mock
async def test_generate_answer_sends_json_schema_and_parses(client) -> None:
    body = {"answer": "확인 [1]", "cited_context_ids": [1], "insufficient_evidence": False}
    route = respx.post(f"{BASE}/api/generate").respond(json={"response": json.dumps(body)})
    answer, _ = await client.generate_answer("q")
    assert answer.cited_context_ids == [1]
    sent = json.loads(route.calls[0].request.content)
    assert sent["format"]["required"] == ["answer", "cited_context_ids", "insufficient_evidence"]


@respx.mock
async def test_generate_answer_non_json_raises_with_raw_text(client) -> None:
    respx.post(f"{BASE}/api/generate").respond(json={"response": "그냥 텍스트 [2]"})
    with pytest.raises(StructuredOutputError) as err:
        await client.generate_answer("q")
    assert err.value.raw_text == "그냥 텍스트 [2]"


@respx.mock
async def test_retries_transient_errors_then_succeeds(client) -> None:
    route = respx.post(f"{BASE}/api/embed")
    route.side_effect = [
        httpx.Response(503),
        httpx.ConnectError("refused"),
        httpx.Response(200, json={"embeddings": [[1.0]]}),
    ]
    assert await client.embed(["x"]) == [[1.0]]
    assert route.call_count == 3


@respx.mock
async def test_gives_up_after_max_retries(client) -> None:
    route = respx.post(f"{BASE}/api/embed").mock(side_effect=httpx.ReadTimeout("slow"))
    with pytest.raises(OllamaError) as err:
        await client.embed(["x"])
    assert err.value.error_type == "OLLAMA_TIMEOUT"
    assert route.call_count == 3  # 1 + 2 retries


@respx.mock
async def test_client_errors_are_not_retried(client) -> None:
    route = respx.post(f"{BASE}/api/embed").respond(404, text="model not found")
    with pytest.raises(OllamaError) as err:
        await client.embed(["x"])
    assert err.value.error_type == "OLLAMA_BAD_REQUEST"
    assert route.call_count == 1


@respx.mock
async def test_embed_sends_dimensions_only_when_truncating() -> None:
    route = respx.post(f"{BASE}/api/embed").respond(json={"embeddings": [[1.0, 0.0]]})
    async with httpx.AsyncClient(base_url=BASE, timeout=5) as http:
        full = OllamaClient(http, llm_model="g", embedding_model="eg2")
        truncated = OllamaClient(
            http, llm_model="g", embedding_model="eg2", embedding_truncate_dim=2
        )
        await full.embed(["a"])
        await truncated.embed(["a"])
    assert "dimensions" not in json.loads(route.calls[0].request.content)
    assert json.loads(route.calls[1].request.content) == {
        "model": "eg2",
        "input": ["a"],
        "dimensions": 2,
    }


@respx.mock
async def test_generate_does_not_think_unless_asked(client) -> None:
    route = respx.post(f"{BASE}/api/generate").respond(json={"response": "ok"})
    await client.generate("q")
    async with httpx.AsyncClient(base_url=BASE, timeout=5) as http:
        thinking = OllamaClient(http, llm_model="g", embedding_model="e", think=True)
        await thinking.generate("q")
    assert json.loads(route.calls[0].request.content)["think"] is False
    assert json.loads(route.calls[1].request.content)["think"] is True
