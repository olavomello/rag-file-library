"""Port for document parsers."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from private_rag.application.dto.parsing import ParsedDocument


class DocumentParser(Protocol):
    """Extracts text content (and page structure where available) from a file."""

    def parse(self, file_path: Path) -> ParsedDocument:
        """Parse the file at ``file_path`` into a :class:`ParsedDocument`.

        Implementations raise :class:`DocumentExtractionError` for corrupted files
        and :class:`NoExtractableTextError` when the file contains no usable text
        (for example a scanned PDF with no text layer).
        """
        ...


class DocumentParserRegistry(Protocol):
    """Selects and runs the correct parser for a file's extension."""

    def parse(self, file_path: Path, extension: str) -> ParsedDocument:
        """Parse ``file_path`` using the parser registered for ``extension``.

        Raises :class:`UnsupportedParserError` when no parser is registered.
        """
        ...
