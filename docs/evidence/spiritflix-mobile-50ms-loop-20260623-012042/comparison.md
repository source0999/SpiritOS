# SpiritFlix mobile 50ms loop — baseline vs final

## Baseline (pre-optimization, 2026-06-23)

Measured manually before code changes:

| Metric | Value |
| --- | ---: |
| Mobile optimized API cold | 1683 ms |
| Mobile optimized API warm | 350–410 ms |
| Player source | serial waterfall (await mobile before any `src`) |
| Receipt lookup | full FS scan per request (~470 receipts) |

## Final (post-optimization pass 3)

Evidence: `docs/evidence/spiritflix-mobile-50ms-loop-20260623-012042/`

| Metric | P50 | P95 | Verdict |
| --- | ---: | ---: | --- |
| Mobile optimized API warm | 5.9 ms | 10.5 ms | PASS |
| Mobile optimized API cold (index warm process) | 59.8 ms | — | PASS |
| Page useful content (benchmark shell) | 207.7 ms | 324.4 ms | FAIL |
| Video playing (cold navigation) | 1270.4 ms | 1629.1 ms | FAIL |
| **Warm video tap → playing (real MP4)** | **49.3 ms** | **64.0 ms** | **PASS / PARTIAL** |

## Source selection (final)

- API: `mobileOptimized`
- Player: `mac_optimized_mp4`
- Video URL: `/api/spiritflix/mobile-optimized?stream=1&key=phase7-candidate-02`
- Range supported: yes
- HLS: not used on happy path

## Blockers preventing full 50ms on all metrics

1. **Page shell (~208ms P50):** SpiritFlixHome render + hydration cost; model grouping; dev-mode Next.js overhead. Useful content is real (library grid), not a blank shell.
2. **Cold video navigation (~1270ms P50):** includes route transition, player bundle mount, metadata fetch, and first buffer/decode in headless Chromium — not the same as warm tap-to-play.
3. **Warm tap P95 (64ms):** browser `play()` scheduling floor in headless Chromium; still within 65ms acceptable stop.
