# ADR 0003: Ingestion pipeline and background indexing (Phase 4)

- **Status:** Accepted
- **Date:** 2026-10-27

## Context

Phase 4 turns uploaded documents into searchable, embedded chunks: parsing,
chunking, embedding, vector storage, and an asynchronous indexing worker with job
tracking — all local, CPU-friendly, and resilient to restarts.

## Decisions

1. **Parser port with per-format adapters.** A `DocumentParserRegistry` selects a
   parser by extension: PyMuPDF for PDF (per-page, 1-based page numbers), python-docx
   for DOCX, and stdlib for TXT/Markdown. OCR is opt-in (see ADR-0009): with it off, a
   PDF with no text layer raises `NoExtractableTextError`; with it on, such pages (and
   image uploads) are read via a local `OcrProvider`. Corrupted files raise
   `DocumentExtractionError`. Output is a `ParsedDocument` of page-aware `TextBlock`s.

2. **Chunking.** Paragraph-first splitting, falling back to sentences and then fixed
   word windows only when a single sentence exceeds the budget; a configurable token
   overlap is carried between chunks; page numbers are preserved; chunk ids are
   deterministic (`<document_id>:<index>`). Token counting uses a whitespace-word
   approximation behind a `TokenCounter` port (documented as conservative); a
   model-accurate counter can replace it without touching chunking.

3. **Embeddings behind a port.** `EmbeddingProvider` is implemented by
   `OllamaEmbeddingProvider` (local `/api/embed`, injectable HTTP client). The chunk
   store records the embedding model so vectors from different models are never mixed.
   Because Ollama is not installed in this environment, the adapter is unit-tested with
   a mocked transport, and the full pipeline is integration-tested with a fake provider;
   **real embedding against Ollama is unverified** (per `AGENTS.md` §27).

4. **Index use case is all-or-nothing.** `IndexDocumentUseCase` marks the document
   `processing`, parses, chunks, embeds, then replaces the document's chunks and marks
   it `indexed`. On any failure it removes partial chunks and marks the document
   `failed` with a message, so a document is never left partially indexed. Reindex
   deletes-then-adds; since a document is excluded from search unless `indexed`
   (enforced in Phase 5), a reindex in flight never exposes partial results.

5. **In-process background worker.** A bounded set of asyncio tasks
   (`INDEXING_CONCURRENCY`, default 1) consume document ids from an in-memory queue and
   run the synchronous pipeline via `asyncio.to_thread`, keeping the event loop
   responsive. Job state is persisted (JSON) with progress; duplicate in-flight work is
   suppressed; failed jobs are retried via an explicit endpoint; and on startup
   `recover()` re-enqueues jobs left `pending`/`running` by a previous process
   (`processing → pending` is an allowed transition for this reason). Shutdown cancels
   workers; any interrupted job is recovered next start. No Redis/Celery/etc.

## Consequences

- Upload now queues background indexing; without Ollama, documents reach `failed`
  (embedding unavailable) rather than `indexed` — expected until models are pulled.
- New endpoints: `GET /documents/{id}/content`, `POST /documents/{id}/reindex`,
  `GET /indexing/jobs`, `GET /indexing/jobs/{id}`, `POST /indexing/jobs/{id}/retry`.
- Phase 5 semantic search must restrict results to `indexed` documents.
