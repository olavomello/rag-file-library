"""Composition root.

The container wires concrete infrastructure implementations to application/domain
ports using explicit dependency injection (no framework). It is created once per
application instance and stored on ``app.state``. The embedded ChromaDB client is
owned here as a single process-wide instance.
"""

from __future__ import annotations

from functools import cached_property
from pathlib import Path

from private_rag.application.ports.health import HealthProbe
from private_rag.domain.repositories.chunk_repository import ChunkVectorRepository
from private_rag.domain.repositories.document_repository import DocumentRepository
from private_rag.domain.repositories.indexing_job_repository import (
    IndexingJobRepository,
)
from private_rag.infrastructure.chroma.chunk_repository import ChromaChunkRepository
from private_rag.infrastructure.chroma.client import ChromaClientProvider
from private_rag.infrastructure.chroma.document_registry import ChromaDocumentRegistry
from private_rag.infrastructure.chroma.health_probe import ChromaHealthProbe
from private_rag.infrastructure.filesystem.file_storage import FileStorage
from private_rag.infrastructure.filesystem.json_indexing_job_repository import (
    JsonIndexingJobRepository,
)
from private_rag.infrastructure.ollama.health_probe import OllamaHealthProbe
from private_rag.settings import Settings


class Container:
    """Builds and holds application-scoped dependencies."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def settings(self) -> Settings:
        return self._settings

    # --- Infrastructure singletons ---

    @cached_property
    def chroma(self) -> ChromaClientProvider:
        return ChromaClientProvider(path=self._settings.chroma_path)

    @cached_property
    def file_storage(self) -> FileStorage:
        return FileStorage(self._settings.upload_dir)

    # --- Repositories (concrete -> port) ---

    @cached_property
    def document_repository(self) -> DocumentRepository:
        return ChromaDocumentRegistry(self.chroma)

    @cached_property
    def chunk_repository(self) -> ChunkVectorRepository:
        return ChromaChunkRepository(self.chroma)

    @cached_property
    def indexing_job_repository(self) -> IndexingJobRepository:
        return JsonIndexingJobRepository(self._settings.jobs_dir)

    # --- Health probes ---

    @cached_property
    def ollama_health_probe(self) -> HealthProbe:
        return OllamaHealthProbe(
            base_url=self._settings.ollama_base_url,
            timeout_seconds=min(self._settings.ollama_request_timeout_seconds, 5.0),
        )

    @cached_property
    def chroma_health_probe(self) -> HealthProbe:
        return ChromaHealthProbe(path=self._settings.chroma_path)

    # --- Lifecycle ---

    def prepare_storage(self) -> None:
        """Ensure local persistence directories exist (filesystem only, fast)."""
        for directory in (
            self._settings.upload_dir,
            self._settings.jobs_dir,
            self._settings.chroma_path,
            self._settings.temp_dir,
            self._settings.config_dir,
        ):
            Path(directory).mkdir(parents=True, exist_ok=True)
