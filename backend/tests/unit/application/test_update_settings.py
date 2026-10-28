"""Unit tests for settings overrides application and the update use case."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from private_rag.application.exceptions import InvalidSettingsError
from private_rag.application.services.settings_overrides import apply_overrides
from private_rag.application.use_cases.settings.update_settings import (
    UpdateSettingsUseCase,
)
from private_rag.settings import Settings


class FakeStore:
    def __init__(self, initial: dict[str, Any] | None = None) -> None:
        self.data: dict[str, Any] = dict(initial or {})
        self.saved = False

    def load(self) -> dict[str, Any]:
        return dict(self.data)

    def save(self, overrides: dict[str, Any]) -> None:
        self.data = dict(overrides)
        self.saved = True


def _base() -> Settings:
    return Settings(_env_file=None)


class TestApplyOverrides:
    def test_maps_public_keys_to_fields(self) -> None:
        result = apply_overrides(_base(), {"generation_model": "qwen3:1.7b", "chunk_size": 800})
        assert result.ollama_generation_model == "qwen3:1.7b"
        assert result.chunk_size == 800

    def test_invalid_combination_raises(self) -> None:
        with pytest.raises(ValidationError):
            apply_overrides(_base(), {"chunk_overlap": 600})  # base chunk_size is 500

    def test_round_trips_ocr_enabled(self) -> None:
        assert apply_overrides(_base(), {"ocr_enabled": True}).ocr_enabled is True
        assert apply_overrides(_base(), {"ocr_enabled": False}).ocr_enabled is False


class TestOcrEnabledUpdate:
    def test_toggling_ocr_requires_restart(self) -> None:
        # OCR is on by default, so disabling it is the change that needs a restart.
        store = FakeStore()
        result = UpdateSettingsUseCase(store=store, settings=_base()).execute(
            {"ocr_enabled": False}
        )
        assert result.settings.ocr_enabled is False
        assert result.requires_restart is True
        assert store.data == {"ocr_enabled": False}


class TestUpdateSettingsUseCase:
    def test_change_requires_restart_and_persists(self) -> None:
        store = FakeStore()
        result = UpdateSettingsUseCase(store=store, settings=_base()).execute({"chunk_size": 900})

        assert result.settings.chunk_size == 900
        assert result.requires_restart is True
        assert result.requires_reindex is False
        assert store.data == {"chunk_size": 900}
        assert "Restart" in result.message

    def test_embedding_model_change_requires_reindex(self) -> None:
        store = FakeStore()
        result = UpdateSettingsUseCase(store=store, settings=_base()).execute(
            {"embedding_model": "nomic-embed-text"}
        )
        assert result.requires_reindex is True
        assert "re-indexing" in result.message

    def test_invalid_patch_is_rejected_and_not_saved(self) -> None:
        store = FakeStore()
        with pytest.raises(InvalidSettingsError):
            UpdateSettingsUseCase(store=store, settings=_base()).execute({"chunk_overlap": 600})
        assert store.saved is False

    def test_no_recognised_changes_is_noop(self) -> None:
        store = FakeStore()
        result = UpdateSettingsUseCase(store=store, settings=_base()).execute({"unknown": 1})
        assert result.requires_restart is False
        assert result.message == "No changes applied."

    def test_merges_with_existing_overrides(self) -> None:
        store = FakeStore({"generation_model": "qwen3:1.7b"})
        UpdateSettingsUseCase(store=store, settings=_base()).execute({"chunk_size": 700})
        assert store.data == {"generation_model": "qwen3:1.7b", "chunk_size": 700}
