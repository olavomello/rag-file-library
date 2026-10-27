# Private RAG — Roadmap

Phased delivery of the application described in `AGENTS.md`, built with Clean
Architecture and Test-Driven Development. Each phase is developed on its own
`feat/phase-N-*` branch and committed when its tests, linting, and type checks pass.

## Status legend

- ✅ Done — implemented, tested (unit + integration), ruff + mypy clean
- 🚧 In progress
- ⬜ Not started

## Phases

| # | Phase | Status | Notes |
|---|-------|--------|-------|
| 1 | Foundation (monorepo, FastAPI, React, config, health, CI) | ✅ | `2b17af2` |
| 2 | Domain model & storage (entities, ChromaDB, filesystem, jobs) | ✅ | `d2c9293` |
| 3 | Document upload (validation, checksum, dedupe, CRUD) | ✅ | `31e18cc` |
| 4 | Ingestion (parsers, chunking, embeddings, background worker) | ✅ | `1621969` |
| 5 | Semantic search (LLM-free retrieval endpoint) | ✅ | `d1ad137` |
| 6 | RAG engine (retrieval, prompt, Ollama generation, streaming, citations) | ⬜ | |
| 7 | Frontend (dashboard, documents, search, chat, settings) | ⬜ | Shell + health dashboard exist from Phase 1 |
| 8 | Testing & quality (coverage, architecture boundaries, offline) | ⬜ | Ongoing per phase |
| 9 | Documentation & delivery (README, ADRs, final report) | 🚧 | ADRs 0001–0004 written |

## Test status

Backend: **147 tests passing**; ruff and mypy clean. Frontend: typecheck + lint
clean, component tests passing, production build working.

## Verified vs. unverified

- **Verified now:** config, health endpoints, domain model & lifecycle, ChromaDB +
  filesystem storage, upload/list/get/download/delete, parsing (PDF/DOCX/TXT/MD),
  chunking, background indexing + jobs, and semantic search — the ingestion and
  search pipelines proven end-to-end with a deterministic **fake** embedding model.
- **Unverified (environment):** real embeddings/generation via **Ollama** (not
  installed on the dev machine). Adapters are implemented behind ports and tested
  with mocks per `AGENTS.md` §27; real runs are pending `ollama pull qwen3:0.6b`
  and `ollama pull embeddinggemma`.

## AI-Dash base

`AGENTS.md` names `olavomello/ai-project-starter` (AI-Dash) as the Priority-1 base.
It was initially unreachable (HTTP 404), so Phases 1–5 were built directly from the
self-contained `AGENTS.md` spec ([ADR-0001](docs/adr/0001-foundation-and-environment-constraints.md)).
The repository is now public, and its **governance layer** (ADR structure, decisions
log, task taxonomy, repo map, `AGENT_TEAM.md`, SemVer, guides) has been adopted at the
management-docs scope ([ADR-0005](docs/adr/0005-adopt-ai-dash-governance-layer.md)).
The enforcement layer (Claude Code hooks, the "gate" workflow, dashboard, CLI/scripts)
was deliberately **not** adopted yet and can be in a follow-up ADR.

## Architecture decision records

- [0001 — Foundation & environment constraints](docs/adr/0001-foundation-and-environment-constraints.md)
- [0002 — Domain model & storage design](docs/adr/0002-domain-model-and-storage-design.md)
- [0003 — Ingestion pipeline & background indexing](docs/adr/0003-ingestion-pipeline-and-background-indexing.md)
- [0004 — Semantic search](docs/adr/0004-semantic-search.md)
- [0005 — Adopt the AI-Dash governance layer](docs/adr/0005-adopt-ai-dash-governance-layer.md)
