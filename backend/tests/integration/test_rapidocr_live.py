"""Live verification against the real RapidOCR engine (skipped when unavailable).

This runs only when ``rapidocr-onnxruntime`` is importable and its models load, so
machines without the package (or without the model weights) skip it. It verifies
the real adapter end to end on a rendered-text image, mirroring the live-Ollama
skip pattern.
"""

from __future__ import annotations

import pymupdf
import pytest

pytestmark = pytest.mark.requires_ocr


def _render_text_png(text: str) -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 100), text, fontsize=28)
    png: bytes = page.get_pixmap(dpi=200).tobytes("png")
    document.close()
    return png


def test_real_rapidocr_reads_rendered_text() -> None:
    try:
        from private_rag.infrastructure.ocr.rapidocr_provider import RapidOcrProvider
    except Exception as exc:  # pragma: no cover - import guard
        pytest.skip(f"rapidocr-onnxruntime is not importable: {exc}")

    provider = RapidOcrProvider()
    try:
        text = provider.image_to_text(_render_text_png("Vacation Policy"))
    except Exception as exc:  # pragma: no cover - engine/model unavailable
        pytest.skip(f"RapidOCR engine is not available: {exc}")

    assert "vacation" in text.lower()
    assert "policy" in text.lower()
