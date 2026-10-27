"""Application-level errors (use-case / input validation failures).

These are distinct from domain errors: they describe problems with a request to
the application layer and map to client-facing HTTP status codes in presentation.
"""

from __future__ import annotations


class ApplicationError(Exception):
    """Base class for application-layer errors."""


class UnsupportedFileTypeError(ApplicationError):
    """Raised when an uploaded file's type is not supported."""

    def __init__(self, extension: str) -> None:
        self.extension = extension
        super().__init__(f"Unsupported file type: {extension!r}")


class FileTooLargeError(ApplicationError):
    """Raised when an uploaded file exceeds the configured maximum size."""

    def __init__(self, size_bytes: int, max_bytes: int) -> None:
        self.size_bytes = size_bytes
        self.max_bytes = max_bytes
        super().__init__(
            f"File is too large: {size_bytes} bytes (maximum {max_bytes} bytes)"
        )


class EmptyDocumentError(ApplicationError):
    """Raised when an uploaded file is empty or has no usable content."""


class InvalidFileContentError(ApplicationError):
    """Raised when a file's content does not match its declared/expected type."""
