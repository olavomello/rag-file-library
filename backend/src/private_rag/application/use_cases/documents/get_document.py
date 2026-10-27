"""Use case: fetch a single document by id."""

from __future__ import annotations

from private_rag.domain.entities.document import Document
from private_rag.domain.repositories.document_repository import DocumentRepository


class GetDocumentUseCase:
    def __init__(self, *, documents: DocumentRepository) -> None:
        self._documents = documents

    def execute(self, document_id: str) -> Document:
        """Return the document, or raise ``DocumentNotFoundError``."""
        return self._documents.get(document_id)
