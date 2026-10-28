# API

Base path: `/api/v1`. Interactive docs (Swagger UI) at `/docs`; the live schema at
`/openapi.json`. The full spec is also committed at
[`backend/openapi.json`](../../backend/openapi.json) for import into Insomnia, Postman,
or any OpenAPI reader. Regenerate it after any endpoint change:

```bash
cd backend
uv run python scripts/export_openapi.py
```

A contract test (`tests/contract/test_openapi_current.py`) fails if the committed spec
drifts from the code.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| GET | `/health/ollama` · `/health/chroma` | Dependency readiness |
| POST | `/documents/upload` | Upload a document (queues indexing) |
| GET | `/documents` | List documents (optional `?status=`) |
| GET | `/documents/{id}` | Document metadata |
| GET | `/documents/{id}/content` | Extracted text |
| GET | `/documents/{id}/download` | Original file |
| POST | `/documents/{id}/reindex` | Re-queue for indexing |
| DELETE | `/documents/{id}` | Delete document + chunks + file + job |
| GET | `/indexing/jobs` · `/indexing/jobs/{id}` | Indexing jobs |
| POST | `/indexing/jobs/{id}/retry` | Retry a job |
| POST | `/search/semantic` | Semantic search (no LLM) |
| POST | `/chat` | Grounded answer with sources |
| POST | `/chat/stream` | Streaming answer (NDJSON: `sources` → `token` → `done`) |
| GET | `/models` · `/models/status` | Configured models and availability |
| POST | `/models/pull` | Download a model into Ollama (NDJSON progress) |
| GET | `/dashboard/stats` | Document/chunk/job counts |
| GET | `/settings` | Effective configuration (no filesystem paths) |
| PATCH | `/settings` | Update settings overrides (persisted; applied on restart) |

Errors use consistent HTTP codes: `400` invalid input, `404` not found, `413` too
large, `415` unsupported type, `422` schema validation.
