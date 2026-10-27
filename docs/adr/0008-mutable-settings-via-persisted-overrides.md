# ADR 0008: Mutable settings via persisted overrides

## Status

Accepted — 2026-10-27. Supersedes the "settings are read-only" deferral in ADR-0007.

## Context

ADR-0007 shipped read-only settings. The application needs a way to change tunables
(models, chunking, limits, concurrency) without editing `.env` by hand, while keeping
configuration validated and the running process stable.

## Decision

Add `PATCH /api/v1/settings` that persists a partial set of **overrides** to
`<config_dir>/overrides.json` (atomic write) under stable public keys, mapped to
`Settings` fields in `application/services/settings_overrides.py`.

- **Validation:** a patch is applied on top of the current settings and the result is
  constructed as a full `Settings`, so all field constraints and the cross-field rule
  (`chunk_overlap < chunk_size`) are enforced; invalid patches return `400` and are not
  persisted.
- **Apply on restart, not live:** overrides are loaded and applied in `create_app`
  (environment → overrides). The endpoint does not mutate the running process — many
  settings are captured when the container, worker, and clients are built, so changing
  them live would be unsafe. The response carries `requires_restart` and a message.
- **Reindex awareness:** changing the embedding model sets `requires_reindex: true`
  with a message, because vectors from different embedding models must not be mixed.
- **Layering:** a `SettingsOverridesStore` port (JSON implementation in infrastructure)
  keeps the use case off infrastructure; the apply/validate logic is a pure application
  service.

## Consequences

- Settings are changeable via the API and survive restarts; the committed
  `backend/openapi.json` now includes `PATCH /settings` (contract test enforces it).
- Applying on restart is a deliberate simplicity/safety trade-off; live hot-reload of
  settings (and a Settings edit form in the UI) remain possible future work.
