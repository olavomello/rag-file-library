"""Registry that selects a parser by file extension."""

from __future__ import annotations

from pathlib import Path

from private_rag.application.dto.parsing import ParsedDocument
from private_rag.application.exceptions import UnsupportedParserError
from private_rag.application.ports.parser import DocumentParser
from private_rag.infrastructure.parsers.docx_parser import DocxParser
from private_rag.infrastructure.parsers.pdf_parser import PdfParser
from private_rag.infrastructure.parsers.text_parser import PlainTextParser


class ParserRegistry:
    """Maps file extensions to concrete parsers."""

    def __init__(self) -> None:
        text_parser = PlainTextParser()
        self._parsers: dict[str, DocumentParser] = {
            ".txt": text_parser,
            ".md": text_parser,
            ".docx": DocxParser(),
            ".pdf": PdfParser(),
        }

    def parse(self, file_path: Path, extension: str) -> ParsedDocument:
        parser = self._parsers.get(extension.lower())
        if parser is None:
            raise UnsupportedParserError(extension)
        return parser.parse(file_path)
