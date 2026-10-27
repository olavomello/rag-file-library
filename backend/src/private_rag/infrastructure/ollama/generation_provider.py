"""Ollama-backed text generation (local inference, no external APIs)."""

from __future__ import annotations

import json
from collections.abc import Iterator

import httpx

from private_rag.application.exceptions import GenerationError


class OllamaGenerationProvider:
    """Generates text via a local Ollama instance's ``/api/generate`` endpoint.

    An ``httpx.Client`` may be injected for testing. All failures surface as
    :class:`GenerationError`.
    """

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        temperature: float = 0.2,
        max_output_tokens: int = 1024,
        context_window: int = 4096,
        timeout_seconds: float = 120.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._context_window = context_window
        self._timeout = timeout_seconds
        self._client = client

    @property
    def model(self) -> str:
        return self._model

    def _payload(self, prompt: str, *, stream: bool) -> dict[str, object]:
        return {
            "model": self._model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": self._temperature,
                "num_predict": self._max_output_tokens,
                "num_ctx": self._context_window,
            },
        }

    @property
    def _url(self) -> str:
        return f"{self._base_url}/api/generate"

    def generate(self, prompt: str) -> str:
        payload = self._payload(prompt, stream=False)
        try:
            if self._client is not None:
                response = self._client.post(self._url, json=payload)
            else:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.post(self._url, json=payload)
        except httpx.HTTPError as exc:
            raise GenerationError(
                f"Ollama generation request failed: {exc.__class__.__name__}"
            ) from exc

        if response.status_code != httpx.codes.OK:
            raise GenerationError(f"Ollama returned HTTP {response.status_code}")

        text = response.json().get("response")
        if not isinstance(text, str):
            raise GenerationError("Ollama response did not contain text")
        return text

    def stream_generate(self, prompt: str) -> Iterator[str]:
        payload = self._payload(prompt, stream=True)
        client = self._client or httpx.Client(timeout=self._timeout)
        owns_client = self._client is None
        try:
            with client.stream("POST", self._url, json=payload) as response:
                if response.status_code != httpx.codes.OK:
                    raise GenerationError(f"Ollama returned HTTP {response.status_code}")
                for line in response.iter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    chunk = data.get("response")
                    if chunk:
                        yield chunk
                    if data.get("done"):
                        break
        except httpx.HTTPError as exc:
            raise GenerationError(
                f"Ollama streaming request failed: {exc.__class__.__name__}"
            ) from exc
        finally:
            if owns_client:
                client.close()
