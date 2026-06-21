# SpiritFlix Mobile Optimizer

The mobile optimizer is an offline lane. It does not change Jellyfin transcoding settings, Jellyfin SQLite, or original media files.

## Diagnostics

Run the read-only playback diagnostic from the Dell host:

```bash
cd /home/source/SpiritOS
bash scripts/spiritflix-playback-diag.sh
```

## Dry Run

Preview the known one-file smoke command without writing an MP4:

```bash
cd /home/source/SpiritOS
node scripts/spiritflix-mobile-optimize.mjs --dry-run --smoke-known
```

## Create One Mobile Copy

The Mac Mini must have `ffmpeg` with `h264_videotoolbox` available on PATH. Output and receipts stay under `/mnt/spirit-8tb/media/.spiritflix-admin/mobile-optimized/`.

```bash
cd /home/source/SpiritOS
node scripts/spiritflix-mobile-optimize.mjs \
  --encoder mac-videotoolbox-h264-mobile \
  --smoke-known
```

For a Jellyfin item that should be discoverable by item id in SpiritFlix playback, pass the Jellyfin item id:

```bash
node scripts/spiritflix-mobile-optimize.mjs \
  --encoder mac-videotoolbox-h264-mobile \
  --item-id JELLYFIN_ITEM_ID \
  --source /mnt/spirit-8tb/media/yes/example.mkv
```
