"""Health probe for a local Ollama instance."""

from __future__ import annotations

import httpx

from private_rag.application.dto.health import ComponentHealth, HealthStatus


class OllamaHealthProbe:
    """Pings the Ollama HTTP API to determine availability.

    Availability is not required for the application to run; when Ollama is
    unreachable the probe reports ``UNAVAILABLE`` rather than raising.
    """

    name = "ollama"

    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def check(self) -> ComponentHealth:
        url = f"{self._base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
        except httpx.HTTPError as exc:
            return ComponentHealth(
                component=self.name,
                status=HealthStatus.UNAVAILABLE,
                detail=f"Ollama is not reachable at {self._base_url}: {exc.__class__.__name__}",
            )

        if response.status_code != httpx.codes.OK:
            return ComponentHealth(
                component=self.name,
                status=HealthStatus.ERROR,
                detail=f"Ollama returned HTTP {response.status_code}",
            )

        try:
            payload = response.json()
            models = [model.get("name", "") for model in payload.get("models", [])]
        except (ValueError, AttributeError):
            models = []

        return ComponentHealth(
            component=self.name,
            status=HealthStatus.OK,
            detail=f"{len(models)} model(s) available",
            metadata={"base_url": self._base_url, "models": ", ".join(models)},
        )
