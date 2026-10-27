"""DTOs describing parsed document content flowing from parsers to chunking."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class TextBlock:
    """A block of extracted text with an optional source page number."""

    text: str
    page_number: int | None = None


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    """The full extracted content of a document as ordered text blocks."""

    blocks: list[TextBlock] = field(default_factory=list)

    @property
    def text(self) -> str:
        """The whole document text, blocks joined by blank lines."""
        return "\n\n".join(block.text for block in self.blocks if block.text)

    def is_empty(self) -> bool:
        return not self.text.strip()
