# AGENT_TEAM.md

How agents on this project create and coordinate other agents. Read at plan time and
by any agent considering a spawn. Adapted from the AI-Dash starter (ADR-0005); this
repo adopted the governance **docs** only, so references here are to what actually
exists in the repo (no `scripts/agent-team.sh`, no `scripts/gate.sh` — the quality
gate is `.github/workflows/ci.yml` plus `scripts/test.ps1`).

## CONFIGS

```
auto_agents: ask
main_merge:  ask
max_agents:  5
```

- **auto_agents** — `true`: any agent may spawn sub-agents within the limits below;
  `false`: no spawning (an agent that spots a worthwhile one names it once and
  continues); `disabled`: no spawning and stop raising it; `ask`: undecided — Main
  asks at the first plan.
- **main_merge** — whether Main may merge PRs it classifies as purely mechanical
  (docs/tests/formatting only, no sensitive paths, < 400 lines) without the
  Administrator. `ask` until decided.
- **max_agents** — at most 5 agents for this project, per `AGENTS.md`.

Sensitive paths (always Administrator, regardless of size): dependency manifests and
lockfiles (`backend/pyproject.toml`, `backend/uv.lock`, `frontend/package*.json`),
`.github/`, CI/deploy config, database/schema, anything under `auth`/`security`,
`VERSION`, `CHANGELOG.md`, `AGENTS.md`, `AGENT_TEAM.md`.

## When to spawn

Spawn only when **all** hold:

1. **Real parallelism** — the work runs at the same time as the caller's, not merely
   instead of it. A step the caller must wait for is the caller's next step, not a spawn.
2. **Declared ownership** — the candidate can name the files it will change; prefer
   splitting work so two agents never touch the same files.
3. **Worth the setup** — more than ~3 tool calls of real work, and the spawn plus its
   report costs less than doing it inline.

Broad read-only search and independent review passes are the usual good fits; anything
whose result the caller needs in the same turn is better done inline or via a subagent
that reports back.

## Contract with a sub-agent

A sub-agent returns a short summary (≈20 lines max) with `file:line` references — never
raw file dumps or transcripts. It does not commit, tag, edit `VERSION`, or change CI.
Findings return to the caller, who decides.

## The quality gate

Before a change is considered done, the gate must pass: backend `ruff`, `mypy`, and
`pytest`; frontend `typecheck`, `lint`, and `vitest`. Run it with `scripts/test.ps1`
locally; CI runs the same checks on every push and PR.
