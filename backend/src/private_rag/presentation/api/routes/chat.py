"""RAG chat endpoints: blocking answer and streaming answer."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Iterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from private_rag.application.dto.chat import ConversationTurn
from private_rag.application.exceptions import GenerationError
from private_rag.container.container import Container
from private_rag.presentation.api.dependencies.providers import get_container
from private_rag.presentation.api.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatSource,
)

router = APIRouter(prefix="/chat", tags=["chat"])


def _history(request: ChatRequest) -> list[ConversationTurn]:
    return [ConversationTurn(role=m.role, content=m.content) for m in request.history]


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    container: Container = Depends(get_container),
) -> ChatResponse:
    answer = await asyncio.to_thread(
        container.answer_question_use_case.answer,
        request.question,
        history=_history(request),
        top_k=request.top_k,
    )
    return ChatResponse(
        answer=answer.text,
        grounded=answer.grounded,
        sources=[ChatSource.from_reference(s) for s in answer.sources],
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    container: Container = Depends(get_container),
) -> StreamingResponse:
    streamed = await asyncio.to_thread(
        container.answer_question_use_case.stream,
        request.question,
        history=_history(request),
        top_k=request.top_k,
    )

    def events() -> Iterator[str]:
        sources = [ChatSource.from_reference(s).model_dump() for s in streamed.sources]
        header = {"type": "sources", "grounded": streamed.grounded, "sources": sources}
        yield json.dumps(header) + "\n"
        try:
            for token in streamed.tokens:
                yield json.dumps({"type": "token", "text": token}) + "\n"
        except GenerationError as exc:
            yield json.dumps({"type": "error", "detail": str(exc)}) + "\n"
            return
        yield json.dumps({"type": "done"}) + "\n"

    return StreamingResponse(events(), media_type="application/x-ndjson")
