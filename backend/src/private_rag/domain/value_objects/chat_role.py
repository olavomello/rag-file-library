"""Chat message roles."""

from __future__ import annotations

from enum import StrEnum


class ChatRole(StrEnum):
    """Role of a participant in a chat conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
