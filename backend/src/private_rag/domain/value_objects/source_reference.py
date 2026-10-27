"""Source reference value object linking an answer/result back to a document chunk."""

from __future__ import annotations

from dataclasses import dataclass

from private_rag.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class SourceReference:
    """An immutable reference to the document chunk that supports an answer."""

    document_id: str
    document_name: str
    chunk_id: str
    page_number: int | None = None

    def __post_init__(self) -> None:
        if not self.document_id:
            raise DomainValidationError("SourceReference.document_id must not be empty")
        if not self.chunk_id:
            raise DomainValidationError("SourceReference.chunk_id must not be empty")
        if self.page_number is not None and self.page_number < 1:
            raise DomainValidationError("SourceReference.page_number must be >= 1 when set")
