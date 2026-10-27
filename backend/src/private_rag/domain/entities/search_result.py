"""SearchResult entity returned by semantic search."""

from __future__ import annotations

from dataclasses import dataclass, field

from private_rag.domain.exceptions import DomainValidationError


@dataclass(slots=True, frozen=True)
class SearchResult:
    """A single ranked match from a semantic search.

    ``distance`` is the raw vector distance reported by the vector store (lower is
    closer). It must not be presented to users as a probability or confidence.
    """

    document_id: str
    document_name: str
    chunk_id: str
    content: str
    distance: float
    page_number: int | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.document_id:
            raise DomainValidationError("SearchResult.document_id must not be empty")
        if not self.chunk_id:
            raise DomainValidationError("SearchResult.chunk_id must not be empty")
        if self.distance < 0:
            raise DomainValidationError("SearchResult.distance must not be negative")
        if self.page_number is not None and self.page_number < 1:
            raise DomainValidationError("SearchResult.page_number must be >= 1 when set")
