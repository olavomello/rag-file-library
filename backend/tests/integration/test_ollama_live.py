"""Live verification against a running Ollama (skipped when unavailable).

These run only when a local Ollama is reachable with the required models, so CI
and machines without Ollama skip them. They verify the real embedding and
generation adapters end to end — the integrations the other suites fake.
"""

from __future__ import annotations

import httpx
import pytest

from private_rag.infrastructure.ollama.embedding_provider import OllamaEmbeddingProvider
from private_rag.infrastructure.ollama.generation_provider import (
    OllamaGenerationProvider,
)

BASE_URL = "http://127.0.0.1:11434"
EMBED_MODEL = "embeddinggemma"
GEN_MODEL = "qwen3:0.6b"

pytestmark = pytest.mark.requires_ollama


def _installed_models() -> list[str] | None:
    try:
        response = httpx.get(f"{BASE_URL}/api/tags", timeout=3.0)
    except httpx.HTTPError:
        return None
    if response.status_code != httpx.codes.OK:
        return None
    return [m.get("name", "") for m in response.json().get("models", [])]


def _has(models: list[str], model: str) -> bool:
    base = model.split(":")[0]
    return any(name == model or name.split(":")[0] == base for name in models)


def test_real_embeddings() -> None:
    models = _installed_models()
    if models is None:
        pytest.skip("Ollama is not reachable")
    if not _has(models, EMBED_MODEL):
        pytest.skip(f"{EMBED_MODEL} is not installed")

    provider = OllamaEmbeddingProvider(base_url=BASE_URL, model=EMBED_MODEL)
    query = provider.embed_query("vacation policy")
    docs = provider.embed_documents(["first chunk of text", "second chunk of text"])

    assert len(query) > 0
    assert len(docs) == 2
    assert len(docs[0]) == len(docs[1]) == len(query)


def test_real_generation() -> None:
    models = _installed_models()
    if models is None:
        pytest.skip("Ollama is not reachable")
    if not _has(models, GEN_MODEL):
        pytest.skip(f"{GEN_MODEL} is not installed")

    # qwen3 is a "thinking" model, so a realistic output budget is needed for a
    # visible answer (a tiny num_predict is consumed by reasoning tokens).
    provider = OllamaGenerationProvider(
        base_url=BASE_URL, model=GEN_MODEL, max_output_tokens=512, timeout_seconds=180.0
    )
    answer = provider.generate("What is 2 + 2? Answer briefly.")
    assert isinstance(answer, str)
    assert answer.strip() != ""
