"""Unit tests for domain entities."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from private_rag.domain.entities.chat_message import ChatMessage
from private_rag.domain.entities.document import Document
from private_rag.domain.entities.document_chunk import DocumentChunk
from private_rag.domain.entities.indexing_job import IndexingJob
from private_rag.domain.entities.search_result import SearchResult
from private_rag.domain.exceptions import (
    DomainValidationError,
    InvalidStateTransitionError,
)
from private_rag.domain.value_objects.chat_role import ChatRole
from private_rag.domain.value_objects.document_status import DocumentStatus
from private_rag.domain.value_objects.job_status import JobStatus

CHECKSUM = "a" * 64
NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
LATER = datetime(2026, 1, 1, 13, 0, 0, tzinfo=UTC)


def _make_document() -> Document:
    return Document.create(
        original_name="policy.pdf",
        stored_name="abc123.pdf",
        mime_type="application/pdf",
        extension=".pdf",
        size_bytes=2048,
        checksum_sha256=CHECKSUM,
        now=NOW,
        document_id="doc-1",
    )


class TestDocument:
    def test_create_starts_uploaded(self) -> None:
        doc = _make_document()
        assert doc.status is DocumentStatus.UPLOADED
        assert doc.created_at == NOW
        assert doc.updated_at == NOW
        assert doc.indexed_at is None

    def test_rejects_invalid_checksum(self) -> None:
        with pytest.raises(DomainValidationError):
            Document.create(
                original_name="a",
                stored_name="b",
                mime_type="text/plain",
                extension=".txt",
                size_bytes=1,
                checksum_sha256="not-a-checksum",
                now=NOW,
            )

    def test_full_indexing_lifecycle(self) -> None:
        doc = _make_document()
        doc.mark_pending(now=LATER)
        assert doc.status is DocumentStatus.PENDING
        doc.mark_processing(now=LATER)
        assert doc.status is DocumentStatus.PROCESSING
        doc.mark_indexed(now=LATER, chunk_count=7)
        assert doc.status is DocumentStatus.INDEXED
        assert doc.indexed_at == LATER
        assert doc.chunk_count == 7
        assert doc.error_message is None

    def test_failure_records_error_message(self) -> None:
        doc = _make_document()
        doc.mark_pending(now=NOW)
        doc.mark_processing(now=NOW)
        doc.mark_failed(now=LATER, error_message="parser crashed")
        assert doc.status is DocumentStatus.FAILED
        assert doc.error_message == "parser crashed"

    def test_retry_clears_error(self) -> None:
        doc = _make_document()
        doc.mark_pending(now=NOW)
        doc.mark_processing(now=NOW)
        doc.mark_failed(now=NOW, error_message="boom")
        doc.mark_pending(now=LATER)  # retry
        assert doc.status is DocumentStatus.PENDING
        assert doc.error_message is None

    def test_illegal_transition_raises(self) -> None:
        doc = _make_document()
        with pytest.raises(InvalidStateTransitionError):
            doc.mark_indexed(now=NOW, chunk_count=1)  # uploaded -> indexed is illegal


class TestDocumentChunk:
    def test_page_number_read_from_metadata(self) -> None:
        chunk = DocumentChunk(
            id="c-1",
            document_id="doc-1",
            content="hello world",
            chunk_index=0,
            token_count=2,
            metadata={"page_number": "5"},
        )
        assert chunk.page_number == 5

    def test_empty_content_rejected(self) -> None:
        with pytest.raises(DomainValidationError):
            DocumentChunk(id="c", document_id="d", content="", chunk_index=0, token_count=0)


class TestIndexingJob:
    def test_lifecycle(self) -> None:
        job = IndexingJob.create(document_id="doc-1", job_id="job-1")
        assert job.status is JobStatus.PENDING
        job.start(now=NOW)
        assert job.status is JobStatus.RUNNING
        job.update_progress(0.5)
        assert job.progress == 0.5
        job.complete(now=LATER)
        assert job.status is JobStatus.COMPLETED
        assert job.progress == 1.0
        assert job.completed_at == LATER

    def test_fail_then_retry(self) -> None:
        job = IndexingJob.create(document_id="doc-1")
        job.start(now=NOW)
        job.fail(now=NOW, error_message="oops")
        assert job.status is JobStatus.FAILED
        job.register_retry()
        assert job.status is JobStatus.PENDING
        assert job.retry_count == 1
        assert job.error_message is None

    def test_progress_out_of_range_rejected(self) -> None:
        job = IndexingJob.create(document_id="doc-1")
        with pytest.raises(DomainValidationError):
            job.update_progress(1.5)


class TestSearchResultAndChatMessage:
    def test_negative_distance_rejected(self) -> None:
        with pytest.raises(DomainValidationError):
            SearchResult(
                document_id="d",
                document_name="n",
                chunk_id="c",
                content="x",
                distance=-0.1,
            )

    def test_chat_message_create(self) -> None:
        msg = ChatMessage.create(role=ChatRole.ASSISTANT, content="answer", now=NOW)
        assert msg.role is ChatRole.ASSISTANT
        assert msg.sources == []
        assert msg.id
