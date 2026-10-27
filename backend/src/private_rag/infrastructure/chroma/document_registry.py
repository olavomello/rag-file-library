"""ChromaDB implementation of the document registry (metadata) repository.

The registry is used purely as a keyed metadata store (get by id, list, filter by
status/checksum) — never for semantic similarity — so each record carries a constant
one-dimensional placeholder embedding.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from private_rag.domain.entities.document import Document
from private_rag.domain.exceptions import DocumentNotFoundError, DuplicateDocumentError
from private_rag.domain.value_objects.document_status import DocumentStatus
from private_rag.infrastructure.chroma.client import ChromaClientProvider

_COLLECTION = "document_registry"
_PLACEHOLDER_EMBEDDING = [0.0]


def _serialize(document: Document) -> dict[str, str | int]:
    return {
        "id": document.id,
        "original_name": document.original_name,
        "stored_name": document.stored_name,
        "mime_type": document.mime_type,
        "extension": document.extension,
        "size_bytes": document.size_bytes,
        "checksum_sha256": document.checksum_sha256,
        "status": document.status.value,
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat(),
        "indexed_at": document.indexed_at.isoformat() if document.indexed_at else "",
        "chunk_count": document.chunk_count,
        "error_message": document.error_message or "",
        "knowledge_base_id": document.knowledge_base_id or "",
    }


def _deserialize(meta: dict[str, Any]) -> Document:
    indexed_at = meta.get("indexed_at") or ""
    error_message = meta.get("error_message") or ""
    knowledge_base_id = meta.get("knowledge_base_id") or ""
    return Document(
        id=str(meta["id"]),
        original_name=str(meta["original_name"]),
        stored_name=str(meta["stored_name"]),
        mime_type=str(meta["mime_type"]),
        extension=str(meta["extension"]),
        size_bytes=int(meta["size_bytes"]),
        checksum_sha256=str(meta["checksum_sha256"]),
        status=DocumentStatus(str(meta["status"])),
        created_at=datetime.fromisoformat(str(meta["created_at"])),
        updated_at=datetime.fromisoformat(str(meta["updated_at"])),
        indexed_at=datetime.fromisoformat(str(indexed_at)) if indexed_at else None,
        chunk_count=int(meta["chunk_count"]),
        error_message=str(error_message) if error_message else None,
        knowledge_base_id=str(knowledge_base_id) if knowledge_base_id else None,
    )


class ChromaDocumentRegistry:
    """Persists document metadata in a dedicated ChromaDB collection."""

    def __init__(self, provider: ChromaClientProvider) -> None:
        self._provider = provider

    def _collection(self) -> Any:
        return self._provider.get_or_create_collection(_COLLECTION, space="l2")

    def _exists(self, document_id: str) -> bool:
        got = self._collection().get(ids=[document_id], include=[])
        return len(got["ids"]) > 0

    def add(self, document: Document) -> None:
        if self._exists(document.id):
            raise DuplicateDocumentError(document.id)
        self._collection().add(
            ids=[document.id],
            embeddings=[_PLACEHOLDER_EMBEDDING],
            documents=[document.original_name],
            metadatas=[_serialize(document)],
        )

    def get(self, document_id: str) -> Document:
        got = self._collection().get(ids=[document_id], include=["metadatas"])
        metadatas = got["metadatas"]
        if not metadatas:
            raise DocumentNotFoundError(document_id)
        return _deserialize(metadatas[0])

    def get_by_checksum(self, checksum: str) -> Document | None:
        got = self._collection().get(
            where={"checksum_sha256": checksum}, include=["metadatas"]
        )
        metadatas = got["metadatas"]
        return _deserialize(metadatas[0]) if metadatas else None

    def list(
        self,
        *,
        status: DocumentStatus | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Document]:
        where = {"status": status.value} if status is not None else None
        got = self._collection().get(where=where, include=["metadatas"])
        documents = [_deserialize(meta) for meta in got["metadatas"]]
        documents.sort(key=lambda doc: doc.created_at, reverse=True)
        if offset:
            documents = documents[offset:]
        if limit is not None:
            documents = documents[:limit]
        return documents

    def update(self, document: Document) -> None:
        if not self._exists(document.id):
            raise DocumentNotFoundError(document.id)
        # Embeddings are passed explicitly here too: if omitted, ChromaDB would
        # re-embed the document text with its default model (an implicit download),
        # which this application must never trigger.
        self._collection().update(
            ids=[document.id],
            embeddings=[_PLACEHOLDER_EMBEDDING],
            documents=[document.original_name],
            metadatas=[_serialize(document)],
        )

    def delete(self, document_id: str) -> None:
        self._collection().delete(ids=[document_id])

    def count(self, *, status: DocumentStatus | None = None) -> int:
        where = {"status": status.value} if status is not None else None
        got = self._collection().get(where=where, include=[])
        return len(got["ids"])
