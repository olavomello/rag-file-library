"""Unit tests for the RAG answer-question use case."""

from __future__ import annotations

from private_rag.application.services.context_builder import ContextBuilder
from private_rag.application.services.prompt_builder import PromptBuilder
from private_rag.application.use_cases.chat.answer_question import (
    INSUFFICIENT_CONTEXT,
    AnswerQuestionUseCase,
)
from private_rag.domain.entities.search_result import SearchResult


class FakeSearch:
    def __init__(self, results: list[SearchResult]) -> None:
        self._results = results
        self.calls: list[str] = []

    def execute(self, query, *, top_k=None, document_ids=None):  # type: ignore[no-untyped-def]
        self.calls.append(query)
        return self._results


class FakeGeneration:
    model = "fake-llm"

    def __init__(self) -> None:
        self.generate_calls = 0

    def generate(self, prompt: str) -> str:
        self.generate_calls += 1
        assert "Context:" in prompt  # prompt was grounded
        return "  The vacation policy grants 20 days. "

    def stream_generate(self, prompt: str):  # type: ignore[no-untyped-def]
        yield from ["The ", "answer ", "here."]


def _result() -> SearchResult:
    return SearchResult(
        document_id="doc-a",
        document_name="policy.txt",
        chunk_id="doc-a:0",
        content="Employees get 20 vacation days.",
        distance=0.1,
        page_number=2,
    )


def _use_case(results: list[SearchResult], generation: FakeGeneration) -> AnswerQuestionUseCase:
    return AnswerQuestionUseCase(
        search=FakeSearch(results),  # type: ignore[arg-type]
        context_builder=ContextBuilder(max_chunks=5, max_chars=4000),
        prompt_builder=PromptBuilder(),
        generation=generation,
        default_top_k=5,
    )


def test_answer_is_grounded_with_sources() -> None:
    gen = FakeGeneration()
    answer = _use_case([_result()], gen).answer("How many vacation days?")

    assert answer.grounded is True
    assert answer.text == "The vacation policy grants 20 days."  # stripped
    assert [s.chunk_id for s in answer.sources] == ["doc-a:0"]
    assert answer.sources[0].page_number == 2
    assert gen.generate_calls == 1


def test_no_results_returns_insufficient_without_calling_llm() -> None:
    gen = FakeGeneration()
    answer = _use_case([], gen).answer("anything")

    assert answer.grounded is False
    assert answer.text == INSUFFICIENT_CONTEXT
    assert answer.sources == []
    assert gen.generate_calls == 0


def test_stream_yields_tokens_and_sources_when_grounded() -> None:
    streamed = _use_case([_result()], FakeGeneration()).stream("q")
    assert streamed.grounded is True
    assert [s.chunk_id for s in streamed.sources] == ["doc-a:0"]
    assert "".join(streamed.tokens) == "The answer here."


def test_stream_without_results_is_insufficient() -> None:
    streamed = _use_case([], FakeGeneration()).stream("q")
    assert streamed.grounded is False
    assert streamed.sources == []
    assert "".join(streamed.tokens) == INSUFFICIENT_CONTEXT
