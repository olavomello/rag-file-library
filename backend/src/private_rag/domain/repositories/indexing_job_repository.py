"""Repository contract for indexing job persistence."""

from __future__ import annotations

from typing import Protocol

from private_rag.domain.entities.indexing_job import IndexingJob
from private_rag.domain.value_objects.job_status import JobStatus


class IndexingJobRepository(Protocol):
    """Durably persists :class:`IndexingJob` state so indexing survives restarts.

    Implementations must raise :class:`IndexingJobNotFoundError` from ``get`` and
    ``update`` when the job does not exist.
    """

    def add(self, job: IndexingJob) -> None: ...

    def get(self, job_id: str) -> IndexingJob: ...

    def get_by_document(self, document_id: str) -> IndexingJob | None: ...

    def list(self, *, status: JobStatus | None = None) -> list[IndexingJob]: ...

    def update(self, job: IndexingJob) -> None: ...

    def delete(self, job_id: str) -> None: ...
