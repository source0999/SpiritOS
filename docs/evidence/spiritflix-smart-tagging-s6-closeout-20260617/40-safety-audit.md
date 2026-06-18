# S6 Safety Audit

Command requested with host-local ripgrep fallback:

```bash
~/.local/bin/rg -n "rename\(|unlink\(|rm\(|move|execute|softDelete|restore|jellyfin|sqlite|ocr|vlm|model|ffmpeg|spawn|exec" src/app/api/spiritflix/admin/smart src/components/spiritflix/admin src/lib/spiritflix/admin/smart || true
```

The plain `rg` command was also attempted first and recorded `rg: command not found`; this is a PATH issue only, not a safety result.

## Hit Review

- `src/app/api/spiritflix/admin/smart/analysis/route.ts`: `executeRename` / `executeMove` hits are in the forbidden-action denylist and comments documenting no execute. PASS.
- `src/lib/spiritflix/admin/smart/metadata-bridge.ts`: `fs.rename` is the atomic temp-file-to-metadata-sidecar write under `.spiritflix-admin/metadata/`; it is not a media rename. PASS.
- `src/lib/spiritflix/admin/smart/rename-preview.ts`: no filesystem mutation APIs. PASS.
- `src/components/spiritflix/admin/SpiritFlixSmartReviewPanel.tsx`: smart panel exposes export metadata and prepare rename preview only; no apply/confirm execute button. PASS.
- `src/components/spiritflix/admin/SpiritFlixAdminActionDialog.tsx` and admin menu files: general Level 2 admin action UI exists outside the smart panel; browser smoke confirmed it is not exposed by S6 smart panel. Not an S6 violation.
- `src/lib/spiritflix/admin/smart/probe.ts`, `scanner.ts`, `sampler` tests: pre-existing scan/probe stages mention ffmpeg/spawn; S6 closeout did not run OCR/model/VLM, folder batch scan, or frame classification. Not part of export/rename execution.
- Test files with `fs.rm`: temp test cleanup only. Not media mutation.
- Jellyfin/sqlite hits in analysis path tests and details UI are guard/display references, not Jellyfin mutation.

## Safety Confirmation

- Metadata sidecar only: PASS.
- Rename preview only: PASS.
- No execute rename/move: PASS.
- No Level 2 execute calls from S6 smart flow: PASS.
- No OCR/model/VLM: PASS.
- No visual frame classification run during this closeout: PASS.
- No real media mutation: PASS.
- No Jellyfin config/SQLite touched: PASS.
- No Jellyfin restart: PASS.
- No git stage/commit/push/reset/checkout/clean/stash: PASS.

Raw safety output: `raw/safety-rg-local-bin.txt`.
