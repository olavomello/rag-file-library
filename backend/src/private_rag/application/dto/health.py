"""DTOs describing infrastructure/component health."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class HealthStatus(StrEnum):
    """Health state of an infrastructure component."""

    OK = "ok"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class ComponentHealth(BaseModel):
    """Health result for a single infrastructure component."""

    component: str
    status: HealthStatus
    detail: str | None = None
    metadata: dict[str, str] = {}

    @property
    def is_ok(self) -> bool:
        return self.status is HealthStatus.OK
