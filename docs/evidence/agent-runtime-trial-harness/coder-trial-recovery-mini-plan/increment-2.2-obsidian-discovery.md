# Increment 2.2 - Obsidian Discovery

## Discovery performed

Checked only configuration and repo-adjacent hints:

- Dell host: `printenv | grep '^OBSIDIAN_' || true`
- Dell repo-limited find: `find . -maxdepth 3 \( -name '.obsidian' -o -iname '*obsidian*' \) ...`
- Windows PowerShell session: checked `OBSIDIAN_*` environment variables.

## Findings

- No `OBSIDIAN_*` configuration was present in the active sessions.
- No vault path is known.
- Repo-limited search found only the newly added Obsidian integration/test files.
- The Windows-side recursive hint command timed out after reporting no `OBSIDIAN_*` env vars; no whole-machine scan was pursued.

## Decisions

- Add config placeholders.
- Keep integration disabled by default.
- Read `.md` only by default.
- Exclude `.obsidian/**`, `private/**`, `secrets/**`, and `archive/**` by default.
- Fail safely when no vault path is configured.
- Do not scan the whole filesystem.
- Do not write to notes.

## Self-check

- Unknown vault path reported: yes.
- No broad filesystem scan: yes.
- Read-only first: yes.
- Secrets/private folders excluded by default: yes.
