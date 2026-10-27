"""Integration tests for PATCH /settings (override persistence + restart apply)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from private_rag.application.services.settings_overrides import apply_overrides
from private_rag.infrastructure.filesystem.json_settings_overrides import (
    JsonSettingsOverridesStore,
)
from private_rag.main import create_app
from private_rag.settings import Settings

SETTINGS = "/api/v1/settings"


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        upload_dir=str(tmp_path / "uploads"),
        jobs_dir=str(tmp_path / "jobs"),
        chroma_path=str(tmp_path / "chroma"),
        temp_dir=str(tmp_path / "temp"),
        config_dir=str(tmp_path / "config"),
    )


def test_patch_persists_override_and_flags_restart(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    with TestClient(create_app(settings=settings)) as client:
        response = client.patch(SETTINGS, json={"chunk_size": 900})
        assert response.status_code == 200
        body = response.json()
        assert body["settings"]["chunk_size"] == 900
        assert body["requires_restart"] is True
        assert body["requires_reindex"] is False
        assert "Restart" in body["message"]

        # GET still reflects the running config until a restart applies the override.
        assert client.get(SETTINGS).json()["chunk_size"] == 500

    # The override is persisted to the config directory.
    assert JsonSettingsOverridesStore(settings.config_dir).load() == {"chunk_size": 900}


def test_patch_embedding_model_requires_reindex(tmp_path: Path) -> None:
    with TestClient(create_app(settings=_settings(tmp_path))) as client:
        body = client.patch(SETTINGS, json={"embedding_model": "nomic-embed-text"}).json()
        assert body["requires_reindex"] is True
        assert "re-indexing" in body["message"]


def test_patch_invalid_combination_is_rejected(tmp_path: Path) -> None:
    with TestClient(create_app(settings=_settings(tmp_path))) as client:
        # overlap >= size within a single request
        response = client.patch(SETTINGS, json={"chunk_size": 10, "chunk_overlap": 20})
        assert response.status_code == 400


def test_patch_schema_validation_rejects_out_of_range(tmp_path: Path) -> None:
    with TestClient(create_app(settings=_settings(tmp_path))) as client:
        assert client.patch(SETTINGS, json={"temperature": 9}).status_code == 422


def test_override_is_applied_on_restart(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    with TestClient(create_app(settings=settings)) as client:
        client.patch(SETTINGS, json={"chunk_size": 777, "generation_model": "qwen3:1.7b"})

    # Simulate a restart: reload base settings and apply the persisted overrides.
    overrides = JsonSettingsOverridesStore(settings.config_dir).load()
    effective = apply_overrides(settings, overrides)
    assert effective.chunk_size == 777
    assert effective.ollama_generation_model == "qwen3:1.7b"
