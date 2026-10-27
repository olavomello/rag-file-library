# ADR 0007: Frontend application and shared OpenAPI spec (Phase 7)

- **Status:** Accepted
- **Date:** 2026-10-27

## Context

Phase 7 delivers the user-facing React application wired to the API, and adds a
committed OpenAPI document so the API can be imported into Insomnia, Postman, and
other readers.

## Decision

1. **Feature-based React app** (Vite + TypeScript + Tailwind + TanStack Query) with a
   typed API layer in `src/services/` over a small `apiClient` (GET/POST/DELETE,
   multipart upload, and an NDJSON streaming reader). Pages:
   - **Dashboard** — live stats (`/dashboard/stats`), infrastructure health, model status.
   - **Documents** — drag-and-drop upload, table with status/chunk counts, content
     preview, download, reindex, and delete (with confirm); auto-refreshes while any
     document is pending/processing.
   - **Search** — semantic search results with document, page, excerpt, and raw distance.
   - **AI Chat** — streamed answers over `/chat/stream` (NDJSON `sources → token → done`),
     rendered sources, "not grounded" marker, and new-conversation reset.
   - **Settings** — read-only effective configuration plus model availability and the
     embedding-model reindex warning. (A write/PATCH settings flow is deferred.)

2. **Two backend read endpoints** added to feed the UI without leaking internals:
   `GET /dashboard/stats` and `GET /settings` (safe subset; no filesystem paths).

3. **Committed OpenAPI spec at `backend/openapi.json`**, generated from the live
   FastAPI app by `backend/scripts/export_openapi.py`. A contract test
   (`tests/contract/test_openapi_current.py`) compares the committed file to the app's
   schema and fails if they diverge, so the spec stays current as endpoints change.
   The live schema remains at `/openapi.json` with Swagger UI at `/docs`.

## Consequences

- The app is usable end to end in the browser against the API.
- The API is importable into Insomnia/Postman from one file, and CI guarantees that
  file matches the code. Regenerate after any endpoint change:
  `uv run python scripts/export_openapi.py`.
- Frontend: typecheck + lint clean, 6 Vitest tests, production build passing. Chat
  streaming and search ranking are proven with the backend's fake-model tests; real
  generation quality still depends on a running Ollama.
