"""Upload validation: file type, size, content signature, and text encoding.

Client-supplied filenames and content types are never trusted for filesystem
paths; only the extension (used to select a parser) and the raw bytes are
inspected here.
"""

from __future__ import annotations

from dataclasses import dataclass

from private_rag.application.exceptions import (
    EmptyDocumentError,
    FileTooLargeError,
    InvalidFileContentError,
    UnsupportedFileTypeError,
)

# Supported extensions mapped to their canonical MIME type.
SUPPORTED_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".tiff": "image/tiff",
    ".bmp": "image/bmp",
    ".webp": "image/webp",
}

_TEXT_EXTENSIONS = frozenset({".txt", ".md"})
_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"})


@dataclass(frozen=True, slots=True)
class ValidatedUpload:
    """The validated, trusted facts derived from an upload."""

    extension: str
    mime_type: str


def extract_extension(filename: str) -> str:
    """Return the lowercase extension (including the dot) of ``filename``."""
    name = filename.strip().lower()
    dot = name.rfind(".")
    if dot <= 0 or dot == len(name) - 1:
        return ""
    return name[dot:]


def _check_signature(extension: str, data: bytes) -> None:
    if extension == ".pdf":
        if not data.startswith(b"%PDF-"):
            raise InvalidFileContentError("File does not look like a valid PDF")
    elif extension == ".docx":
        # DOCX is a ZIP container.
        if not data.startswith(b"PK\x03\x04"):
            raise InvalidFileContentError("File does not look like a valid DOCX")
    elif extension in _TEXT_EXTENSIONS:
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise InvalidFileContentError("Text file is not valid UTF-8") from exc
        if not text.strip():
            raise EmptyDocumentError("Text file has no readable content")
    elif extension in _IMAGE_EXTENSIONS:
        _check_image_signature(extension, data)


def _check_image_signature(extension: str, data: bytes) -> None:
    """Validate an image's magic bytes. Images are binary: no UTF-8 check."""
    if extension == ".png":
        valid = data.startswith(b"\x89PNG\r\n\x1a\n")
    elif extension in (".jpg", ".jpeg"):
        valid = data.startswith(b"\xff\xd8\xff")
    elif extension == ".bmp":
        valid = data.startswith(b"BM")
    elif extension == ".tiff":
        valid = data.startswith(b"II*\x00") or data.startswith(b"MM\x00*")
    elif extension == ".webp":
        valid = len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    else:  # pragma: no cover - unreachable, kept for exhaustiveness
        valid = False
    if not valid:
        raise InvalidFileContentError(
            f"File does not look like a valid {extension.lstrip('.').upper()} image"
        )


def validate_upload(filename: str, data: bytes, *, max_size_bytes: int) -> ValidatedUpload:
    """Validate an uploaded file and return its trusted type facts.

    Raises an :class:`ApplicationError` subclass on any validation failure.
    """
    extension = extract_extension(filename)
    if extension not in SUPPORTED_TYPES:
        raise UnsupportedFileTypeError(extension or filename)

    if len(data) == 0:
        raise EmptyDocumentError("Uploaded file is empty")
    if len(data) > max_size_bytes:
        raise FileTooLargeError(len(data), max_size_bytes)

    _check_signature(extension, data)

    return ValidatedUpload(extension=extension, mime_type=SUPPORTED_TYPES[extension])
