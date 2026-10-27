"""Use case: apply, validate, and persist settings overrides."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from private_rag.application.dto.settings import UpdateSettingsResult
from private_rag.application.exceptions import InvalidSettingsError
from private_rag.application.ports.settings_overrides import SettingsOverridesStore
from private_rag.application.services.settings_overrides import (
    OVERRIDABLE_FIELDS,
    apply_overrides,
    filter_overridable,
)
from private_rag.settings import Settings


class UpdateSettingsUseCase:
    """Validates a settings patch, persists it, and reports required follow-ups.

    Overrides are applied on the next application start; this use case does not
    mutate the running process. Changing the embedding model additionally requires
    re-indexing so vectors from different models are never mixed.
    """

    def __init__(self, *, store: SettingsOverridesStore, settings: Settings) -> None:
        self._store = store
        self._settings = settings

    def execute(self, patch: Mapping[str, Any]) -> UpdateSettingsResult:
        cleaned = filter_overridable(patch)

        try:
            effective = apply_overrides(self._settings, cleaned)
        except ValidationError as exc:
            raise InvalidSettingsError(self._format(exc)) from exc

        merged = {**self._store.load(), **cleaned}
        self._store.save(merged)

        changed = [
            key
            for key in cleaned
            if getattr(effective, OVERRIDABLE_FIELDS[key])
            != getattr(self._settings, OVERRIDABLE_FIELDS[key])
        ]
        requires_reindex = (
            "embedding_model" in cleaned
            and cleaned["embedding_model"] != self._settings.ollama_embedding_model
        )

        return UpdateSettingsResult(
            settings=effective,
            requires_restart=bool(changed),
            requires_reindex=requires_reindex,
            message=self._message(changed, requires_reindex),
        )

    @staticmethod
    def _message(changed: list[str], requires_reindex: bool) -> str:
        if not changed:
            return "No changes applied."
        parts = ["Settings saved. Restart the application for changes to take effect."]
        if requires_reindex:
            parts.append(
                "Changing the embedding model requires re-indexing all documents, "
                "so vectors are not mixed across models."
            )
        return " ".join(parts)

    @staticmethod
    def _format(exc: ValidationError) -> str:
        messages = []
        for error in exc.errors():
            location = ".".join(str(part) for part in error.get("loc", ()))
            messages.append(f"{location}: {error.get('msg', 'invalid')}")
        return "Invalid settings: " + "; ".join(messages)
