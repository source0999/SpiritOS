#!/bin/bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$SCRIPT_DIR/spiritos-health-lib.sh"

SCRIPT_NAME="${0##*/}"
spiritos_health_lock "$SCRIPT_NAME"
LOG="$(spiritos_health_log_path "$SCRIPT_NAME")"

{
  write_header "$SCRIPT_NAME"
  run_readonly uptime
  echo
  echo "## boot history"
  journalctl --list-boots 2>&1 || true
  echo
  echo "## previous boot warning logs"
  journalctl -b -1 -p warning..alert --no-pager 2>&1 | tail -240 || true
  echo
  echo "## previous boot kernel logs"
  journalctl -k -b -1 --no-pager 2>&1 | tail -200 || true
  echo
  echo "## last records"
  last -x 2>&1 | head -80 || true
} >"$LOG" 2>&1

echo "$LOG"
