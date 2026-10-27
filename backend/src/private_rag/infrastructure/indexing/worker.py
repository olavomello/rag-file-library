"""In-process background indexing worker.

A bounded set of asyncio tasks consume document ids from a queue and run the
(synchronous, CPU/IO-bound) indexing pipeline in a thread so the event loop stays
responsive. Job state is persisted to the job repository, so progress is visible
and interrupted work can be recovered after a restart. No external job
infrastructure (Redis/Celery/etc.) is used.
"""

from __future__ import annotations

import asyncio
import logging

from private_rag.application.ports.clock import Clock
from private_rag.application.use_cases.indexing.index_document import (
    IndexDocumentUseCase,
)
from private_rag.domain.entities.indexing_job import IndexingJob
from private_rag.domain.exceptions import DocumentNotFoundError
from private_rag.domain.repositories.document_repository import DocumentRepository
from private_rag.domain.repositories.indexing_job_repository import (
    IndexingJobRepository,
)
from private_rag.domain.value_objects.document_status import (
    DocumentStatus,
    can_transition,
)
from private_rag.domain.value_objects.job_status import JobStatus

logger = logging.getLogger(__name__)


class IndexingWorker:
    def __init__(
        self,
        *,
        index_use_case: IndexDocumentUseCase,
        documents: DocumentRepository,
        jobs: IndexingJobRepository,
        clock: Clock,
        concurrency: int = 1,
    ) -> None:
        self._index = index_use_case
        self._documents = documents
        self._jobs = jobs
        self._clock = clock
        self._concurrency = max(1, concurrency)
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._tasks: list[asyncio.Task[None]] = []
        self._inflight: set[str] = set()
        self._lock = asyncio.Lock()
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._tasks = [
            asyncio.create_task(self._worker_loop(), name=f"indexing-worker-{i}")
            for i in range(self._concurrency)
        ]

    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []

    async def enqueue(self, document_id: str) -> IndexingJob:
        """Schedule a document for indexing, creating/resetting its job.

        Idempotent while a document is in flight: a second enqueue returns the
        existing job without scheduling duplicate work.
        """
        async with self._lock:
            job = self._jobs.get_by_document(document_id)
            if document_id in self._inflight:
                return job if job is not None else self._create_job(document_id)

            if job is None:
                job = self._create_job(document_id)
            else:
                job.reset_for_requeue()
                self._jobs.update(job)

            self._mark_document_pending(document_id)
            self._inflight.add(document_id)
            await self._queue.put(document_id)
            return job

    async def retry(self, job_id: str) -> IndexingJob:
        """Re-queue a job, counting it as a retry."""
        job = self._jobs.get(job_id)  # raises IndexingJobNotFoundError
        async with self._lock:
            job.register_retry()
            self._jobs.update(job)
        return await self.enqueue(job.document_id)

    async def recover(self) -> int:
        """Re-enqueue jobs left pending or running by a previous process."""
        requeued = 0
        for job in self._jobs.list():
            if job.status in (JobStatus.PENDING, JobStatus.RUNNING):
                await self.enqueue(job.document_id)
                requeued += 1
        return requeued

    async def wait_for_idle(self) -> None:
        """Block until all queued work has been processed (test/support helper)."""
        await self._queue.join()

    # --- internals ---

    def _create_job(self, document_id: str) -> IndexingJob:
        job = IndexingJob.create(document_id=document_id)
        self._jobs.add(job)
        return job

    def _mark_document_pending(self, document_id: str) -> None:
        try:
            document = self._documents.get(document_id)
        except DocumentNotFoundError:
            return
        if document.status is DocumentStatus.PENDING:
            return
        if can_transition(document.status, DocumentStatus.PENDING):
            document.mark_pending(now=self._clock.now())
            self._documents.update(document)

    async def _worker_loop(self) -> None:
        while True:
            document_id = await self._queue.get()
            try:
                await self._process(document_id)
            except asyncio.CancelledError:
                raise
            except Exception:  # pragma: no cover - defensive; errors recorded on job
                logger.exception("Unexpected error indexing %s", document_id)
            finally:
                self._queue.task_done()
                async with self._lock:
                    self._inflight.discard(document_id)

    async def _process(self, document_id: str) -> None:
        job = self._jobs.get_by_document(document_id)
        if job is None:
            return

        job.start(now=self._clock.now())
        self._jobs.update(job)

        def on_progress(value: float) -> None:
            job.update_progress(value)
            self._jobs.update(job)

        try:
            await asyncio.to_thread(
                self._index.execute, document_id, progress=on_progress
            )
            job.complete(now=self._clock.now())
            self._jobs.update(job)
        except Exception as exc:
            job.fail(
                now=self._clock.now(),
                error_message=str(exc) or exc.__class__.__name__,
            )
            self._jobs.update(job)
