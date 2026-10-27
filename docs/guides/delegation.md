# Delegation

Read when deciding whether to hand work to a sub-agent. Default is to do the work
inline. This project allows at most 5 agents (`AGENTS.md`); see `AGENT_TEAM.md` for
the spawn policy.

## When to delegate

- Broad search across many files where only the conclusion is needed.
- Genuinely independent work that can run in parallel.
- A review pass that benefits from not having written the code.

Not for: anything under ~3 tool calls, or work whose context you already hold.

## Contract with a sub-agent

The sub-agent returns a summary of at most ~20 lines with `file:line` references —
never raw file contents, never a transcript. It does not commit, tag, edit `VERSION`,
or change CI. Findings come back to the caller, who decides.

## Reviewers by change type

Match the change; don't fan out. One reviewer per change:

| Change | Reviewer focus |
|---|---|
| ChromaDB / storage / data migration | storage & data-integrity review |
| Uploads, parsing, anything network-reachable | security review (see `docs/guides/security.md`) |
| Backend type/build/CI failures | fix the gate (`ruff`, `mypy`, `pytest`) |
| Everything else | the language reviewer for that stack (Python / TypeScript) |
