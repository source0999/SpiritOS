# S6 Commit Preflight

## date
2026-06-18T19:50:58-04:00

## git status
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
 M src/components/spiritflix/SpiritFlixPlayer.tsx
 M src/components/spiritflix/admin/SpiritFlixSmartReviewPanel.tsx
 M src/components/spiritflix/admin/SpiritFlixSmartTagPill.tsx
 M src/components/spiritflix/admin/__tests__/SpiritFlixSmartReviewPanel.test.tsx
 M src/components/spiritflix/admin/__tests__/SpiritFlixSmartTagPill.test.tsx
 M src/lib/spiritflix-jellyfin-client.ts
 M src/lib/spiritflix/admin/smart/index.ts
 M src/lib/spiritflix/admin/smart/review.ts
 M src/lib/spiritflix/admin/smart/types.ts
 M src/lib/spiritflix/jellyfin-client.ts
 M src/styles/spiritflix.css
?? docs/evidence/live-hiccup-triage-20260617/
?? docs/evidence/repo-cleanup-manifest-watchers-20260617/
?? docs/evidence/repo-host-cleanup-stability-audit-20260617/
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-54c0f44cc0a7a4a9.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-701f9c2e9284296f.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7a529ebb43342143.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7e95ea289935d428.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-c19c477cba35858e.json
?? docs/evidence/source-proxy-glm-3x10-audit-20260617/
?? docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/
?? docs/evidence/spiritos-readonly-watchers-install-20260617/
?? scripts/headroom-proxy-dev.sh
?? scripts/media/face_verification_report.json
?? scripts/postinstall-repomix-shim.mjs
?? scripts/repomix-llm.mjs
?? scripts/spiritos-health/
?? src/app/api/spiritflix/hls/
?? src/lib/spiritflix-jellyfin-client.test.ts
?? src/lib/spiritflix/admin/smart/__tests__/metadata-bridge.test.ts
?? src/lib/spiritflix/admin/smart/__tests__/rename-preview.test.ts
?? src/lib/spiritflix/admin/smart/__tests__/review-metadata.test.ts
?? src/lib/spiritflix/admin/smart/metadata-bridge.ts
?? src/lib/spiritflix/admin/smart/rename-preview.ts
?? src/lib/spiritflix/admin/smart/review-metadata.ts

## git diff --stat
 README.md                                          |    42 +-
 docs/media/spiritflix-smart-tagging-rename-plan.md |    14 +
 package-lock.json                                  |     3 +
 package.json                                       |    14 +-
 repomix.config.json                                |     2 +-
 scripts/media-ingest-worker.mjs                    |    47 +-
 scripts/media/face_enrolled_performers.html        | 10780 ++++++++++++-------
 scripts/media/face_enrolled_performers.json        |  9138 +++++++++++++---
 scripts/media/face_enrollment_queue.html           |  4595 +++-----
 scripts/media/face_enrollment_queue.json           |  5929 +++-------
 scripts/media/face_gallery.html                    |  2255 ++--
 scripts/media/face_gallery.json                    |    76 +-
 scripts/media/face_organizer.py                    |   330 +-
 scripts/media/face_verification_full_audit.html    |  7621 ++++++++-----
 scripts/media/known_db_audit.html                  |    25 +-
 scripts/media/known_db_audit.json                  |    60 +-
 scripts/media/manual_crop.html                     |    15 +-
 scripts/media/model_index.json                     |    20 +-
 scripts/media/performer_verification.json          |   373 +-
 scripts/media/test_face_organizer_schema.py        |    33 +
 scripts/runtime-port-guard.sh                      |    26 +-
 scripts/source-context-compress.mjs                |   272 +-
 scripts/spiritos-lan-watchdog.sh                   |    13 +-
 .../admin/__tests__/smart-analysis-route.test.ts   |    88 +-
 .../api/spiritflix/admin/smart/analysis/route.ts   |    72 +-
 src/app/layout.tsx                                 |     7 -
 src/components/spiritflix/SpiritFlixPlayer.tsx     |   114 +-
 .../admin/SpiritFlixSmartReviewPanel.tsx           |   386 +-
 .../spiritflix/admin/SpiritFlixSmartTagPill.tsx    |    44 +-
 .../__tests__/SpiritFlixSmartReviewPanel.test.tsx  |    79 +-
 .../__tests__/SpiritFlixSmartTagPill.test.tsx      |    12 +-
 src/lib/spiritflix-jellyfin-client.ts              |    40 +-
 src/lib/spiritflix/admin/smart/index.ts            |    29 +
 src/lib/spiritflix/admin/smart/review.ts           |    34 +-
 src/lib/spiritflix/admin/smart/types.ts            |   100 +
 src/lib/spiritflix/jellyfin-client.ts              |    40 +-
 src/styles/spiritflix.css                          |    99 +
 37 files changed, 25451 insertions(+), 17376 deletions(-)

## git diff --name-status
M	README.md
M	docs/media/spiritflix-smart-tagging-rename-plan.md
M	package-lock.json
M	package.json
M	repomix.config.json
M	scripts/media-ingest-worker.mjs
M	scripts/media/face_enrolled_performers.html
M	scripts/media/face_enrolled_performers.json
M	scripts/media/face_enrollment_queue.html
M	scripts/media/face_enrollment_queue.json
M	scripts/media/face_gallery.html
M	scripts/media/face_gallery.json
M	scripts/media/face_organizer.py
M	scripts/media/face_verification_full_audit.html
M	scripts/media/known_db_audit.html
M	scripts/media/known_db_audit.json
M	scripts/media/manual_crop.html
M	scripts/media/model_index.json
M	scripts/media/performer_verification.json
M	scripts/media/test_face_organizer_schema.py
M	scripts/runtime-port-guard.sh
M	scripts/source-context-compress.mjs
M	scripts/spiritos-lan-watchdog.sh
M	src/app/api/spiritflix/admin/__tests__/smart-analysis-route.test.ts
M	src/app/api/spiritflix/admin/smart/analysis/route.ts
M	src/app/layout.tsx
M	src/components/spiritflix/SpiritFlixPlayer.tsx
M	src/components/spiritflix/admin/SpiritFlixSmartReviewPanel.tsx
M	src/components/spiritflix/admin/SpiritFlixSmartTagPill.tsx
M	src/components/spiritflix/admin/__tests__/SpiritFlixSmartReviewPanel.test.tsx
M	src/components/spiritflix/admin/__tests__/SpiritFlixSmartTagPill.test.tsx
M	src/lib/spiritflix-jellyfin-client.ts
M	src/lib/spiritflix/admin/smart/index.ts
M	src/lib/spiritflix/admin/smart/review.ts
M	src/lib/spiritflix/admin/smart/types.ts
M	src/lib/spiritflix/jellyfin-client.ts
M	src/styles/spiritflix.css
