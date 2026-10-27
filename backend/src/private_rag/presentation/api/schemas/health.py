"""Response schemas for health endpoints."""

from __future__ import annotations

from pydantic import BaseModel

from private_rag.application.dto.health import ComponentHealth


class LivenessResponse(BaseModel):
    """Basic application liveness response."""

    status: str
    app_name: str
    app_env: str
    version: str


class ComponentHealthResponse(BaseModel):
    """Health response for a single infrastructure component."""

    component: str
    status: str
    detail: str | None = None
    metadata: dict[str, str] = {}

    @classmethod
    def from_dto(cls, dto: ComponentHealth) -> ComponentHealthResponse:
        return cls(
            component=dto.component,
            status=dto.status.value,
            detail=dto.detail,
            metadata=dto.metadata,
        )
