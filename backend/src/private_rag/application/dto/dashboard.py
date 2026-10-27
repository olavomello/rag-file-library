"""DTO for dashboard statistics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DashboardStats:
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
