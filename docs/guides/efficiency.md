# Efficiency

Read when tuning cost, routing models, or calling an LLM API directly. For this
project, all inference is local (Ollama); the notes below still apply to any direct
API use and to session hygiene.

## Model routing

- Mechanical work (rename, format, fill a template, summarize logs, mass edits) goes
  to the small fast model.
- Architecture, security review, ambiguous specs, and anything irreversible go to the
  strongest model.
- The cost of a wrong answer decides the model, not the size of the diff.

## Prompt caching (direct API use)

- Order the prompt **stable → volatile**: system rules, `AGENTS.md`, tool definitions,
  reference docs first; task input and conversation last.
- Nothing dynamic in the stable prefix — a timestamp or request id invalidates the
  cache from that point on.
- Watch the cache-read vs. cache-creation token ratio; a low read ratio means the
  prefix isn't actually stable.

## Session hygiene

- One task per session; start fresh context between unrelated tasks.
- Compact at milestones — after a spec is agreed, after a module lands — keeping
  decisions and open items, dropping exploration.
- Avoid the last 20% of the context window for multi-file refactors.

## Project memory (committed, shared)

| File | Content | Invalidate when |
|---|---|---|
| `docs/repo-map.md` | Directory map, entry points, key modules (≤150 lines) | Structure changes |
| `docs/decisions.md` | One line per durable decision, with date | Never — append only |
| `docs/adr/` | Full architecture decision records | Superseded (add a new ADR) |

This is the project's own memory — committed and reviewed in PRs — distinct from an
agent tool's per-machine auto memory, which is never a source of truth here.
