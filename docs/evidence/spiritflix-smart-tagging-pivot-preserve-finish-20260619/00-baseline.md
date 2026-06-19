# SpiritFlix Smart Tagging Pivot Baseline

Captured: 2026-06-19

Raw baseline:

- `raw/00-baseline.txt`

Summary:

- Repo path inspected from Windows mapped workspace: `Z:\`
- Dell host path verified separately: `/home/source/SpiritOS`
- Current branch: `master`
- Recent smart-tagging commits present:
  - `dff4e3b5 feat: preserve SpiritFlix smart review metadata`
- Existing S7 evidence folder is present:
  - `docs/evidence/spiritflix-smart-tagging-s7-batch-20260618-214438/`
- S7 smart-tagging source files are present as uncommitted scoped work:
  - `src/lib/spiritflix/admin/smart/batch.ts`
  - `src/app/api/spiritflix/admin/smart/batch/route.ts`
  - `src/components/spiritflix/admin/SpiritFlixSmartBatchPanel.tsx`
  - S7 tests under `src/lib/spiritflix/admin/smart/__tests__/` and `src/app/api/spiritflix/admin/__tests__/`
  - Admin app, toolbar, and interaction-test wiring

Boundary notes:

- The dirty tree contains many unrelated Source Proxy and media-generated files.
- This task is limited to SpiritFlix smart tagging / auto naming.
- No Source Proxy implementation or runtime work is part of this baseline.
- No real media rename, move, delete, Jellyfin mutation, model calls, OCR, or VLM work has been performed in this pivot evidence capture.
