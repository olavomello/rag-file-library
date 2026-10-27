"""Health probe for the embedded ChromaDB persistent store."""

from __future__ import annotations

import asyncio
from pathlib import Path

from private_rag.application.dto.health import ComponentHealth, HealthStatus


class ChromaHealthProbe:
    """Verifies that the embedded ChromaDB directory is usable.

    The check confirms the persistence directory exists and is writable. A deeper
    client heartbeat is performed lazily to avoid importing/initialising ChromaDB
    on every liveness check.
    """

    name = "chroma"

    def __init__(self, path: str) -> None:
        self._path = Path(path)

    async def check(self) -> ComponentHealth:
        return await asyncio.to_thread(self._check_sync)

    def _check_sync(self) -> ComponentHealth:
        try:
            self._path.mkdir(parents=True, exist_ok=True)
            probe_file = self._path / ".write_probe"
            probe_file.write_text("ok", encoding="utf-8")
            probe_file.unlink(missing_ok=True)
        except OSError as exc:
            return ComponentHealth(
                component=self.name,
                status=HealthStatus.ERROR,
                detail=f"ChromaDB path is not writable: {exc.strerror or exc}",
                metadata={"path": str(self._path)},
            )

        return ComponentHealth(
            component=self.name,
            status=HealthStatus.OK,
            detail="Persistent store directory is ready",
            metadata={"path": str(self._path)},
        )
