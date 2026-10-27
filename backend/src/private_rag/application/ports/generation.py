"""Port for local text generation (the LLM)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol


class GenerationProvider(Protocol):
    """Generates text from a prompt, with blocking and streaming variants."""

    @property
    def model(self) -> str: ...

    def generate(self, prompt: str) -> str:
        """Return the full completion for ``prompt``."""
        ...

    def stream_generate(self, prompt: str) -> Iterator[str]:
        """Yield completion tokens/chunks for ``prompt`` as they are produced."""
        ...
