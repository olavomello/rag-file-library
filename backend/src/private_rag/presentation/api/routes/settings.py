"""Settings endpoint (read-only view of effective configuration)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from private_rag.container.container import Container
from private_rag.presentation.api.dependencies.providers import get_container
from private_rag.presentation.api.schemas.settings import SettingsResponse

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(
    container: Container = Depends(get_container),
) -> SettingsResponse:
    return SettingsResponse.from_settings(container.settings)
