"""Unit tests for upload file validation."""

from __future__ import annotations

import pytest

from private_rag.application.exceptions import (
    EmptyDocumentError,
    FileTooLargeError,
    InvalidFileContentError,
    UnsupportedFileTypeError,
)
from private_rag.application.services.file_validation import (
    extract_extension,
    validate_upload,
)

MAX = 1024


class TestExtractExtension:
    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("report.PDF", ".pdf"),
            ("notes.md", ".md"),
            ("archive.tar.gz", ".gz"),
            ("noext", ""),
            (".hidden", ""),
            ("trailingdot.", ""),
        ],
    )
    def test_cases(self, filename: str, expected: str) -> None:
        assert extract_extension(filename) == expected


class TestValidateUpload:
    def test_accepts_valid_txt(self) -> None:
        result = validate_upload("a.txt", b"hello world", max_size_bytes=MAX)
        assert result.extension == ".txt"
        assert result.mime_type == "text/plain"

    def test_accepts_valid_pdf_signature(self) -> None:
        result = validate_upload("a.pdf", b"%PDF-1.7\n...", max_size_bytes=MAX)
        assert result.extension == ".pdf"

    def test_accepts_valid_docx_signature(self) -> None:
        result = validate_upload("a.docx", b"PK\x03\x04rest", max_size_bytes=MAX)
        assert result.mime_type.endswith("wordprocessingml.document")

    def test_rejects_unsupported_type(self) -> None:
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("a.exe", b"MZ", max_size_bytes=MAX)

    def test_rejects_empty(self) -> None:
        with pytest.raises(EmptyDocumentError):
            validate_upload("a.txt", b"", max_size_bytes=MAX)

    def test_rejects_too_large(self) -> None:
        with pytest.raises(FileTooLargeError):
            validate_upload("a.txt", b"x" * (MAX + 1), max_size_bytes=MAX)

    def test_rejects_pdf_with_wrong_signature(self) -> None:
        with pytest.raises(InvalidFileContentError):
            validate_upload("a.pdf", b"not a pdf", max_size_bytes=MAX)

    def test_rejects_non_utf8_text(self) -> None:
        with pytest.raises(InvalidFileContentError):
            validate_upload("a.txt", b"\xff\xfe\x00bad", max_size_bytes=MAX)

    def test_rejects_whitespace_only_text(self) -> None:
        with pytest.raises(EmptyDocumentError):
            validate_upload("a.md", b"   \n\t  ", max_size_bytes=MAX)
