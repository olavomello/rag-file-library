# ADR 0001: Foundation, stack, and environment constraints

- **Status:** Accepted
- **Date:** 2026-10-26

## Context

Private RAG is built per the master specification in `AGENTS.md`. Phase 1
establishes the monorepo, backend, frontend, tooling, and CI foundation. Several
environment realities on the development machine shape these decisions.

## Decisions

1. **Clean Architecture + TDD.** The backend is split into `domain`, `application`,
   `infrastructure`, and `presentation` layers. Dependencies point inward; the domain
   has no framework/I/O imports. Features are built test-first.

2. **`uv` manages the backend Python environment.** The system `python` is 3.9, which
   does not satisfy the required 3.12+. `uv` provides a managed CPython 3.12.14, so all
   backend commands run through `uv run`. This keeps the toolchain reproducible via
   `uv.lock`.

3. **ChromaDB embedded persistent client is the only database.** No separate server,
   and no additional relational/document/cache database is introduced in V1.

4. **Explicit dependency injection via a `Container`.** A single composition root wires
   infrastructure implementations to application ports. No DI framework is used.

5. **Health endpoints degrade gracefully.** `/health` is a pure liveness probe.
   `/health/ollama` and `/health/chroma` are readiness probes that return `503` with a
   descriptive body when a dependency is unavailable, rather than failing the process.

## Environment constraints (and their consequences)

- **Ollama is not installed / not serving** on this machine. Per `AGENTS.md` §27,
  Ollama-dependent adapters (embeddings, generation) are developed behind application
  ports and verified with mocks/fakes. Real end-to-end verification against Ollama is
  deferred and will be explicitly marked as unverified until a local Ollama with the
  required models is available.

- **The AI-Dash starter (`olavomello/ai-project-starter`) is inaccessible** — the
  repository returns HTTP 404 (private or renamed). `AGENTS.md` names it as the
  Priority-1 base. Since it cannot be read, the architecture is implemented directly
  from the fully self-contained `AGENTS.md` specification. If the starter becomes
  accessible, its security/agent-management/base patterns should be reconciled against
  this foundation in a follow-up ADR.

## Consequences

- The app runs and is testable today without Ollama; AI features are reachable but
  report unavailability until models are pulled.
- CI runs backend (ruff, mypy, pytest) and frontend (typecheck, lint, vitest) checks
  without requiring Ollama.
