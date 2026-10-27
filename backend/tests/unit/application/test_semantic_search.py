"""Unit tests for the semantic search use case."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from private_rag.application.exceptions import InvalidSearchQueryError
from private_rag.application.use_cases.search.semantic_search import (
    SemanticSearchUseCase,
)
from private_rag.domain.entities.document import Document
from private_rag.domain.entities.search_result import SearchResult
from private_rag.domain.value_objects.document_status import DocumentStatus

NOW = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)


class FakeDocuments:
    def __init__(self, indexed_ids: list[str]) -> None:
        self._indexed = indexed_ids

    def list(self, *, status=None, limit=None, offset=0):  # type: ignore[no-untyped-def]
        assert status is DocumentStatus.INDEXED
        return [
            Document(
                id=doc_id,
                original_name=f"{doc_id}.txt",
                stored_name=f"{doc_id}.txt",
                mime_type="text/plain",
                extension=".txt",
                size_bytes=1,
                checksum_sha256="a" * 64,
                status=DocumentStatus.INDEXED,
                created_at=NOW,
                updated_at=NOW,
            )
            for doc_id in self._indexed
        ]


class FakeChunks:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def query(self, embedding, *, top_k, document_ids=None):  # type: ignore[no-untyped-def]
        self.calls.append(
            {"embedding": embedding, "top_k": top_k, "document_ids": list(document_ids or [])}
        )
        return [
            SearchResult(
                document_id="doc-a",
                document_name="doc-a.txt",
                chunk_id="doc-a:0",
                content="match",
                distance=0.1,
                page_number=1,
            )
        ]


class FakeEmbeddings:
    model = "fake"

    def __init__(self) -> None:
        self.queries: list[str] = []

    def embed_query(self, text: str) -> list[float]:
        self.queries.append(text)
        return [1.0, 0.0]

    def embed_documents(self, texts):  # type: ignore[no-untyped-def]
        raise NotImplementedError


def _use_case(indexed_ids, chunks, embeddings, default_top_k=5):  # type: ignore[no-untyped-def]
    return SemanticSearchUseCase(
        embeddings=embeddings,
        chunks=chunks,
        documents=FakeDocuments(indexed_ids),
        default_top_k=default_top_k,
    )


def test_empty_query_raises_without_embedding() -> None:
    embeddings = FakeEmbeddings()
    with pytest.raises(InvalidSearchQueryError):
        _use_case(["doc-a"], FakeChunks(), embeddings).execute("   ")
    assert embeddings.queries == []


def test_no_indexed_documents_returns_empty_without_embedding() -> None:
    embeddings = FakeEmbeddings()
    chunks = FakeChunks()
    results = _use_case([], chunks, embeddings).execute("anything")
    assert results == []
    assert embeddings.queries == []
    assert chunks.calls == []


def test_search_scopes_to_indexed_documents_and_uses_default_top_k() -> None:
    chunks = FakeChunks()
    results = _use_case(["doc-a", "doc-b"], chunks, FakeEmbeddings()).execute("policy")

    assert len(results) == 1
    assert chunks.calls[0]["top_k"] == 5
    assert set(chunks.calls[0]["document_ids"]) == {"doc-a", "doc-b"}


def test_explicit_document_ids_are_intersected_with_indexed() -> None:
    chunks = FakeChunks()
    _use_case(["doc-a", "doc-b"], chunks, FakeEmbeddings()).execute(
        "policy", document_ids=["doc-b", "doc-missing"]
    )
    assert chunks.calls[0]["document_ids"] == ["doc-b"]


def test_explicit_top_k_is_passed_through() -> None:
    chunks = FakeChunks()
    _use_case(["doc-a"], chunks, FakeEmbeddings()).execute("policy", top_k=3)
    assert chunks.calls[0]["top_k"] == 3
