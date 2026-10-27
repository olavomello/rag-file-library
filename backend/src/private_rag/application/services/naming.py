"""Safe internal filename generation and validation (pure policy).

Lives in the application layer so use cases and infrastructure both depend on it
inward; it performs no I/O.
"""

from __future__ import annotations

import re

SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
_EXTENSION_RE = re.compile(r"^\.[A-Za-z0-9]+$")


class UnsafeStoredNameError(ValueError):
    """Raised when a stored filename is unsafe for use on the filesystem."""


def validate_stored_name(stored_name: str) -> str:
    """Validate that ``stored_name`` is a safe single-path-segment filename."""
    if not stored_name or stored_name in {".", ".."}:
        raise UnsafeStoredNameError(f"Unsafe stored name: {stored_name!r}")
    if not SAFE_NAME_RE.match(stored_name):
        raise UnsafeStoredNameError(
            f"Stored name contains illegal characters: {stored_name!r}"
        )
    return stored_name


def build_stored_name(document_id: str, extension: str) -> str:
    """Build a safe internal filename from a document id and extension.

    The client-supplied original filename is never used as a path; only the
    server-generated document id and a validated extension are.
    """
    if not SAFE_NAME_RE.match(document_id):
        raise UnsafeStoredNameError(f"Unsafe document id: {document_id!r}")

    ext = extension.lower()
    if ext and not ext.startswith("."):
        ext = f".{ext}"
    if ext and not _EXTENSION_RE.match(ext):
        raise UnsafeStoredNameError(f"Unsafe extension: {extension!r}")

    return f"{document_id}{ext}"
