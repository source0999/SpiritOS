# SpiritFlix Mobile Latency Loop Closeout

Date: 2026-06-25

## Verdict

PARTIAL PASS.

The local Dell-hosted app path now proves the warm playback target and mobile optimized source path, but the run cannot be marked PASS because authenticated real-library cards were not proven and the Tailscale hostname still has a hydration/source-selection blocker.

## Baseline

- Command: `PLAYWRIGHT_BASE_URL=https://spirit.tailb69ea6.ts.net:3000 SPIRITFLIX_BENCHMARK_RUNS=3 node scripts/spiritflix-mobile-benchmark.mjs --runs=3`
- Result: aborted before writing benchmark JSON.
- Baseline evidence directory: `docs/evidence/spiritflix-mobile-50ms-loop-20260625-041259`
- Failure: `measurePlayerStart` timed out waiting for the player to reach playing state.

## Final Metrics

Final local route command:

`PLAYWRIGHT_BASE_URL=https://127.0.0.1:3000 SPIRITFLIX_BENCHMARK_RUNS=3 node scripts/spiritflix-mobile-benchmark.mjs --runs=3`

| Metric | Final p50 | Final p75 | Final p95 | Result |
| --- | ---: | ---: | ---: | --- |
| Mobile optimized API warm | 5.8 ms | 6.4 ms | 6.4 ms | PASS |
| Mobile optimized API cold | 57.0 ms | n/a | n/a | PASS |
| Warm tap to playing | 60.3 ms | 62.0 ms | 62.0 ms | PARTIAL |
| Shell useful content | 189.7 ms | 210.7 ms | 210.7 ms | FAIL vs 50-60 ms target |
| Player route to playing | 4264.0 ms | 5240.9 ms | 5240.9 ms | FAIL |
| Real `/spiritflix` useful content | n/a | n/a | n/a | INCONCLUSIVE: no stored Jellyfin session |
| Real `/spiritflix` initial requests | 14 | 14 | 14 | No full-library fetch observed before login |
| Real `/spiritflix` bytes | 247647 | 247647 | 247647 | Login wall, not library proof |
| Real `/spiritflix` thumbnail requests | 0 | 0 | 0 | Login wall, not thumbnail proof |

Tailscale hostname command:

`PLAYWRIGHT_BASE_URL=https://spirit.tailb69ea6.ts.net:3000 SPIRITFLIX_BENCHMARK_RUNS=3 node scripts/spiritflix-mobile-benchmark.mjs --runs=3`

Tailscale evidence: `docs/evidence/spiritflix-mobile-50ms-loop-20260625-053137`

- Mobile optimized API warm p50: 5.8 ms.
- `/spiritflix` stayed on the restore shell and made no library API calls.
- Player route timed out before playing.
- Browser console repeatedly reported failed HMR websocket handshakes for `wss://spirit.tailb69ea6.ts.net:3000/_next/webpack-hmr`.

## Changes Covered

- Initial mobile home load now requests bounded compact pages instead of full library-sized card metadata.
- Library, Favorites, Latest Added, and Continue Watching have server paging metadata plus load-more handlers.
- Rails render only a small initial window and ask for more near the end.
- Image loading now uses a cacheable same-origin Jellyfin image proxy, prioritizes current viewport images, lazy-loads offscreen thumbnails, and tries the next Jellyfin image type before falling back.
- Player source selection now avoids swapping away from an already-playing direct MP4 when the optimized receipt arrives late.
- Playback marks now include loadedmetadata, waiting, stalled, and error events.
- Benchmark script now records real-route request/byte/thumbnail counts and preserves measurement failures instead of aborting the entire run.

## Verification

- `npm run typecheck`: PASS.
- `vitest run src/lib/spiritflix-jellyfin-client.test.ts src/components/spiritflix/__tests__/SpiritFlixImage.test.tsx src/app/api/spiritflix/mobile-optimized/__tests__/route.test.ts`: 16 tests PASS.
- `vitest run src/components/spiritflix/__tests__/SpiritFlixHome.test.tsx`: 15 tests PASS.
- `vitest run src/components/spiritflix/__tests__/SpiritFlixPlayer.test.tsx`: 42 tests PASS.

Known test noise: existing React `act(...)` warnings remain in Home and Player tests.

## Blockers

- No authenticated Jellyfin session was available to Playwright, so real `/spiritflix` card, thumbnail, Favorites, and Continue Watching proof stopped at the login screen on local HTTPS.
- The Tailscale hostname currently blocks reliable mobile proof: `/spiritflix` remains on the restore shell and benchmark player playback does not reach a source, while local HTTPS does.
- Cold player route to playing is still several seconds even on local HTTPS, despite the warm tap path hitting the target band.

## Next Loop

1. Add a secret-safe benchmark login/session seeding path so Playwright can prove real library cards without storing credentials in evidence.
2. Fix the Tailscale/dev HTTPS hydration and player source path, or run the mobile proof against a production build URL that does not rely on dev HMR.
3. Reduce cold player route startup by cutting duplicate player API calls and prewarming only the active optimized MP4 source.
4. Once real authenticated route proof exists, measure first viewport thumbnail success rate against actual Jellyfin items.
