"""JSON-file implementation of the settings-overrides store (atomic writes)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from private_rag.infrastructure.filesystem.atomic import atomic_write_text

_FILENAME = "overrides.json"


class JsonSettingsOverridesStore:
    """Persists settings overrides as a single JSON file under the config dir."""

    def __init__(self, config_dir: str | Path) -> None:
        self._path = Path(config_dir) / _FILENAME

    def load(self) -> dict[str, Any]:
        if not self._path.is_file():
            return {}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return {}
        return data if isinstance(data, dict) else {}

    def save(self, overrides: dict[str, Any]) -> None:
        atomic_write_text(
            self._path, json.dumps(overrides, indent=2, ensure_ascii=False)
        )
