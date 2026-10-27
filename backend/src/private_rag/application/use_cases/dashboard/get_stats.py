"""Use case: aggregate dashboard statistics."""

from __future__ import annotations

from private_rag.application.dto.dashboard import DashboardStats
from private_rag.domain.repositories.chunk_repository import ChunkVectorRepository
from private_rag.domain.repositories.document_repository import DocumentRepository
from private_rag.domain.repositories.indexing_job_repository import (
    IndexingJobRepository,
)
from private_rag.domain.value_objects.document_status import DocumentStatus
from private_rag.domain.value_objects.job_status import JobStatus


class GetDashboardStatsUseCase:
    def __init__(
        self,
        *,
        documents: DocumentRepository,
        chunks: ChunkVectorRepository,
        jobs: IndexingJobRepository,
        generation_model: str,
        embedding_model: str,
    ) -> None:
        self._documents = documents
        self._chunks = chunks
        self._jobs = jobs
        self._generation_model = generation_model
        self._embedding_model = embedding_model

    def execute(self) -> DashboardStats:
        documents = self._documents.list()
        tally = dict.fromkeys(DocumentStatus, 0)
        for document in documents:
            tally[document.status] += 1

        active_jobs = sum(
            1
            for job in self._jobs.list()
            if job.status in (JobStatus.PENDING, JobStatus.RUNNING)
        )

        return DashboardStats(
            total_documents=len(documents),
            uploaded=tally[DocumentStatus.UPLOADED],
            pending=tally[DocumentStatus.PENDING],
            processing=tally[DocumentStatus.PROCESSING],
            indexed=tally[DocumentStatus.INDEXED],
            failed=tally[DocumentStatus.FAILED],
            deleting=tally[DocumentStatus.DELETING],
            total_chunks=self._chunks.count(),
            active_jobs=active_jobs,
            generation_model=self._generation_model,
            embedding_model=self._embedding_model,
        )
