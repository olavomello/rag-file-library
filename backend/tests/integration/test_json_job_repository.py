"""Integration tests for the JSON-backed indexing job repository."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from private_rag.domain.entities.indexing_job import IndexingJob
from private_rag.domain.exceptions import IndexingJobNotFoundError
from private_rag.domain.value_objects.job_status import JobStatus
from private_rag.infrastructure.filesystem.json_indexing_job_repository import (
    JsonIndexingJobRepository,
)

NOW = datetime(2026, 1, 1, 9, 30, tzinfo=UTC)


@pytest.fixture
def repo(tmp_path: Path) -> JsonIndexingJobRepository:
    store = JsonIndexingJobRepository(tmp_path / "jobs")
    store.ensure_ready()
    return store


def test_add_and_get_roundtrip_preserves_state(repo: JsonIndexingJobRepository) -> None:
    job = IndexingJob.create(document_id="doc-1", job_id="job-1")
    job.start(now=NOW)
    job.update_progress(0.4)
    repo.add(job)

    loaded = repo.get("job-1")
    assert loaded.document_id == "doc-1"
    assert loaded.status is JobStatus.RUNNING
    assert loaded.progress == 0.4
    assert loaded.started_at == NOW
    assert loaded.completed_at is None


def test_get_missing_raises(repo: JsonIndexingJobRepository) -> None:
    with pytest.raises(IndexingJobNotFoundError):
        repo.get("nope")


def test_update_missing_raises(repo: JsonIndexingJobRepository) -> None:
    job = IndexingJob.create(document_id="doc-1", job_id="ghost")
    with pytest.raises(IndexingJobNotFoundError):
        repo.update(job)


def test_update_persists_changes(repo: JsonIndexingJobRepository) -> None:
    job = IndexingJob.create(document_id="doc-1", job_id="job-1")
    repo.add(job)
    job.fail(now=NOW, error_message="boom")
    repo.update(job)

    loaded = repo.get("job-1")
    assert loaded.status is JobStatus.FAILED
    assert loaded.error_message == "boom"


def test_list_filters_by_status(repo: JsonIndexingJobRepository) -> None:
    a = IndexingJob.create(document_id="doc-a", job_id="a")
    b = IndexingJob.create(document_id="doc-b", job_id="b")
    b.start(now=NOW)
    b.complete(now=NOW)
    repo.add(a)
    repo.add(b)

    assert {j.id for j in repo.list()} == {"a", "b"}
    assert [j.id for j in repo.list(status=JobStatus.COMPLETED)] == ["b"]
    assert [j.id for j in repo.list(status=JobStatus.PENDING)] == ["a"]


def test_get_by_document(repo: JsonIndexingJobRepository) -> None:
    job = IndexingJob.create(document_id="doc-xyz", job_id="j1")
    repo.add(job)
    found = repo.get_by_document("doc-xyz")
    assert found is not None
    assert found.id == "j1"
    assert repo.get_by_document("missing") is None


def test_delete(repo: JsonIndexingJobRepository) -> None:
    job = IndexingJob.create(document_id="doc-1", job_id="job-1")
    repo.add(job)
    repo.delete("job-1")
    with pytest.raises(IndexingJobNotFoundError):
        repo.get("job-1")
