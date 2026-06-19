# Dirty Tree Classification

Captured: 2026-06-19

## A. Legitimate S7 Smart-Tagging Work

These files match the requested S7 batch folder analysis scope and are candidates for the S7 preservation commit after focused verification:

- `src/lib/spiritflix/admin/smart/batch.ts`
- `src/lib/spiritflix/admin/smart/__tests__/batch.test.ts`
- `src/lib/spiritflix/admin/smart/index.ts`
- `src/app/api/spiritflix/admin/smart/batch/route.ts`
- `src/app/api/spiritflix/admin/__tests__/smart-batch-route.test.ts`
- `src/components/spiritflix/admin/SpiritFlixSmartBatchPanel.tsx`
- `src/components/spiritflix/admin/SpiritFlixAdminApp.tsx`
- `src/components/spiritflix/admin/SpiritFlixAdminToolbar.tsx`
- `src/components/spiritflix/admin/__tests__/SpiritFlixAdminInteractions.test.tsx`
- `docs/evidence/spiritflix-smart-tagging-s7-batch-20260618-214438/`

## B. Follow-On Smart-Tagging Work

These files belong to the current pivot task and should be committed only with the S8/S8-lite finish work after final verification:

- `docs/evidence/spiritflix-smart-tagging-pivot-preserve-finish-20260619/`

Additional S8/S8-lite files will be added to this section if implemented.

## C. Unrelated Dirty Files To Leave Untouched

The baseline found unrelated dirty files outside the smart-tagging scope. They must not be staged, reset, cleaned, or modified by this task.

- `README.md`
- `package.json`
- `package-lock.json`
- Source Proxy evidence and runtime health files under `docs/evidence/source-proxy-*`
- Source Proxy and host utility scripts such as `scripts/source-context-compress.mjs`, `scripts/runtime-port-guard.sh`, `scripts/spiritos-lan-watchdog.sh`, and related new helper scripts
- Media face-organizer generated HTML/JSON/test files under `scripts/media/`
- Non-admin SpiritFlix runtime/player files such as `src/components/spiritflix/SpiritFlixPlayer.tsx`, `src/components/spiritflix/__tests__/SpiritFlixPlayer.test.tsx`, `src/app/api/spiritflix/stream/route.ts`, `src/app/api/spiritflix/jellyfin-image/route.ts`, `src/app/api/spiritflix/hls/`, and Jellyfin client files
- `src/app/layout.tsx`
- Repo cleanup/live triage evidence folders under `docs/evidence/live-hiccup-*` and `docs/evidence/repo-*`

## D. Suspicious Or Unsafe Changes Requiring Stop

None found inside the SpiritFlix smart-tagging scope at classification time.

Important boundaries remain active:

- Do not touch Source Proxy.
- Do not rename, move, or delete real media.
- Do not mutate Jellyfin SQLite/config.
- Do not restart Jellyfin, Docker, Ollama, Source Proxy, Next, SearXNG, CasaOS, or spirit-whisper.
- Do not run model, OCR, or VLM lanes.
- Do not push.
