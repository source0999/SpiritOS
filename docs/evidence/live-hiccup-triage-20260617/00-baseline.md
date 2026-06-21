# Baseline

```text
=== date -Is ===
2026-06-18T03:56:12-04:00
[exit 0]

=== hostname ===
source-server
[exit 0]

=== pwd ===
/home/source/SpiritOS
[exit 0]

=== uptime ===
 03:56:12 up  6:49,  9 users,  load average: 1.03, 1.09, 0.70
[exit 0]

=== free -h ===
               total        used        free      shared  buff/cache   available
Mem:            15Gi       6.8Gi       1.1Gi       148Mi       8.1Gi       8.8Gi
Swap:          4.0Gi       1.8Gi       2.2Gi
[exit 0]

=== df -h / /mnt/spirit-8tb || true ===
Filesystem      Size  Used Avail Use% Mounted on
/dev/sdb2       457G  282G  152G  65% /
/dev/sda1       7.3T  156G  6.8T   3% /mnt/spirit-8tb
[exit 0]

=== git status --branch --short --untracked-files=normal ===
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
?? docs/evidence/repo-cleanup-manifest-watchers-20260617/
?? docs/evidence/repo-host-cleanup-stability-audit-20260617/
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-54c0f44cc0a7a4a9.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-701f9c2e9284296f.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7a529ebb43342143.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7e95ea289935d428.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-c19c477cba35858e.json
?? docs/evidence/source-proxy-glm-3x10-audit-20260617/
?? docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/
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
```
