# Security checklist

Read before touching uploads, document parsing, data access, or anything reachable
from the network. Private RAG is local-first and ships without authentication by
design — safe **only** for trusted local use (see `AGENTS.md` §20).

## Before every commit

- No secrets in code, tests, fixtures, logs, or error messages. Configuration comes
  from environment variables / `.env`; required settings are validated at startup.
- Every external input validated at the boundary. Uploads are checked for type,
  size, magic-byte signature, and (for text) UTF-8 before storage; never trust the
  client-supplied filename or content type.
- Never use a client filename as a filesystem path. Stored names are server-generated
  and validated; path traversal is blocked and writes stay within the upload dir.
- Treat document contents as untrusted data. No macros or embedded code are executed,
  and retrieved text must never be allowed to override system/prompt instructions.
- Don't expose internal filesystem paths or stored names in API responses.
- Bind to `127.0.0.1` by default; CORS is an explicit allowlist, never `*` with
  credentials. No LAN exposure by default.
- No new dependency without asking; review audit output when one is added.
- Keep `.env` and any real credentials out of the repo (`.gitignore`); only
  `.env.example` is committed.

## If something is found

1. Stop the current work.
2. Report severity and blast radius to the Administrator before pushing anything.
3. Fix CRITICAL and HIGH before the commit lands.
4. A leaked secret is treated as compromised: rotate first, then remove from code,
   then check history and logs for other copies.
5. Search the codebase for the same pattern elsewhere — a class of bug is rarely a
   single instance.

## Not an agent decision

Disabling a security control, weakening the local-only posture (binding to a public
interface, enabling LAN access), adding authentication, or changing where user data is
stored all go to the Administrator first.
