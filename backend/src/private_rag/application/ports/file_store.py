"""Port for storing and retrieving original document bytes."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class FileStore(Protocol):
    """Persists original uploaded files under safe internal names."""

    def save(self, stored_name: str, data: bytes) -> Path: ...

    def read(self, stored_name: str) -> bytes: ...

    def exists(self, stored_name: str) -> bool: ...

    def delete(self, stored_name: str) -> None: ...

    def path_for(self, stored_name: str) -> Path: ...
