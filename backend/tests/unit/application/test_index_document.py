"""Unit tests for IndexDocumentUseCase using fakes (no Ollama, no Chroma)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from private_rag.application.dto.parsing import ParsedDocument, TextBlock
from private_rag.application.exceptions import EmbeddingError, NoExtractableTextError
from private_rag.application.services.chunking import Chunker
from private_rag.application.services.token_counter import WhitespaceTokenCounter
from private_rag.application.use_cases.indexing.index_document import (
    IndexDocumentUseCase,
)
from private_rag.domain.entities.document import Document
from private_rag.domain.exceptions import DocumentNotFoundError
from private_rag.domain.value_objects.document_status import DocumentStatus

NOW = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)


class FakeDocuments:
    def __init__(self, document: Document) -> None:
        self.doc = document

    def get(self, document_id: str) -> Document:
        if document_id != self.doc.id:
            raise DocumentNotFoundError(document_id)
        return self.doc

    def update(self, document: Document) -> None:
        self.doc = document


class RecordingChunks:
    def __init__(self) -> None:
        self.log: list[tuple[str, object]] = []

    def add_chunks(self, chunks, embeddings, *, embedding_model) -> None:  # type: ignore[no-untyped-def]
        assert len(chunks) == len(embeddings)
        self.log.append(("add", len(chunks)))

    def delete_by_document(self, document_id: str) -> None:
        self.log.append(("delete", document_id))

    def query(self, embedding, *, top_k, document_ids=None):  # type: ignore[no-untyped-def]
        return []

    def count(self, *, document_id=None) -> int:  # type: ignore[no-untyped-def]
        return 0


class FakeStorage:
    def save(self, stored_name, data):  # type: ignore[no-untyped-def]
        return Path(stored_name)

    def read(self, stored_name):  # type: ignore[no-untyped-def]
        return b""

    def exists(self, stored_name) -> bool:  # type: ignore[no-untyped-def]
        return True

    def delete(self, stored_name) -> None:  # type: ignore[no-untyped-def]
        pass

    def path_for(self, stored_name):  # type: ignore[no-untyped-def]
        return Path(stored_name)


class FakeParser:
    def __init__(self, parsed: ParsedDocument) -> None:
        self._parsed = parsed

    def parse(self, file_path, extension):  # type: ignore[no-untyped-def]
        return self._parsed


class FakeEmbeddings:
    model = "fake-embed"

    def embed_documents(self, texts):  # type: ignore[no-untyped-def]
        return [[float(len(t)), 1.0] for t in texts]

    def embed_query(self, text):  # type: ignore[no-untyped-def]
        return [float(len(text)), 1.0]


class FailingEmbeddings(FakeEmbeddings):
    def embed_documents(self, texts):  # type: ignore[no-untyped-def]
        raise EmbeddingError("ollama down")


class FixedClock:
    def now(self) -> datetime:
        return NOW


def _pending_document() -> Document:
    doc = Document.create(
        original_name="a.txt",
        stored_name="doc-1.txt",
        mime_type="text/plain",
        extension=".txt",
        size_bytes=10,
        checksum_sha256="a" * 64,
        now=NOW,
        document_id="doc-1",
    )
    doc.mark_pending(now=NOW)
    return doc


def _use_case(documents, chunks, parser, embeddings) -> IndexDocumentUseCase:  # type: ignore[no-untyped-def]
    return IndexDocumentUseCase(
        documents=documents,
        chunks=chunks,
        storage=FakeStorage(),
        parser=parser,
        chunker=Chunker(chunk_size=10, chunk_overlap=2, token_counter=WhitespaceTokenCounter()),
        embeddings=embeddings,
        clock=FixedClock(),
    )


def test_successful_indexing_marks_indexed_and_stores_chunks() -> None:
    documents = FakeDocuments(_pending_document())
    chunks = RecordingChunks()
    parsed = ParsedDocument(
        blocks=[TextBlock("one two three. four five six. seven eight nine.", page_number=1)]
    )
    use_case = _use_case(documents, chunks, FakeParser(parsed), FakeEmbeddings())

    count = use_case.execute("doc-1")

    assert count > 0
    assert documents.doc.status is DocumentStatus.INDEXED
    assert documents.doc.chunk_count == count
    # Old chunks are cleared before new ones are added.
    assert chunks.log[0] == ("delete", "doc-1")
    assert ("add", count) in chunks.log


def test_empty_extraction_fails_document() -> None:
    documents = FakeDocuments(_pending_document())
    chunks = RecordingChunks()
    use_case = _use_case(documents, chunks, FakeParser(ParsedDocument(blocks=[])), FakeEmbeddings())

    with pytest.raises(NoExtractableTextError):
        use_case.execute("doc-1")

    assert documents.doc.status is DocumentStatus.FAILED
    assert documents.doc.error_message
    assert ("delete", "doc-1") in chunks.log  # partial cleanup


def test_embedding_failure_fails_document() -> None:
    documents = FakeDocuments(_pending_document())
    parsed = ParsedDocument(blocks=[TextBlock("alpha beta gamma", page_number=None)])
    use_case = _use_case(documents, RecordingChunks(), FakeParser(parsed), FailingEmbeddings())

    with pytest.raises(EmbeddingError):
        use_case.execute("doc-1")

    assert documents.doc.status is DocumentStatus.FAILED
    assert "ollama down" in (documents.doc.error_message or "")


def test_missing_document_raises() -> None:
    documents = FakeDocuments(_pending_document())
    parsed = ParsedDocument(blocks=[TextBlock("x y z", page_number=None)])
    use_case = _use_case(documents, RecordingChunks(), FakeParser(parsed), FakeEmbeddings())

    with pytest.raises(DocumentNotFoundError):
        use_case.execute("other")


def test_progress_callback_invoked() -> None:
    documents = FakeDocuments(_pending_document())
    parsed = ParsedDocument(blocks=[TextBlock("alpha beta gamma", page_number=None)])
    use_case = _use_case(documents, RecordingChunks(), FakeParser(parsed), FakeEmbeddings())

    seen: list[float] = []
    use_case.execute("doc-1", progress=seen.append)

    assert seen[-1] == 1.0
    assert seen == sorted(seen)  # monotonically non-decreasing
