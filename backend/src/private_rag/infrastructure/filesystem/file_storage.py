"""Local filesystem storage for original uploaded documents."""

from __future__ import annotations

from pathlib import Path

from private_rag.infrastructure.filesystem.atomic import atomic_write_bytes
from private_rag.infrastructure.filesystem.naming import (
    UnsafeStoredNameError,
    validate_stored_name,
)


class FileStorage:
    """Stores and retrieves original document bytes under a base directory.

    All access is confined to the base directory: filenames are validated as safe
    single path segments and the resolved path is verified to stay within the base,
    preventing path traversal.
    """

    def __init__(self, base_dir: str | Path) -> None:
        self._base = Path(base_dir)

    def ensure_ready(self) -> None:
        self._base.mkdir(parents=True, exist_ok=True)

    def path_for(self, stored_name: str) -> Path:
        validate_stored_name(stored_name)
        candidate = self._base / stored_name
        base_resolved = self._base.resolve()
        resolved = candidate.resolve()
        if resolved != base_resolved and base_resolved not in resolved.parents:
            raise UnsafeStoredNameError(
                f"Stored name escapes the storage directory: {stored_name!r}"
            )
        return candidate

    def save(self, stored_name: str, data: bytes) -> Path:
        path = self.path_for(stored_name)
        atomic_write_bytes(path, data)
        return path

    def read(self, stored_name: str) -> bytes:
        return self.path_for(stored_name).read_bytes()

    def exists(self, stored_name: str) -> bool:
        return self.path_for(stored_name).is_file()

    def delete(self, stored_name: str) -> None:
        self.path_for(stored_name).unlink(missing_ok=True)
