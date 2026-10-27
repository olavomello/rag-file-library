"""Aggregates all versioned API routers under ``/api/v1``."""

from __future__ import annotations

from fastapi import APIRouter

from private_rag.presentation.api.routes import (
    chat,
    documents,
    health,
    indexing,
    models,
    search,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(documents.router)
api_router.include_router(indexing.router)
api_router.include_router(search.router)
api_router.include_router(chat.router)
api_router.include_router(models.router)
