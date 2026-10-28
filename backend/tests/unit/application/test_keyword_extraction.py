"""Unit tests for keyword extraction used by hybrid retrieval."""

from __future__ import annotations

from private_rag.application.services.keyword_extraction import (
    MAX_KEYWORDS,
    contains_variants,
    extract_keywords,
)


def test_drops_stopwords_keeps_meaningful_terms() -> None:
    assert extract_keywords("Temos algo sobre SEO?") == ["SEO"]
    assert extract_keywords("What is the vacation policy") == ["vacation", "policy"]


def test_keeps_short_acronyms_but_drops_single_chars() -> None:
    assert extract_keywords("AI e o R") == ["AI"]


def test_dedupes_case_insensitively_and_caps_count() -> None:
    assert extract_keywords("SEO seo Seo") == ["SEO"]
    many = extract_keywords("alpha beta gamma delta epsilon zeta")
    assert len(many) == MAX_KEYWORDS


def test_stopwords_only_query_has_no_keywords() -> None:
    assert extract_keywords("o que é isso") == []


def test_contains_variants_covers_common_casings() -> None:
    variants = contains_variants(["SEO"])
    assert "SEO" in variants and "seo" in variants and "Seo" in variants
