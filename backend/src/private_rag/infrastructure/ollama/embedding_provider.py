"""Ollama-backed embedding provider (local inference, no external APIs)."""

from __future__ import annotations

import httpx

from private_rag.application.exceptions import EmbeddingError

# Embed at most this many texts per request by default. Long documents produce
# many chunks; sending them all in one request can exceed the read timeout
# (especially on CPU), so they are split into bounded batches.
DEFAULT_BATCH_SIZE = 16
# Retry a timed-out batch this many times. The first embedding call can time out
# while Ollama loads the model into memory (cold start); a retry then succeeds.
DEFAULT_MAX_ATTEMPTS = 3


class OllamaEmbeddingProvider:
    """Generates embeddings via a local Ollama instance's ``/api/embed`` endpoint.

    Texts are embedded in bounded batches so a long document does not time out,
    and a timed-out batch is retried (handling the model cold-start). An
    ``httpx.Client`` may be injected for testing; otherwise one is created per
    request. All failures (connection, HTTP, malformed response, inconsistent
    dimensions) are surfaced as :class:`EmbeddingError`.
    """

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float = 120.0,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout_seconds
        self._batch_size = max(1, batch_size)
        self._max_attempts = max(1, max_attempts)
        self._client = client

    @property
    def model(self) -> str:
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            batch_vectors = self._embed(batch)
            if len(batch_vectors) != len(batch):
                raise EmbeddingError(
                    f"Expected {len(batch)} embeddings, received {len(batch_vectors)}"
                )
            vectors.extend(batch_vectors)

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
        payload: dict[str, object] = {"model": self._model, "input": inputs}
        response = self._post_with_retry(url, payload)

        if response.status_code != httpx.codes.OK:
            raise EmbeddingError(f"Ollama returned HTTP {response.status_code}")

        body = response.json()
        embeddings = body.get("embeddings")
        if not isinstance(embeddings, list) or not embeddings:
            raise EmbeddingError("Ollama response did not contain embeddings")

        return [[float(value) for value in vector] for vector in embeddings]

    def _post_with_retry(self, url: str, payload: dict[str, object]) -> httpx.Response:
        for attempt in range(1, self._max_attempts + 1):
            try:
                return self._post(url, payload)
            except httpx.TimeoutException as exc:
                # Transient: retry until attempts are exhausted, then surface it.
                if attempt >= self._max_attempts:
                    raise EmbeddingError(
                        f"Ollama embedding request failed: {exc.__class__.__name__}"
                    ) from exc
            except httpx.HTTPError as exc:
                raise EmbeddingError(
                    f"Ollama embedding request failed: {exc.__class__.__name__}"
                ) from exc
        raise EmbeddingError("Ollama embedding request failed")  # unreachable

    def _post(self, url: str, payload: dict[str, object]) -> httpx.Response:
        if self._client is not None:
            return self._client.post(url, json=payload)
        with httpx.Client(timeout=self._timeout) as client:
            return client.post(url, json=payload)

    @staticmethod
    def _validate_dimensions(vectors: list[list[float]]) -> None:
        dimensions = {len(vector) for vector in vectors}
        if len(dimensions) != 1 or 0 in dimensions:
            raise EmbeddingError("Embeddings have inconsistent or empty dimensions")
