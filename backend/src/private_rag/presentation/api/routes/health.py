"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from private_rag import __version__
from private_rag.application.dto.health import HealthStatus
from private_rag.container.container import Container
from private_rag.presentation.api.dependencies.providers import get_container
from private_rag.presentation.api.schemas.health import (
    ComponentHealthResponse,
    LivenessResponse,
)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=LivenessResponse)
async def liveness(container: Container = Depends(get_container)) -> LivenessResponse:
    """Liveness probe: confirms the API process is up (no external dependencies)."""
    settings = container.settings
    return LivenessResponse(
        status="ok",
        app_name=settings.app_name,
        app_env=settings.app_env,
        version=__version__,
    )


@router.get("/health/ollama", response_model=ComponentHealthResponse)
async def ollama_health(
    response: Response,
    container: Container = Depends(get_container),
) -> ComponentHealthResponse:
    """Readiness probe for the local Ollama instance."""
    result = await container.ollama_health_probe.check()
    if result.status is not HealthStatus.OK:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ComponentHealthResponse.from_dto(result)


@router.get("/health/chroma", response_model=ComponentHealthResponse)
async def chroma_health(
    response: Response,
    container: Container = Depends(get_container),
) -> ComponentHealthResponse:
    """Readiness probe for the embedded ChromaDB store."""
    result = await container.chroma_health_probe.check()
    if result.status is not HealthStatus.OK:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ComponentHealthResponse.from_dto(result)
