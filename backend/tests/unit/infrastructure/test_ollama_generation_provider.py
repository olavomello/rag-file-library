"""Unit tests for the Ollama generation provider (mocked transport, no network)."""

from __future__ import annotations

import httpx
import pytest

from private_rag.application.exceptions import GenerationError
from private_rag.infrastructure.ollama.generation_provider import (
    OllamaGenerationProvider,
)


def _provider(handler) -> OllamaGenerationProvider:  # type: ignore[no-untyped-def]
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OllamaGenerationProvider(
        base_url="http://ollama.test", model="qwen3:0.6b", client=client
    )


def test_generate_returns_text() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": "Grounded answer.", "done": True})

    assert _provider(handler).generate("prompt") == "Grounded answer."


def test_generate_http_error_raises() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    with pytest.raises(GenerationError):
        _provider(handler).generate("prompt")


def test_generate_connection_error_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(GenerationError):
        _provider(handler).generate("prompt")


def test_generate_missing_response_field_raises() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"done": True})

    with pytest.raises(GenerationError):
        _provider(handler).generate("prompt")


def test_stream_generate_yields_chunks_until_done() -> None:
    body = (
        b'{"response":"Hello","done":false}\n'
        b'{"response":" world","done":false}\n'
        b'{"response":"!","done":true}\n'
    )

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    chunks = list(_provider(handler).stream_generate("prompt"))
    assert chunks == ["Hello", " world", "!"]
    assert "".join(chunks) == "Hello world!"


def test_model_property() -> None:
    assert _provider(lambda _: httpx.Response(200, json={"response": "x"})).model == "qwen3:0.6b"
