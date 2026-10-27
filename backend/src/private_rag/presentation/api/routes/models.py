"""Model info endpoints."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends

from private_rag.container.container import Container
from private_rag.presentation.api.dependencies.providers import get_container
from private_rag.presentation.api.schemas.models import (
    ModelsResponse,
    ModelsStatusResponse,
)

router = APIRouter(prefix="/models", tags=["models"])


def _is_present(model: str, available: list[str]) -> bool:
    base = model.split(":")[0]
    return any(name == model or name.split(":")[0] == base for name in available)


@router.get("", response_model=ModelsResponse)
async def list_models(container: Container = Depends(get_container)) -> ModelsResponse:
    reachable, names = await asyncio.to_thread(container.model_catalog.fetch)
    settings = container.settings
    return ModelsResponse(
        generation_model=settings.ollama_generation_model,
        embedding_model=settings.ollama_embedding_model,
        ollama_available=reachable,
        generation_available=reachable and _is_present(settings.ollama_generation_model, names),
        embedding_available=reachable and _is_present(settings.ollama_embedding_model, names),
        available_models=names,
    )


@router.get("/status", response_model=ModelsStatusResponse)
async def models_status(
    container: Container = Depends(get_container),
) -> ModelsStatusResponse:
    reachable, names = await asyncio.to_thread(container.model_catalog.fetch)
    settings = container.settings
    return ModelsStatusResponse(
        generation_model=settings.ollama_generation_model,
        embedding_model=settings.ollama_embedding_model,
        ollama_available=reachable,
        generation_available=reachable and _is_present(settings.ollama_generation_model, names),
        embedding_available=reachable and _is_present(settings.ollama_embedding_model, names),
    )
