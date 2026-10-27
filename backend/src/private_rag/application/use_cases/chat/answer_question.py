"""Use case: answer a question from the user's documents (RAG)."""

from __future__ import annotations

from private_rag.application.dto.chat import Answer, StreamedAnswer
from private_rag.application.ports.generation import GenerationProvider
from private_rag.application.services.context_builder import BuiltContext, ContextBuilder
from private_rag.application.services.prompt_builder import PromptBuilder
from private_rag.application.use_cases.search.semantic_search import (
    SemanticSearchUseCase,
)

INSUFFICIENT_CONTEXT = (
    "I couldn't find anything in your indexed documents to answer that."
)


class AnswerQuestionUseCase:
    """Retrieves relevant chunks, builds a grounded prompt, and generates an answer.

    When retrieval finds nothing, the answer states that it cannot be established
    from the documents and no LLM call is made — search and generation stay
    decoupled, and the question is never answered ungrounded.
    """

    def __init__(
        self,
        *,
        search: SemanticSearchUseCase,
        context_builder: ContextBuilder,
        prompt_builder: PromptBuilder,
        generation: GenerationProvider,
        default_top_k: int,
    ) -> None:
        self._search = search
        self._context_builder = context_builder
        self._prompt_builder = prompt_builder
        self._generation = generation
        self._default_top_k = default_top_k

    def _context(self, question: str, top_k: int | None) -> BuiltContext | None:
        results = self._search.execute(
            question, top_k=top_k or self._default_top_k
        )
        if not results:
            return None
        built = self._context_builder.build(results)
        return None if built.is_empty() else built

    def answer(self, question: str, *, top_k: int | None = None) -> Answer:
        context = self._context(question, top_k)
        if context is None:
            return Answer(text=INSUFFICIENT_CONTEXT, sources=[], grounded=False)

        prompt = self._prompt_builder.build(question=question, context=context.text)
        text = self._generation.generate(prompt).strip()
        return Answer(
            text=text or INSUFFICIENT_CONTEXT,
            sources=context.sources,
            grounded=True,
        )

    def stream(self, question: str, *, top_k: int | None = None) -> StreamedAnswer:
        context = self._context(question, top_k)
        if context is None:
            return StreamedAnswer(
                sources=[], grounded=False, tokens=iter([INSUFFICIENT_CONTEXT])
            )

        prompt = self._prompt_builder.build(question=question, context=context.text)
        return StreamedAnswer(
            sources=context.sources,
            grounded=True,
            tokens=self._generation.stream_generate(prompt),
        )
