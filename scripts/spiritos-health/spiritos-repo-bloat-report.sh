#!/bin/bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$SCRIPT_DIR/spiritos-health-lib.sh"

SCRIPT_NAME="${0##*/}"
spiritos_health_lock "$SCRIPT_NAME"
LOG="$(spiritos_health_log_path "$SCRIPT_NAME")"
REPO="${SPIRITOS_REPO:-/home/source/SpiritOS}"

{
  write_header "$SCRIPT_NAME"
  echo "Repo: $REPO"
  if [ -d "$REPO/.git" ]; then
    cd "$REPO" || exit 0
    run_readonly git status --short --untracked-files=normal
    run_readonly git count-objects -vH
    echo
    echo "## top-level file counts"
    find . -path ./.git -prune -o -type f -printf '%h\n' | sort | uniq -c | sort -nr | head -80 || true
  else
    echo "Repo not found: $REPO"
  fi
} >"$LOG" 2>&1

echo "$LOG"
