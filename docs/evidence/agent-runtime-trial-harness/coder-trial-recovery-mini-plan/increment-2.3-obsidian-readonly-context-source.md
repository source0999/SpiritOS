# Increment 2.3 - Obsidian Read-only Context Source

## Implementation

Added:

- `source_proxy/context/obsidian.py`
- `source_proxy/api/obsidian_context.py`
- `source_proxy/main.py` route registration
- `source_proxy/self_status.py` memory-context diagnostics
- `source_proxy/decision/prompt_packet.py` context metadata diagnostics

## Config shape

- `OBSIDIAN_CONTEXT_ENABLED=false`
- `OBSIDIAN_VAULT_PATH=`
- `OBSIDIAN_INCLUDE_GLOBS=*.md`
- `OBSIDIAN_EXCLUDE_GLOBS=.obsidian/**, private/**, secrets/**, archive/**`
- `OBSIDIAN_MAX_NOTES=`
- `OBSIDIAN_MAX_CHARS_PER_NOTE=`

## Safety

- Disabled by default.
- Missing vault path returns `missing_vault_path`.
- Excluded folders are filtered before reading.
- Only markdown files are candidates by default.
- The integration only reads files and returns safe excerpts.
- No Obsidian note write/update/delete path was added.

## Self-check

- Disabled-by-default confirmed by tests: yes.
- Missing vault path fails safely: yes.
- Excluded folders respected: yes.
- Read-only status appears in diagnostics: yes.
