"""KnowledgeBase entity.

A single default knowledge base is used in V1; the entity exists so the rest of
the system can reference it and so multiple knowledge bases remain a non-breaking
future extension.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from private_rag.domain.exceptions import DomainValidationError


@dataclass(slots=True)
class KnowledgeBase:
    """A named collection of documents."""

    id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    document_count: int = 0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise DomainValidationError("KnowledgeBase.name must not be empty")
        if self.document_count < 0:
            raise DomainValidationError("KnowledgeBase.document_count must not be negative")

    @classmethod
    def create(
        cls,
        *,
        name: str,
        description: str = "",
        now: datetime,
        kb_id: str | None = None,
    ) -> KnowledgeBase:
        return cls(
            id=kb_id or str(uuid.uuid4()),
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
        )
