#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${SPIRITFLIX_REPO_ROOT:-/home/source/SpiritOS}"
DROP_DIR="${SPIRITFLIX_UPLOAD_DROP_DIR:-/mnt/storage8tb/media/yes}"
LIBRARY_DIR="${SPIRITFLIX_UPLOAD_LIBRARY_DIR:-/mnt/spirit-8tb/media/yes}"
DROP_TARGET="${SPIRITFLIX_UPLOAD_DROP_TARGET:-/DATA/yes}"
PYTHON="${SPIRITFLIX_FACE_ORGANIZER_PYTHON:-$REPO_ROOT/.venv-face-organizer/bin/python}"
SCAN_LIMIT="${SPIRITFLIX_UPLOAD_SCAN_LIMIT:-12}"
MAX_AGE_HOURS="${SPIRITFLIX_UPLOAD_MAX_AGE_HOURS:-72}"
POLL_SECONDS="${SPIRITFLIX_UPLOAD_POLL_SECONDS:-60}"
FACE_SCAN_NICE="${SPIRITFLIX_UPLOAD_FACE_SCAN_NICE:-15}"
FACE_SCAN_CPUSET="${SPIRITFLIX_UPLOAD_FACE_SCAN_CPUSET:-6,7}"
FACE_SCAN_THREADS="${SPIRITFLIX_UPLOAD_FACE_SCAN_THREADS:-2}"
LOG_PATH="${SPIRITFLIX_UPLOAD_WATCHDOG_LOG:-$REPO_ROOT/.codex-spiritflix-upload-watchdog.log}"
STATE_PATH="${SPIRITFLIX_UPLOAD_WATCHDOG_STATE:-$REPO_ROOT/.codex-spiritflix-upload-watchdog.state}"

VIDEO_FIND_EXPR=(
  -iname '*.mp4' -o
  -iname '*.mkv' -o
  -iname '*.mov' -o
  -iname '*.avi' -o
  -iname '*.webm'
)

log() {
  printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" | tee -a "$LOG_PATH"
}

ensure_drop_points_to_library() {
  if [ -L "$DROP_DIR" ]; then
    return 0
  fi
  if [ -d "$DROP_DIR" ] && [ "$(readlink -f "$DROP_DIR")" = "$(readlink -f "$LIBRARY_DIR")" ]; then
    return 0
  fi
  if [ -d "$DROP_DIR" ]; then
    local backup_dir
    backup_dir="$(dirname "$LIBRARY_DIR")/.spiritflix-admin/upload-drop-backups/$(date +%Y%m%dT%H%M%S)"
    mkdir -p "$backup_dir"
    find "$DROP_DIR" -maxdepth 1 -type f \( "${VIDEO_FIND_EXPR[@]}" \) ! -name '*.tmp' -print0 |
      while IFS= read -r -d '' file_path; do
        cp -n "$file_path" "$LIBRARY_DIR/"
      done
    mv "$DROP_DIR" "$backup_dir/misdirected-yes"
    ln -s "$DROP_TARGET" "$DROP_DIR"
    log "repointed upload drop to library; target=$DROP_TARGET backup=$backup_dir/misdirected-yes"
    return 0
  fi
  ln -s "$DROP_TARGET" "$DROP_DIR"
  log "created upload drop symlink to library target=$DROP_TARGET"
}

refresh_jellyfin() {
  cd "$REPO_ROOT"
  python3 - <<'PY'
import importlib.util
import sys

name = "sync_folder_playlists"
spec = importlib.util.spec_from_file_location(name, "/home/source/SpiritOS/services/jellyfin/sync_folder_playlists.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[name] = mod
spec.loader.exec_module(mod)
session = mod.get_session()
api = mod.JellyfinApi(session)
status, text = api.request("POST", "/Library/Refresh")
if status < 200 or status >= 300:
    raise SystemExit(f"Jellyfin refresh failed with HTTP {status}: {text[:300]}")
PY
}

sync_playlists() {
  cd "$REPO_ROOT"
  python3 services/jellyfin/sync_folder_playlists.py
}

scan_recent_uploads() {
  cd "$REPO_ROOT"
  local command=("$PYTHON")
  if [ -n "$FACE_SCAN_CPUSET" ] && command -v taskset >/dev/null 2>&1; then
    command=(taskset -c "$FACE_SCAN_CPUSET" "${command[@]}")
  fi
  if [ -n "$FACE_SCAN_NICE" ] && command -v nice >/dev/null 2>&1; then
    command=(nice -n "$FACE_SCAN_NICE" "${command[@]}")
  fi
  OMP_NUM_THREADS="$FACE_SCAN_THREADS" \
  OPENBLAS_NUM_THREADS="$FACE_SCAN_THREADS" \
  MKL_NUM_THREADS="$FACE_SCAN_THREADS" \
  NUMEXPR_NUM_THREADS="$FACE_SCAN_THREADS" \
  "${command[@]}" - <<PY
import importlib.util
import sys

name = "face_organizer"
spec = importlib.util.spec_from_file_location(name, "$REPO_ROOT/scripts/media/face_organizer.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[name] = mod
spec.loader.exec_module(mod)
args = mod.parse_args([
    "--source", "$LIBRARY_DIR",
    "--ctx-id", "-1",
    "--apply",
])
config = mod.make_config(args)
scanned = mod.scan_recent_unscanned_videos(
    config,
    limit=int("$SCAN_LIMIT"),
    max_age_hours=int("$MAX_AGE_HOURS"),
    refresh_pages=False,
)
print("\\n".join(scanned))
PY
}

recent_snapshot() {
  local library_real="$1"
  find "$library_real" -maxdepth 1 -type f \( "${VIDEO_FIND_EXPR[@]}" \) -mmin "-$((MAX_AGE_HOURS * 60))" ! -name '*.tmp' -printf '%T@ %s %p\n' | sort
}

missing_recent_sidecar_count() {
  local library_real="$1"
  local count=0
  while IFS= read -r video_path; do
    if [ ! -f "${video_path}.face-meta.json" ]; then
      count=$((count + 1))
    fi
  done < <(find "$library_real" -maxdepth 1 -type f \( "${VIDEO_FIND_EXPR[@]}" \) -mmin "-$((MAX_AGE_HOURS * 60))" ! -name '*.tmp' -print)
  printf '%s\n' "$count"
}

run_once() {
  ensure_drop_points_to_library
  local library_real
  library_real="$(readlink -f "$LIBRARY_DIR")"
  local snapshot missing_count
  snapshot="$(recent_snapshot "$library_real")"
  missing_count="$(missing_recent_sidecar_count "$library_real")"
  if [ -f "$STATE_PATH" ] && [ "$missing_count" = "0" ] && cmp -s "$STATE_PATH" <(printf '%s\n' "$snapshot"); then
    log "idle no recent upload changes"
    return 0
  fi
  local before_count after_count
  before_count="$(printf '%s\n' "$snapshot" | sed '/^$/d' | wc -l)"
  refresh_jellyfin
  sync_playlists | tee -a "$LOG_PATH"
  local scanned
  scanned=""
  if [ "$missing_count" != "0" ]; then
    scanned="$(scan_recent_uploads || true)"
  fi
  if [ -n "$scanned" ]; then
    log "smart-scanned recent uploads:"
    printf '%s\n' "$scanned" | tee -a "$LOG_PATH"
    refresh_jellyfin
    sync_playlists | tee -a "$LOG_PATH"
  fi
  recent_snapshot "$library_real" > "$STATE_PATH"
  after_count="$(sed '/^$/d' "$STATE_PATH" | wc -l)"
  log "cycle complete recent_before=$before_count recent_after=$after_count"
}

if [ "${1:-}" = "--once" ]; then
  run_once
  exit 0
fi

log "starting SpiritFlix upload watchdog drop=$DROP_DIR library=$LIBRARY_DIR poll=${POLL_SECONDS}s"
while true; do
  run_once || log "cycle failed"
  sleep "$POLL_SECONDS"
done
