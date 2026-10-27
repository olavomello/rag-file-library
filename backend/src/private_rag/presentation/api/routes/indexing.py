"""Indexing job endpoints: list, get, retry."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, Query, status

from private_rag.container.container import Container
from private_rag.domain.value_objects.job_status import JobStatus
from private_rag.presentation.api.dependencies.providers import get_container
from private_rag.presentation.api.schemas.indexing import JobListResponse, JobResponse

router = APIRouter(prefix="/indexing", tags=["indexing"])


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    container: Container = Depends(get_container),
) -> JobListResponse:
    jobs = await asyncio.to_thread(
        container.indexing_job_repository.list, status=status_filter
    )
    return JobListResponse(
        items=[JobResponse.from_entity(job) for job in jobs], total=len(jobs)
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    container: Container = Depends(get_container),
) -> JobResponse:
    job = await asyncio.to_thread(container.indexing_job_repository.get, job_id)
    return JobResponse.from_entity(job)


@router.post(
    "/jobs/{job_id}/retry",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def retry_job(
    job_id: str,
    container: Container = Depends(get_container),
) -> JobResponse:
    job = await container.indexing_worker.retry(job_id)
    return JobResponse.from_entity(job)
