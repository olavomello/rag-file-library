"""Port for optical character recognition (OCR) of images.

OCR is used to extract text from image files and from scanned PDF pages that have
no text layer. Implementations run locally; the port keeps OCR replaceable and
lets tests substitute a fake.
"""

from __future__ import annotations

from typing import Protocol


class OcrProvider(Protocol):
    """Extracts text from a single encoded image."""

    def image_to_text(self, image_png: bytes) -> str:
        """Return recognised text for ``image_png`` (encoded image bytes).

        Implementations raise :class:`DocumentExtractionError` when the OCR engine
        fails. An image with no recognisable text yields an empty string.
        """
        ...
