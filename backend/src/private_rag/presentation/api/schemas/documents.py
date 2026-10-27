"""Response schemas for document endpoints.

Internal filesystem paths and stored filenames are deliberately excluded.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from private_rag.domain.entities.document import Document


class DocumentResponse(BaseModel):
    id: str
    original_name: str
    mime_type: str
    extension: str
    size_bytes: int
    checksum_sha256: str
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime
    indexed_at: datetime | None = None
    error_message: str | None = None

    @classmethod
    def from_entity(cls, document: Document) -> DocumentResponse:
        return cls(
            id=document.id,
            original_name=document.original_name,
            mime_type=document.mime_type,
            extension=document.extension,
            size_bytes=document.size_bytes,
            checksum_sha256=document.checksum_sha256,
            status=document.status.value,
            chunk_count=document.chunk_count,
            created_at=document.created_at,
            updated_at=document.updated_at,
            indexed_at=document.indexed_at,
            error_message=document.error_message,
        )


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int


class UploadResponse(BaseModel):
    document: DocumentResponse
    is_duplicate: bool


class DocumentContentResponse(BaseModel):
    document_id: str
    content: str
    char_count: int
