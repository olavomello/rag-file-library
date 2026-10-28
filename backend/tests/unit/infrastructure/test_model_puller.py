"""Unit tests for the Ollama model puller (streaming /api/pull)."""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import pytest

from private_rag.application.exceptions import ModelPullError
from private_rag.infrastructure.ollama.model_puller import OllamaModelPuller

Handler = Callable[[httpx.Request], httpx.Response]


def _puller(handler: Handler) -> OllamaModelPuller:
    return OllamaModelPuller(
        base_url="http://ollama.test",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def _ndjson(*objects: dict[str, object]) -> bytes:
    return "".join(json.dumps(obj) + "\n" for obj in objects).encode()


def test_streams_progress_then_completes() -> None:
    body = _ndjson(
        {"status": "pulling manifest"},
        {"status": "downloading", "completed": 50, "total": 100},
        {"status": "success"},
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    events = list(_puller(handler).stream_pull("qwen3:1.7b"))

    assert [e["status"] for e in events] == ["pulling manifest", "downloading", "success"]
    assert events[1]["completed"] == 50
    assert events[1]["total"] == 100


def test_error_line_raises_model_pull_error() -> None:
    body = _ndjson({"status": "pulling"}, {"error": "model 'nope' not found"})

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    with pytest.raises(ModelPullError):
        list(_puller(handler).stream_pull("nope"))


def test_non_200_raises_model_pull_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, content=b"")

    with pytest.raises(ModelPullError):
        list(_puller(handler).stream_pull("x"))
