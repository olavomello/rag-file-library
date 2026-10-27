"""Port describing a health probe for an infrastructure component."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from private_rag.application.dto.health import ComponentHealth


@runtime_checkable
class HealthProbe(Protocol):
    """Checks the availability of a single infrastructure component."""

    @property
    def name(self) -> str:
        """Stable identifier of the component (e.g. ``"ollama"``)."""
        ...

    async def check(self) -> ComponentHealth:
        """Return the current health of the component.

        Implementations must not raise for expected unavailability; they should
        return a :class:`ComponentHealth` with an appropriate status instead.
        """
        ...
