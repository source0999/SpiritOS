# SpiritFlix mobile 50ms loop evidence

Generated: 2026-06-23T01:17:18.601Z
Evidence: `/home/source/SpiritOS/docs/evidence/spiritflix-mobile-50ms-loop-20260623-011656`
Base URL: https://localhost:3000
Item ID: phase7-candidate-02
Mode: warm

## Commands

- `git status --short`
- `node scripts/spiritflix-mobile-benchmark.mjs --runs=10`
- `npm run typecheck`
- `vitest run src/components/spiritflix src/lib/spiritflix src/app/api/spiritflix/mobile-optimized`

## Metrics

| Metric | P50 | P75 | P95 | Verdict |
| --- | ---: | ---: | ---: | --- |
| Page useful content (shell) | 189.2 ms | 194.9 ms | 216.5 ms | FAIL |
| Video playing (real API player) | 1264.8 ms | 1328.2 ms | 1773.8 ms | FAIL |
| Mobile optimized API warm | 6.7 ms | 9.6 ms | 11.6 ms | PASS |
| Mobile optimized API cold | 2100.0 ms | — | — | — |

## Source selection

- API source: mobileOptimized
- Player playback class: mac_optimized_mp4
- Player video src: https://localhost:3000/api/spiritflix/mobile-optimized?stream=1&key=phase7-candidate-02
- Range supported: yes
- Mobile optimized available: yes

## Notes

Shell route uses seeded SpiritFlixHome data. Player route uses real /api/spiritflix/mobile-optimized and stream APIs with benchmark Jellyfin client stubs for auth-only calls.

## Git status

```
M package.json
 M src/app/api/spiritflix/mobile-optimized/route.ts
 M src/components/spiritflix/SpiritFlixApp.tsx
 M src/components/spiritflix/SpiritFlixHome.tsx
 M src/components/spiritflix/SpiritFlixPlayer.tsx
 M src/components/spiritflix/__tests__/SpiritFlixPlayer.test.tsx
 M src/lib/spiritflix-jellyfin-client.ts
 M src/lib/spiritflix/mobile-optimized.ts
?? docs/evidence/spiritflix-mobile-50ms-loop-20260623-011418/
?? scripts/__tests__/spiritflix-mobile-benchmark.test.ts
?? scripts/spiritflix-mobile-benchmark-report.mjs
?? scripts/spiritflix-mobile-benchmark.mjs
?? source-proxy-min-context.xml
?? spiritos-full-repo-context.xml
?? src/app/spiritflix/benchmark/
?? src/lib/spiritflix/__tests__/mobile-optimized-index.test.ts
?? src/lib/spiritflix/__tests__/mobile-source-cache.test.ts
?? src/lib/spiritflix/benchmark-client.ts
```
