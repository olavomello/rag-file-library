"""Use case: index a single document (parse -> chunk -> embed -> store)."""

from __future__ import annotations

import contextlib
from collections.abc import Callable

from private_rag.application.exceptions import NoExtractableTextError
from private_rag.application.ports.clock import Clock
from private_rag.application.ports.embeddings import EmbeddingProvider
from private_rag.application.ports.file_store import FileStore
from private_rag.application.ports.parser import DocumentParserRegistry
from private_rag.application.services.chunking import Chunker
from private_rag.domain.repositories.chunk_repository import ChunkVectorRepository
from private_rag.domain.repositories.document_repository import DocumentRepository

ProgressCallback = Callable[[float], None]


class IndexDocumentUseCase:
    """Runs the full ingestion pipeline for one document.

    On success the document ends ``INDEXED`` with its chunks stored. On any
    failure the document ends ``FAILED`` with an error message and any partial
    chunks are removed, so a document is never left partially indexed.
    """

    def __init__(
        self,
        *,
        documents: DocumentRepository,
        chunks: ChunkVectorRepository,
        storage: FileStore,
        parser: DocumentParserRegistry,
        chunker: Chunker,
        embeddings: EmbeddingProvider,
        clock: Clock,
    ) -> None:
        self._documents = documents
        self._chunks = chunks
        self._storage = storage
        self._parser = parser
        self._chunker = chunker
        self._embeddings = embeddings
        self._clock = clock

    def execute(
        self, document_id: str, *, progress: ProgressCallback | None = None
    ) -> int:
        document = self._documents.get(document_id)  # raises DocumentNotFoundError

        document.mark_processing(now=self._clock.now())
        self._documents.update(document)
        self._report(progress, 0.05)

        try:
            path = self._storage.path_for(document.stored_name)
            parsed = self._parser.parse(path, document.extension)
            if parsed.is_empty():
                raise NoExtractableTextError("Document has no extractable text")
            self._report(progress, 0.3)

            chunks = self._chunker.chunk(
                parsed, document_id=document.id, document_name=document.original_name
            )
            if not chunks:
                raise NoExtractableTextError("Document produced no chunks")

            vectors = self._embeddings.embed_documents([c.content for c in chunks])
            self._report(progress, 0.8)

            # Replace any existing chunks atomically from the reader's perspective:
            # the document is PROCESSING (excluded from search) until marked INDEXED.
            self._chunks.delete_by_document(document.id)
            self._chunks.add_chunks(
                chunks, vectors, embedding_model=self._embeddings.model
            )

            document.mark_indexed(now=self._clock.now(), chunk_count=len(chunks))
            self._documents.update(document)
            self._report(progress, 1.0)
            return len(chunks)
        except Exception as exc:
            self._handle_failure(document, exc)
            raise

    def _handle_failure(self, document, exc: Exception) -> None:  # type: ignore[no-untyped-def]
        # Best-effort cleanup; the original error is re-raised by the caller.
        with contextlib.suppress(Exception):
            self._chunks.delete_by_document(document.id)
        message = str(exc) or exc.__class__.__name__
        document.mark_failed(now=self._clock.now(), error_message=message)
        self._documents.update(document)

    @staticmethod
    def _report(progress: ProgressCallback | None, value: float) -> None:
        if progress is not None:
            progress(value)
