"""Request/response schemas for RAG chat."""

from __future__ import annotations

from pydantic import BaseModel, Field

from private_rag.domain.value_objects.source_reference import SourceReference


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int | None = Field(default=None, ge=1, le=50)


class ChatSource(BaseModel):
    document_id: str
    document_name: str
    chunk_id: str
    page_number: int | None = None

    @classmethod
    def from_reference(cls, reference: SourceReference) -> ChatSource:
        return cls(
            document_id=reference.document_id,
            document_name=reference.document_name,
            chunk_id=reference.chunk_id,
            page_number=reference.page_number,
        )


class ChatResponse(BaseModel):
    answer: str
    grounded: bool
    sources: list[ChatSource]
