2026-06-18T20:04:38-04:00
source-server
/home/source/SpiritOS
## master
 M README.md
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
 M src/app/layout.tsx
 M src/components/spiritflix/SpiritFlixPlayer.tsx
 M src/components/spiritflix/admin/SpiritFlixSmartTagPill.tsx
 M src/components/spiritflix/admin/__tests__/SpiritFlixSmartTagPill.test.tsx
 M src/lib/spiritflix-jellyfin-client.ts
 M src/lib/spiritflix/admin/smart/review.ts
 M src/lib/spiritflix/admin/smart/types.ts
 M src/lib/spiritflix/jellyfin-client.ts
?? docs/evidence/live-hiccup-triage-20260617/
?? docs/evidence/repo-cleanup-finish-phase-20260618/
?? docs/evidence/repo-cleanup-manifest-watchers-20260617/
?? docs/evidence/repo-host-cleanup-stability-audit-20260617/
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-54c0f44cc0a7a4a9.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-701f9c2e9284296f.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7a529ebb43342143.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-7e95ea289935d428.json
?? docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-c19c477cba35858e.json
?? docs/evidence/source-proxy-glm-3x10-audit-20260617/
?? docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/s6-commit-closeout.md
?? docs/evidence/spiritos-readonly-watchers-install-20260617/watcher-commit-closeout.md
?? scripts/headroom-proxy-dev.sh
?? scripts/media/face_verification_report.json
?? scripts/postinstall-repomix-shim.mjs
?? scripts/repomix-llm.mjs
?? scripts/spiritos-health/README.md
?? src/app/api/spiritflix/hls/
?? src/lib/spiritflix-jellyfin-client.test.ts
?? src/lib/spiritflix/admin/smart/__tests__/review-metadata.test.ts
?? src/lib/spiritflix/admin/smart/review-metadata.ts
372e6c1e Add SpiritOS read-only health watchers
111d4fe9 SpiritFlix smart tagging S6 metadata bridge preview
158b489f docs: preserve proxy evidence and SpiritFlix handoff
514d3ea0 test: cover SpiritFlix smart tag menu
5f12741a feat: add SpiritFlix smart tag review
e2fade56 feat: preserve media face organizer workflow
2f4587f8 feat: add SpiritFlix admin explorer
d82fd141 feat: harden source proxy FIP runtime lanes
/home/source/SpiritOS  372e6c1e [master]
/home/source/SpiritOS
372e6c1e81a5ca1d22063cc8c0d03a01c9737239
● spiritos-health-snapshot.timer - Run SpiritOS health snapshot periodically
     Loaded: loaded (/etc/systemd/system/spiritos-health-snapshot.timer; enabled; preset: enabled)
     Active: active (waiting) since Thu 2026-06-18 19:44:21 EDT; 20min ago
    Trigger: Thu 2026-06-18 20:15:10 EDT; 10min left
   Triggers: ● spiritos-health-snapshot.service

Jun 18 19:44:21 source-server systemd[1]: Started spiritos-health-snapshot.timer - Run SpiritOS health snapshot periodically.
○ spiritos-health-snapshot.service - SpiritOS health snapshot (safe read-only)
     Loaded: loaded (/etc/systemd/system/spiritos-health-snapshot.service; static)
     Active: inactive (dead) since Thu 2026-06-18 19:45:13 EDT; 19min ago
TriggeredBy: ● spiritos-health-snapshot.timer
    Process: 997094 ExecStart=/home/source/SpiritOS/scripts/spiritos-health/spiritos-host-health-snapshot.sh (code=exited, status=0/SUCCESS)
    Process: 997114 ExecStart=/home/source/SpiritOS/scripts/spiritos-health/spiritos-service-health-snapshot.sh (code=exited, status=0/SUCCESS)
    Process: 997152 ExecStart=/home/source/SpiritOS/scripts/spiritos-health/spiritos-model-storage-guard.sh (code=exited, status=0/SUCCESS)
    Process: 997169 ExecStart=/home/source/SpiritOS/scripts/spiritos-health/spiritos-repo-bloat-report.sh (code=exited, status=0/SUCCESS)
   Main PID: 997169 (code=exited, status=0/SUCCESS)
        CPU: 3.455s

Jun 18 19:45:10 source-server systemd[1]: Starting spiritos-health-snapshot.service - SpiritOS health snapshot (safe read-only)...
Jun 18 19:45:10 source-server spiritos-host-health-snapshot.sh[997094]: /mnt/spirit-8tb/spiritos-health/spiritos-host-health-snapshot.sh.2026-06-18T19-45-10-04-00.log
Jun 18 19:45:10 source-server spiritos-service-health-snapshot.sh[997114]: /mnt/spirit-8tb/spiritos-health/spiritos-service-health-snapshot.sh.2026-06-18T19-45-10-04-00.log
Jun 18 19:45:10 source-server spiritos-model-storage-guard.sh[997152]: /mnt/spirit-8tb/spiritos-health/spiritos-model-storage-guard.sh.2026-06-18T19-45-10-04-00.log
Jun 18 19:45:13 source-server spiritos-repo-bloat-report.sh[997169]: /mnt/spirit-8tb/spiritos-health/spiritos-repo-bloat-report.sh.2026-06-18T19-45-10-04-00.log
Jun 18 19:45:13 source-server systemd[1]: spiritos-health-snapshot.service: Deactivated successfully.
Jun 18 19:45:13 source-server systemd[1]: Finished spiritos-health-snapshot.service - SpiritOS health snapshot (safe read-only).
Jun 18 19:45:13 source-server systemd[1]: spiritos-health-snapshot.service: Consumed 3.455s CPU time.
○ spiritos-boot-postmortem.service - SpiritOS boot postmortem snapshot (safe read-only)
     Loaded: loaded (/etc/systemd/system/spiritos-boot-postmortem.service; enabled; preset: enabled)
     Active: inactive (dead) since Thu 2026-06-18 19:45:47 EDT; 18min ago
    Process: 997753 ExecStart=/home/source/SpiritOS/scripts/spiritos-health/spiritos-boot-postmortem.sh (code=exited, status=0/SUCCESS)
   Main PID: 997753 (code=exited, status=0/SUCCESS)
        CPU: 321ms

Jun 18 19:45:46 source-server systemd[1]: Starting spiritos-boot-postmortem.service - SpiritOS boot postmortem snapshot (safe read-only)...
Jun 18 19:45:47 source-server spiritos-boot-postmortem.sh[997753]: /mnt/spirit-8tb/spiritos-health/spiritos-boot-postmortem.sh.2026-06-18T19-45-46-04-00.log
Jun 18 19:45:47 source-server systemd[1]: spiritos-boot-postmortem.service: Deactivated successfully.
Jun 18 19:45:47 source-server systemd[1]: Finished spiritos-boot-postmortem.service - SpiritOS boot postmortem snapshot (safe read-only).
  UNIT                         LOAD   ACTIVE SUB    DESCRIPTION
● mnt-spirit\x2dprojects.mount loaded failed failed /mnt/spirit-projects

Legend: LOAD   → Reflects whether the unit definition was properly loaded.
        ACTIVE → The high-level unit activation state, i.e. generalization of SUB.
        SUB    → The low-level unit activation state, values depend on unit type.

1 loaded units listed.
2026-06-18 19:39 /mnt/spirit-8tb/spiritos-health/spiritos-host-health-snapshot.sh.2026-06-18T19-39-22-04-00.log
2026-06-18 19:39 /mnt/spirit-8tb/spiritos-health/spiritos-service-health-snapshot.sh.2026-06-18T19-39-37-04-00.log
2026-06-18 19:40 /mnt/spirit-8tb/spiritos-health/spiritos-boot-postmortem.sh.2026-06-18T19-39-39-04-00.log
2026-06-18 19:40 /mnt/spirit-8tb/spiritos-health/spiritos-model-storage-guard.sh.2026-06-18T19-40-14-04-00.log
2026-06-18 19:40 /mnt/spirit-8tb/spiritos-health/spiritos-repo-bloat-report.sh.2026-06-18T19-40-15-04-00.log
2026-06-18 19:45 /mnt/spirit-8tb/spiritos-health/locks/spiritos-boot-postmortem.sh.lock
2026-06-18 19:45 /mnt/spirit-8tb/spiritos-health/locks/spiritos-host-health-snapshot.sh.lock
2026-06-18 19:45 /mnt/spirit-8tb/spiritos-health/locks/spiritos-model-storage-guard.sh.lock
2026-06-18 19:45 /mnt/spirit-8tb/spiritos-health/locks/spiritos-repo-bloat-report.sh.lock
2026-06-18 19:45 /mnt/spirit-8tb/spiritos-health/locks/spiritos-service-health-snapshot.sh.lock
2026-06-18 19:45 /mnt/spirit-8tb/spiritos-health/spiritos-boot-postmortem.sh.2026-06-18T19-45-46-04-00.log
2026-06-18 19:45 /mnt/spirit-8tb/spiritos-health/spiritos-host-health-snapshot.sh.2026-06-18T19-45-10-04-00.log
2026-06-18 19:45 /mnt/spirit-8tb/spiritos-health/spiritos-model-storage-guard.sh.2026-06-18T19-45-10-04-00.log
2026-06-18 19:45 /mnt/spirit-8tb/spiritos-health/spiritos-repo-bloat-report.sh.2026-06-18T19-45-10-04-00.log
2026-06-18 19:45 /mnt/spirit-8tb/spiritos-health/spiritos-service-health-snapshot.sh.2026-06-18T19-45-10-04-00.log
