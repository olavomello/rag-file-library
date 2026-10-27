"""Plain-text and Markdown parser (standard library only)."""

from __future__ import annotations

from pathlib import Path

from private_rag.application.dto.parsing import ParsedDocument, TextBlock
from private_rag.application.exceptions import (
    DocumentExtractionError,
    NoExtractableTextError,
)
from private_rag.application.services.text_normalization import normalize_text


class PlainTextParser:
    """Parses ``.txt`` and ``.md`` files as UTF-8 text."""

    def parse(self, file_path: Path) -> ParsedDocument:
        try:
            raw = file_path.read_bytes()
        except OSError as exc:
            raise DocumentExtractionError(f"Could not read file: {exc}") from exc

        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise DocumentExtractionError("File is not valid UTF-8 text") from exc

        normalized = normalize_text(text)
        if not normalized:
            raise NoExtractableTextError("Document has no readable text")

        return ParsedDocument(blocks=[TextBlock(text=normalized, page_number=None)])
