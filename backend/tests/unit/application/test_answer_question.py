"""Unit tests for the RAG answer-question use case."""

from __future__ import annotations

from private_rag.application.dto.chat import ConversationTurn
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
        self.last_prompt = ""

    def generate(self, prompt: str) -> str:
        self.generate_calls += 1
        self.last_prompt = prompt
        assert "Context:" in prompt  # prompt was grounded
        return "  The vacation policy grants 20 days. "

    def stream_generate(self, prompt: str):  # type: ignore[no-untyped-def]
        self.last_prompt = prompt
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


def test_history_biases_retrieval_query_toward_prior_subject() -> None:
    """A short follow-up must retrieve against the ongoing subject, not alone.

    Reproduces the reported bug: after "Who is Olavo?", asking "Date of birth"
    must search with "Olavo" in the query so it does not match other people.
    """
    search = FakeSearch([_result()])
    use_case = AnswerQuestionUseCase(
        search=search,  # type: ignore[arg-type]
        context_builder=ContextBuilder(max_chunks=5, max_chars=4000),
        prompt_builder=PromptBuilder(),
        generation=FakeGeneration(),
        default_top_k=5,
    )
    history = [
        ConversationTurn(role="user", content="Who is Olavo?"),
        ConversationTurn(role="assistant", content="Olavo is a Full Stack Developer."),
    ]

    use_case.answer("Date of birth", history=history)

    assert "Olavo" in search.calls[0]
    assert "Date of birth" in search.calls[0]


def test_history_is_included_in_the_generation_prompt() -> None:
    search = FakeSearch([_result()])
    gen = FakeGeneration()
    use_case = AnswerQuestionUseCase(
        search=search,  # type: ignore[arg-type]
        context_builder=ContextBuilder(max_chunks=5, max_chars=4000),
        prompt_builder=PromptBuilder(),
        generation=gen,
        default_top_k=5,
    )
    history = [ConversationTurn(role="user", content="Who is Olavo?")]

    use_case.answer("Date of birth", history=history)

    assert "Who is Olavo?" in gen.last_prompt
    assert "Date of birth" in gen.last_prompt


def test_no_history_searches_with_the_bare_question() -> None:
    search = FakeSearch([_result()])
    use_case = AnswerQuestionUseCase(
        search=search,  # type: ignore[arg-type]
        context_builder=ContextBuilder(max_chunks=5, max_chars=4000),
        prompt_builder=PromptBuilder(),
        generation=FakeGeneration(),
        default_top_k=5,
    )

    use_case.answer("How many vacation days?")

    assert search.calls[0] == "How many vacation days?"
