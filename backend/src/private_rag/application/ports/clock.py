"""Clock port, so use cases can obtain the current time deterministically."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Supplies the current time."""

    def now(self) -> datetime: ...
