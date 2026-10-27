"""Builds grounded context from retrieved search results for the RAG prompt."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from private_rag.domain.entities.search_result import SearchResult
from private_rag.domain.value_objects.source_reference import SourceReference


@dataclass(slots=True)
class BuiltContext:
    """Assembled context text plus the sources actually included, in order."""

    text: str
    sources: list[SourceReference] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.text.strip()


class ContextBuilder:
    """Selects and formats retrieved chunks into a bounded, numbered context.

    Chunks are included in rank order up to a maximum count and character budget.
    Each included chunk is numbered (``[Source N]``) so the prompt can refer to it,
    and the matching :class:`SourceReference` list is returned 1:1 for citations.
    """

    def __init__(self, *, max_chunks: int, max_chars: int) -> None:
        self._max_chunks = max_chunks
        self._max_chars = max_chars

    def build(self, results: Sequence[SearchResult]) -> BuiltContext:
        blocks: list[str] = []
        sources: list[SourceReference] = []
        total = 0

        for result in results:
            if len(sources) >= self._max_chunks:
                break
            label = f"[Source {len(sources) + 1}]"
            block = f"{label} {result.content}".strip()
            if blocks and total + len(block) > self._max_chars:
                break
            blocks.append(block)
            total += len(block)
            sources.append(
                SourceReference(
                    document_id=result.document_id,
                    document_name=result.document_name,
                    chunk_id=result.chunk_id,
                    page_number=result.page_number,
                )
            )

        return BuiltContext(text="\n\n".join(blocks), sources=sources)
