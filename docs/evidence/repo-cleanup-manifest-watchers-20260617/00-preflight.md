# Preflight

```text
$ pwd
/home/source/SpiritOS
[exit 0]

$ hostname
source-server
[exit 0]

$ date -Is
2026-06-17T22:13:50-04:00
[exit 0]

$ git status --branch --short --untracked-files=normal
## master
 M README.md
 M docs/media/spiritflix-smart-tagging-rename-plan.md
 M package-lock.json
 M package.json
 M repomix.config.json
 M scripts/media-ingest-worker.mjs
 M scripts/media/face_enrolled_performers.html
 M scripts/media/face_enrolled_performers.json
 M scripts/media/face_enrollment_queue.html
 M scripts/media/face_enrollment_queue.json
 M scripts/media/face_gallery.html
 M scripts/media/face_gallery.json
 M scripts/media/face_organizer.py
 M scripts/media/face_verification_full_audit.html
 M scripts/media/known_db_audit.html
 M scripts/media/known_db_audit.json
 M scripts/media/manual_crop.html
 M scripts/media/model_index.json
 M scripts/media/performer_verification.json
 M scripts/media/test_face_organizer_schema.py
 M scripts/runtime-port-guard.sh
 M scripts/source-context-compress.mjs
 M scripts/spiritos-lan-watchdog.sh
 M src/app/api/spiritflix/admin/__tests__/smart-analysis-route.test.ts
 M src/app/api/spiritflix/admin/smart/analysis/route.ts
 M src/app/layout.tsx
 M src/components/spiritflix/admin/SpiritFlixSmartReviewPanel.tsx
 M src/components/spiritflix/admin/SpiritFlixSmartTagPill.tsx
 M src/components/spiritflix/admin/__tests__/SpiritFlixSmartReviewPanel.test.tsx
 M src/components/spiritflix/admin/__tests__/SpiritFlixSmartTagPill.test.tsx
 M src/lib/spiritflix/admin/smart/index.ts
 M src/lib/spiritflix/admin/smart/review.ts
 M src/lib/spiritflix/admin/smart/types.ts
 M src/styles/spiritflix.css
?? docs/evidence/repo-host-cleanup-stability-audit-20260617/
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-54c0f44cc0a7a4a9.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-701f9c2e9284296f.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7a529ebb43342143.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7e95ea289935d428.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-c19c477cba35858e.json
?? docs/evidence/source-proxy-glm-3x10-audit-20260617/
?? scripts/headroom-proxy-dev.sh
?? scripts/media/face_verification_report.json
?? scripts/postinstall-repomix-shim.mjs
?? scripts/repomix-llm.mjs
?? src/lib/spiritflix/admin/smart/__tests__/metadata-bridge.test.ts
?? src/lib/spiritflix/admin/smart/__tests__/rename-preview.test.ts
?? src/lib/spiritflix/admin/smart/__tests__/review-metadata.test.ts
?? src/lib/spiritflix/admin/smart/metadata-bridge.ts
?? src/lib/spiritflix/admin/smart/rename-preview.ts
?? src/lib/spiritflix/admin/smart/review-metadata.ts
[exit 0]

$ git worktree list
/home/source/SpiritOS  158b489f [master]
[exit 0]

$ git rev-parse --show-toplevel
/home/source/SpiritOS
[exit 0]

$ git rev-parse HEAD
158b489fcf813a701f8a7a1bf3f8be5770511448
[exit 0]
```
