"""DocumentChunk entity."""

from __future__ import annotations

from dataclasses import dataclass, field

from private_rag.domain.exceptions import DomainValidationError


@dataclass(slots=True, frozen=True)
class DocumentChunk:
    """A contiguous, searchable fragment of a document's text."""

    id: str
    document_id: str
    content: str
    chunk_index: int
    token_count: int
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise DomainValidationError("DocumentChunk.id must not be empty")
        if not self.document_id:
            raise DomainValidationError("DocumentChunk.document_id must not be empty")
        if not self.content:
            raise DomainValidationError("DocumentChunk.content must not be empty")
        if self.chunk_index < 0:
            raise DomainValidationError("DocumentChunk.chunk_index must not be negative")
        if self.token_count < 0:
            raise DomainValidationError("DocumentChunk.token_count must not be negative")

    @property
    def page_number(self) -> int | None:
        """Convenience accessor for the page number stored in metadata, if any."""
        raw = self.metadata.get("page_number")
        if raw is None or raw == "":
            return None
        try:
            return int(raw)
        except ValueError:
            return None
