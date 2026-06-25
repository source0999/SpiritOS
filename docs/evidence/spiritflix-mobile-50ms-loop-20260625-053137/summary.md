# SpiritFlix mobile 50ms loop evidence

Generated: 2026-06-25T05:35:26.251Z
Evidence: `/home/source/SpiritOS/docs/evidence/spiritflix-mobile-50ms-loop-20260625-053137`
Base URL: https://spirit.tailb69ea6.ts.net:3000
Item ID: phase7-candidate-02
Mode: warm

## Commands

- `git status --short`
- `node scripts/spiritflix-mobile-benchmark.mjs --runs=3`
- `npm run typecheck`
- `vitest run src/components/spiritflix src/lib/spiritflix src/app/api/spiritflix/mobile-optimized`

## Metrics

| Metric | P50 | P75 | P95 | Verdict |
| --- | ---: | ---: | ---: | --- |
| Page useful content (shell) | 2737.7 ms | 8403.9 ms | 8403.9 ms | FAIL |
| Real route useful content | n/a ms | n/a ms | n/a ms | INCONCLUSIVE |
| Real route requests | 12 | 12 | 12 | â€” |
| Real route bytes | 137344 | 185776 | 185776 | â€” |
| Real route thumbnail requests | 0 | 0 | 0 | â€” |
| Video playing (real API player) | n/a ms | n/a ms | n/a ms | INCONCLUSIVE |
| Warm video tap → playing | n/a ms | n/a ms | n/a ms | INCONCLUSIVE |
| Mobile optimized API warm | 5.8 ms | 5.9 ms | 5.9 ms | PASS |
| Mobile optimized API cold | 811.9 ms | — | — | — |

## Source selection

- API source: mobileOptimized
- Player playback class: unknown
- Player video src: unknown
- Range supported: yes
- Mobile optimized available: yes

## Notes

Shell route uses seeded SpiritFlixHome data. Player route uses real /api/spiritflix/mobile-optimized and stream APIs with benchmark Jellyfin client stubs for auth-only calls.

## Git status

```
M docs/evidence/source-proxy-runtime-health-status-patch-20260618/raw/81-corrected-safety-scan.txt
 M docs/evidence/source-proxy-runtime-health-status-patch-20260618/raw/safety-scan.txt
 D home/source/spiritos-evidence/plan-02-continuation-patch-4/task-a-verifier-target-task_09558f6aa41b.html
 D home/source/spiritos-evidence/plan-02-continuation-patch-4/task-a-verifier-target-task_213d4e2ed36d.html
 D home/source/spiritos-evidence/plan-02-continuation-patch-4/task-a-verifier-target-task_31c65ec0a877.html
 D home/source/spiritos-evidence/plan-02-continuation-patch-4/task-a-verifier-target-task_3b97a5d8a3cd.html
 D home/source/spiritos-evidence/plan-02-continuation-patch-4/task-a-verifier-target-task_3e99285fac3d.html
 D home/source/spiritos-evidence/plan-02-continuation-patch-4/task-a-verifier-target-task_8c64815cc022.html
 D home/source/spiritos-evidence/plan-02-continuation-patch-4/task-a-verifier-target-task_bb1f95ce8f48.html
 M scripts/spiritflix-mobile-benchmark-report.mjs
 M scripts/spiritflix-mobile-benchmark.mjs
 M src/app/api/spiritflix/jellyfin-image/route.ts
 M src/app/api/spiritflix/videos/[itemId]/model/route.ts
 M src/app/api/spiritflix/videos/[itemId]/tags/route.ts
 M src/components/spiritflix/SpiritFlixApp.tsx
 M src/components/spiritflix/SpiritFlixCard.tsx
 M src/components/spiritflix/SpiritFlixHome.tsx
 M src/components/spiritflix/SpiritFlixImage.tsx
 M src/components/spiritflix/SpiritFlixPlayer.tsx
 M src/components/spiritflix/SpiritFlixRail.tsx
 M src/components/spiritflix/__tests__/SpiritFlixDetailsModal.test.tsx
 M src/components/spiritflix/__tests__/SpiritFlixHome.test.tsx
 M src/components/spiritflix/__tests__/SpiritFlixPlayer.test.tsx
 M src/lib/spiritflix-jellyfin-client.test.ts
 M src/lib/spiritflix-jellyfin-client.ts
 M src/lib/spiritflix-types.ts
 M src/lib/spiritflix/__tests__/manual-models.test.ts
 M src/lib/spiritflix/__tests__/manual-tags.test.ts
 M src/lib/spiritflix/manual-models.ts
 M src/lib/spiritflix/manual-tags.ts
 M src/styles/spiritflix.css
 M vitest.config.mjs
?? docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/runs/
?? docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/glm-set-a-stability-hardline-audit-20260625.md
?? nul
?? src/components/spiritflix/__tests__/SpiritFlixImage.test.tsx
```
