"""Document lifecycle status and valid transitions."""

from __future__ import annotations

from enum import StrEnum


class DocumentStatus(StrEnum):
    """Lifecycle states of a document."""

    UPLOADED = "uploaded"
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
    DELETING = "deleting"


# Allowed transitions between states.
#   uploaded   -> pending (queued), failed, deleting
#   pending    -> processing, failed, deleting
#   processing -> indexed, failed, deleting
#   indexed    -> pending (reindex), deleting
#   failed     -> pending (retry), deleting
#   deleting   -> (terminal)
_VALID_TRANSITIONS: dict[DocumentStatus, frozenset[DocumentStatus]] = {
    DocumentStatus.UPLOADED: frozenset(
        {DocumentStatus.PENDING, DocumentStatus.FAILED, DocumentStatus.DELETING}
    ),
    DocumentStatus.PENDING: frozenset(
        {DocumentStatus.PROCESSING, DocumentStatus.FAILED, DocumentStatus.DELETING}
    ),
    DocumentStatus.PROCESSING: frozenset(
        {
            DocumentStatus.INDEXED,
            DocumentStatus.FAILED,
            DocumentStatus.DELETING,
            DocumentStatus.PENDING,  # re-queued after an interrupted run (recovery)
        }
    ),
    DocumentStatus.INDEXED: frozenset(
        {DocumentStatus.PENDING, DocumentStatus.DELETING}
    ),
    DocumentStatus.FAILED: frozenset(
        {DocumentStatus.PENDING, DocumentStatus.DELETING}
    ),
    DocumentStatus.DELETING: frozenset(),
}


def allowed_transitions(status: DocumentStatus) -> frozenset[DocumentStatus]:
    """Return the set of states reachable from ``status``."""
    return _VALID_TRANSITIONS[status]


def can_transition(source: DocumentStatus, target: DocumentStatus) -> bool:
    """Return whether moving from ``source`` to ``target`` is permitted."""
    return target in _VALID_TRANSITIONS[source]


def is_terminal(status: DocumentStatus) -> bool:
    """Return whether no further transitions are allowed from ``status``."""
    return len(_VALID_TRANSITIONS[status]) == 0
