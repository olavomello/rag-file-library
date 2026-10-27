"""Port for generating embeddings locally."""

from __future__ import annotations

from typing import Protocol


class EmbeddingProvider(Protocol):
    """Generates vector embeddings for documents and queries."""

    @property
    def model(self) -> str:
        """Identifier of the embedding model (recorded with stored vectors)."""
        ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of document texts (same length and order as ``texts``)."""
        ...

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        ...
