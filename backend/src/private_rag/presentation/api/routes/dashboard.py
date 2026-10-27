"""Dashboard statistics endpoint."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends

from private_rag.container.container import Container
from private_rag.presentation.api.dependencies.providers import get_container
from private_rag.presentation.api.schemas.dashboard import DashboardStatsResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def dashboard_stats(
    container: Container = Depends(get_container),
) -> DashboardStatsResponse:
    stats = await asyncio.to_thread(container.get_dashboard_stats_use_case.execute)
    return DashboardStatsResponse.from_dto(stats)
