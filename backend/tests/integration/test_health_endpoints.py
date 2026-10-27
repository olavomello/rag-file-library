"""Integration tests for the health API endpoints."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from private_rag.application.dto.health import ComponentHealth, HealthStatus
from private_rag.container.container import Container
from private_rag.main import create_app
from private_rag.settings import Settings


class _FakeProbe:
    """Deterministic health probe used to exercise the endpoints."""

    def __init__(self, name: str, status: HealthStatus) -> None:
        self._name = name
        self._status = status

    @property
    def name(self) -> str:
        return self._name

    async def check(self) -> ComponentHealth:
        return ComponentHealth(component=self._name, status=self._status, detail="fake")


def _build_client(
    tmp_path: Path,
    ollama_status: HealthStatus,
    chroma_status: HealthStatus,
) -> TestClient:
    settings = Settings(_env_file=None, chroma_path=str(tmp_path / "chroma"))
    container = Container(settings)
    # Prime the cached_property slots with deterministic fakes.
    container.__dict__["ollama_health_probe"] = _FakeProbe("ollama", ollama_status)
    container.__dict__["chroma_health_probe"] = _FakeProbe("chroma", chroma_status)
    app = create_app(settings=settings, container=container)
    return TestClient(app)


@pytest.fixture
def healthy_client(tmp_path: Path) -> Iterator[TestClient]:
    with _build_client(tmp_path, HealthStatus.OK, HealthStatus.OK) as client:
        yield client


def test_liveness_returns_ok(healthy_client: TestClient) -> None:
    response = healthy_client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app_name"] == "Private RAG"
    assert body["version"] == "0.1.0"


def test_ollama_health_ok(healthy_client: TestClient) -> None:
    response = healthy_client.get("/api/v1/health/ollama")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["component"] == "ollama"


def test_chroma_health_ok(healthy_client: TestClient) -> None:
    response = healthy_client.get("/api/v1/health/chroma")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ollama_health_returns_503_when_unavailable(tmp_path: Path) -> None:
    with _build_client(tmp_path, HealthStatus.UNAVAILABLE, HealthStatus.OK) as client:
        response = client.get("/api/v1/health/ollama")

    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"


def test_openapi_schema_is_served(healthy_client: TestClient) -> None:
    response = healthy_client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/health" in response.json()["paths"]
