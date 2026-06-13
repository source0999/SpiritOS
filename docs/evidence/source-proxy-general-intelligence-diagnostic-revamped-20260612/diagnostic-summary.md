# Source Proxy Revamped Product Diagnostic - 2026-06-12

Mode: existing `run_human_messy_homepage(..., mode="product")` path. Prompts are blunt; no target hints were added. Evidence is in disposable workspaces only.

| prompt | source proxy status | behavior truth | files | html | reason codes |
|---|---|---|---:|---|---|
| init a repo and make homepage for agent lab expermients | GO | PASS | 1 | index.html |  |
| make a timer app | GO | PASS | 3 | index.html |  |
| make a calculator app | GO | PASS | 3 | index.html |  |
| make dark theme switcher page | GO | PASS | 3 | dark-theme-switcher.html |  |
| make a todo list app | GO | PASS | 3 | index.html |  |
| make a weather card demo | GO | PASS | 3 | weather-card.html |  |
| make a music player mockup | EXPECTED-BLOCKED | FAIL | 0 |  | no_artifact_files |
| make a habit tracker | GO | FAIL | 3 | habit_tracker.html | habit_controls_or_state_change_missing |
| make a notes app | GO | FAIL | 1 |  | notes_create_edit_interaction_missing |
| make a password strength checker | EXPECTED-BLOCKED | FAIL | 0 |  | no_artifact_files |
| make a simple drawing pad | EXPECTED-BLOCKED | FAIL | 0 |  | no_artifact_files |

## Anti-cheat / hand-holding visibility

- The model prompt and raw response are preserved in each `transcript.txt` and `evidence-packet.json`.
- Per-run receipts preserve model calls, context packets, parsed actions, executions, and diagnostics.
- The batch used the product route context; it did not provide exact target filenames unless the existing intake contract did so.
- Browser behavior checks were not run inside this generation batch; static behavior probes are labeled accordingly.

## Files

- `manifest.json`
- `runs/<slug>/receipt.json`
- `runs/<slug>/score.json`
- `runs/<slug>/transcript.txt`
- `runs/<slug>/workspace.diff`
- `runs/<slug>/evidence-packet.json`
- `runs/<slug>/workspace/*`
