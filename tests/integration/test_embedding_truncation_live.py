"""Live check of Matryoshka truncation against a local Ollama (skipped when it is not there).

`dimensions` is forwarded to /api/embed; Ollama >= 0.40 returns the first N dimensions
L2-normalised. Needs the embeddinggemma-2:270m model that is already on the host.
"""

import math

import httpx
import pytest

from app.services.ollama_client import OllamaClient

BASE = "http://localhost:11434"
MODEL = "embeddinggemma-2:270m"


def _available() -> bool:
    try:
        tags = httpx.get(f"{BASE}/api/tags", timeout=2).json()
    except (httpx.HTTPError, ValueError):
        return False
    return any(m.get("name") == MODEL for m in tags.get("models", []))


pytestmark = pytest.mark.skipif(not _available(), reason=f"{MODEL} not on a local Ollama")


@pytest.mark.parametrize("dim", [512, 256, 128])
async def test_truncated_embedding_has_requested_size_and_unit_norm(dim) -> None:
    async with httpx.AsyncClient(base_url=BASE, timeout=30) as http:
        full = await OllamaClient(http, llm_model="-", embedding_model=MODEL).embed(["임상시험"])
        client = OllamaClient(
            http, llm_model="-", embedding_model=MODEL, embedding_truncate_dim=dim
        )
        (vec,) = await client.embed(["임상시험"])
    assert len(vec) == dim
    assert math.isclose(math.sqrt(sum(x * x for x in vec)), 1.0, abs_tol=1e-4)
    head = full[0][:dim]
    norm = math.sqrt(sum(x * x for x in head))
    assert max(abs(a - b / norm) for a, b in zip(vec, head, strict=True)) < 1e-5
