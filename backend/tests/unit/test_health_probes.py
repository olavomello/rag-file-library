"""Unit tests for infrastructure health probes."""

from __future__ import annotations

from pathlib import Path

import pytest

from private_rag.application.dto.health import HealthStatus
from private_rag.infrastructure.chroma.health_probe import ChromaHealthProbe
from private_rag.infrastructure.ollama.health_probe import OllamaHealthProbe


@pytest.mark.asyncio
async def test_chroma_probe_reports_ok_for_writable_path(tmp_path: Path) -> None:
    probe = ChromaHealthProbe(path=str(tmp_path / "chroma"))

    result = await probe.check()

    assert result.component == "chroma"
    assert result.status is HealthStatus.OK
    assert (tmp_path / "chroma").is_dir()


@pytest.mark.asyncio
async def test_ollama_probe_reports_unavailable_when_unreachable() -> None:
    # Port 1 is reserved and will refuse connections immediately.
    probe = OllamaHealthProbe(base_url="http://127.0.0.1:1", timeout_seconds=1.0)

    result = await probe.check()

    assert result.component == "ollama"
    assert result.status is HealthStatus.UNAVAILABLE
