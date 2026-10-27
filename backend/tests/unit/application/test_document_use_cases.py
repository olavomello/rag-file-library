"""Unit tests for document use cases using in-memory fakes."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from private_rag.application.exceptions import UnsupportedFileTypeError
from private_rag.application.use_cases.documents.delete_document import (
    DeleteDocumentUseCase,
)
from private_rag.application.use_cases.documents.upload_document import (
    UploadDocumentUseCase,
)
from private_rag.domain.entities.document import Document
from private_rag.domain.entities.indexing_job import IndexingJob
from private_rag.domain.exceptions import DocumentNotFoundError, DuplicateDocumentError
from private_rag.domain.value_objects.document_status import DocumentStatus

NOW = datetime(2026, 3, 1, 8, 0, tzinfo=UTC)


class FakeDocumentRepository:
    def __init__(self) -> None:
        self.by_id: dict[str, Document] = {}

    def add(self, document: Document) -> None:
        if document.id in self.by_id:
            raise DuplicateDocumentError(document.id)
        self.by_id[document.id] = document

    def get(self, document_id: str) -> Document:
        if document_id not in self.by_id:
            raise DocumentNotFoundError(document_id)
        return self.by_id[document_id]

    def get_by_checksum(self, checksum: str) -> Document | None:
        return next(
            (d for d in self.by_id.values() if d.checksum_sha256 == checksum), None
        )

    def list(self, *, status=None, limit=None, offset=0):  # type: ignore[no-untyped-def]
        docs = [d for d in self.by_id.values() if status is None or d.status is status]
        return docs[offset : (offset + limit) if limit is not None else None]

    def update(self, document: Document) -> None:
        self.by_id[document.id] = document

    def delete(self, document_id: str) -> None:
        self.by_id.pop(document_id, None)

    def count(self, *, status=None) -> int:  # type: ignore[no-untyped-def]
        return len(self.by_id)


class FailingAddRepository(FakeDocumentRepository):
    def add(self, document: Document) -> None:
        raise RuntimeError("registry is down")


class FakeChunkRepository:
    def __init__(self) -> None:
        self.deleted: list[str] = []

    def add_chunks(self, chunks, embeddings, *, embedding_model) -> None:  # type: ignore[no-untyped-def]
        raise NotImplementedError

    def query(self, embedding, *, top_k, document_ids=None):  # type: ignore[no-untyped-def]
        return []

    def delete_by_document(self, document_id: str) -> None:
        self.deleted.append(document_id)

    def count(self, *, document_id=None) -> int:  # type: ignore[no-untyped-def]
        return 0


class FakeJobRepository:
    def __init__(self) -> None:
        self.by_id: dict[str, IndexingJob] = {}

    def add(self, job: IndexingJob) -> None:
        self.by_id[job.id] = job

    def get(self, job_id: str) -> IndexingJob:
        return self.by_id[job_id]

    def get_by_document(self, document_id: str) -> IndexingJob | None:
        return next(
            (j for j in self.by_id.values() if j.document_id == document_id), None
        )

    def list(self, *, status=None):  # type: ignore[no-untyped-def]
        return list(self.by_id.values())

    def update(self, job: IndexingJob) -> None:
        self.by_id[job.id] = job

    def delete(self, job_id: str) -> None:
        self.by_id.pop(job_id, None)


class FakeFileStore:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    def save(self, stored_name: str, data: bytes) -> Path:
        self.files[stored_name] = data
        return Path(stored_name)

    def read(self, stored_name: str) -> bytes:
        return self.files[stored_name]

    def exists(self, stored_name: str) -> bool:
        return stored_name in self.files

    def delete(self, stored_name: str) -> None:
        self.files.pop(stored_name, None)

    def path_for(self, stored_name: str) -> Path:
        return Path(stored_name)


class FixedClock:
    def now(self) -> datetime:
        return NOW


class TestUploadDocument:
    def test_stores_new_document(self) -> None:
        documents = FakeDocumentRepository()
        storage = FakeFileStore()
        use_case = UploadDocumentUseCase(
            documents=documents, storage=storage, clock=FixedClock(), max_upload_size_bytes=1024
        )

        result = use_case.execute(filename="notes.txt", data=b"hello world")

        assert result.is_duplicate is False
        assert result.document.status is DocumentStatus.UPLOADED
        assert result.document.original_name == "notes.txt"
        assert result.document.id in documents.by_id
        assert len(storage.files) == 1
        # Stored name is the server-generated id, never the client filename.
        stored_name = next(iter(storage.files))
        assert stored_name != "notes.txt"
        assert stored_name.endswith(".txt")

    def test_duplicate_content_returns_existing(self) -> None:
        documents = FakeDocumentRepository()
        storage = FakeFileStore()
        use_case = UploadDocumentUseCase(
            documents=documents, storage=storage, clock=FixedClock(), max_upload_size_bytes=1024
        )

        first = use_case.execute(filename="a.txt", data=b"same bytes")
        second = use_case.execute(filename="different-name.txt", data=b"same bytes")

        assert second.is_duplicate is True
        assert second.document.id == first.document.id
        assert len(storage.files) == 1  # no second copy stored

    def test_unsupported_type_rejected_before_storage(self) -> None:
        storage = FakeFileStore()
        use_case = UploadDocumentUseCase(
            documents=FakeDocumentRepository(),
            storage=storage,
            clock=FixedClock(),
            max_upload_size_bytes=1024,
        )

        with pytest.raises(UnsupportedFileTypeError):
            use_case.execute(filename="malware.exe", data=b"MZ...")

        assert storage.files == {}

    def test_registry_failure_rolls_back_stored_file(self) -> None:
        storage = FakeFileStore()
        use_case = UploadDocumentUseCase(
            documents=FailingAddRepository(),
            storage=storage,
            clock=FixedClock(),
            max_upload_size_bytes=1024,
        )

        with pytest.raises(RuntimeError):
            use_case.execute(filename="notes.txt", data=b"content")

        assert storage.files == {}  # orphan file cleaned up


class TestDeleteDocument:
    def _seed(
        self,
    ) -> tuple[FakeDocumentRepository, FakeChunkRepository, FakeJobRepository, FakeFileStore]:
        documents = FakeDocumentRepository()
        chunks = FakeChunkRepository()
        jobs = FakeJobRepository()
        storage = FakeFileStore()
        doc = Document.create(
            original_name="a.txt",
            stored_name="doc-1.txt",
            mime_type="text/plain",
            extension=".txt",
            size_bytes=4,
            checksum_sha256="a" * 64,
            now=NOW,
            document_id="doc-1",
        )
        documents.add(doc)
        storage.save("doc-1.txt", b"data")
        jobs.add(IndexingJob.create(document_id="doc-1", job_id="job-1"))
        return documents, chunks, jobs, storage

    def test_deletes_all_derived_data(self) -> None:
        documents, chunks, jobs, storage = self._seed()
        use_case = DeleteDocumentUseCase(
            documents=documents, chunks=chunks, jobs=jobs, storage=storage
        )

        use_case.execute("doc-1")

        assert "doc-1" not in documents.by_id
        assert chunks.deleted == ["doc-1"]
        assert storage.files == {}
        assert jobs.get_by_document("doc-1") is None

    def test_delete_missing_raises(self) -> None:
        documents, chunks, jobs, storage = self._seed()
        use_case = DeleteDocumentUseCase(
            documents=documents, chunks=chunks, jobs=jobs, storage=storage
        )

        with pytest.raises(DocumentNotFoundError):
            use_case.execute("missing")
