# SpiritFlix Anime Importer

Use `scripts/media/spiritflix_anime_import.py` to place authorized anime episodes into the Jellyfin-backed SpiritFlix anime folder.

This importer is for media you own, created, or have written permission/license to download and process. It refuses known unauthorized streaming mirror hosts and does not bypass DRM, site protections, or copyright restrictions.

## Folder Decision

The live Jellyfin compose file mounts:

- Host: `/mnt/spirit-8tb/media/anime`
- Jellyfin: `/media/anime`

The existing Rurouni Kenshin layout on the host is:

```text
/mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/
  Season 01/
  Season 02/
```

So this importer uses that existing pattern instead of creating a parallel `/Caasca/SpiritFlix/...` tree:

```text
/mnt/spirit-8tb/media/anime/<Series Name>/Season NN/
```

For Rurouni Kenshin, keep using:

```text
/mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 01/
```

## One-Episode Test

Run this on the Dell host. It tests episode 1 and stops. Because `S01E01` already exists, the command should skip the existing file and write a receipt rather than duplicate it.

```bash
cd /home/source/SpiritOS
python3 scripts/media/spiritflix_anime_import.py \
  --series "Rurouni Kenshin (1996)" \
  --season 1 \
  --episode 1 \
  --stop-after 1 \
  --audio dub \
  --source-file "/mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 01/Rurouni Kenshin (1996) - S01E01.mkv" \
  --affirm-authorized \
  --authorization-note "One-episode SpiritFlix placement smoke test."
```

Receipt log:

```text
/mnt/spirit-8tb/media/anime/.spiritos-import-receipts/YYYYMMDD.jsonl
```

## Import From an Authorized URL

Install `yt-dlp` on the host first if needed. Then use a direct or supported URL that you are allowed to download:

```bash
cd /home/source/SpiritOS
python3 scripts/media/spiritflix_anime_import.py \
  --series "Example Anime (2026)" \
  --season 1 \
  --episode 1 \
  --stop-after 1 \
  --audio dub \
  --source-url "https://example.com/authorized-episode-1" \
  --affirm-authorized \
  --authorization-note "Licensed or owned test episode."
```

## Batch / Season Import

For any series, create a CSV manifest with one row per episode. The downloader/importer uses the row metadata to place files into the right series and season folder.

```csv
series,season,episode,audio,source_url,source_file,episode_title
Rurouni Kenshin (1996),1,1,dub,,/mnt/spirit-8tb/media-originals/keep-for-30-days/anime/mi-mpzx6l69-9a89a8d2/Rurouni Kenshin (1996) - S01E01.mkv,
Example Anime (2026),1,1,dub,https://example.com/authorized-episode-1,,
Example Anime (2026),1,2,dub,https://example.com/authorized-episode-2,,
```

Run the whole manifest:

```bash
cd /home/source/SpiritOS
python3 scripts/media/spiritflix_anime_import.py \
  --manifest /mnt/spirit-8tb/media-processing/my-anime-manifest.csv \
  --affirm-authorized \
  --authorization-note "Authorized anime batch import."
```

Test only the first row and stop:

```bash
cd /home/source/SpiritOS
python3 scripts/media/spiritflix_anime_import.py \
  --manifest /mnt/spirit-8tb/media-processing/my-anime-manifest.csv \
  --stop-after 1 \
  --affirm-authorized \
  --authorization-note "One-episode manifest smoke test."
```

The script is safe to re-run. Existing target files are skipped unless `--force` is provided.
By default, filenames match the existing SpiritFlix convention and do not include a quality tag. Add `--include-detected-quality` or `--quality 1080p` only when you intentionally want names like `[1080p]`.

## Dual-Audio HLS Via Mac Optimization

Use `scripts/media/spiritflix_dual_audio_anime_import.py` when episode input is split across two authorized HLS streams: one sub/Japanese stream with video and native audio, plus one dub/English stream with the dub audio. Run it from the Dell host. It SSHes to the Mac, downloads both HLS URLs with `yt-dlp`, remuxes Japanese + English audio, encodes the video with `hevc_videotoolbox`, writes a cloud copy under `~/yes/anime`, then copies the verified MP4 into the Jellyfin anime library.

One-episode test:

```bash
cd /home/source/SpiritOS
python3 scripts/media/spiritflix_dual_audio_anime_import.py \
  --series "Example Anime (2026)" \
  --season 1 \
  --episode 1 \
  --sub-url "https://example.com/authorized-sub-episode-1.m3u8" \
  --dub-url "https://example.com/authorized-dub-episode-1.m3u8" \
  --affirm-authorized \
  --authorization-note "Authorized dual-audio Episode 1 import."
```

The default final SpiritFlix path is:

```text
/mnt/spirit-8tb/media/anime/<Series Name>/Season NN/<Series Name> - SNNENN [1080p].mp4
```

The Mac cloud-monitored copy is:

```text
~/yes/anime/<Series Name>/Season NN/<Series Name> - SNNENN [1080p].mp4
```

For a full series, use a manifest:

```csv
series,season,episode,episode_title,sub_m3u8_url,dub_m3u8_url
Example Anime (2026),1,1,,https://example.com/authorized-sub-episode-1.m3u8,https://example.com/authorized-dub-episode-1.m3u8
Example Anime (2026),1,2,,https://example.com/authorized-sub-episode-2.m3u8,https://example.com/authorized-dub-episode-2.m3u8
```

Run only Episode 1 from a manifest:

```bash
cd /home/source/SpiritOS
python3 scripts/media/spiritflix_dual_audio_anime_import.py \
  --manifest /mnt/spirit-8tb/media-processing/dual-audio-anime.csv \
  --stop-after 1 \
  --affirm-authorized \
  --authorization-note "Authorized dual-audio manifest smoke test."
```

Useful knobs:

- `--mac-host spirit-mac-mini`: SSH target used from the Dell host.
- `--mac-cloud-root ~/yes/anime`: cloud-monitored output root on the Mac.
- `--video-bitrate 900k --maxrate 1600k --bufsize 3200k`: default mobile-friendly HEVC settings.
- `--force`: replace an existing target episode.
- `--dry-run`: write a receipt and show the planned target path without downloading.

## Send Downloads Through The Converter

Use `--send-to-converter` when the source file still needs SpiritOS conversion. This writes to the watched inbox:

```text
/mnt/spirit-8tb/media-inbox/anime/<Series Name>/Season NN/
```

The `media-ingest-worker` then converts it and moves the accepted output to:

```text
/mnt/spirit-8tb/media/anime/<Series Name>/Season NN/
```

Example one-episode handoff:

```bash
cd /home/source/SpiritOS
python3 scripts/media/spiritflix_anime_import.py \
  --series "Rurouni Kenshin (1996)" \
  --season 1 \
  --episode 2 \
  --audio dub \
  --source-file "/path/to/authorized/source-episode-2.mkv" \
  --send-to-converter \
  --affirm-authorized \
  --authorization-note "Authorized dub import for converter."
```

For downloader workflows, prefer `--send-to-converter`; otherwise the importer writes directly to the final Jellyfin library and bypasses conversion.

## Auto-Optimize The Yes Library

The media ingest worker also watches the existing SpiritFlix yes library:

```text
/mnt/spirit-8tb/media/yes
```

Files copied or uploaded directly into that folder are treated as library-source jobs. After the worker sees a stable file, it moves the file into active processing, creates the smaller MKV output under the same `media/yes` tree, writes a `.media-ingest.json` receipt beside the accepted output, and deletes the original large upload only after `ffprobe` verifies the converted output and the final move succeeds.

The default watch root can be changed with `MEDIA_INGEST_LIBRARY_WATCH_ROOTS`. Use the platform path separator to watch more than one root.

```bash
cd /home/source/SpiritOS
MEDIA_INGEST_ENCODER=mac-videotoolbox-hevc \
MEDIA_INGEST_LIBRARY_WATCH_ROOTS=/mnt/spirit-8tb/media/yes \
node ./scripts/media-ingest-worker.mjs
```

Set `MEDIA_INGEST_DELETE_LIBRARY_ORIGINALS=0` for a dry/holding run where library originals should not be deleted after successful conversion.

Manifest columns:

- `series`: Jellyfin series folder name, such as `Rurouni Kenshin (1996)`.
- `season`: Season number.
- `episode`: Episode number.
- `audio`: `dub`, `sub`, or `original`.
- `source_url`: Authorized URL to fetch with `yt-dlp`.
- `source_file`: Authorized local file to copy into the library.
- `episode_title`: Optional title to append to the filename.

## Safety Rules

- Default write root is `/mnt/spirit-8tb/media/anime`.
- Custom roots require `--allow-custom-root`.
- `--affirm-authorized` is required.
- Known unauthorized mirror hosts are refused.
- Existing files are not overwritten unless `--force` is provided.
- JSONL receipts include source, target, status, quality, audio lane, detected audio languages, and SHA-256 when available.
