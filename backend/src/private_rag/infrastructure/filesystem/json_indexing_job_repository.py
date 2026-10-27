"""Durable JSON-file implementation of the indexing job repository.

Each job is stored as one JSON file (``<job_id>.json``) written atomically, so job
state survives application restarts and incomplete writes never corrupt the store.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from private_rag.domain.entities.indexing_job import IndexingJob
from private_rag.domain.exceptions import IndexingJobNotFoundError
from private_rag.domain.value_objects.job_status import JobStatus
from private_rag.infrastructure.filesystem.atomic import atomic_write_text


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _parse(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _to_dict(job: IndexingJob) -> dict[str, object]:
    return {
        "id": job.id,
        "document_id": job.document_id,
        "status": job.status.value,
        "progress": job.progress,
        "started_at": _iso(job.started_at),
        "completed_at": _iso(job.completed_at),
        "error_message": job.error_message,
        "retry_count": job.retry_count,
    }


def _from_dict(data: dict[str, Any]) -> IndexingJob:
    return IndexingJob(
        id=str(data["id"]),
        document_id=str(data["document_id"]),
        status=JobStatus(str(data["status"])),
        progress=float(data["progress"]),
        started_at=_parse(data.get("started_at")),
        completed_at=_parse(data.get("completed_at")),
        error_message=(
            str(data["error_message"]) if data.get("error_message") is not None else None
        ),
        retry_count=int(data["retry_count"]),
    )


class JsonIndexingJobRepository:
    """Stores indexing jobs as individual JSON files in a directory."""

    def __init__(self, base_dir: str | Path) -> None:
        self._base = Path(base_dir)

    def ensure_ready(self) -> None:
        self._base.mkdir(parents=True, exist_ok=True)

    def _path(self, job_id: str) -> Path:
        return self._base / f"{job_id}.json"

    def add(self, job: IndexingJob) -> None:
        self._write(job)

    def get(self, job_id: str) -> IndexingJob:
        path = self._path(job_id)
        if not path.is_file():
            raise IndexingJobNotFoundError(job_id)
        return _from_dict(json.loads(path.read_text(encoding="utf-8")))

    def get_by_document(self, document_id: str) -> IndexingJob | None:
        for job in self.list():
            if job.document_id == document_id:
                return job
        return None

    def list(self, *, status: JobStatus | None = None) -> list[IndexingJob]:
        if not self._base.is_dir():
            return []
        jobs: list[IndexingJob] = []
        for path in self._base.glob("*.json"):
            job = _from_dict(json.loads(path.read_text(encoding="utf-8")))
            if status is None or job.status is status:
                jobs.append(job)
        return jobs

    def update(self, job: IndexingJob) -> None:
        if not self._path(job.id).is_file():
            raise IndexingJobNotFoundError(job.id)
        self._write(job)

    def delete(self, job_id: str) -> None:
        self._path(job_id).unlink(missing_ok=True)

    def _write(self, job: IndexingJob) -> None:
        atomic_write_text(
            self._path(job.id),
            json.dumps(_to_dict(job), ensure_ascii=False, indent=2),
        )
