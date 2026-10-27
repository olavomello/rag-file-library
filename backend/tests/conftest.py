"""Shared test fixtures.

Integration tests each create their own embedded ChromaDB ``PersistentClient``.
ChromaDB keeps a process-wide registry of initialized systems; across a large
suite this can accumulate and intermittently raise. Clearing the shared-system
cache after every test keeps clients independent and the suite deterministic.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest


def _clear_chroma_system_cache() -> None:
    try:
        from chromadb.api.shared_system_client import SharedSystemClient

        SharedSystemClient.clear_system_cache()
    except Exception:  # pragma: no cover - defensive across chromadb versions
        pass


@pytest.fixture(autouse=True)
def _reset_chroma() -> Iterator[None]:
    yield
    _clear_chroma_system_cache()
