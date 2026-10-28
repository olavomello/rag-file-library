"""PDF parser built on PyMuPDF (fitz), with optional OCR fallback."""

from __future__ import annotations

from pathlib import Path

import pymupdf  # PyMuPDF

from private_rag.application.dto.parsing import ParsedDocument, TextBlock
from private_rag.application.exceptions import (
    DocumentExtractionError,
    NoExtractableTextError,
)
from private_rag.application.ports.ocr import OcrProvider
from private_rag.application.services.text_normalization import normalize_text


class PdfParser:
    """Extracts text per page, preserving 1-based page numbers.

    The fast path reads the embedded text layer. When a page has no extractable
    text and OCR is enabled (and an :class:`OcrProvider` is supplied), that page is
    rasterised and run through OCR as a fallback. A document that still yields no
    text raises :class:`NoExtractableTextError` (the same behaviour as when OCR is
    off, e.g. a scanned PDF with OCR disabled).
    """

    def __init__(
        self, ocr: OcrProvider | None = None, *, ocr_enabled: bool = False
    ) -> None:
        self._ocr = ocr
        self._ocr_enabled = ocr_enabled

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
                if not normalized and self._ocr_enabled and self._ocr is not None:
                    normalized = self._ocr_page(page)
                if normalized:
                    blocks.append(TextBlock(text=normalized, page_number=index + 1))
        except Exception as exc:
            raise DocumentExtractionError(f"Could not read PDF pages: {exc}") from exc
        finally:
            document.close()

        if not blocks:
            raise NoExtractableTextError(
                "PDF has no extractable text (it may be scanned; enable OCR in Settings)"
            )

        return ParsedDocument(blocks=blocks)

    def _ocr_page(self, page: pymupdf.Page) -> str:
        assert self._ocr is not None  # guarded by caller
        png: bytes = page.get_pixmap().tobytes("png")
        return normalize_text(self._ocr.image_to_text(png))
