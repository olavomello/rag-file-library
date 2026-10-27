"""Semantic search endpoint (independent of the LLM)."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends

from private_rag.container.container import Container
from private_rag.presentation.api.dependencies.providers import get_container
from private_rag.presentation.api.schemas.search import (
    SearchResultResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    container: Container = Depends(get_container),
) -> SemanticSearchResponse:
    results = await asyncio.to_thread(
        container.semantic_search_use_case.execute,
        request.query,
        top_k=request.top_k,
        document_ids=request.document_ids,
    )
    return SemanticSearchResponse(
        query=request.query,
        count=len(results),
        results=[SearchResultResponse.from_entity(result) for result in results],
    )
