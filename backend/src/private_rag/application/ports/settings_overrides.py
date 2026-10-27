"""Port for persisting user settings overrides."""

from __future__ import annotations

from typing import Any, Protocol


class SettingsOverridesStore(Protocol):
    """Durably stores a map of public setting keys to override values."""

    def load(self) -> dict[str, Any]: ...

    def save(self, overrides: dict[str, Any]) -> None: ...
