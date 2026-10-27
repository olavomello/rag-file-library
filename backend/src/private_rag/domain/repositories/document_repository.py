"""Repository contract for document registry metadata persistence."""

from __future__ import annotations

from typing import Protocol

from private_rag.domain.entities.document import Document
from private_rag.domain.value_objects.document_status import DocumentStatus


class DocumentRepository(Protocol):
    """Persists and retrieves :class:`Document` metadata.

    Implementations must raise :class:`DocumentNotFoundError` from ``get`` and
    ``update`` when the document does not exist, and :class:`DuplicateDocumentError`
    from ``add`` when a document with the same id already exists.
    """

    def add(self, document: Document) -> None: ...

    def get(self, document_id: str) -> Document: ...

    def get_by_checksum(self, checksum: str) -> Document | None: ...

    def list(
        self,
        *,
        status: DocumentStatus | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Document]: ...

    def update(self, document: Document) -> None: ...

    def delete(self, document_id: str) -> None: ...

    def count(self, *, status: DocumentStatus | None = None) -> int: ...
