"""Composition root.

The container wires concrete infrastructure implementations to application ports
using explicit dependency injection (no framework). It is created once per
application instance and stored on ``app.state``.
"""

from __future__ import annotations

from functools import cached_property

from private_rag.application.ports.health import HealthProbe
from private_rag.infrastructure.chroma.health_probe import ChromaHealthProbe
from private_rag.infrastructure.ollama.health_probe import OllamaHealthProbe
from private_rag.settings import Settings


class Container:
    """Builds and holds application-scoped dependencies."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def settings(self) -> Settings:
        return self._settings

    @cached_property
    def ollama_health_probe(self) -> HealthProbe:
        return OllamaHealthProbe(
            base_url=self._settings.ollama_base_url,
            timeout_seconds=min(self._settings.ollama_request_timeout_seconds, 5.0),
        )

    @cached_property
    def chroma_health_probe(self) -> HealthProbe:
        return ChromaHealthProbe(path=self._settings.chroma_path)
