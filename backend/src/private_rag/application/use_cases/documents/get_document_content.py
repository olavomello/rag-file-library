"""Use case: return the extracted text content of a document."""

from __future__ import annotations

from private_rag.application.ports.file_store import FileStore
from private_rag.application.ports.parser import DocumentParserRegistry
from private_rag.domain.repositories.document_repository import DocumentRepository


class GetDocumentContentUseCase:
    """Parses a stored document on demand and returns its extracted text."""

    def __init__(
        self,
        *,
        documents: DocumentRepository,
        storage: FileStore,
        parser: DocumentParserRegistry,
    ) -> None:
        self._documents = documents
        self._storage = storage
        self._parser = parser

    def execute(self, document_id: str) -> str:
        document = self._documents.get(document_id)  # raises DocumentNotFoundError
        parsed = self._parser.parse(
            self._storage.path_for(document.stored_name), document.extension
        )
        return parsed.text
