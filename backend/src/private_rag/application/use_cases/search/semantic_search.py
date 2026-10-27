"""Use case: semantic search over indexed documents (no LLM required)."""

from __future__ import annotations

from collections.abc import Sequence

from private_rag.application.exceptions import InvalidSearchQueryError
from private_rag.application.ports.embeddings import EmbeddingProvider
from private_rag.domain.entities.search_result import SearchResult
from private_rag.domain.repositories.chunk_repository import ChunkVectorRepository
from private_rag.domain.repositories.document_repository import DocumentRepository
from private_rag.domain.value_objects.document_status import DocumentStatus


class SemanticSearchUseCase:
    """Embeds a query and retrieves the closest chunks.

    Results are restricted to documents that are fully ``INDEXED``, so a document
    that is still processing or failed never surfaces partial content. The LLM is
    not involved; only the embedding model and vector store are used.
    """

    def __init__(
        self,
        *,
        embeddings: EmbeddingProvider,
        chunks: ChunkVectorRepository,
        documents: DocumentRepository,
        default_top_k: int,
    ) -> None:
        self._embeddings = embeddings
        self._chunks = chunks
        self._documents = documents
        self._default_top_k = default_top_k

    def execute(
        self,
        query: str,
        *,
        top_k: int | None = None,
        document_ids: Sequence[str] | None = None,
    ) -> list[SearchResult]:
        cleaned = query.strip()
        if not cleaned:
            raise InvalidSearchQueryError("Search query must not be empty")

        indexed_ids = [
            document.id
            for document in self._documents.list(status=DocumentStatus.INDEXED)
        ]
        if document_ids is not None:
            requested = set(document_ids)
            indexed_ids = [doc_id for doc_id in indexed_ids if doc_id in requested]

        if not indexed_ids:
            return []

        embedding = self._embeddings.embed_query(cleaned)
        limit = top_k if top_k is not None else self._default_top_k
        return self._chunks.query(
            embedding, top_k=max(1, limit), document_ids=indexed_ids
        )
