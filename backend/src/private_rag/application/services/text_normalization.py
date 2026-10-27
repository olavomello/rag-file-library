"""Whitespace normalization for extracted text.

Collapses redundant spaces and blank lines while preserving paragraph boundaries,
so chunking can rely on blank lines as paragraph separators.
"""

from __future__ import annotations

import re

_TRAILING_WS = re.compile(r"[ \t]+(\n)")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")
_MULTI_BLANK = re.compile(r"\n{3,}")


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _MULTI_SPACE.sub(" ", text)
    text = _TRAILING_WS.sub(r"\1", text)
    text = _MULTI_BLANK.sub("\n\n", text)
    return text.strip()
