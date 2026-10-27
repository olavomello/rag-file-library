"""IndexingJob entity."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from private_rag.domain.exceptions import DomainValidationError
from private_rag.domain.value_objects.job_status import JobStatus


@dataclass(slots=True)
class IndexingJob:
    """Tracks the progress and outcome of indexing a single document."""

    id: str
    document_id: str
    status: JobStatus
    progress: float = 0.0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    retry_count: int = 0

    def __post_init__(self) -> None:
        if not self.document_id:
            raise DomainValidationError("IndexingJob.document_id must not be empty")
        if not 0.0 <= self.progress <= 1.0:
            raise DomainValidationError("IndexingJob.progress must be within [0.0, 1.0]")
        if self.retry_count < 0:
            raise DomainValidationError("IndexingJob.retry_count must not be negative")

    @classmethod
    def create(
        cls,
        *,
        document_id: str,
        job_id: str | None = None,
    ) -> IndexingJob:
        return cls(
            id=job_id or str(uuid.uuid4()),
            document_id=document_id,
            status=JobStatus.PENDING,
            progress=0.0,
        )

    def start(self, *, now: datetime) -> None:
        self.status = JobStatus.RUNNING
        self.started_at = now
        self.completed_at = None
        self.error_message = None

    def update_progress(self, value: float) -> None:
        if not 0.0 <= value <= 1.0:
            raise DomainValidationError("progress must be within [0.0, 1.0]")
        self.progress = value

    def complete(self, *, now: datetime) -> None:
        self.status = JobStatus.COMPLETED
        self.progress = 1.0
        self.completed_at = now
        self.error_message = None

    def fail(self, *, now: datetime, error_message: str) -> None:
        self.status = JobStatus.FAILED
        self.completed_at = now
        self.error_message = error_message

    def register_retry(self) -> None:
        """Reset the job to a fresh pending state and count the retry."""
        self.retry_count += 1
        self.status = JobStatus.PENDING
        self.progress = 0.0
        self.started_at = None
        self.completed_at = None
        self.error_message = None
