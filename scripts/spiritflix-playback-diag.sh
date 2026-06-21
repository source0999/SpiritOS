#!/usr/bin/env bash
set -euo pipefail

CONTAINER="${SPIRITFLIX_JELLYFIN_CONTAINER:-spirit-jellyfin}"
CACHE_TRANSCODES="${SPIRITFLIX_JELLYFIN_CACHE_TRANSCODES:-/mnt/spirit-8tb/services/jellyfin/cache/transcodes}"
TRANSCODES="${SPIRITFLIX_JELLYFIN_TRANSCODES:-/mnt/spirit-8tb/services/jellyfin/transcodes}"
LOG_ROOT="${SPIRITFLIX_JELLYFIN_LOG_ROOT:-/mnt/spirit-8tb/services/jellyfin/config/log}"
MAC_HOST="${SPIRITFLIX_MAC_HOST:-spirit-mac-mini}"

section() {
  printf '\n== %s ==\n' "$1"
}

section "jellyfin ffmpeg processes"
docker top "$CONTAINER" 2>/dev/null | awk 'NR == 1 || /ffmpeg|jellyfin-ffmpeg|hls|transcode/i' || true

section "jellyfin docker stats"
docker stats --no-stream "$CONTAINER" 2>/dev/null || true

section "recent cache transcodes"
find "$CACHE_TRANSCODES" -maxdepth 1 -type f -printf '%TY-%Tm-%Td %TH:%TM:%TS %s %p\n' 2>/dev/null | sort | tail -20 || true

section "recent transcodes"
find "$TRANSCODES" -maxdepth 1 -type f -printf '%TY-%Tm-%Td %TH:%TM:%TS %s %p\n' 2>/dev/null | sort | tail -20 || true

section "container /dev/dri"
docker exec "$CONTAINER" sh -c 'ls -l /dev/dri 2>/dev/null || true' 2>/dev/null || true

section "mac playback/optimizer processes"
ssh "$MAC_HOST" "ps aux | egrep -i 'ffmpeg|videotoolbox|media-ingest|spiritflix-mobile' | grep -v egrep || true" 2>/dev/null || true

section "recent jellyfin log lines"
latest_log="$(find "$LOG_ROOT" -maxdepth 1 -type f \( -name '*.log' -o -name 'log_*.txt' \) -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)"
if [ -n "${latest_log:-}" ]; then
  grep -Ei 'ffmpeg|transcod|hls|error|fail|vaapi|playback' "$latest_log" 2>/dev/null | tail -80 || true
else
  echo "No Jellyfin log file found under $LOG_ROOT"
fi
