"""Unit tests for the background indexing worker."""

from __future__ import annotations

from datetime import UTC, datetime

from private_rag.domain.entities.document import Document
from private_rag.domain.entities.indexing_job import IndexingJob
from private_rag.domain.exceptions import IndexingJobNotFoundError
from private_rag.domain.value_objects.document_status import DocumentStatus
from private_rag.domain.value_objects.job_status import JobStatus
from private_rag.infrastructure.indexing.worker import IndexingWorker

NOW = datetime(2026, 5, 1, 9, 0, tzinfo=UTC)


class InMemoryDocuments:
    def __init__(self) -> None:
        self.by_id: dict[str, Document] = {}

    def add(self, document: Document) -> None:
        self.by_id[document.id] = document

    def get(self, document_id: str) -> Document:
        from private_rag.domain.exceptions import DocumentNotFoundError

        if document_id not in self.by_id:
            raise DocumentNotFoundError(document_id)
        return self.by_id[document_id]

    def update(self, document: Document) -> None:
        self.by_id[document.id] = document


class InMemoryJobs:
    def __init__(self) -> None:
        self.by_id: dict[str, IndexingJob] = {}

    def add(self, job: IndexingJob) -> None:
        self.by_id[job.id] = job

    def get(self, job_id: str) -> IndexingJob:
        if job_id not in self.by_id:
            raise IndexingJobNotFoundError(job_id)
        return self.by_id[job_id]

    def get_by_document(self, document_id: str) -> IndexingJob | None:
        return next(
            (j for j in self.by_id.values() if j.document_id == document_id), None
        )

    def list(self, *, status=None):  # type: ignore[no-untyped-def]
        return [j for j in self.by_id.values() if status is None or j.status is status]

    def update(self, job: IndexingJob) -> None:
        self.by_id[job.id] = job

    def delete(self, job_id: str) -> None:
        self.by_id.pop(job_id, None)


class FakeIndex:
    def __init__(self, documents: InMemoryDocuments) -> None:
        self._documents = documents
        self.fail = False
        self.chunk_count = 3
        self.calls: list[str] = []

    def execute(self, document_id: str, *, progress=None):  # type: ignore[no-untyped-def]
        self.calls.append(document_id)
        document = self._documents.get(document_id)
        document.mark_processing(now=NOW)
        self._documents.update(document)
        if self.fail:
            # Mirror IndexDocumentUseCase: mark the document failed, then raise.
            document.mark_failed(now=NOW, error_message="index boom")
            self._documents.update(document)
            raise RuntimeError("index boom")
        if progress is not None:
            progress(1.0)
        document.mark_indexed(now=NOW, chunk_count=self.chunk_count)
        self._documents.update(document)
        return self.chunk_count


class FixedClock:
    def now(self) -> datetime:
        return NOW


def _document(doc_id: str, status: DocumentStatus = DocumentStatus.UPLOADED) -> Document:
    doc = Document(
        id=doc_id,
        original_name=f"{doc_id}.txt",
        stored_name=f"{doc_id}.txt",
        mime_type="text/plain",
        extension=".txt",
        size_bytes=10,
        checksum_sha256="a" * 64,
        status=status,
        created_at=NOW,
        updated_at=NOW,
    )
    return doc


def _worker(documents: InMemoryDocuments, jobs: InMemoryJobs, index: FakeIndex) -> IndexingWorker:
    return IndexingWorker(
        index_use_case=index,  # type: ignore[arg-type]
        documents=documents,  # type: ignore[arg-type]
        jobs=jobs,  # type: ignore[arg-type]
        clock=FixedClock(),
        concurrency=1,
    )


async def test_enqueue_indexes_document() -> None:
    documents = InMemoryDocuments()
    documents.add(_document("doc-1"))
    jobs = InMemoryJobs()
    index = FakeIndex(documents)
    worker = _worker(documents, jobs, index)

    await worker.start()
    job = await worker.enqueue("doc-1")
    await worker.wait_for_idle()
    await worker.stop()

    assert index.calls == ["doc-1"]
    assert jobs.get(job.id).status is JobStatus.COMPLETED
    assert documents.get("doc-1").status is DocumentStatus.INDEXED


async def test_duplicate_enqueue_does_not_schedule_twice() -> None:
    documents = InMemoryDocuments()
    documents.add(_document("doc-1"))
    jobs = InMemoryJobs()
    index = FakeIndex(documents)
    worker = _worker(documents, jobs, index)

    # No workers started yet, so nothing drains the queue.
    first = await worker.enqueue("doc-1")
    second = await worker.enqueue("doc-1")

    assert first.id == second.id
    assert len(jobs.list()) == 1
    assert worker._queue.qsize() == 1  # only one scheduled

    await worker.start()
    await worker.wait_for_idle()
    await worker.stop()
    assert index.calls == ["doc-1"]


async def test_failure_marks_job_and_document_failed() -> None:
    documents = InMemoryDocuments()
    documents.add(_document("doc-1"))
    jobs = InMemoryJobs()
    index = FakeIndex(documents)
    index.fail = True
    worker = _worker(documents, jobs, index)

    await worker.start()
    job = await worker.enqueue("doc-1")
    await worker.wait_for_idle()
    await worker.stop()

    assert jobs.get(job.id).status is JobStatus.FAILED
    assert jobs.get(job.id).error_message
    assert documents.get("doc-1").status is DocumentStatus.FAILED


async def test_retry_requeues_and_counts() -> None:
    documents = InMemoryDocuments()
    documents.add(_document("doc-1"))
    jobs = InMemoryJobs()
    index = FakeIndex(documents)
    index.fail = True
    worker = _worker(documents, jobs, index)

    await worker.start()
    job = await worker.enqueue("doc-1")
    await worker.wait_for_idle()
    assert jobs.get(job.id).status is JobStatus.FAILED

    index.fail = False
    retried = await worker.retry(job.id)
    await worker.wait_for_idle()
    await worker.stop()

    assert jobs.get(retried.id).status is JobStatus.COMPLETED
    assert jobs.get(retried.id).retry_count == 1
    assert documents.get("doc-1").status is DocumentStatus.INDEXED


async def test_recover_requeues_interrupted_jobs() -> None:
    documents = InMemoryDocuments()
    documents.add(_document("doc-1", status=DocumentStatus.PROCESSING))
    jobs = InMemoryJobs()
    interrupted = IndexingJob.create(document_id="doc-1", job_id="job-1")
    interrupted.start(now=NOW)  # left RUNNING by a previous process
    jobs.add(interrupted)
    index = FakeIndex(documents)
    worker = _worker(documents, jobs, index)

    await worker.start()
    count = await worker.recover()
    await worker.wait_for_idle()
    await worker.stop()

    assert count == 1
    assert jobs.get("job-1").status is JobStatus.COMPLETED
    assert documents.get("doc-1").status is DocumentStatus.INDEXED
