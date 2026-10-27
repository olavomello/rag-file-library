"""Reads the list of models available from a local Ollama instance."""

from __future__ import annotations

import httpx


class OllamaModelCatalog:
    """Fetches installed model names from Ollama's ``/api/tags`` endpoint.

    Never raises for an unreachable Ollama; returns ``(reachable, names)``.
    """

    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float = 5.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._client = client

    def fetch(self) -> tuple[bool, list[str]]:
        url = f"{self._base_url}/api/tags"
        try:
            if self._client is not None:
                response = self._client.get(url)
            else:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.get(url)
        except httpx.HTTPError:
            return (False, [])

        if response.status_code != httpx.codes.OK:
            return (False, [])

        try:
            models = response.json().get("models", [])
            names = [str(model.get("name", "")) for model in models]
        except (ValueError, AttributeError):
            return (True, [])

        return (True, [name for name in names if name])
