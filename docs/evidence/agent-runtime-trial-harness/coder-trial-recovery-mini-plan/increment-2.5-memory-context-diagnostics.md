# Increment 2.5 - Memory Context Diagnostics

## Diagnostics added

The Obsidian helper reports:

- `obsidian_context_enabled`
- `obsidian_context_used`
- `obsidian_notes_considered`
- `obsidian_notes_selected`
- `obsidian_context_chars`
- `obsidian_context_paths`

Additional safety/config diagnostics:

- `obsidian_status`
- `obsidian_vault_path_configured`
- `obsidian_include_globs`
- `obsidian_exclude_globs`
- `obsidian_max_notes`
- `obsidian_max_chars_per_note`
- `obsidian_read_only`

## Surfaces

- `/v1/self/status`
- `/v1/context/index`
- `/v1/context/obsidian/query`
- Prompt packet `context_metadata.memory_context_diagnostics`

## Tests

Passed:

```text
.venv-source-proxy/bin/python -m unittest source_proxy.tests.test_obsidian_context source_proxy.tests.test_self_status source_proxy.tests.test_prompt_packet_context_metadata
```

Result: `Ran 42 tests ... OK`.

## Self-check

- Diagnostics show whether Obsidian was used: yes.
- If unused, status says disabled/missing/no relevant notes: yes.
- No note content is copied into status diagnostics: yes.
