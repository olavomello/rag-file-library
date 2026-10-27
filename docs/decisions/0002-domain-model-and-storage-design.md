# ADR 0002: Domain model and storage design (Phase 2)

- **Status:** Accepted
- **Date:** 2026-10-26

## Context

Phase 2 implements the domain entities and the persistence layer: document
metadata, chunk vectors, and indexing-job state. `AGENTS.md` requires ChromaDB to
be the only database, allows local JSON files for durable operational state, and
mandates local-first, offline operation.

## Decisions

1. **Entities are plain dataclasses** in the domain layer with no framework or I/O
   imports. Business rules live on the entities: `Document` enforces its lifecycle
   (`uploaded → pending → processing → indexed`, with `failed`/`deleting` branches,
   reindex via `indexed → pending`, retry via `failed → pending`) and raises
   `InvalidStateTransitionError` on illegal moves. Identifiers and timestamps are
   injected (callers pass `now`) to keep entities deterministic and testable.

2. **Repository contracts live in `domain/repositories`** as `Protocol`s referencing
   only domain types. They are synchronous, matching ChromaDB's embedded client and
   the filesystem; the application layer will offload them to threads where needed to
   avoid blocking the event loop.

3. **Chunk vectors → ChromaDB collection `document_chunks`** (cosine space). The
   repository accepts embeddings explicitly, so it is model-agnostic and testable
   with deterministic vectors.

4. **Document registry → ChromaDB collection `document_registry`.** To honour "all
   metadata in ChromaDB" while never running similarity over the registry, each
   record carries a constant one-dimensional placeholder embedding and is accessed
   only by id, by `$in` metadata filters, and by full scans (the registry is small).
   Timestamps/enums are serialized to strings; `None` is stored as `""`.

5. **Indexing-job state → durable JSON files** (one `<job_id>.json` per job) under
   `data/jobs`, written atomically (temp file + `os.replace`). Job state is simple
   operational data that must survive restarts; JSON keeps it transparent and avoids
   forcing placeholder vectors through ChromaDB for frequently-updated records.

6. **Explicit-embeddings invariant.** ChromaDB's `embedding_function=None` does **not**
   disable its default model — if `add`/`update`/`query` is ever called without
   embeddings, ChromaDB downloads and runs a ~79 MB ONNX model. Every write therefore
   passes embeddings explicitly (real vectors for chunks, the placeholder for the
   registry) and every search passes `query_embeddings`. This preserves offline
   operation and keeps tests fast and network-free.

7. **Single embedded client.** `ChromaClientProvider` lazily creates one
   `PersistentClient` per process, owned by the DI `Container`, satisfying the
   single-writer requirement. Telemetry is disabled.

## Consequences

- The full persistence layer is implemented and tested without Ollama (storage needs
  no embedding model; vectors are supplied by tests).
- Repository implementations are wired into the container as their port types, so the
  type checker verifies structural conformance.
- Future knowledge-base filtering is a metadata-filter addition, not a schema change.
