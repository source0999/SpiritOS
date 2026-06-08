# Increment 3.4 - Obsidian Context Smoke

Status: passed.

Verified:
- Disabled by default.
- Missing vault path fails safely.
- Excluded folders are respected.
- Only `.md` notes are scanned.
- No writes occur.
- Small relevant excerpts are selected.
- Diagnostics show paths/counts/chars without unsafe dumps.

Focused tests:
- `source_proxy.tests.test_obsidian_context`
- `source_proxy.tests.test_self_status`
- `source_proxy.tests.test_prompt_packet_context_metadata`

Result:
- 42 tests passed across context metadata, Obsidian, and self-status.

Live status:
- `/v1/self/status`: `obsidian_context_enabled=false`, `obsidian_status=disabled`, `obsidian_read_only=true`, include globs present.

Manual/self-check:
- Obsidian context remains optional/read-only/disabled-by-default.
- Live prompt packet exposes Obsidian diagnostics summary, not raw note bodies.
