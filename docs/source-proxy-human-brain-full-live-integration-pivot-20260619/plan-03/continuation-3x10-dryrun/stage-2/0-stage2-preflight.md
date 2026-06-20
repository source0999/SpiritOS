# Stage 2 Preflight

Recorded: 2026-06-20T13:06:00-04:00
Host: source-server
Repo: /home/source/SpiritOS

## Current HEAD

- `4c553554dfda690615255d192e279853305b1b96`
- `4c553554 Implement Plan 3 durable execution and repair`

## Staging Gate

- staged files count: 0
- staged files: none

## Dirty Scope

Dirty `source_proxy` files before/inside Stage 2:

```text
M source_proxy/tasks/durable_execution.py
 M source_proxy/tests/test_plan3_durable_execution.py
```

Dirty Plan 3 files:

```text
M docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/operator-check.sh
?? docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/acceptance-review/
?? docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/
```

Unrelated dirty tree summary:

```text
M docs/handoff/spiritflix-llm-pack/file-list.txt
 M docs/handoff/spiritflix-llm-pack/instructions.md
 M docs/handoff/spiritflix-llm-pack/spiritflix-only-repomix.md
 M docs/handoff/spiritflix-llm-pack/spiritflix-only-repomix.xml
 D docs/handoff/spiritflix-llm-pack/stage/PACK_INSTRUCTIONS.md
 M docs/handoff/spiritflix-llm-pack/stage/package.json
 D docs/handoff/spiritflix-llm-pack/stage/repomix.config.json
 M docs/handoff/spiritflix-llm-pack/stage/src/app/api/spiritflix/jellyfin-image/route.ts
 M docs/handoff/spiritflix-llm-pack/stage/src/app/api/spiritflix/stream/route.ts
 M docs/handoff/spiritflix-llm-pack/stage/src/app/spiritflix/page.tsx
 M docs/handoff/spiritflix-llm-pack/stage/src/components/spiritflix/SpiritFlixApp.tsx
 M docs/handoff/spiritflix-llm-pack/stage/src/components/spiritflix/SpiritFlixHome.tsx
 M docs/handoff/spiritflix-llm-pack/stage/src/components/spiritflix/SpiritFlixImage.tsx
 M docs/handoff/spiritflix-llm-pack/stage/src/components/spiritflix/SpiritFlixPlayer.tsx
 M docs/handoff/spiritflix-llm-pack/stage/src/components/spiritflix/__tests__/SpiritFlixHome.test.tsx
 M docs/handoff/spiritflix-llm-pack/stage/src/components/spiritflix/__tests__/SpiritFlixPlayer.test.tsx
 M docs/handoff/spiritflix-llm-pack/stage/src/lib/spiritflix-jellyfin-client.ts
 M docs/handoff/spiritflix-llm-pack/stage/src/lib/spiritflix/jellyfin-client.ts
 M docs/handoff/spiritflix-llm-pack/stage/src/styles/spiritflix.css
 M package-lock.json
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
 M scripts/spiritos-lan-watchdog.sh
 M src/app/api/spiritflix/jellyfin-image/route.ts
 M src/app/api/spiritflix/stream/route.ts
 M src/app/layout.tsx
 M src/components/spiritflix/SpiritFlixApp.tsx
 M src/components/spiritflix/SpiritFlixHome.tsx
 M src/components/spiritflix/SpiritFlixImage.tsx
 M src/components/spiritflix/SpiritFlixPlayer.tsx
 M src/components/spiritflix/__tests__/SpiritFlixHome.test.tsx
 M src/components/spiritflix/__tests__/SpiritFlixPlayer.test.tsx
 M src/lib/spiritflix-jellyfin-client.ts
 M src/lib/spiritflix-types.ts
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
?? "docs/evidence/source-proxy-productive-go-hardening-20260618/raw/10-evidence-read.txt\r"
?? docs/evidence/source-proxy-return-checkpoint-20260618/
?? docs/evidence/source-proxy-runtime-health-status-live-proof-20260618/
?? docs/handoff/spiritflix-llm-pack/stage/docs/media-server/jellyfin-basic-media-server-handoff.md
?? docs/handoff/spiritflix-llm-pack/stage/docs/media-server/jellyfin-basic-media-server-plan.md
?? docs/handoff/spiritflix-llm-pack/stage/docs/media-server/jellyfin-folder-map.md
?? docs/handoff/spiritflix-llm-pack/stage/docs/media/spiritflix-admin-explorer-plan.md
?? docs/handoff/spiritflix-llm-pack/stage/docs/media/spiritflix-smart-tagging-rename-plan.md
?? docs/handoff/spiritflix-llm-pack/stage/scripts/media-ingest-worker.mjs
?? docs/handoff/spiritflix-llm-pack/stage/scripts/restart-spiritflix-stable-3001.sh
?? docs/handoff/spiritflix-llm-pack/stage/scripts/spiritflix-admin-dev.sh
?? docs/handoff/spiritflix-llm-pack/stage/scripts/spiritflix-stable-watchdog.sh
?? docs/handoff/spiritflix-llm-pack/stage/services/
?? docs/handoff/spiritflix-llm-pack/stage/src/app/api/spiritflix/admin/
?? docs/handoff/spiritflix-llm-pack/stage/src/app/api/spiritflix/hls/
?? docs/handoff/spiritflix-llm-pack/stage/src/app/spiritflix/admin/
?? docs/handoff/spiritflix-llm-pack/stage/src/app/spiritflix/layout.tsx
?? docs/handoff/spiritflix-llm-pack/stage/src/components/spiritflix/__tests__/SpiritFlixApp.test.ts
?? docs/handoff/spiritflix-llm-pack/stage/src/components/spiritflix/admin/
?? docs/handoff/spiritflix-llm-pack/stage/src/lib/spiritflix-jellyfin-client.test.ts
?? docs/handoff/spiritflix-llm-pack/stage/src/lib/spiritflix/admin/
?? docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-00/artifacts/
?? docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-00/codex-review/
?? docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-01/codex-acceptance-review/
?? docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-02/acceptance-review-patch-3/
?? docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-02/acceptance-review-patch-4/
?? docs/spiritflix-mobile-optimizer.md
?? fold7-media-grabber/
?? home/
?? scripts/media/face_verification_report.json
?? scripts/postinstall-repomix-shim.mjs
?? scripts/spiritflix-mobile-optimize.mjs
?? scripts/spiritflix-playback-diag.sh
?? scripts/spiritos-health/README.md
?? src/app/api/spiritflix/hls/
?? src/app/api/spiritflix/mobile-optimized/
?? src/app/spiritflix/watch/
?? src/components/spiritflix/__tests__/SpiritFlixApp.test.ts
?? src/lib/spiritflix-jellyfin-client.test.ts
?? src/lib/spiritflix/mobile-optimized.ts
```

## Raw Evidence

- path: `/home/source/spiritos-evidence/plan-03-3x10-dryrun/stage-2/`
- writable: yes

## Acceptance Review Blockers Read Back

- Policy proof must include downstream consumer evidence in the same durable trace, with latest_consumer_event_id populated.
- Recovery proof must include downstream consumer evidence in the same durable trace, with latest_consumer_event_id populated.
- Repair proof must include explicit failure, repair, reverify, and consumer evidence in the same durable trace.
- Operator checks must fail on missing consumer evidence and missing repair failure-event evidence.
- Broad requested selector/gate environment must be documented or fixed.

## Scope Confirmation

Stage 2 only. Stage 3 was not started, no dry-run harness was selected, no Set A or 3x10 prompts were run, Plan 4 was not started, and media/Jellyfin files were not touched by this Stage 2 patch.
