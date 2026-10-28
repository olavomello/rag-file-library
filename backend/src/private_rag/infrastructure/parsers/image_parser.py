"""Image parser that extracts text via OCR.

Images carry no text layer, so extraction relies entirely on an injected
:class:`OcrProvider`. OCR is opt-in: when disabled the parser refuses images with a
clear, actionable message rather than silently producing empty documents.
"""

from __future__ import annotations

from pathlib import Path

from private_rag.application.dto.parsing import ParsedDocument, TextBlock
from private_rag.application.exceptions import (
    DocumentExtractionError,
    NoExtractableTextError,
)
from private_rag.application.ports.ocr import OcrProvider
from private_rag.application.services.text_normalization import normalize_text

SUPPORTED_IMAGE_EXTENSIONS = frozenset(
    {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
)


class ImageParser:
    """Extracts text from image files using OCR (single logical page)."""

    def __init__(self, ocr: OcrProvider, *, ocr_enabled: bool = False) -> None:
        self._ocr = ocr
        self._ocr_enabled = ocr_enabled

    def parse(self, file_path: Path) -> ParsedDocument:
        if not self._ocr_enabled:
            raise NoExtractableTextError(
                "Image OCR is disabled; enable OCR in Settings"
            )

        try:
            data = file_path.read_bytes()
        except OSError as exc:
            raise DocumentExtractionError(f"Could not read image: {exc}") from exc

        normalized = normalize_text(self._ocr.image_to_text(data))
        if not normalized:
            raise NoExtractableTextError("Image contains no recognisable text")

        return ParsedDocument(blocks=[TextBlock(text=normalized, page_number=1)])
