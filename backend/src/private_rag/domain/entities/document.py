"""Document entity and its lifecycle behaviour."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime

from private_rag.domain.exceptions import (
    DomainValidationError,
    InvalidStateTransitionError,
)
from private_rag.domain.value_objects.document_status import (
    DocumentStatus,
    can_transition,
)

_CHECKSUM_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(slots=True)
class Document:
    """A document uploaded by the user and tracked through the indexing lifecycle."""

    id: str
    original_name: str
    stored_name: str
    mime_type: str
    extension: str
    size_bytes: int
    checksum_sha256: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    indexed_at: datetime | None = None
    chunk_count: int = 0
    error_message: str | None = None
    knowledge_base_id: str | None = None

    def __post_init__(self) -> None:
        if not self.original_name.strip():
            raise DomainValidationError("Document.original_name must not be empty")
        if not self.stored_name.strip():
            raise DomainValidationError("Document.stored_name must not be empty")
        if self.size_bytes < 0:
            raise DomainValidationError("Document.size_bytes must not be negative")
        if not _CHECKSUM_RE.match(self.checksum_sha256):
            raise DomainValidationError(
                "Document.checksum_sha256 must be a 64-character lowercase hex SHA-256"
            )
        if self.chunk_count < 0:
            raise DomainValidationError("Document.chunk_count must not be negative")

    @classmethod
    def create(
        cls,
        *,
        original_name: str,
        stored_name: str,
        mime_type: str,
        extension: str,
        size_bytes: int,
        checksum_sha256: str,
        now: datetime,
        document_id: str | None = None,
        knowledge_base_id: str | None = None,
    ) -> Document:
        """Create a new document in the ``UPLOADED`` state."""
        return cls(
            id=document_id or str(uuid.uuid4()),
            original_name=original_name,
            stored_name=stored_name,
            mime_type=mime_type,
            extension=extension,
            size_bytes=size_bytes,
            checksum_sha256=checksum_sha256,
            status=DocumentStatus.UPLOADED,
            created_at=now,
            updated_at=now,
            knowledge_base_id=knowledge_base_id,
        )

    def transition_to(
        self,
        target: DocumentStatus,
        *,
        now: datetime,
        error_message: str | None = None,
    ) -> None:
        """Move the document to ``target`` if the transition is permitted."""
        if not can_transition(self.status, target):
            raise InvalidStateTransitionError("Document", self.status, target)

        self.status = target
        self.updated_at = now

        if target is DocumentStatus.INDEXED:
            self.indexed_at = now
            self.error_message = None
        elif target is DocumentStatus.FAILED:
            self.error_message = error_message
        elif target is DocumentStatus.PENDING:
            # Queued for (re)indexing: clear any previous failure.
            self.error_message = None

    def mark_pending(self, *, now: datetime) -> None:
        self.transition_to(DocumentStatus.PENDING, now=now)

    def mark_processing(self, *, now: datetime) -> None:
        self.transition_to(DocumentStatus.PROCESSING, now=now)

    def mark_indexed(self, *, now: datetime, chunk_count: int) -> None:
        if chunk_count < 0:
            raise DomainValidationError("chunk_count must not be negative")
        self.transition_to(DocumentStatus.INDEXED, now=now)
        self.chunk_count = chunk_count

    def mark_failed(self, *, now: datetime, error_message: str) -> None:
        self.transition_to(DocumentStatus.FAILED, now=now, error_message=error_message)

    def mark_deleting(self, *, now: datetime) -> None:
        self.transition_to(DocumentStatus.DELETING, now=now)
