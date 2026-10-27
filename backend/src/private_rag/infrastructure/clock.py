"""System clock implementation of the :class:`Clock` port."""

from __future__ import annotations

from datetime import UTC, datetime


class SystemClock:
    """Returns the current UTC time."""

    def now(self) -> datetime:
        return datetime.now(UTC)
