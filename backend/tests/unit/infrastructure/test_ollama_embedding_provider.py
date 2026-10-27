"""Unit tests for the Ollama embedding provider (mocked transport, no network)."""

from __future__ import annotations

import json

import httpx
import pytest

from private_rag.application.exceptions import EmbeddingError
from private_rag.infrastructure.ollama.embedding_provider import OllamaEmbeddingProvider


def _provider(handler) -> OllamaEmbeddingProvider:  # type: ignore[no-untyped-def]
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OllamaEmbeddingProvider(
        base_url="http://ollama.test", model="embeddinggemma", client=client
    )


def _ok_handler(request: httpx.Request) -> httpx.Response:
    payload = json.loads(request.content)
    inputs = payload["input"]
    count = len(inputs) if isinstance(inputs, list) else 1
    return httpx.Response(200, json={"embeddings": [[0.1, 0.2, 0.3]] * count})


def test_embed_documents_returns_vectors() -> None:
    provider = _provider(_ok_handler)
    vectors = provider.embed_documents(["a", "b"])
    assert vectors == [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]


def test_embed_documents_empty_short_circuits() -> None:
    def fail(_: httpx.Request) -> httpx.Response:  # pragma: no cover - must not be called
        raise AssertionError("should not call Ollama for empty input")

    assert _provider(fail).embed_documents([]) == []


def test_embed_query_returns_single_vector() -> None:
    assert _provider(_ok_handler).embed_query("hello") == [0.1, 0.2, 0.3]


def test_connection_error_becomes_embedding_error() -> None:
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(EmbeddingError):
        _provider(boom).embed_query("x")


def test_http_500_becomes_embedding_error() -> None:
    def error(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    with pytest.raises(EmbeddingError):
        _provider(error).embed_query("x")


def test_missing_embeddings_field_raises() -> None:
    def empty(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    with pytest.raises(EmbeddingError):
        _provider(empty).embed_query("x")


def test_inconsistent_dimensions_raise() -> None:
    def ragged(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2], [0.1]]})

    with pytest.raises(EmbeddingError):
        _provider(ragged).embed_documents(["a", "b"])


def test_model_property() -> None:
    assert _provider(_ok_handler).model == "embeddinggemma"
