"""Request/response schemas for semantic search."""

from __future__ import annotations

from pydantic import BaseModel, Field

from private_rag.domain.entities.search_result import SearchResult


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=50)
    document_ids: list[str] | None = None


class SearchResultResponse(BaseModel):
    document_id: str
    document_name: str
    chunk_id: str
    excerpt: str
    distance: float
    page_number: int | None = None
    metadata: dict[str, str] = {}

    @classmethod
    def from_entity(cls, result: SearchResult) -> SearchResultResponse:
        return cls(
            document_id=result.document_id,
            document_name=result.document_name,
            chunk_id=result.chunk_id,
            excerpt=result.content,
            distance=result.distance,
            page_number=result.page_number,
            metadata=result.metadata,
        )


class SemanticSearchResponse(BaseModel):
    query: str
    count: int
    results: list[SearchResultResponse]
