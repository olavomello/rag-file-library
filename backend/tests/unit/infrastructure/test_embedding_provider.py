"""Unit tests for the Ollama embedding provider (batching + retry)."""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import pytest

from private_rag.application.exceptions import EmbeddingError
from private_rag.infrastructure.ollama.embedding_provider import OllamaEmbeddingProvider

Handler = Callable[[httpx.Request], httpx.Response]


def _provider(handler: Handler, **kwargs: object) -> OllamaEmbeddingProvider:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OllamaEmbeddingProvider(
        base_url="http://ollama.test",
        model="embeddinggemma",
        client=client,
        **kwargs,  # type: ignore[arg-type]
    )


def test_embeds_long_input_in_bounded_batches() -> None:
    sizes: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        inputs = json.loads(request.content)["input"]
        sizes.append(len(inputs))
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2, 0.3] for _ in inputs]})

    provider = _provider(handler, batch_size=2)
    vectors = provider.embed_documents([f"chunk {i}" for i in range(5)])

    assert len(vectors) == 5
    # 5 texts with batch_size 2 -> three requests (no single oversized request).
    assert sizes == [2, 2, 1]


def test_retries_a_timed_out_batch_then_succeeds() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ReadTimeout("model is loading", request=request)
        inputs = json.loads(request.content)["input"]
        return httpx.Response(200, json={"embeddings": [[1.0, 2.0] for _ in inputs]})

    provider = _provider(handler, batch_size=10, max_attempts=3)
    vectors = provider.embed_documents(["a", "b"])

    assert len(vectors) == 2
    assert calls["n"] == 2  # one timeout, then one successful retry


def test_raises_embedding_error_after_exhausting_retries() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("still slow", request=request)

    provider = _provider(handler, max_attempts=2)
    with pytest.raises(EmbeddingError):
        provider.embed_documents(["a"])


def test_empty_input_makes_no_request() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("no request should be made for empty input")

    assert _provider(handler).embed_documents([]) == []
