#!/bin/bash
set -u

SPIRITOS_HEALTH_DIR="${SPIRITOS_HEALTH_DIR:-/mnt/spirit-8tb/spiritos-health}"
SPIRITOS_HEALTH_LOCK_DIR="$SPIRITOS_HEALTH_DIR/locks"
SPIRITOS_HEALTH_RUN_ID="$(date -Is | tr ':' '-')"

mkdir -p "$SPIRITOS_HEALTH_DIR" "$SPIRITOS_HEALTH_LOCK_DIR" 2>/dev/null || exit 0

spiritos_health_lock() {
  local lock_name="$1"
  exec 9>"$SPIRITOS_HEALTH_LOCK_DIR/${lock_name}.lock"
  if ! flock -n 9; then
    echo "already running: $lock_name"
    exit 0
  fi
}

spiritos_health_log_path() {
  local script_name="$1"
  printf '%s/%s.%s.log\n' "$SPIRITOS_HEALTH_DIR" "$script_name" "$SPIRITOS_HEALTH_RUN_ID"
}

run_readonly() {
  echo
  echo "## $*"
  "$@" 2>&1 || true
}

curl_timed() {
  local label="$1"
  local url="$2"
  echo
  echo "## $label"
  curl -skS -m 8 -w '\nHTTP=%{http_code} time_total=%{time_total} connect=%{time_connect} starttransfer=%{time_starttransfer}\n' "$url" 2>&1 || true
}

write_header() {
  local script_name="$1"
  echo "spiritos read-only health snapshot: $script_name"
  date -Is
  hostname
}
