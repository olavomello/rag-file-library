"""Response schemas for indexing job endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from private_rag.domain.entities.indexing_job import IndexingJob


class JobResponse(BaseModel):
    id: str
    document_id: str
    status: str
    progress: float
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    retry_count: int

    @classmethod
    def from_entity(cls, job: IndexingJob) -> JobResponse:
        return cls(
            id=job.id,
            document_id=job.document_id,
            status=job.status.value,
            progress=job.progress,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
            retry_count=job.retry_count,
        )


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
