"""Domain exceptions package."""

from __future__ import annotations

from private_rag.domain.exceptions.errors import (
    DocumentNotFoundError,
    DomainError,
    DomainValidationError,
    DuplicateDocumentError,
    IndexingJobNotFoundError,
    InvalidStateTransitionError,
)

__all__ = [
    "DocumentNotFoundError",
    "DomainError",
    "DomainValidationError",
    "DuplicateDocumentError",
    "IndexingJobNotFoundError",
    "InvalidStateTransitionError",
]
