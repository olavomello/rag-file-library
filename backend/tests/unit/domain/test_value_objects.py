"""Unit tests for domain value objects."""

from __future__ import annotations

import pytest

from private_rag.domain.exceptions import DomainValidationError
from private_rag.domain.value_objects.document_status import (
    DocumentStatus,
    allowed_transitions,
    can_transition,
    is_terminal,
)
from private_rag.domain.value_objects.job_status import JobStatus
from private_rag.domain.value_objects.job_status import is_terminal as job_is_terminal
from private_rag.domain.value_objects.source_reference import SourceReference


class TestDocumentStatusTransitions:
    def test_uploaded_can_be_queued_or_deleted(self) -> None:
        assert can_transition(DocumentStatus.UPLOADED, DocumentStatus.PENDING)
        assert can_transition(DocumentStatus.UPLOADED, DocumentStatus.DELETING)

    def test_processing_can_complete_or_fail(self) -> None:
        assert can_transition(DocumentStatus.PROCESSING, DocumentStatus.INDEXED)
        assert can_transition(DocumentStatus.PROCESSING, DocumentStatus.FAILED)

    def test_indexed_can_be_reindexed(self) -> None:
        assert can_transition(DocumentStatus.INDEXED, DocumentStatus.PENDING)

    def test_failed_can_be_retried(self) -> None:
        assert can_transition(DocumentStatus.FAILED, DocumentStatus.PENDING)

    def test_illegal_transitions_are_rejected(self) -> None:
        assert not can_transition(DocumentStatus.UPLOADED, DocumentStatus.INDEXED)
        assert not can_transition(DocumentStatus.INDEXED, DocumentStatus.PROCESSING)

    def test_deleting_is_terminal(self) -> None:
        assert is_terminal(DocumentStatus.DELETING)
        assert allowed_transitions(DocumentStatus.DELETING) == frozenset()


class TestJobStatus:
    def test_completed_and_cancelled_are_terminal(self) -> None:
        assert job_is_terminal(JobStatus.COMPLETED)
        assert job_is_terminal(JobStatus.CANCELLED)

    def test_running_is_not_terminal(self) -> None:
        assert not job_is_terminal(JobStatus.RUNNING)


class TestSourceReference:
    def test_valid_reference(self) -> None:
        ref = SourceReference(
            document_id="doc-1", document_name="policy.pdf", chunk_id="c-1", page_number=3
        )
        assert ref.page_number == 3

    def test_empty_document_id_rejected(self) -> None:
        with pytest.raises(DomainValidationError):
            SourceReference(document_id="", document_name="x", chunk_id="c-1")

    def test_page_number_must_be_positive(self) -> None:
        with pytest.raises(DomainValidationError):
            SourceReference(
                document_id="d", document_name="x", chunk_id="c", page_number=0
            )

    def test_is_immutable(self) -> None:
        ref = SourceReference(document_id="d", document_name="x", chunk_id="c")
        with pytest.raises(AttributeError):
            ref.document_id = "other"  # type: ignore[misc]
