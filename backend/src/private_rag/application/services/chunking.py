"""Chunking engine: splits parsed documents into overlapping, searchable chunks.

Chunks respect semantic boundaries (paragraphs, then sentences, then words only
when a single sentence exceeds the budget), carry a configurable token overlap,
preserve page numbers, and receive deterministic identifiers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from private_rag.application.dto.parsing import ParsedDocument
from private_rag.application.ports.token_counter import TokenCounter
from private_rag.domain.entities.document_chunk import DocumentChunk
from private_rag.domain.exceptions import DomainValidationError

_PARAGRAPH_SPLIT = re.compile(r"\n{2,}")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass(slots=True)
class _Unit:
    text: str
    page_number: int | None
    paragraph_index: int
    tokens: int


class Chunker:
    def __init__(
        self,
        *,
        chunk_size: int,
        chunk_overlap: int,
        token_counter: TokenCounter,
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise DomainValidationError("chunk_overlap must be smaller than chunk_size")
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._counter = token_counter

    def chunk(
        self,
        parsed: ParsedDocument,
        *,
        document_id: str,
        document_name: str,
    ) -> list[DocumentChunk]:
        units = self._build_units(parsed)
        if not units:
            return []

        chunks: list[DocumentChunk] = []
        for index, group in enumerate(self._pack(units)):
            content = self._render(group)
            page = next((u.page_number for u in group if u.page_number is not None), None)
            metadata = {"document_name": document_name}
            if page is not None:
                metadata["page_number"] = str(page)
            chunks.append(
                DocumentChunk(
                    id=f"{document_id}:{index}",
                    document_id=document_id,
                    content=content,
                    chunk_index=index,
                    token_count=self._counter.count(content),
                    metadata=metadata,
                )
            )
        return chunks

    # --- internals ---

    def _build_units(self, parsed: ParsedDocument) -> list[_Unit]:
        units: list[_Unit] = []
        paragraph_index = 0
        for block in parsed.blocks:
            for paragraph in _PARAGRAPH_SPLIT.split(block.text):
                stripped = paragraph.strip()
                if not stripped:
                    continue
                for piece in self._split_to_fit(stripped):
                    units.append(
                        _Unit(
                            text=piece,
                            page_number=block.page_number,
                            paragraph_index=paragraph_index,
                            tokens=self._counter.count(piece),
                        )
                    )
                paragraph_index += 1
        return units

    def _split_to_fit(self, paragraph: str) -> list[str]:
        """Split a paragraph into units no larger than the chunk size.

        A paragraph within budget stays whole. A larger one is split into
        individual sentences (so packing can overlap on sentence boundaries), and
        any single sentence still over budget is split into fixed word windows.
        """
        if self._counter.count(paragraph) <= self._chunk_size:
            return [paragraph]

        pieces: list[str] = []
        for sentence in _SENTENCE_SPLIT.split(paragraph):
            stripped = sentence.strip()
            if not stripped:
                continue
            if self._counter.count(stripped) > self._chunk_size:
                pieces.extend(self._split_words(stripped))
            else:
                pieces.append(stripped)
        return pieces

    def _split_words(self, sentence: str) -> list[str]:
        words = sentence.split()
        return [
            " ".join(words[i : i + self._chunk_size])
            for i in range(0, len(words), self._chunk_size)
        ]

    def _pack(self, units: list[_Unit]) -> list[list[_Unit]]:
        chunks: list[list[_Unit]] = []
        current: list[_Unit] = []
        current_tokens = 0
        for unit in units:
            if current and current_tokens + unit.tokens > self._chunk_size:
                chunks.append(current)
                current, current_tokens = self._overlap_seed(current)
            current.append(unit)
            current_tokens += unit.tokens
        if current:
            chunks.append(current)
        return chunks

    def _overlap_seed(self, previous: list[_Unit]) -> tuple[list[_Unit], int]:
        if self._chunk_overlap <= 0:
            return [], 0
        seed: list[_Unit] = []
        tokens = 0
        for unit in reversed(previous):
            if tokens + unit.tokens > self._chunk_overlap:
                break
            seed.insert(0, unit)
            tokens += unit.tokens
        return seed, tokens

    @staticmethod
    def _render(units: list[_Unit]) -> str:
        parts: list[tuple[int, str]] = []
        for unit in units:
            if parts and parts[-1][0] == unit.paragraph_index:
                parts[-1] = (unit.paragraph_index, f"{parts[-1][1]} {unit.text}")
            else:
                parts.append((unit.paragraph_index, unit.text))
        return "\n\n".join(text for _, text in parts)
