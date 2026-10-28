"""Unit tests for OCR-backed parsing: image parser and PDF OCR fallback.

These use a fake :class:`OcrProvider` so they are deterministic and do not require
the real RapidOCR engine. The real adapter is exercised by the opt-in live test.
"""

from __future__ import annotations

from pathlib import Path

import pymupdf
import pytest

from private_rag.application.exceptions import NoExtractableTextError
from private_rag.infrastructure.parsers.image_parser import ImageParser
from private_rag.infrastructure.parsers.pdf_parser import PdfParser


class FakeOcrProvider:
    """Returns a preset text for any image, recording how often it is called."""

    def __init__(self, text: str) -> None:
        self._text = text
        self.calls = 0

    def image_to_text(self, image_png: bytes) -> str:
        self.calls += 1
        return self._text


def _write_png(path: Path) -> None:
    """Write a tiny valid PNG so the parser has real bytes to read."""
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 4, 4), False)
    pix.clear_with(255)
    path.write_bytes(pix.tobytes("png"))


class TestImageParser:
    def test_extracts_text_when_ocr_enabled(self, tmp_path: Path) -> None:
        path = tmp_path / "scan.png"
        _write_png(path)
        ocr = FakeOcrProvider("Vacation policy details")

        result = ImageParser(ocr, ocr_enabled=True).parse(path)

        assert ocr.calls == 1
        assert result.blocks[0].text == "Vacation policy details"
        assert result.blocks[0].page_number == 1

    def test_raises_when_ocr_disabled(self, tmp_path: Path) -> None:
        path = tmp_path / "scan.png"
        _write_png(path)
        ocr = FakeOcrProvider("should not be read")

        with pytest.raises(NoExtractableTextError):
            ImageParser(ocr, ocr_enabled=False).parse(path)
        assert ocr.calls == 0

    def test_raises_when_ocr_returns_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "scan.png"
        _write_png(path)
        ocr = FakeOcrProvider("   \n\t  ")

        with pytest.raises(NoExtractableTextError):
            ImageParser(ocr, ocr_enabled=True).parse(path)


def _scanned_pdf(path: Path) -> None:
    """Create a single-page PDF with no text layer (a scanned-like page)."""
    document = pymupdf.open()
    document.new_page()  # empty page: page.get_text("text") == ""
    document.save(str(path))
    document.close()


class TestPdfOcrFallback:
    def test_ocr_fallback_extracts_text_from_scanned_pdf(self, tmp_path: Path) -> None:
        path = tmp_path / "scanned.pdf"
        _scanned_pdf(path)
        ocr = FakeOcrProvider("Recovered scanned text")

        result = PdfParser(ocr, ocr_enabled=True).parse(path)

        assert ocr.calls == 1
        assert result.blocks[0].page_number == 1
        assert "Recovered scanned text" in result.blocks[0].text

    def test_scanned_pdf_still_raises_when_ocr_disabled(self, tmp_path: Path) -> None:
        path = tmp_path / "scanned.pdf"
        _scanned_pdf(path)
        ocr = FakeOcrProvider("never used")

        with pytest.raises(NoExtractableTextError):
            PdfParser(ocr, ocr_enabled=False).parse(path)
        assert ocr.calls == 0

    def test_text_pdf_does_not_invoke_ocr(self, tmp_path: Path) -> None:
        path = tmp_path / "text.pdf"
        document = pymupdf.open()
        page = document.new_page()
        page.insert_text((72, 72), "Real text layer content")
        document.save(str(path))
        document.close()
        ocr = FakeOcrProvider("should not run")

        result = PdfParser(ocr, ocr_enabled=True).parse(path)

        assert ocr.calls == 0
        assert "Real text layer content" in result.text
