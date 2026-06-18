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
  run_readonly free -h
  run_readonly df -h / /mnt/spirit-8tb
  run_readonly systemctl --failed --no-pager
  echo
  echo "## warning logs, last 60 minutes"
  journalctl -b -0 -p warning..alert --since "60 minutes ago" --no-pager 2>&1 | tail -240 || true
  echo
  echo "## kernel logs, last 60 minutes"
  journalctl -k -b -0 --since "60 minutes ago" --no-pager 2>&1 | tail -160 || true
} >"$LOG" 2>&1

echo "$LOG"
