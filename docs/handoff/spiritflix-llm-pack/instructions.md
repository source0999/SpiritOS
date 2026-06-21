# SpiritFlix Mini Context Pack

This pack contains the SpiritFlix/Jellyfin-facing parts of SpiritOS for LLM review or debugging. It is intentionally scoped to the app, admin explorer, API routes, Jellyfin helpers, media scripts, focused docs, and minimal project config needed to understand imports and runtime assumptions.

## Focus Areas

- SpiritFlix user app: app shell, home rails/cards, details modal, login, image handling, video player, gestures, resume state, and focused tests.
- SpiritFlix admin: file-manager-first explorer, read-only filesystem APIs, action dialogs, thumbnails, smart tagging/review/batch support, path rules, and tests.
- Jellyfin integration: client wrapper, direct/proxy stream URLs, image/gallery routes, resume diagnostics, folder playlist sync, and deployment docs.
- Operational context: live SpiritOS normally runs on the Dell host; the stable SpiritFlix sidecar has historically used `:3001`, while Jellyfin uses `:8096`. Prefer current code over this note if they conflict.

## Boundaries

- Do not assume unrelated SpiritOS modules are present unless imported by included files.
- Do not infer secrets from omitted `.env*` files; this pack deliberately excludes them.
- Treat `stage/` as a source snapshot for convenience. The authoritative packed views are `spiritflix-only-repomix.md` and `spiritflix-only-repomix.xml`.
