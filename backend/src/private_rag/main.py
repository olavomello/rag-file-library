"""FastAPI application factory and ASGI entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from private_rag import __version__
from private_rag.container.container import Container
from private_rag.presentation.api.router import api_router
from private_rag.settings import Settings


def create_app(
    settings: Settings | None = None,
    container: Container | None = None,
) -> FastAPI:
    """Build and configure the FastAPI application.

    Args:
        settings: Optional pre-built settings. When omitted, settings are loaded
            from the environment / ``.env`` file.
        container: Optional pre-built container, primarily for testing with fakes.
    """
    settings = settings or Settings()
    container = container or Container(settings)

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Local, private Retrieval-Augmented Generation over your documents.",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    app.state.container = container
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app


app = create_app()
