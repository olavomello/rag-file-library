"""Ollama-backed embedding provider (local inference, no external APIs)."""

from __future__ import annotations

import httpx

from private_rag.application.exceptions import EmbeddingError


class OllamaEmbeddingProvider:
    """Generates embeddings via a local Ollama instance's ``/api/embed`` endpoint.

    An ``httpx.Client`` may be injected for testing; otherwise one is created per
    request. All failures (connection, HTTP, malformed response, inconsistent
    dimensions) are surfaced as :class:`EmbeddingError`.
    """

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float = 120.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout_seconds
        self._client = client

    @property
    def model(self) -> str:
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._embed(texts)
        if len(vectors) != len(texts):
            raise EmbeddingError(
                f"Expected {len(texts)} embeddings, received {len(vectors)}"
            )
        self._validate_dimensions(vectors)
        return vectors

    def embed_query(self, text: str) -> list[float]:
        vectors = self._embed([text])
        if len(vectors) != 1:
            raise EmbeddingError("Expected a single embedding for the query")
        self._validate_dimensions(vectors)
        return vectors[0]

    def _embed(self, inputs: list[str]) -> list[list[float]]:
        url = f"{self._base_url}/api/embed"
        payload = {"model": self._model, "input": inputs}
        try:
            if self._client is not None:
                response = self._client.post(url, json=payload)
            else:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.post(url, json=payload)
        except httpx.HTTPError as exc:
            raise EmbeddingError(
                f"Ollama embedding request failed: {exc.__class__.__name__}"
            ) from exc

        if response.status_code != httpx.codes.OK:
            raise EmbeddingError(f"Ollama returned HTTP {response.status_code}")

        body = response.json()
        embeddings = body.get("embeddings")
        if not isinstance(embeddings, list) or not embeddings:
            raise EmbeddingError("Ollama response did not contain embeddings")

        return [[float(value) for value in vector] for vector in embeddings]

    @staticmethod
    def _validate_dimensions(vectors: list[list[float]]) -> None:
        dimensions = {len(vector) for vector in vectors}
        if len(dimensions) != 1 or 0 in dimensions:
            raise EmbeddingError("Embeddings have inconsistent or empty dimensions")
