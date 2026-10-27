"""Use case: delete a document and all of its derived data."""

from __future__ import annotations

from private_rag.application.ports.file_store import FileStore
from private_rag.domain.repositories.chunk_repository import ChunkVectorRepository
from private_rag.domain.repositories.document_repository import DocumentRepository
from private_rag.domain.repositories.indexing_job_repository import (
    IndexingJobRepository,
)


class DeleteDocumentUseCase:
    """Removes a document's chunks, original file, job, and registry entry.

    The registry entry is removed last so that, if an earlier step fails, the
    document remains visible and the deletion can be retried.
    """

    def __init__(
        self,
        *,
        documents: DocumentRepository,
        chunks: ChunkVectorRepository,
        jobs: IndexingJobRepository,
        storage: FileStore,
    ) -> None:
        self._documents = documents
        self._chunks = chunks
        self._jobs = jobs
        self._storage = storage

    def execute(self, document_id: str) -> None:
        document = self._documents.get(document_id)  # raises DocumentNotFoundError

        self._chunks.delete_by_document(document_id)
        self._storage.delete(document.stored_name)

        job = self._jobs.get_by_document(document_id)
        if job is not None:
            self._jobs.delete(job.id)

        self._documents.delete(document_id)
