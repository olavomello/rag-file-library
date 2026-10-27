"""Default token counter.

Token counting uses a whitespace-word approximation: it needs no model and is
deterministic and offline. This over-counts relative to sub-word tokenizers, so
configured chunk sizes behave conservatively (chunks are a little smaller than the
equivalent model-token budget). The :class:`TokenCounter` port allows swapping in a
model-accurate counter later without touching the chunking logic.
"""

from __future__ import annotations


class WhitespaceTokenCounter:
    """Counts tokens as whitespace-separated words."""

    def count(self, text: str) -> int:
        return len(text.split())
