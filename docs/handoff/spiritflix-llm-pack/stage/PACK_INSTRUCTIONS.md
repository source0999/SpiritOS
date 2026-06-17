This pack contains only the SpiritFlix/Jellyfin-facing code from SpiritOS needed for LLM review or debugging.
Focus areas:
- SpiritFlix UI route, app shell, cards, rails, details modal, player, login, image handling.
- Jellyfin client wrappers and resume/playback helpers.
- SpiritFlix API proxy routes for Jellyfin, images, gallery, face metadata, and stream fallback.
- SpiritFlix-specific CSS and focused tests.
- Minimal Next/Vitest/package config so imports and runtime assumptions are understandable.
Do not infer unrelated SpiritOS modules are present unless imported by these files.
Recent operational context: the :3001 sidecar should stream directly to Jellyfin :8096 where possible instead of proxying video through /api/spiritflix/stream.
