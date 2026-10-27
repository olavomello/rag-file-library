# Decisions

Append only. One line each: `YYYY-MM-DD — decision — reason`. Durable decisions that
don't warrant a full ADR; significant ones link to an ADR in `docs/adr/`.

- 2026-10-26 — Use `uv`-managed Python 3.12 for the backend — system Python is 3.9; `uv` gives a reproducible 3.12 toolchain (ADR-0001).
- 2026-10-26 — ChromaDB is the only database; registry metadata in a collection, job state in atomic JSON — honours "ChromaDB only" while keeping frequently-updated job state transparent (ADR-0002).
- 2026-10-26 — Always pass embeddings explicitly to ChromaDB — `embedding_function=None` still attaches a default model that would download ~79MB and break offline operation (ADR-0002).
- 2026-10-27 — Indexing is all-or-nothing and search is restricted to INDEXED documents — a document is never exposed partially indexed (ADR-0003, ADR-0004).
- 2026-10-27 — Background indexing runs as an in-process asyncio worker — no Redis/Celery; satisfies §13 with restart recovery and persisted jobs (ADR-0003).
- 2026-10-27 — Commit once per completed build phase on its `feat/phase-N-*` branch — keeps phase history reviewable; push/merge on request.
- 2026-10-27 — Adopt the AI-Dash governance layer (management-docs scope only) — fills the project-management gap without changing the app or agent runtime (ADR-0005).
- 2026-10-27 — RAG chat answers only from retrieved context, cites only real sources, and skips the LLM when retrieval is empty — grounded, injection-safe answering that keeps search and generation independent (ADR-0006).
- 2026-10-27 — Frontend is feature-based with a typed service layer; chat streams over NDJSON; Settings is read-only for now (ADR-0007).
- 2026-10-27 — Commit the OpenAPI spec at backend/openapi.json (Insomnia/Postman importable) and enforce freshness with a contract test; regenerate via scripts/export_openapi.py after any endpoint change (ADR-0007).
