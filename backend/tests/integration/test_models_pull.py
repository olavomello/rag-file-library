"""Integration tests for POST /models/pull (streaming, with a fake puller)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from private_rag.application.exceptions import ModelPullError
from private_rag.container.container import Container
from private_rag.main import create_app
from private_rag.settings import Settings

PULL = "/api/v1/models/pull"


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        upload_dir=str(tmp_path / "uploads"),
        jobs_dir=str(tmp_path / "jobs"),
        chroma_path=str(tmp_path / "chroma"),
        temp_dir=str(tmp_path / "temp"),
        config_dir=str(tmp_path / "config"),
    )


class FakePuller:
    def stream_pull(self, model: str) -> Iterator[dict[str, object]]:
        yield {"status": "downloading", "completed": 1, "total": 2}
        yield {"status": "success", "completed": 2, "total": 2}


class FailingPuller:
    def stream_pull(self, model: str) -> Iterator[dict[str, object]]:
        yield {"status": "pulling", "completed": None, "total": None}
        raise ModelPullError("model not found")


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = _settings(tmp_path)
    container = Container(settings)
    container.__dict__["model_puller"] = FakePuller()
    with TestClient(create_app(settings=settings, container=container)) as test_client:
        yield test_client


def test_pull_streams_progress_then_done(client: TestClient) -> None:
    response = client.post(PULL, json={"model": "qwen3:1.7b"})
    assert response.status_code == 200

    events = [json.loads(line) for line in response.text.splitlines() if line.strip()]
    assert events[0] == {"type": "progress", "status": "downloading", "completed": 1, "total": 2}
    assert events[-1] == {"type": "done"}


def test_pull_reports_error_event(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    container = Container(settings)
    container.__dict__["model_puller"] = FailingPuller()
    with TestClient(create_app(settings=settings, container=container)) as client:
        events = [
            json.loads(line)
            for line in client.post(PULL, json={"model": "nope"}).text.splitlines()
            if line.strip()
        ]
    assert events[-1]["type"] == "error"
    assert "not found" in events[-1]["detail"]


def test_pull_rejects_invalid_model_name(client: TestClient) -> None:
    assert client.post(PULL, json={"model": "bad name!"}).status_code == 422
    assert client.post(PULL, json={"model": ""}).status_code == 422
