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
SMART_RESCAN_API_URL="${SPIRITFLIX_UPLOAD_SMART_RESCAN_API_URL:-http://127.0.0.1:3000/api/spiritflix/library-smart-rescan}"
DRY_RUN=0
ENQUEUE_ONLY="${SPIRITFLIX_UPLOAD_ENQUEUE_ONLY:-1}"
LEGACY_FACE_SCAN="${SPIRITFLIX_UPLOAD_LEGACY_FACE_SCAN:-0}"
RUN_MODE="daemon"

VIDEO_FIND_EXPR=(
  -iname '*.mp4' -o
  -iname '*.mkv' -o
  -iname '*.mov' -o
  -iname '*.avi' -o
  -iname '*.webm'
)

usage() {
  cat <<'USAGE'
Usage: scripts/spiritflix-upload-watchdog.sh [--once] [--dry-run] [--enqueue-only]

  --dry-run       Print planned upload watchdog/enqueue actions; never mutate media or call APIs.
  --enqueue-only  Opt into enqueue-safe smart-rescan API calls instead of face scanning.
  --once          Run one cycle, then exit.

Default daemon mode now enqueues worker jobs. Set SPIRITFLIX_UPLOAD_LEGACY_FACE_SCAN=1 to run the old direct face scan path.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --once) RUN_MODE="once" ;;
    --dry-run) DRY_RUN=1 ;;
    --enqueue-only) ENQUEUE_ONLY=1 ;;
    --legacy-face-scan) LEGACY_FACE_SCAN=1; ENQUEUE_ONLY=0 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

log() {
  printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" | tee -a "$LOG_PATH"
}

ensure_drop_points_to_library() {
  if [ "$DRY_RUN" = "1" ]; then
    log "dry-run would ensure upload drop points to library drop=$DROP_DIR library=$LIBRARY_DIR target=$DROP_TARGET"
    return 0
  fi
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
  if [ "$DRY_RUN" = "1" ] || [ "$ENQUEUE_ONLY" = "1" ]; then
    log "planned skip Jellyfin refresh dry_run=$DRY_RUN enqueue_only=$ENQUEUE_ONLY"
    return 0
  fi
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
  if [ "$DRY_RUN" = "1" ] || [ "$ENQUEUE_ONLY" = "1" ]; then
    log "planned skip playlist sync dry_run=$DRY_RUN enqueue_only=$ENQUEUE_ONLY"
    return 0
  fi
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

recent_upload_paths() {
  local library_real="$1"
  find "$library_real" -maxdepth 1 -type f \( "${VIDEO_FIND_EXPR[@]}" \) -mmin "-$((MAX_AGE_HOURS * 60))" ! -name '*.tmp' -print | sort
}

enqueue_recent_uploads() {
  local library_real="$1"
  local planned=0
  while IFS= read -r video_path; do
    [ -n "$video_path" ] || continue
    planned=$((planned + 1))
    if [ -f "${video_path}.face-meta.json" ]; then
      continue
    fi
    local payload
    payload=$(python3 - "$video_path" <<'PY'
import json
import sys
print(json.dumps({"path": sys.argv[1]}))
PY
)
    if [ "$DRY_RUN" = "1" ]; then
      log "dry-run planned enqueue POST $SMART_RESCAN_API_URL payload=$payload"
      continue
    fi
    curl --fail --silent --show-error \
      -H 'Content-Type: application/json' \
      --data "$payload" \
      "$SMART_RESCAN_API_URL" | tee -a "$LOG_PATH"
    printf '\n' | tee -a "$LOG_PATH" >/dev/null
  done < <(recent_upload_paths "$library_real")
  log "planned enqueue count=$planned dry_run=$DRY_RUN enqueue_only=$ENQUEUE_ONLY"
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
  if [ "$DRY_RUN" = "1" ] || [ "$ENQUEUE_ONLY" = "1" ] || [ "$LEGACY_FACE_SCAN" != "1" ]; then
    enqueue_recent_uploads "$library_real"
    recent_snapshot "$library_real" > "$STATE_PATH"
    log "cycle complete enqueue_only recent_before=$(printf '%s\n' "$snapshot" | sed '/^$/d' | wc -l) dry_run=$DRY_RUN legacy_face_scan=$LEGACY_FACE_SCAN"
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

if [ "$RUN_MODE" = "once" ]; then
  run_once
  exit 0
fi

log "starting SpiritFlix upload watchdog drop=$DROP_DIR library=$LIBRARY_DIR poll=${POLL_SECONDS}s dry_run=$DRY_RUN enqueue_only=$ENQUEUE_ONLY legacy_face_scan=$LEGACY_FACE_SCAN"
while true; do
  run_once || log "cycle failed"
  sleep "$POLL_SECONDS"
done
