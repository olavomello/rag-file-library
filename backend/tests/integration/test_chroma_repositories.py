"""Integration tests for the ChromaDB chunk and document-registry repositories.

These run against a real embedded ChromaDB instance in a temporary directory.
Embeddings are supplied explicitly (no model is downloaded).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from private_rag.domain.entities.document import Document
from private_rag.domain.entities.document_chunk import DocumentChunk
from private_rag.domain.exceptions import DocumentNotFoundError, DuplicateDocumentError
from private_rag.domain.value_objects.document_status import DocumentStatus
from private_rag.infrastructure.chroma.chunk_repository import ChromaChunkRepository
from private_rag.infrastructure.chroma.client import ChromaClientProvider
from private_rag.infrastructure.chroma.document_registry import ChromaDocumentRegistry

CHECKSUM = "b" * 64
NOW = datetime(2026, 2, 1, 10, 0, tzinfo=UTC)
LATER = datetime(2026, 2, 2, 10, 0, tzinfo=UTC)


@pytest.fixture
def provider(tmp_path: Path) -> ChromaClientProvider:
    return ChromaClientProvider(str(tmp_path / "chroma"))


def _chunk(
    chunk_id: str, content: str, index: int, *, document_id: str, page: int
) -> DocumentChunk:
    return DocumentChunk(
        id=chunk_id,
        document_id=document_id,
        content=content,
        chunk_index=index,
        token_count=len(content.split()),
        metadata={"document_name": "policy.pdf", "page_number": str(page)},
    )


def _document(
    doc_id: str,
    *,
    status: DocumentStatus = DocumentStatus.UPLOADED,
    created: datetime = NOW,
) -> Document:
    return Document(
        id=doc_id,
        original_name=f"{doc_id}.pdf",
        stored_name=f"{doc_id}.pdf",
        mime_type="application/pdf",
        extension=".pdf",
        size_bytes=1234,
        checksum_sha256=CHECKSUM,
        status=status,
        created_at=created,
        updated_at=created,
    )


class TestChromaChunkRepository:
    def test_add_and_count(self, provider: ChromaClientProvider) -> None:
        repo = ChromaChunkRepository(provider)
        chunks = [
            _chunk("c0", "alpha", 0, document_id="doc-1", page=1),
            _chunk("c1", "beta", 1, document_id="doc-1", page=2),
        ]
        repo.add_chunks(chunks, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], embedding_model="test-embed")

        assert repo.count() == 2
        assert repo.count(document_id="doc-1") == 2
        assert repo.count(document_id="missing") == 0

    def test_query_returns_nearest_with_mapped_metadata(
        self, provider: ChromaClientProvider
    ) -> None:
        repo = ChromaChunkRepository(provider)
        chunks = [
            _chunk("c0", "alpha", 0, document_id="doc-1", page=3),
            _chunk("c1", "beta", 1, document_id="doc-1", page=4),
            _chunk("c2", "gamma", 2, document_id="doc-1", page=5),
        ]
        repo.add_chunks(
            chunks,
            [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            embedding_model="test-embed",
        )

        results = repo.query([0.9, 0.1, 0.0], top_k=2)

        assert len(results) == 2
        assert results[0].chunk_id == "c0"
        assert results[0].document_id == "doc-1"
        assert results[0].document_name == "policy.pdf"
        assert results[0].page_number == 3
        assert results[0].distance >= 0.0

    def test_query_scoped_to_document_ids(self, provider: ChromaClientProvider) -> None:
        repo = ChromaChunkRepository(provider)
        repo.add_chunks(
            [_chunk("a", "x", 0, document_id="doc-a", page=1)], [[1.0, 0.0]], embedding_model="e"
        )
        repo.add_chunks(
            [_chunk("b", "y", 0, document_id="doc-b", page=1)], [[0.0, 1.0]], embedding_model="e"
        )

        results = repo.query([1.0, 1.0], top_k=5, document_ids=["doc-b"])
        assert [r.document_id for r in results] == ["doc-b"]

    def test_delete_by_document(self, provider: ChromaClientProvider) -> None:
        repo = ChromaChunkRepository(provider)
        repo.add_chunks(
            [_chunk("a", "x", 0, document_id="doc-a", page=1)], [[1.0, 0.0]], embedding_model="e"
        )
        repo.add_chunks(
            [_chunk("b", "y", 0, document_id="doc-b", page=1)], [[0.0, 1.0]], embedding_model="e"
        )
        repo.delete_by_document("doc-a")
        assert repo.count(document_id="doc-a") == 0
        assert repo.count(document_id="doc-b") == 1

    def test_mismatched_lengths_raise(self, provider: ChromaClientProvider) -> None:
        repo = ChromaChunkRepository(provider)
        with pytest.raises(ValueError):
            repo.add_chunks(
                [_chunk("a", "x", 0, document_id="d", page=1)], [], embedding_model="e"
            )


class TestChromaDocumentRegistry:
    def test_add_and_get_roundtrip(self, provider: ChromaClientProvider) -> None:
        repo = ChromaDocumentRegistry(provider)
        doc = _document("doc-1")
        repo.add(doc)

        loaded = repo.get("doc-1")
        assert loaded.original_name == "doc-1.pdf"
        assert loaded.status is DocumentStatus.UPLOADED
        assert loaded.checksum_sha256 == CHECKSUM
        assert loaded.created_at == NOW
        assert loaded.indexed_at is None
        assert loaded.error_message is None

    def test_duplicate_add_raises(self, provider: ChromaClientProvider) -> None:
        repo = ChromaDocumentRegistry(provider)
        repo.add(_document("doc-1"))
        with pytest.raises(DuplicateDocumentError):
            repo.add(_document("doc-1"))

    def test_get_missing_raises(self, provider: ChromaClientProvider) -> None:
        repo = ChromaDocumentRegistry(provider)
        with pytest.raises(DocumentNotFoundError):
            repo.get("nope")

    def test_update_persists_status_and_timestamps(self, provider: ChromaClientProvider) -> None:
        repo = ChromaDocumentRegistry(provider)
        doc = _document("doc-1")
        repo.add(doc)

        doc.mark_pending(now=LATER)
        doc.mark_processing(now=LATER)
        doc.mark_indexed(now=LATER, chunk_count=9)
        repo.update(doc)

        loaded = repo.get("doc-1")
        assert loaded.status is DocumentStatus.INDEXED
        assert loaded.chunk_count == 9
        assert loaded.indexed_at == LATER

    def test_update_missing_raises(self, provider: ChromaClientProvider) -> None:
        repo = ChromaDocumentRegistry(provider)
        with pytest.raises(DocumentNotFoundError):
            repo.update(_document("ghost"))

    def test_get_by_checksum(self, provider: ChromaClientProvider) -> None:
        repo = ChromaDocumentRegistry(provider)
        repo.add(_document("doc-1"))
        found = repo.get_by_checksum(CHECKSUM)
        assert found is not None and found.id == "doc-1"
        assert repo.get_by_checksum("c" * 64) is None

    def test_list_filter_sort_and_paginate(self, provider: ChromaClientProvider) -> None:
        repo = ChromaDocumentRegistry(provider)
        older = _document("old", created=NOW)
        newer = _document("new", status=DocumentStatus.FAILED, created=LATER)
        repo.add(older)
        repo.add(newer)

        all_docs = repo.list()
        assert [d.id for d in all_docs] == ["new", "old"]  # created_at desc

        failed = repo.list(status=DocumentStatus.FAILED)
        assert [d.id for d in failed] == ["new"]

        assert [d.id for d in repo.list(limit=1)] == ["new"]
        assert [d.id for d in repo.list(limit=1, offset=1)] == ["old"]

    def test_count_and_delete(self, provider: ChromaClientProvider) -> None:
        repo = ChromaDocumentRegistry(provider)
        repo.add(_document("doc-1"))
        repo.add(_document("doc-2", status=DocumentStatus.FAILED))
        assert repo.count() == 2
        assert repo.count(status=DocumentStatus.FAILED) == 1

        repo.delete("doc-1")
        assert repo.count() == 1
        with pytest.raises(DocumentNotFoundError):
            repo.get("doc-1")
