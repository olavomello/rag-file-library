"""Unit tests for the chunking engine."""

from __future__ import annotations

import pytest

from private_rag.application.dto.parsing import ParsedDocument, TextBlock
from private_rag.application.services.chunking import Chunker
from private_rag.application.services.token_counter import WhitespaceTokenCounter
from private_rag.domain.exceptions import DomainValidationError


def _chunker(size: int = 10, overlap: int = 4) -> Chunker:
    return Chunker(
        chunk_size=size, chunk_overlap=overlap, token_counter=WhitespaceTokenCounter()
    )


def test_overlap_must_be_smaller_than_size() -> None:
    with pytest.raises(DomainValidationError):
        Chunker(chunk_size=5, chunk_overlap=5, token_counter=WhitespaceTokenCounter())


def test_empty_document_yields_no_chunks() -> None:
    result = _chunker().chunk(ParsedDocument(blocks=[]), document_id="d", document_name="n")
    assert result == []


def test_small_document_is_single_chunk() -> None:
    parsed = ParsedDocument(blocks=[TextBlock("alpha beta gamma", page_number=None)])

    chunks = _chunker().chunk(parsed, document_id="doc-1", document_name="n.txt")

    assert len(chunks) == 1
    assert chunks[0].id == "doc-1:0"
    assert chunks[0].chunk_index == 0
    assert chunks[0].content == "alpha beta gamma"
    assert chunks[0].token_count == 3
    assert chunks[0].metadata["document_name"] == "n.txt"


def test_page_number_is_preserved() -> None:
    parsed = ParsedDocument(blocks=[TextBlock("alpha beta", page_number=7)])
    chunks = _chunker().chunk(parsed, document_id="d", document_name="n")
    assert chunks[0].page_number == 7
    assert chunks[0].metadata["page_number"] == "7"


def test_paragraph_boundaries_preserved_within_chunk() -> None:
    parsed = ParsedDocument(blocks=[TextBlock("alpha beta\n\ngamma delta", page_number=None)])
    chunks = _chunker().chunk(parsed, document_id="d", document_name="n")
    assert len(chunks) == 1
    assert chunks[0].content == "alpha beta\n\ngamma delta"


def test_large_document_splits_with_overlap_and_order() -> None:
    sentences = " ".join(f"word{i} alpha beta." for i in range(20))  # 20 * 3 tokens
    parsed = ParsedDocument(blocks=[TextBlock(sentences, page_number=None)])

    chunks = _chunker(size=10, overlap=4).chunk(parsed, document_id="doc-1", document_name="n")

    assert len(chunks) > 1
    # Deterministic, ordered ids.
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    assert [c.id for c in chunks] == [f"doc-1:{i}" for i in range(len(chunks))]
    # Each chunk stays within size (+ overlap carried from the previous chunk).
    for chunk in chunks:
        assert chunk.token_count <= 10 + 4
    # Overlap means total tokens across chunks exceeds the unique token count.
    total = sum(c.token_count for c in chunks)
    unique = WhitespaceTokenCounter().count(sentences)
    assert total > unique


def test_oversized_single_sentence_is_word_split() -> None:
    long_sentence = " ".join(f"w{i}" for i in range(25))  # one 25-token "sentence"
    parsed = ParsedDocument(blocks=[TextBlock(long_sentence, page_number=None)])

    chunks = _chunker(size=10, overlap=0).chunk(parsed, document_id="d", document_name="n")

    assert len(chunks) == 3  # 25 words / 10 per window
    for chunk in chunks:
        assert chunk.token_count <= 10


def test_unicode_is_handled() -> None:
    parsed = ParsedDocument(blocks=[TextBlock("café résumé naïve", page_number=None)])
    chunks = _chunker().chunk(parsed, document_id="d", document_name="n")
    assert chunks[0].content == "café résumé naïve"
