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
    # True when a changed field can be applied to the running process immediately
    # (the generation model/options), so no restart is needed for it.
    live_reload: bool = False
