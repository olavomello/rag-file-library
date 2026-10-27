"""Integration tests for the dashboard stats and settings endpoints."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from private_rag.main import create_app
from private_rag.settings import Settings


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(
        _env_file=None,
        upload_dir=str(tmp_path / "uploads"),
        jobs_dir=str(tmp_path / "jobs"),
        chroma_path=str(tmp_path / "chroma"),
        temp_dir=str(tmp_path / "temp"),
        config_dir=str(tmp_path / "config"),
    )
    with TestClient(create_app(settings=settings)) as test_client:
        yield test_client


def test_dashboard_stats_on_empty_system(client: TestClient) -> None:
    body = client.get("/api/v1/dashboard/stats").json()
    assert body["total_documents"] == 0
    assert body["total_chunks"] == 0
    assert body["active_jobs"] == 0
    assert body["indexed"] == 0
    assert body["generation_model"] == "qwen3:0.6b"
    assert body["embedding_model"] == "embeddinggemma"


def test_settings_endpoint_exposes_config_without_paths(client: TestClient) -> None:
    response = client.get("/api/v1/settings")
    assert response.status_code == 200
    body = response.json()
    assert body["chunk_size"] == 500
    assert body["chunk_overlap"] == 75
    assert body["search_top_k"] == 5
    assert body["generation_model"] == "qwen3:0.6b"
    # No internal filesystem paths leaked (field names like max_upload_size_mb are fine).
    serialized = str(body)
    for path_fragment in ("data/", "./data", "\\data", "/uploads", "/chroma", "jobs_dir"):
        assert path_fragment not in serialized
    assert "stored_name" not in serialized
