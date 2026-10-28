"""Use case: semantic search over indexed documents (no LLM required)."""

from __future__ import annotations

from collections.abc import Sequence
from itertools import zip_longest

from private_rag.application.exceptions import InvalidSearchQueryError
from private_rag.application.ports.embeddings import EmbeddingProvider
from private_rag.application.services.keyword_extraction import (
    contains_variants,
    extract_keywords,
)
from private_rag.domain.entities.search_result import SearchResult
from private_rag.domain.repositories.chunk_repository import ChunkVectorRepository
from private_rag.domain.repositories.document_repository import DocumentRepository
from private_rag.domain.value_objects.document_status import DocumentStatus


class SemanticSearchUseCase:
    """Hybrid retrieval: semantic (vector) search plus a lexical keyword pass.

    Pure vector search ranks short exact terms (acronyms like "SEO") poorly, so a
    lexical pass retrieves chunks that literally contain the query's keywords and
    the two are interleaved — keeping strong semantic matches while surfacing exact
    terms. Results are restricted to fully ``INDEXED`` documents, so a document that
    is still processing or failed never surfaces partial content. The LLM is not
    involved; only the embedding model and vector store are used.
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
        limit = max(1, top_k if top_k is not None else self._default_top_k)

        semantic = self._chunks.query(
            embedding, top_k=limit, document_ids=indexed_ids
        )

        keywords = extract_keywords(cleaned)
        lexical: list[SearchResult] = []
        if keywords:
            lexical = self._chunks.query(
                embedding,
                top_k=limit,
                document_ids=indexed_ids,
                contains=contains_variants(keywords),
            )

        return self._interleave(lexical, semantic, limit)

    @staticmethod
    def _interleave(
        lexical: list[SearchResult], semantic: list[SearchResult], limit: int
    ) -> list[SearchResult]:
        """Interleave exact-term hits with semantic hits, deduped, up to ``limit``.

        Taking lexical first in each pair surfaces exact-term chunks that vector
        search alone ranks too low, without dropping the best semantic matches.
        """
        merged: list[SearchResult] = []
        seen: set[str] = set()
        for lex, sem in zip_longest(lexical, semantic):
            for result in (lex, sem):
                if result is None or result.chunk_id in seen:
                    continue
                seen.add(result.chunk_id)
                merged.append(result)
                if len(merged) >= limit:
                    return merged
        return merged
