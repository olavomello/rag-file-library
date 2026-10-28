"""DTOs for RAG chat answers."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

from private_rag.domain.value_objects.source_reference import SourceReference


@dataclass(frozen=True, slots=True)
class ConversationTurn:
    """A prior message in the conversation, used to ground follow-up questions."""

    role: str  # "user" | "assistant"
    content: str


@dataclass(slots=True)
class Answer:
    """A complete grounded answer with its sources."""

    text: str
    sources: list[SourceReference] = field(default_factory=list)
    grounded: bool = True


@dataclass(slots=True)
class StreamedAnswer:
    """A streamed answer: sources resolved up front, then a token iterator."""

    sources: list[SourceReference]
    grounded: bool
    tokens: Iterator[str]
