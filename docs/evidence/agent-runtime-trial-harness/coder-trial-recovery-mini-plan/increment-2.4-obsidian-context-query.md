# Increment 2.4 - Obsidian Context Query

## Endpoint

Added:

```text
POST /v1/context/obsidian/query
```

Request:

```json
{"task":"find relevant notes for this task"}
```

Response includes:

- `status`
- `notes[].title`
- `notes[].path`
- `notes[].safe_excerpt`
- `notes[].why_matched`
- `notes[].char_estimate`
- `notes[].used_in_prompt_context`
- `diagnostics`

## Query behavior

- Disabled config returns no notes and does not scan.
- Enabled config with no vault path returns `missing_vault_path`.
- Candidate files are repo/vault-relative markdown files matching include globs and not matching exclude globs.
- Selection is small and bounded by `OBSIDIAN_MAX_NOTES`.
- Excerpts are redacted/truncated by `OBSIDIAN_MAX_CHARS_PER_NOTE`.

## Self-check

- Query returns small relevant context: yes.
- Excluded/private folders omitted: yes.
- Why notes matched is shown: yes.
- Can be turned off: yes, default off.
