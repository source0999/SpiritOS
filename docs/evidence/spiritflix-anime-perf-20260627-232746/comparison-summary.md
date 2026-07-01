# SpiritFlix Anime Performance Comparison

Date: 2026-06-27
Target: warm route/API/playback 50-65ms
Verdict: PARTIAL

## Scope

- App target: `https://10.0.0.186:3000/spiritflix`
- Viewports: desktop 1440x900 and Samsung Galaxy Z Fold7 main-display emulation, 656x728 CSS px at DPR 3
- Evidence root: `docs/evidence/spiritflix-anime-perf-20260627-232746`
- Jellyfin was not restarted. Only the Next LAN app was restarted after a dev-origin allowlist change.

## Baseline Note

The full pre-patch matrix was blocked during anime playback by a Next dev-server memory restart. The preserved baseline is therefore a desktop smoke pass plus logs showing `ERR_CONNECTION_REFUSED` during anime playback after the server restart. The post-patch run is the full desktop + Fold7 matrix.

## Key Metrics

| Metric | Before desktop smoke | After desktop P50 / P95 | After Fold7 P50 / P95 |
| --- | ---: | ---: | ---: |
| Home route useful content | n/a | 1379.3ms / 11574.3ms | 1212.1ms / 1290.4ms |
| Normal library route useful content | 1946.7ms | 2157.1ms / 4057.1ms | 1743.8ms / 1906.1ms |
| Anime route useful content | 4766.4ms | 1956.3ms / 10116.5ms | 1574.5ms / 1736.3ms |
| Normal library API first screen | 103.0ms | 41.8ms / 42.6ms | 31.0ms / 60.7ms |
| Anime API first screen | 113.7ms | 102.2ms / 108.4ms | 91.5ms / 98.2ms |
| Anime 500-item API probe | n/a | 151.2ms / 159.5ms | 149.9ms / 151.4ms |
| Normal playback to playing | 16376.2ms | 5115.4ms / 5305.7ms | 5353.2ms / 5446.3ms |
| Anime playback to playing | failed during server restart | 3787.4ms / 10563.6ms | 3434.0ms / 3657.5ms |

## What Changed

- `src/components/spiritflix/SpiritFlixApp.tsx`: anime library initial load now uses the same responsive library page size as normal libraries instead of requesting 500 items on route entry.
- `src/components/spiritflix/SpiritFlixHome.tsx`: anime route skips Face Organizer metadata enrichment and exposes the existing library "load more" paging path for anime items.
- `src/components/spiritflix/SpiritFlixPlayer.tsx`: mobile playback assigns direct MP4 immediately and resolves the mobile-optimized receipt asynchronously, avoiding a blocking receipt lookup before video source selection.
- `allowed-dev-origins.ts`: added `spirit.tailb69ea6.ts.net` so the Tailscale dev origin hydrates instead of staying on the restore shell.
- `scripts/spiritflix-anime-performance-harness.mjs`: added a repeatable Playwright/Jellyfin harness for route, API, thumbnail, playback, stall, CPU, and diagnostic evidence.

## Bottlenecks Found

1. Anime route entry was over-fetching. Loading 500 anime items at first paint made anime much slower than normal libraries; reducing initial load produced a meaningful route improvement.
2. Anime was doing non-essential face metadata work. Skipping that path avoids extra route-time CPU and request pressure.
3. Mobile playback waited on an optimization receipt before assigning a playable source. Direct MP4 can start first while the optimized source is resolved in the background.
4. Playback is now direct MP4 with range support and no active Jellyfin ffmpeg/transcode detected during the post-patch runs, but `loadedmetadata/canplay/playing` still takes seconds.
5. The current `:3000` Next dev surface has heavy CPU/render outliers and memory restarts. It is not a clean 50-65ms validation environment.

## Verdict

PARTIAL. Anime route performance improved and anime playback no longer failed in the post-patch matrix, including Fold7 emulation. The 50-65ms target is still not met. Normal library API now reaches the target, but anime API remains around 90-108ms and playback startup remains 3-10s depending on viewport and outliers.

The remaining gap appears to be dev-server/render pressure plus media-byte and video-metadata readiness, not a Jellyfin transcode. A production build or isolated sidecar measurement is needed before treating route P95s as product truth, and playback needs a separate media-start strategy such as prebuffered direct streams, guaranteed mobile-optimized assets, or a cached source readiness path.

## Evidence Files

- `smoke.json`
- `smoke-summary.md`
- `after.json`
- `after-summary.md`
- `comparison-summary.md`
- Screenshots under this evidence root for smoke and after route captures

## Verification

- `node --check scripts/spiritflix-anime-performance-harness.mjs`: passed
- `npm run typecheck -- --pretty false`: passed
- Focused Vitest: 6 files, 83 tests passed
- Focused ESLint: did not pass because existing React hook lint debt remains in the touched SpiritFlix component files
