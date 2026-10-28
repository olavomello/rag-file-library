"""Extracts significant keywords from a query for hybrid (lexical) retrieval.

Pure semantic search ranks short, exact terms (acronyms like "SEO") poorly, so a
lexical pass complements it: the query's meaningful words are matched literally
against chunk text. Common stop words (English and Portuguese) are removed so the
lexical pass stays selective.
"""

from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[0-9A-Za-zÀ-ÿ]+")
MAX_KEYWORDS = 4

_STOPWORDS: frozenset[str] = frozenset(
    {
        # English
        "the", "a", "an", "of", "in", "on", "at", "to", "for", "and", "or", "is",
        "are", "was", "were", "be", "been", "do", "does", "did", "what", "which",
        "who", "whom", "where", "when", "how", "why", "about", "with", "without",
        "this", "that", "these", "those", "it", "its", "we", "you", "my", "our",
        "your", "have", "has", "had", "can", "could", "would", "should", "there",
        "here", "any", "some", "all", "from", "as", "by", "me", "i",
        # Portuguese
        "o", "os", "de", "da", "dos", "das", "e", "em", "no",
        "na", "nos", "nas", "um", "uma", "uns", "umas", "que", "qual", "quais",
        "sobre", "com", "sem", "por", "para", "pra", "se", "ao", "à", "às", "aos",
        "algo", "alguma", "algum", "tem", "temos", "tenho", "ter", "é", "são",
        "foi", "ser", "isso", "este", "esta", "isto", "meu", "minha", "como",
        "quando", "onde", "quem", "não", "sim", "ou", "mais", "nós",
    }
)


def extract_keywords(query: str) -> list[str]:
    """Return up to :data:`MAX_KEYWORDS` significant terms from ``query``.

    Stop words and single characters are dropped; the original casing of the first
    occurrence is kept, and duplicates (case-insensitively) are removed.
    """
    seen: set[str] = set()
    keywords: list[str] = []
    for token in _TOKEN_RE.findall(query):
        lowered = token.lower()
        if len(token) < 2 or lowered in _STOPWORDS or lowered in seen:
            continue
        seen.add(lowered)
        keywords.append(token)
        if len(keywords) >= MAX_KEYWORDS:
            break
    return keywords


def contains_variants(keywords: list[str]) -> list[str]:
    """Expand keywords to case variants for case-insensitive literal matching."""
    terms: list[str] = []
    seen: set[str] = set()
    for keyword in keywords:
        for variant in (keyword, keyword.lower(), keyword.upper(), keyword.capitalize()):
            if variant and variant not in seen:
                seen.add(variant)
                terms.append(variant)
    return terms
