# SpiritFlix Anime Performance smoke

Generated: 2026-06-28T03:22:33.376Z
Base URL: https://spirit.tailb69ea6.ts.net:3000
Jellyfin URL: http://127.0.0.1:8096
Runs: 1
Auth source: Jellyfin local DB device token for Source (Diag), token redacted.

## Libraries

- Anime: Anime (121 playable items)
- Normal: Home Videos and Photos (763 playable items)
- Anime playback item: Bust Through the Heavens with Your Drill!!
- Normal playback item: ۟ - hiiiiiiiiiiii was i missed ：p [2039892035646488576]

## Metrics

| Viewport | Anime route P50/P95 | Normal route P50/P95 | Anime API P50/P95 | Normal API P50/P95 | Anime play to playing P50/P95 | Normal play to playing P50/P95 | Anime thumbnails P50 | Anime source | Normal source |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Desktop 1440x900 | n/a / n/a | n/a / n/a | 114.5 ms / 114.5 ms | 302.1 ms / 302.1 ms | n/a / n/a | n/a / n/a | n/a | n/a | n/a |

## Route Detail

### Desktop 1440x900
- home: useful n/a P50 / n/a P95; API n/a P50 / n/a P95; requests n/a P50; thumbnails n/a P50; bytes-before-useful n/a P50.
- library: useful n/a P50 / n/a P95; API n/a P50 / n/a P95; requests n/a P50; thumbnails n/a P50; bytes-before-useful n/a P50.
- anime: useful n/a P50 / n/a P95; API n/a P50 / n/a P95; requests n/a P50; thumbnails n/a P50; bytes-before-useful n/a P50.

## Playback Detail

### Desktop 1440x900
- anime: visible n/a P50; metadata n/a P50; canplay n/a P50; playing n/a P50; range no; waiting 0; stalled 0; source n/a.
- normal: visible n/a P50; metadata n/a P50; canplay n/a P50; playing n/a P50; range no; waiting 0; stalled 0; source n/a.

## Commands

- `node scripts/spiritflix-anime-performance-harness.mjs --label=smoke --runs=1 --evidence-dir=/home/source/SpiritOS/docs/evidence/spiritflix-anime-perf-20260627-232231`

## Errors

- desktop/home: page.waitForFunction: Timeout 30000ms exceeded.
- desktop/library: page.waitForFunction: Timeout 30000ms exceeded.
- desktop/anime: page.waitForFunction: Timeout 30000ms exceeded.
- desktop/anime-playback: Route setup failed: page.waitForFunction: Timeout 30000ms exceeded.
- desktop/normal-playback: Route setup failed: page.waitForFunction: Timeout 30000ms exceeded.

## Evidence

- JSON: /home/source/SpiritOS/docs/evidence/spiritflix-anime-perf-20260627-232231/smoke.json
- Screenshots: /home/source/SpiritOS/docs/evidence/spiritflix-anime-perf-20260627-232231/screenshots
