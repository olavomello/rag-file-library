"""Domain-level exceptions.

These express business-rule violations and are independent of any framework,
transport, or storage technology.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain errors."""


class DomainValidationError(DomainError):
    """Raised when an entity or value object violates an invariant."""


class InvalidStateTransitionError(DomainError):
    """Raised when an entity is moved between incompatible lifecycle states."""

    def __init__(self, entity: str, source: str, target: str) -> None:
        self.entity = entity
        self.source = source
        self.target = target
        super().__init__(
            f"Invalid {entity} state transition: {source!r} -> {target!r}"
        )


class DocumentNotFoundError(DomainError):
    """Raised when a document cannot be found in a repository."""

    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        super().__init__(f"Document not found: {document_id}")


class DuplicateDocumentError(DomainError):
    """Raised when attempting to persist a document that already exists."""

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"Document already exists: {identifier}")


class IndexingJobNotFoundError(DomainError):
    """Raised when an indexing job cannot be found in a repository."""

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Indexing job not found: {job_id}")
