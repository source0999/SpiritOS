# SpiritFlix Smart Tagging S8.2 Baseline

Captured raw baseline:

- `raw/00-baseline.txt`

Initial state observed:

- Working tree was already dirty before this task; scoped changes are limited to SpiritFlix smart batch UI/tests/styles and this evidence folder.
- Current smart batch implementation lives in `src/components/spiritflix/admin/SpiritFlixSmartBatchPanel.tsx`.
- Batch orchestration/types live under `src/lib/spiritflix/admin/smart`.
- Existing admin interaction coverage exercises the batch panel through `SpiritFlixAdminInteractions.test.tsx`.

Boundary confirmations for this task:

- No real media rename/move/delete is required or allowed.
- No Jellyfin SQLite/config mutation is required or allowed.
- No Source Proxy, model, OCR, or VLM lane is required or allowed.
- Rename planning remains preview/export only; real apply stays disabled.
