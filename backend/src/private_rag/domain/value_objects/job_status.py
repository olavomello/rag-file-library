"""Indexing job status."""

from __future__ import annotations

from enum import StrEnum


class JobStatus(StrEnum):
    """Lifecycle states of an indexing job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


_TERMINAL = frozenset({JobStatus.COMPLETED, JobStatus.CANCELLED})


def is_terminal(status: JobStatus) -> bool:
    """Return whether a job in ``status`` has reached a terminal state."""
    return status in _TERMINAL
