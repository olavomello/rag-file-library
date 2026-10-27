"""Use case: upload and persist a new document."""

from __future__ import annotations

import uuid

from private_rag.application.dto.document import UploadResult
from private_rag.application.ports.clock import Clock
from private_rag.application.ports.file_store import FileStore
from private_rag.application.services.file_validation import validate_upload
from private_rag.application.services.naming import build_stored_name
from private_rag.domain.entities.document import Document
from private_rag.domain.repositories.document_repository import DocumentRepository
from private_rag.domain.services.hashing import sha256_hex


class UploadDocumentUseCase:
    """Validates, deduplicates, and stores an uploaded document.

    Duplicate detection is by SHA-256 checksum: re-uploading identical content
    returns the existing document instead of storing a second copy.
    """

    def __init__(
        self,
        *,
        documents: DocumentRepository,
        storage: FileStore,
        clock: Clock,
        max_upload_size_bytes: int,
    ) -> None:
        self._documents = documents
        self._storage = storage
        self._clock = clock
        self._max_upload_size_bytes = max_upload_size_bytes

    def execute(self, *, filename: str, data: bytes) -> UploadResult:
        validated = validate_upload(
            filename, data, max_size_bytes=self._max_upload_size_bytes
        )

        checksum = sha256_hex(data)
        existing = self._documents.get_by_checksum(checksum)
        if existing is not None:
            return UploadResult(document=existing, is_duplicate=True)

        document_id = str(uuid.uuid4())
        stored_name = build_stored_name(document_id, validated.extension)
        self._storage.save(stored_name, data)

        document = Document.create(
            original_name=filename.strip(),
            stored_name=stored_name,
            mime_type=validated.mime_type,
            extension=validated.extension,
            size_bytes=len(data),
            checksum_sha256=checksum,
            now=self._clock.now(),
            document_id=document_id,
        )

        try:
            self._documents.add(document)
        except Exception:
            # Roll back the stored file so a failed registry write leaves no orphan.
            self._storage.delete(stored_name)
            raise

        return UploadResult(document=document, is_duplicate=False)
