"""Ownership and provisioning of the single embedded ChromaDB client.

The FastAPI application owns exactly one :class:`PersistentClient` for the process
(ChromaDB's embedded store must not be written by multiple independent processes).
Collections are created without a server-side embedding function: the application
always supplies embeddings explicitly, so no model is ever downloaded implicitly.
"""

from __future__ import annotations

from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings


class ChromaClientProvider:
    """Lazily creates and caches one embedded ChromaDB persistent client."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._client: Any | None = None

    def client(self) -> Any:
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self._path,
                settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
            )
        return self._client

    def get_or_create_collection(self, name: str, *, space: str = "cosine") -> Any:
        return self.client().get_or_create_collection(
            name=name,
            embedding_function=None,
            metadata={"hnsw:space": space},
        )

    def reset(self) -> None:
        """Drop all data (test/maintenance helper)."""
        self.client().reset()
