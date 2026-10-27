"""Composition root.

The container wires concrete infrastructure implementations to application/domain
ports using explicit dependency injection (no framework). It is created once per
application instance and stored on ``app.state``. The embedded ChromaDB client is
owned here as a single process-wide instance.
"""

from __future__ import annotations

from functools import cached_property
from pathlib import Path

from private_rag.application.ports.clock import Clock
from private_rag.application.ports.embeddings import EmbeddingProvider
from private_rag.application.ports.generation import GenerationProvider
from private_rag.application.ports.health import HealthProbe
from private_rag.application.services.chunking import Chunker
from private_rag.application.services.context_builder import ContextBuilder
from private_rag.application.services.prompt_builder import PromptBuilder
from private_rag.application.services.token_counter import WhitespaceTokenCounter
from private_rag.application.use_cases.chat.answer_question import (
    AnswerQuestionUseCase,
)
from private_rag.application.use_cases.documents.delete_document import (
    DeleteDocumentUseCase,
)
from private_rag.application.use_cases.documents.get_document import GetDocumentUseCase
from private_rag.application.use_cases.documents.get_document_content import (
    GetDocumentContentUseCase,
)
from private_rag.application.use_cases.documents.list_documents import (
    ListDocumentsUseCase,
)
from private_rag.application.use_cases.documents.upload_document import (
    UploadDocumentUseCase,
)
from private_rag.application.use_cases.indexing.index_document import (
    IndexDocumentUseCase,
)
from private_rag.application.use_cases.search.semantic_search import (
    SemanticSearchUseCase,
)
from private_rag.domain.repositories.chunk_repository import ChunkVectorRepository
from private_rag.domain.repositories.document_repository import DocumentRepository
from private_rag.domain.repositories.indexing_job_repository import (
    IndexingJobRepository,
)
from private_rag.infrastructure.chroma.chunk_repository import ChromaChunkRepository
from private_rag.infrastructure.chroma.client import ChromaClientProvider
from private_rag.infrastructure.chroma.document_registry import ChromaDocumentRegistry
from private_rag.infrastructure.chroma.health_probe import ChromaHealthProbe
from private_rag.infrastructure.clock import SystemClock
from private_rag.infrastructure.filesystem.file_storage import FileStorage
from private_rag.infrastructure.filesystem.json_indexing_job_repository import (
    JsonIndexingJobRepository,
)
from private_rag.infrastructure.indexing.worker import IndexingWorker
from private_rag.infrastructure.ollama.embedding_provider import OllamaEmbeddingProvider
from private_rag.infrastructure.ollama.generation_provider import (
    OllamaGenerationProvider,
)
from private_rag.infrastructure.ollama.health_probe import OllamaHealthProbe
from private_rag.infrastructure.ollama.model_catalog import OllamaModelCatalog
from private_rag.infrastructure.parsers.registry import ParserRegistry
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

    @cached_property
    def clock(self) -> Clock:
        return SystemClock()

    # --- Document use cases ---

    @cached_property
    def upload_document_use_case(self) -> UploadDocumentUseCase:
        return UploadDocumentUseCase(
            documents=self.document_repository,
            storage=self.file_storage,
            clock=self.clock,
            max_upload_size_bytes=self._settings.max_upload_size_bytes,
        )

    @cached_property
    def list_documents_use_case(self) -> ListDocumentsUseCase:
        return ListDocumentsUseCase(documents=self.document_repository)

    @cached_property
    def get_document_use_case(self) -> GetDocumentUseCase:
        return GetDocumentUseCase(documents=self.document_repository)

    @cached_property
    def delete_document_use_case(self) -> DeleteDocumentUseCase:
        return DeleteDocumentUseCase(
            documents=self.document_repository,
            chunks=self.chunk_repository,
            jobs=self.indexing_job_repository,
            storage=self.file_storage,
        )

    @cached_property
    def get_document_content_use_case(self) -> GetDocumentContentUseCase:
        return GetDocumentContentUseCase(
            documents=self.document_repository,
            storage=self.file_storage,
            parser=self.parser_registry,
        )

    # --- Ingestion pipeline ---

    @cached_property
    def parser_registry(self) -> ParserRegistry:
        return ParserRegistry()

    @cached_property
    def chunker(self) -> Chunker:
        return Chunker(
            chunk_size=self._settings.chunk_size,
            chunk_overlap=self._settings.chunk_overlap,
            token_counter=WhitespaceTokenCounter(),
        )

    @cached_property
    def embedding_provider(self) -> EmbeddingProvider:
        return OllamaEmbeddingProvider(
            base_url=self._settings.ollama_base_url,
            model=self._settings.ollama_embedding_model,
            timeout_seconds=self._settings.ollama_request_timeout_seconds,
        )

    @cached_property
    def index_document_use_case(self) -> IndexDocumentUseCase:
        return IndexDocumentUseCase(
            documents=self.document_repository,
            chunks=self.chunk_repository,
            storage=self.file_storage,
            parser=self.parser_registry,
            chunker=self.chunker,
            embeddings=self.embedding_provider,
            clock=self.clock,
        )

    @cached_property
    def indexing_worker(self) -> IndexingWorker:
        return IndexingWorker(
            index_use_case=self.index_document_use_case,
            documents=self.document_repository,
            jobs=self.indexing_job_repository,
            clock=self.clock,
            concurrency=self._settings.indexing_concurrency,
        )

    # --- Search ---

    @cached_property
    def semantic_search_use_case(self) -> SemanticSearchUseCase:
        return SemanticSearchUseCase(
            embeddings=self.embedding_provider,
            chunks=self.chunk_repository,
            documents=self.document_repository,
            default_top_k=self._settings.search_top_k,
        )

    # --- RAG chat ---

    @cached_property
    def generation_provider(self) -> GenerationProvider:
        return OllamaGenerationProvider(
            base_url=self._settings.ollama_base_url,
            model=self._settings.ollama_generation_model,
            temperature=self._settings.ollama_temperature,
            max_output_tokens=self._settings.ollama_max_output_tokens,
            context_window=self._settings.ollama_context_window,
            timeout_seconds=self._settings.ollama_request_timeout_seconds,
        )

    @cached_property
    def context_builder(self) -> ContextBuilder:
        return ContextBuilder(
            max_chunks=self._settings.rag_max_context_chunks,
            max_chars=self._settings.rag_max_context_chars,
        )

    @cached_property
    def prompt_builder(self) -> PromptBuilder:
        return PromptBuilder()

    @cached_property
    def answer_question_use_case(self) -> AnswerQuestionUseCase:
        return AnswerQuestionUseCase(
            search=self.semantic_search_use_case,
            context_builder=self.context_builder,
            prompt_builder=self.prompt_builder,
            generation=self.generation_provider,
            default_top_k=self._settings.search_top_k,
        )

    @cached_property
    def model_catalog(self) -> OllamaModelCatalog:
        return OllamaModelCatalog(
            base_url=self._settings.ollama_base_url,
            timeout_seconds=min(self._settings.ollama_request_timeout_seconds, 5.0),
        )

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
