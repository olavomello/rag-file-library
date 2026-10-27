# ADR 0005: Adopt the AI-Dash governance layer (management-docs scope)

- **Status:** Accepted
- **Date:** 2026-10-27

## Context

`AGENTS.md` names `olavomello/ai-project-starter` (AI-Dash) as the Priority-1 base.
At the start of the build that repository returned HTTP 404 and could not be read, so
the architecture was built directly from the self-contained `AGENTS.md` spec (see
ADR-0001). The Administrator has now made AI-Dash public.

On inspection, AI-Dash is a **Claude Code project-starter / governance layer**, not
application code: its `template/` provides an agent-team policy, an ADR structure, a
decisions log, a task taxonomy, a repo map, SemVer (`CHANGELOG.md` + `VERSION`),
reference guides, and (optionally) Claude Code hooks, a quality "gate" workflow, and a
self-hosted dashboard with Node scripts. It is complementary to the Private RAG
backend/frontend, which already follow `AGENTS.md`.

## Decision

Adopt the **management-docs** subset of AI-Dash, chosen by the Administrator, without
changing the application architecture or agent runtime behaviour:

- Migrate existing ADRs to `docs/adr/` and add AI-Dash's `template.md` and an index.
- Add `docs/decisions.md` (append-only log), `docs/tasks.md` (task taxonomy),
  `docs/repo-map.md`, and `AGENT_TEAM.md` (spawn/merge policy), adapted to this repo.
- Add `CHANGELOG.md` (Keep a Changelog) and `VERSION` (SemVer), seeded at `0.1.0`.
- Add `docs/guides/` with `delegation.md`, `efficiency.md`, and `security.md`, adapted
  to this stack.

Deliberately **not** adopted in this scope (deferred, can be a later ADR):

- `.claude/` hooks, `settings.json` denials, and the `semver-release` skill — they
  change agent/CI behaviour and the existing `.github/workflows/ci.yml` already runs
  the quality gate (ruff, mypy, pytest, frontend checks).
- The AI-Dash CLI, desktop app, mods, dashboard (`ai-dash/`), and `scripts/*.mjs`.
- `docs/guides/claude-code.md` — it describes the `CLAUDE.md`→`AGENTS.md` import and
  mod machinery this project does not use, so it would be misleading here.

The project's own `AGENTS.md` (the RAG master prompt) and `README.md` are kept; they
are not overwritten by AI-Dash's generic versions.

## Consequences

- The project-management gap the Administrator noticed is filled with the AI-Dash
  conventions, and future work follows that structure (ADRs, decisions log, tasks).
- Governance guidance is now committed and tool-agnostic, readable by any agent.
- A follow-up ADR can adopt the enforcement layer (hooks, gate, dashboard) if wanted;
  `ai-project-starter adopt`/`update` can track the baseline from here.
