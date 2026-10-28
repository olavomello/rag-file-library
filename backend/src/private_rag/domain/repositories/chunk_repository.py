"""Repository contract for chunk vectors and semantic retrieval."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from private_rag.domain.entities.document_chunk import DocumentChunk
from private_rag.domain.entities.search_result import SearchResult


class ChunkVectorRepository(Protocol):
    """Stores chunk embeddings and performs vector similarity search.

    Embeddings are supplied by the caller (the embedding model lives behind a
    separate port), so this repository is independent of any specific model and
    can be tested with deterministic vectors.
    """

    def add_chunks(
        self,
        chunks: Sequence[DocumentChunk],
        embeddings: Sequence[Sequence[float]],
        *,
        embedding_model: str,
    ) -> None:
        """Persist ``chunks`` with their ``embeddings``.

        ``chunks`` and ``embeddings`` must be the same length. ``embedding_model``
        is recorded so incompatible vectors are never mixed across models.
        """
        ...

    def query(
        self,
        embedding: Sequence[float],
        *,
        top_k: int,
        document_ids: Sequence[str] | None = None,
        contains: Sequence[str] | None = None,
    ) -> list[SearchResult]:
        """Return the ``top_k`` closest chunks, optionally scoped to documents.

        When ``contains`` is given, results are additionally restricted to chunks
        whose text literally contains at least one of those terms (lexical filter).
        """
        ...

    def delete_by_document(self, document_id: str) -> None:
        """Remove every chunk belonging to ``document_id``."""
        ...

    def count(self, *, document_id: str | None = None) -> int:
        """Count stored chunks, optionally for a single document."""
        ...
