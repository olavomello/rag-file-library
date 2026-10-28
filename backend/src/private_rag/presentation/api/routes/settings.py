"""Settings endpoints: read effective config and update overrides."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends

from private_rag.application.services.settings_overrides import apply_overrides
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
    # Reflect saved overrides (the effective-after-restart view) so a saved change
    # is visible immediately, not only after the next restart. Settings that need a
    # restart to take effect are flagged as such on save.
    overrides = await asyncio.to_thread(container.settings_overrides_store.load)
    effective = apply_overrides(container.settings, overrides)
    return SettingsResponse.from_settings(effective)


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
