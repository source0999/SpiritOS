# SpiritFlix Anime Performance smoke

Generated: 2026-06-28T03:27:47.734Z
Base URL: https://10.0.0.186:3000
Jellyfin URL: http://127.0.0.1:8096
Runs: 1
Auth source: Jellyfin local DB device token for Source (SpiritFlix Web), token redacted.

## Libraries

- Anime: Anime (121 playable items)
- Normal: Home Videos and Photos (763 playable items)
- Anime playback item: Bust Through the Heavens with Your Drill!!
- Normal playback item: ۟ - hiiiiiiiiiiii was i missed ：p [2039892035646488576]

## Metrics

| Viewport | Anime route P50/P95 | Normal route P50/P95 | Anime API P50/P95 | Normal API P50/P95 | Anime play to playing P50/P95 | Normal play to playing P50/P95 | Anime thumbnails P50 | Anime source | Normal source |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Desktop 1440x900 | 4766.4 ms / 4766.4 ms | 1946.7 ms / 1946.7 ms | 113.7 ms / 113.7 ms | 103.0 ms / 103.0 ms | n/a / n/a | 16376.2 ms / 16376.2 ms | 4920.8 ms | n/a | directMp4 |

## Route Detail

### Desktop 1440x900
- home: useful 1573.1 ms P50 / 1573.1 ms P95; API 388.2 ms P50 / 526.9 ms P95; requests 21 P50; thumbnails 0 P50; bytes-before-useful 137344 P50.
- library: useful 1946.7 ms P50 / 1946.7 ms P95; API 271.6 ms P50 / 500.6 ms P95; requests 21 P50; thumbnails 0 P50; bytes-before-useful 137344 P50.
- anime: useful 4766.4 ms P50 / 4766.4 ms P95; API 311.2 ms P50 / 633.3 ms P95; requests 21 P50; thumbnails 0 P50; bytes-before-useful 137344 P50.

## Playback Detail

### Desktop 1440x900
- anime: visible n/a P50; metadata n/a P50; canplay n/a P50; playing n/a P50; range no; waiting 0; stalled 0; source n/a.
- normal: visible 964.7 ms P50; metadata 14134.1 ms P50; canplay 16375.8 ms P50; playing 16376.2 ms P50; range yes; waiting 1; stalled 1; source directMp4.

## Commands

- `node scripts/spiritflix-anime-performance-harness.mjs --label=smoke --runs=1 --evidence-dir=/home/source/SpiritOS/docs/evidence/spiritflix-anime-perf-20260627-232746`

## Errors

- desktop/anime-playback: locator.waitFor: Timeout 15000ms exceeded.
Call log:
  - waiting for locator('.spiritflix-player video').first()


## Evidence

- JSON: /home/source/SpiritOS/docs/evidence/spiritflix-anime-perf-20260627-232746/smoke.json
- Screenshots: /home/source/SpiritOS/docs/evidence/spiritflix-anime-perf-20260627-232746/screenshots
