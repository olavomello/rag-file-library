"""PDF parser built on PyMuPDF (fitz)."""

from __future__ import annotations

from pathlib import Path

import pymupdf  # PyMuPDF

from private_rag.application.dto.parsing import ParsedDocument, TextBlock
from private_rag.application.exceptions import (
    DocumentExtractionError,
    NoExtractableTextError,
)
from private_rag.application.services.text_normalization import normalize_text


class PdfParser:
    """Extracts text per page, preserving 1-based page numbers.

    No OCR is performed. A PDF whose pages contain no extractable text (e.g. a
    scanned document) raises :class:`NoExtractableTextError`.
    """

    def parse(self, file_path: Path) -> ParsedDocument:
        try:
            document = pymupdf.open(str(file_path))
        except Exception as exc:
            raise DocumentExtractionError(f"Could not open PDF: {exc}") from exc

        blocks: list[TextBlock] = []
        try:
            for index in range(document.page_count):
                page = document.load_page(index)
                normalized = normalize_text(page.get_text("text"))
                if normalized:
                    blocks.append(TextBlock(text=normalized, page_number=index + 1))
        except Exception as exc:
            raise DocumentExtractionError(f"Could not read PDF pages: {exc}") from exc
        finally:
            document.close()

        if not blocks:
            raise NoExtractableTextError(
                "PDF has no extractable text (it may be scanned; OCR is not supported)"
            )

        return ParsedDocument(blocks=blocks)
