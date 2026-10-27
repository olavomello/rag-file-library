"""Unit tests for the RAG context and prompt builders."""

from __future__ import annotations

from private_rag.application.services.context_builder import ContextBuilder
from private_rag.application.services.prompt_builder import PromptBuilder
from private_rag.domain.entities.search_result import SearchResult


def _result(
    doc: str, chunk: str, content: str, *, page: int | None = None, distance: float = 0.1
) -> SearchResult:
    return SearchResult(
        document_id=doc,
        document_name=f"{doc}.txt",
        chunk_id=chunk,
        content=content,
        distance=distance,
        page_number=page,
    )


class TestContextBuilder:
    def test_empty_results_give_empty_context(self) -> None:
        built = ContextBuilder(max_chunks=5, max_chars=1000).build([])
        assert built.is_empty()
        assert built.sources == []

    def test_numbers_sources_and_maps_one_to_one(self) -> None:
        results = [
            _result("doc-a", "doc-a:0", "alpha content", page=1),
            _result("doc-b", "doc-b:0", "beta content", page=2),
        ]
        built = ContextBuilder(max_chunks=5, max_chars=1000).build(results)

        assert "[Source 1] alpha content" in built.text
        assert "[Source 2] beta content" in built.text
        assert [s.chunk_id for s in built.sources] == ["doc-a:0", "doc-b:0"]
        assert built.sources[1].page_number == 2

    def test_respects_max_chunks(self) -> None:
        results = [_result("d", f"d:{i}", f"chunk {i}") for i in range(5)]
        built = ContextBuilder(max_chunks=2, max_chars=10000).build(results)
        assert len(built.sources) == 2

    def test_respects_char_budget_but_keeps_first(self) -> None:
        results = [
            _result("d", "d:0", "x" * 100),
            _result("d", "d:1", "y" * 100),
        ]
        built = ContextBuilder(max_chunks=5, max_chars=50).build(results)
        assert len(built.sources) == 1  # second would exceed budget


class TestPromptBuilder:
    def test_prompt_contains_rules_context_and_question(self) -> None:
        prompt = PromptBuilder().build(question="What is the policy?", context="[Source 1] text")
        assert "ONLY the provided" in prompt
        assert "untrusted data" in prompt  # prompt-injection guard
        assert "[Source 1] text" in prompt
        assert "What is the policy?" in prompt
        assert prompt.rstrip().endswith("Answer:")
