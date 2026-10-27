"""ChatMessage entity."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from private_rag.domain.exceptions import DomainValidationError
from private_rag.domain.value_objects.chat_role import ChatRole
from private_rag.domain.value_objects.source_reference import SourceReference


@dataclass(slots=True)
class ChatMessage:
    """A single message in a RAG chat conversation, optionally with sources."""

    id: str
    role: ChatRole
    content: str
    created_at: datetime
    sources: list[SourceReference] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.content:
            raise DomainValidationError("ChatMessage.content must not be empty")

    @classmethod
    def create(
        cls,
        *,
        role: ChatRole,
        content: str,
        now: datetime,
        sources: list[SourceReference] | None = None,
        message_id: str | None = None,
    ) -> ChatMessage:
        return cls(
            id=message_id or str(uuid.uuid4()),
            role=role,
            content=content,
            created_at=now,
            sources=list(sources) if sources else [],
        )
