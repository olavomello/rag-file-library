"""DTO for the result of updating settings."""

from __future__ import annotations

from dataclasses import dataclass

from private_rag.settings import Settings


@dataclass(slots=True)
class UpdateSettingsResult:
    """Outcome of a settings update: the new effective settings and side-effects."""

    settings: Settings
    requires_restart: bool
    requires_reindex: bool
    message: str
