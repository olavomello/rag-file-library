"""Request/response schemas for RAG chat."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from private_rag.domain.value_objects.source_reference import SourceReference


class ChatHistoryMessage(BaseModel):
    """A prior message in the conversation, sent so follow-ups stay on-subject."""

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int | None = Field(default=None, ge=1, le=50)
    history: list[ChatHistoryMessage] = Field(default_factory=list, max_length=20)


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
