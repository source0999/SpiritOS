# Fixes and Observations — Claude 3x10 Battery

## Fixes applied to Source Proxy

NONE. The battery exposed no blocker that required patching `source_proxy` or `src`.
The only authored artifact is the additive runner `scripts/source_proxy_claude_3x10_battery_runner.py`
plus disposable evidence under `docs/evidence/source-proxy-claude-3x10-audit-20260615/`.

The one design accommodation (not a proxy fix): the runner pre-seeds each disposable
target file with a placeholder before posting, because the proxy never creates files
(FIP-4 emits a proposed diff only) and a missing target under a non-`agent-lab` path
hits the `target_missing` gate. Pre-seeding lets the row exercise the real FIP-4
`replace_file` path. This mirrors how Level 5R2 used pre-seeded `level-5-targets/*.txt`.

## Observation O1 — concurrent unrelated repo activity during the run (NOT caused by battery)

During Set 2 (~2026-06-16 00:00 UTC) these tracked files changed on disk:

- `source_proxy/tasks/long_running.py` (repomix -> `npm run context:compress` migration)
- `package.json`, `package-lock.json` (new `context:compress` script + deps)
- `README.md`, `scripts/source-context-compress.mjs`

Evidence this was NOT the battery:
- Every one of the 30 battery rows had `diff_summary.changed_files` strictly inside
  `docs/evidence/source-proxy-claude-3x10-audit-20260615/targets/` (verified across all receipts).
- The proxy never applies coder diffs (FIP-4 produces `proposed_diff` only; no `write_text`
  of coder output exists in `decision.py`).
- The change is a coherent feature migration unrelated to any battery prompt.
- File mtimes cluster at 23:59-00:02 UTC, consistent with a human/agent multi-file edit.

Action taken: NONE. Per boundaries, I did not stage, commit, revert, or modify this
unrelated work. Recorded as a runtime-hygiene risk: the live proxy (pid 1632339) was
NOT restarted after these edits, so it keeps serving the previously loaded code while
the on-disk source diverges. This is the same staleness class as the documented
"Windows Z:\ edits not live until restart" warning, now observed live on Linux.

This does not affect battery integrity: the running proxy used its loaded code for all
30 rows, every row produced a durable receipt + matching FIP-6 trace.
