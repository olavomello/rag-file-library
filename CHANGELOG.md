# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- **Phase 1 — Foundation:** monorepo, FastAPI backend (Clean Architecture), React/Vite/Tailwind frontend, validated settings, health endpoints, CI, and Windows scripts.
- **Phase 2 — Domain & storage:** domain entities and lifecycle, repository ports, embedded ChromaDB chunk + document-registry repositories, path-safe filesystem storage, and atomic JSON indexing-job store.
- **Phase 3 — Document upload:** validation (type/size/signature/UTF-8), SHA-256 duplicate detection, and upload/list/get/download/delete endpoints.
- **Phase 4 — Ingestion:** PDF/DOCX/TXT/MD parsers, chunking with overlap and page numbers, Ollama embedding adapter, all-or-nothing index use case, and an in-process background indexing worker with job tracking, retry, and restart recovery; content/reindex/indexing-jobs endpoints.
- **Phase 5 — Semantic search:** LLM-free `POST /api/v1/search/semantic`, scoped to indexed documents.
- **Governance:** adopted the AI-Dash management layer (ADRs under `docs/adr/`, `docs/decisions.md`, `docs/tasks.md`, `docs/repo-map.md`, `AGENT_TEAM.md`, guides) — see ADR-0005.

### Notes
- Real Ollama embedding/generation is unverified on the dev machine (Ollama not installed); adapters are tested with mocks and the pipeline end-to-end with a fake embedder.
