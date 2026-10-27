"""FastAPI dependency providers that expose the container to routes."""

from __future__ import annotations

from fastapi import Request

from private_rag.container.container import Container
from private_rag.settings import Settings


def get_container(request: Request) -> Container:
    """Return the application container stored on ``app.state``."""
    container: Container = request.app.state.container
    return container


def get_settings(request: Request) -> Settings:
    return get_container(request).settings
