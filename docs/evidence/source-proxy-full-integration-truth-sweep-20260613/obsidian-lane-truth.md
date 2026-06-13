# Obsidian Lane Truth

## Existing Files

- `source_proxy/context/obsidian.py`
- `source_proxy/api/obsidian_context.py`
- `source_proxy/tests/test_obsidian_context.py`
- prompt/coder diagnostics references in `source_proxy/tasks/long_running.py`

## What Exists

There is a read-only Obsidian context source:

- Config from `OBSIDIAN_CONTEXT_ENABLED`, `OBSIDIAN_VAULT_PATH`, include/exclude globs, max notes, and max chars.
- Default local vault path is `data/design-vault`.
- Query function can score Markdown notes and return safe excerpts.
- API route exists at `/v1/context/obsidian/query`.

## Live Prompt Wiring

Current coder diagnostics include Obsidian diagnostics, but the base diagnostics explicitly set:

- `obsidian_context_used_in_prompt: False`
- `memory_context_diagnostics: obsidian_context_diagnostics()`

`_coder_context_packet_summary()` also includes `obsidian_context_summary`, but it is a diagnostics summary, not selected note content.

Recent Level 3/4 artifact evidence did not show Obsidian context invocation. Status: WIRED_UNUSED for manual/query capability; NOT_INVOKED in recent artifact runs.

## Needed Wiring

- Add context-needed router step before model call.
- If Obsidian is useful, call `query_obsidian_context(task)`.
- Insert bounded note excerpts into the context packet.
- Prevent secret/private note paths by existing globs and receipt redaction.
- Emit explicit positive/negative receipt fields.

## Receipt Fields

- `obsidian_needed`
- `obsidian_enabled`
- `obsidian_vault_path_configured`
- `obsidian_query_run`
- `obsidian_notes_considered`
- `obsidian_notes_selected`
- `obsidian_context_chars`
- `obsidian_context_paths`
- `used_in_model_prompt`
- `skip_reason`
