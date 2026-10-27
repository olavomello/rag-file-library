"""Use case: list documents, optionally filtered by status."""

from __future__ import annotations

from private_rag.domain.entities.document import Document
from private_rag.domain.repositories.document_repository import DocumentRepository
from private_rag.domain.value_objects.document_status import DocumentStatus


class ListDocumentsUseCase:
    def __init__(self, *, documents: DocumentRepository) -> None:
        self._documents = documents

    def execute(
        self,
        *,
        status: DocumentStatus | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Document]:
        return self._documents.list(status=status, limit=limit, offset=offset)
