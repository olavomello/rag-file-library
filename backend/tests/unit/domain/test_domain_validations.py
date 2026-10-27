"""Unit tests for domain invariants and remaining entity behaviours."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from private_rag.domain.entities.chat_message import ChatMessage
from private_rag.domain.entities.document import Document
from private_rag.domain.entities.document_chunk import DocumentChunk
from private_rag.domain.entities.indexing_job import IndexingJob
from private_rag.domain.entities.knowledge_base import KnowledgeBase
from private_rag.domain.entities.search_result import SearchResult
from private_rag.domain.exceptions import DomainValidationError
from private_rag.domain.value_objects.chat_role import ChatRole
from private_rag.domain.value_objects.document_status import DocumentStatus
from private_rag.domain.value_objects.source_reference import SourceReference

NOW = datetime(2026, 1, 1, tzinfo=UTC)
CHECKSUM = "a" * 64


class TestKnowledgeBase:
    def test_create_defaults(self) -> None:
        kb = KnowledgeBase.create(name="Default", now=NOW)
        assert kb.id
        assert kb.name == "Default"
        assert kb.document_count == 0
        assert kb.created_at == NOW

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(DomainValidationError):
            KnowledgeBase.create(name="   ", now=NOW)

    def test_negative_document_count_rejected(self) -> None:
        with pytest.raises(DomainValidationError):
            KnowledgeBase(
                id="kb-1", name="x", description="", created_at=NOW, updated_at=NOW,
                document_count=-1,
            )


class TestDocumentValidation:
    def _doc(self, **overrides: object) -> Document:
        params: dict[str, object] = {
            "original_name": "a.txt",
            "stored_name": "a.txt",
            "mime_type": "text/plain",
            "extension": ".txt",
            "size_bytes": 1,
            "checksum_sha256": CHECKSUM,
            "now": NOW,
        }
        params.update(overrides)
        return Document.create(**params)  # type: ignore[arg-type]

    def test_empty_original_name_rejected(self) -> None:
        with pytest.raises(DomainValidationError):
            self._doc(original_name="  ")

    def test_empty_stored_name_rejected(self) -> None:
        with pytest.raises(DomainValidationError):
            self._doc(stored_name="")

    def test_negative_size_rejected(self) -> None:
        with pytest.raises(DomainValidationError):
            self._doc(size_bytes=-1)

    def test_mark_deleting_from_uploaded(self) -> None:
        doc = self._doc()
        doc.mark_deleting(now=NOW)
        assert doc.status is DocumentStatus.DELETING

    def test_mark_indexed_rejects_negative_chunk_count(self) -> None:
        doc = self._doc()
        doc.mark_pending(now=NOW)
        doc.mark_processing(now=NOW)
        with pytest.raises(DomainValidationError):
            doc.mark_indexed(now=NOW, chunk_count=-1)


class TestDocumentChunkValidation:
    def test_empty_id_rejected(self) -> None:
        with pytest.raises(DomainValidationError):
            DocumentChunk(id="", document_id="d", content="x", chunk_index=0, token_count=0)

    def test_empty_document_id_rejected(self) -> None:
        with pytest.raises(DomainValidationError):
            DocumentChunk(id="c", document_id="", content="x", chunk_index=0, token_count=0)

    def test_negative_index_rejected(self) -> None:
        with pytest.raises(DomainValidationError):
            DocumentChunk(id="c", document_id="d", content="x", chunk_index=-1, token_count=0)

    def test_negative_token_count_rejected(self) -> None:
        with pytest.raises(DomainValidationError):
            DocumentChunk(id="c", document_id="d", content="x", chunk_index=0, token_count=-1)

    def test_page_number_absent_or_invalid_is_none(self) -> None:
        plain = DocumentChunk(
            id="c", document_id="d", content="x", chunk_index=0, token_count=1
        )
        assert plain.page_number is None
        bad = DocumentChunk(
            id="c", document_id="d", content="x", chunk_index=0, token_count=1,
            metadata={"page_number": "not-a-number"},
        )
        assert bad.page_number is None


class TestSearchResultAndSourceAndChat:
    def test_search_result_empty_chunk_id_rejected(self) -> None:
        with pytest.raises(DomainValidationError):
            SearchResult(
                document_id="d", document_name="n", chunk_id="", content="x", distance=0.1
            )

    def test_search_result_bad_page_rejected(self) -> None:
        with pytest.raises(DomainValidationError):
            SearchResult(
                document_id="d", document_name="n", chunk_id="c", content="x",
                distance=0.1, page_number=0,
            )

    def test_source_reference_empty_chunk_id_rejected(self) -> None:
        with pytest.raises(DomainValidationError):
            SourceReference(document_id="d", document_name="n", chunk_id="")

    def test_chat_message_empty_content_rejected(self) -> None:
        with pytest.raises(DomainValidationError):
            ChatMessage.create(role=ChatRole.USER, content="", now=NOW)


class TestIndexingJobValidation:
    def test_empty_document_id_rejected(self) -> None:
        with pytest.raises(DomainValidationError):
            IndexingJob(id="j", document_id="", status=IndexingJob.create(document_id="x").status)

    def test_progress_out_of_range_rejected_on_construction(self) -> None:
        with pytest.raises(DomainValidationError):
            IndexingJob.create(document_id="d").update_progress(2.0)

    def test_reset_for_requeue_clears_state(self) -> None:
        job = IndexingJob.create(document_id="d", job_id="j")
        job.start(now=NOW)
        job.fail(now=NOW, error_message="boom")
        job.reset_for_requeue()
        assert job.error_message is None
        assert job.started_at is None
        assert job.progress == 0.0
        assert job.retry_count == 0
