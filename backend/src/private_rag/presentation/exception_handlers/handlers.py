"""Maps domain/application errors to consistent HTTP responses."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from private_rag.application.exceptions import (
    ApplicationError,
    EmptyDocumentError,
    FileTooLargeError,
    InvalidFileContentError,
    UnsupportedFileTypeError,
)
from private_rag.domain.exceptions import (
    DocumentNotFoundError,
    DomainValidationError,
    IndexingJobNotFoundError,
)

# Each mapped exception type -> HTTP status code.
_STATUS_MAP: list[tuple[type[Exception], int]] = [
    (DocumentNotFoundError, status.HTTP_404_NOT_FOUND),
    (IndexingJobNotFoundError, status.HTTP_404_NOT_FOUND),
    (UnsupportedFileTypeError, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE),
    (FileTooLargeError, status.HTTP_413_CONTENT_TOO_LARGE),
    (EmptyDocumentError, status.HTTP_400_BAD_REQUEST),
    (InvalidFileContentError, status.HTTP_400_BAD_REQUEST),
    (DomainValidationError, status.HTTP_400_BAD_REQUEST),
    # Fallbacks (checked last).
    (ApplicationError, status.HTTP_400_BAD_REQUEST),
]


def _make_handler(status_code: int):  # type: ignore[no-untyped-def]
    async def handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    return handler


def register_exception_handlers(app: FastAPI) -> None:
    for exc_type, status_code in _STATUS_MAP:
        app.add_exception_handler(exc_type, _make_handler(status_code))
