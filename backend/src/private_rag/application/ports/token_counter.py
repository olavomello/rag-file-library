"""Port for counting tokens in text."""

from __future__ import annotations

from typing import Protocol


class TokenCounter(Protocol):
    """Counts the number of tokens in a piece of text."""

    def count(self, text: str) -> int: ...
