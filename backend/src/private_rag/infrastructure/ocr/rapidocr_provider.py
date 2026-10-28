"""Local OCR adapter built on RapidOCR (ONNX Runtime, CPU-only, offline).

RapidOCR runs entirely on the CPU with no CUDA dependency and no external system
binary, matching the project's local-first, integrated-GPU target. The engine is
heavy to construct, so it is lazily initialised once on first use.
"""

from __future__ import annotations

from typing import Any

from private_rag.application.exceptions import DocumentExtractionError
from private_rag.application.services.text_normalization import normalize_text


class RapidOcrProvider:
    """Implements :class:`OcrProvider` using ``rapidocr-onnxruntime``."""

    def __init__(self) -> None:
        self._engine: Any | None = None

    def _get_engine(self) -> Any:
        if self._engine is None:
            try:
                from rapidocr_onnxruntime import RapidOCR
            except ImportError as exc:  # pragma: no cover - packaging guard
                raise DocumentExtractionError(
                    "OCR support is unavailable: rapidocr-onnxruntime is not installed"
                ) from exc
            try:
                self._engine = RapidOCR()
            except Exception as exc:
                raise DocumentExtractionError(
                    f"Could not initialise the OCR engine: {exc}"
                ) from exc
        return self._engine

    def image_to_text(self, image_png: bytes) -> str:
        engine = self._get_engine()
        try:
            result, _elapsed = engine(image_png)
        except Exception as exc:
            raise DocumentExtractionError(f"OCR failed to process image: {exc}") from exc

        if not result:
            return ""

        # RapidOCR returns a list of [box, text, score] entries in reading order.
        lines = [str(entry[1]) for entry in result if len(entry) >= 2 and entry[1]]
        return normalize_text("\n".join(lines))
