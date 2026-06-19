# SpiritFlix Smart Tagging S8.1 Baseline

Captured: 2026-06-19

Raw baseline:

- `raw/00-baseline.txt`

Starting commits:

- `f5638db1 feat: finish SpiritFlix smart tagging review and rename preview workflow`
- `537b1044 feat: add SpiritFlix smart tagging batch analysis`

Scope:

- Patch SpiritFlix smart-tagging UI/API/tests only.
- Evidence lives under `docs/evidence/spiritflix-smart-tagging-s8-operator-results-visibility-20260619/`.

Initial observation:

- Batch results could show `Current: 12`, `Needs review: 12`, `Rename previews: 0`, `Failed: 0`.
- Rows only exposed filename plus compact status text such as `current / unreviewed / 4 tags`.
- The existing S8 implementation had the data needed to know analysis/review state, but the batch API and panel did not expose enough operator detail to explain tags, blockers, or next actions.

Unrelated dirty files:

- The repo already had unrelated dirty files outside this task, including Source Proxy evidence, media face-organizer outputs, runtime scripts, package files, and SpiritFlix runtime/player files.
- Those files are not part of this task and must remain untouched.

Boundaries:

- No real media rename/move/delete.
- No Jellyfin SQLite/config mutation.
- No Source Proxy patching or restart.
- No model calls, OCR, VLM, or dependency lane.
- No push.
