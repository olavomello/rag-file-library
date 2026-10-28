"""Registry that selects a parser by file extension."""

from __future__ import annotations

from pathlib import Path

from private_rag.application.dto.parsing import ParsedDocument
from private_rag.application.exceptions import UnsupportedParserError
from private_rag.application.ports.ocr import OcrProvider
from private_rag.application.ports.parser import DocumentParser
from private_rag.infrastructure.parsers.docx_parser import DocxParser
from private_rag.infrastructure.parsers.image_parser import (
    SUPPORTED_IMAGE_EXTENSIONS,
    ImageParser,
)
from private_rag.infrastructure.parsers.pdf_parser import PdfParser
from private_rag.infrastructure.parsers.text_parser import PlainTextParser


class ParserRegistry:
    """Maps file extensions to concrete parsers.

    When an :class:`OcrProvider` is supplied, image extensions are registered and
    the PDF parser gains an OCR fallback for scanned pages. OCR itself remains
    opt-in via ``ocr_enabled``; with it off a scanned PDF or image raises
    :class:`NoExtractableTextError` exactly as before.
    """

    def __init__(
        self, *, ocr: OcrProvider | None = None, ocr_enabled: bool = False
    ) -> None:
        text_parser = PlainTextParser()
        self._parsers: dict[str, DocumentParser] = {
            ".txt": text_parser,
            ".md": text_parser,
            ".docx": DocxParser(),
            ".pdf": PdfParser(ocr, ocr_enabled=ocr_enabled),
        }
        if ocr is not None:
            image_parser = ImageParser(ocr, ocr_enabled=ocr_enabled)
            for extension in SUPPORTED_IMAGE_EXTENSIONS:
                self._parsers[extension] = image_parser

    def parse(self, file_path: Path, extension: str) -> ParsedDocument:
        parser = self._parsers.get(extension.lower())
        if parser is None:
            raise UnsupportedParserError(extension)
        return parser.parse(file_path)
