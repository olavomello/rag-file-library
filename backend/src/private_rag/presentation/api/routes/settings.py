"""Settings endpoints: read effective config and update overrides."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends

from private_rag.container.container import Container
from private_rag.presentation.api.dependencies.providers import get_container
from private_rag.presentation.api.schemas.settings import (
    SettingsResponse,
    SettingsUpdateRequest,
    SettingsUpdateResponse,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(
    container: Container = Depends(get_container),
) -> SettingsResponse:
    return SettingsResponse.from_settings(container.settings)


@router.patch("", response_model=SettingsUpdateResponse)
async def update_settings(
    request: SettingsUpdateRequest,
    container: Container = Depends(get_container),
) -> SettingsUpdateResponse:
    patch = request.model_dump(exclude_none=True)
    result = await asyncio.to_thread(
        container.update_settings_use_case.execute, patch
    )
    return SettingsUpdateResponse(
        settings=SettingsResponse.from_settings(result.settings),
        requires_restart=result.requires_restart,
        requires_reindex=result.requires_reindex,
        message=result.message,
    )
