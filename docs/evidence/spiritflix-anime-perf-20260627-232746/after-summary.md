# SpiritFlix Anime Performance after

Generated: 2026-06-28T03:32:48.656Z
Base URL: https://10.0.0.186:3000
Jellyfin URL: http://127.0.0.1:8096
Runs: 3
Auth source: Jellyfin local DB device token for Source (SpiritFlix Web), token redacted.

## Libraries

- Anime: Anime (121 playable items)
- Normal: Home Videos and Photos (763 playable items)
- Anime playback item: Bust Through the Heavens with Your Drill!!
- Normal playback item: ۟ - hiiiiiiiiiiii was i missed ：p [2039892035646488576]

## Metrics

| Viewport | Anime route P50/P95 | Normal route P50/P95 | Anime API P50/P95 | Normal API P50/P95 | Anime play to playing P50/P95 | Normal play to playing P50/P95 | Anime thumbnails P50 | Anime source | Normal source |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Desktop 1440x900 | 1956.3 ms / 10116.5 ms | 2157.1 ms / 4057.1 ms | 102.2 ms / 108.4 ms | 41.8 ms / 42.6 ms | 3787.4 ms / 10563.6 ms | 5115.4 ms / 5305.7 ms | 2182.0 ms | directMp4 | directMp4 |
| Samsung Fold 7 main display emulation | 1574.5 ms / 1736.3 ms | 1743.8 ms / 1906.1 ms | 91.5 ms / 98.2 ms | 31.0 ms / 60.7 ms | 3434.0 ms / 3657.5 ms | 5353.2 ms / 5446.3 ms | 1629.1 ms | directMp4 | directMp4 |

## Route Detail

### Desktop 1440x900
- home: useful 1379.3 ms P50 / 11574.3 ms P95; API 434.1 ms P50 / 949.0 ms P95; requests 20 P50; thumbnails 0 P50; bytes-before-useful 137344 P50.
- library: useful 2157.1 ms P50 / 4057.1 ms P95; API 375.4 ms P50 / 2171.5 ms P95; requests 20 P50; thumbnails 0 P50; bytes-before-useful 137344 P50.
- anime: useful 1956.3 ms P50 / 10116.5 ms P95; API 312.4 ms P50 / 636.6 ms P95; requests 20 P50; thumbnails 0 P50; bytes-before-useful 137344 P50.
### Samsung Fold 7 main display emulation
- home: useful 1212.1 ms P50 / 1290.4 ms P95; API 220.1 ms P50 / 378.1 ms P95; requests 21 P50; thumbnails 0 P50; bytes-before-useful 137344 P50.
- library: useful 1743.8 ms P50 / 1906.1 ms P95; API 206.0 ms P50 / 500.3 ms P95; requests 21 P50; thumbnails 0 P50; bytes-before-useful 137344 P50.
- anime: useful 1574.5 ms P50 / 1736.3 ms P95; API 200.6 ms P50 / 381.0 ms P95; requests 21 P50; thumbnails 0 P50; bytes-before-useful 137344 P50.

## Playback Detail

### Desktop 1440x900
- anime: visible 734.1 ms P50; metadata 3686.2 ms P50; canplay 3786.2 ms P50; playing 3787.4 ms P50; range yes; waiting 3; stalled 1; source directMp4.
- normal: visible 1208.9 ms P50; metadata 5068.2 ms P50; canplay 5115.2 ms P50; playing 5115.4 ms P50; range yes; waiting 3; stalled 3; source directMp4.
### Samsung Fold 7 main display emulation
- anime: visible 484.3 ms P50; metadata 3358.0 ms P50; canplay 3433.8 ms P50; playing 3434.0 ms P50; range yes; waiting 3; stalled 0; source directMp4.
- normal: visible 1050.8 ms P50; metadata 5319.9 ms P50; canplay 5353.0 ms P50; playing 5353.2 ms P50; range yes; waiting 3; stalled 3; source directMp4.

## Commands

- `node scripts/spiritflix-anime-performance-harness.mjs --label=after --runs=3 --evidence-dir=/home/source/SpiritOS/docs/evidence/spiritflix-anime-perf-20260627-232746`

## Errors

- None

## Evidence

- JSON: /home/source/SpiritOS/docs/evidence/spiritflix-anime-perf-20260627-232746/after.json
- Screenshots: /home/source/SpiritOS/docs/evidence/spiritflix-anime-perf-20260627-232746/screenshots
