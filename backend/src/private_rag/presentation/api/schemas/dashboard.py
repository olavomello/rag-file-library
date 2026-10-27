"""Response schema for dashboard statistics."""

from __future__ import annotations

from pydantic import BaseModel

from private_rag.application.dto.dashboard import DashboardStats


class DashboardStatsResponse(BaseModel):
    total_documents: int
    uploaded: int
    pending: int
    processing: int
    indexed: int
    failed: int
    deleting: int
    total_chunks: int
    active_jobs: int
    generation_model: str
    embedding_model: str

    @classmethod
    def from_dto(cls, stats: DashboardStats) -> DashboardStatsResponse:
        return cls(
            total_documents=stats.total_documents,
            uploaded=stats.uploaded,
            pending=stats.pending,
            processing=stats.processing,
            indexed=stats.indexed,
            failed=stats.failed,
            deleting=stats.deleting,
            total_chunks=stats.total_chunks,
            active_jobs=stats.active_jobs,
            generation_model=stats.generation_model,
            embedding_model=stats.embedding_model,
        )
