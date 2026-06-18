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
  echo "OLLAMA model storage evidence only; no environment dump."
  run_readonly systemctl status ollama --no-pager
  run_readonly ls -ld /mnt/spirit-8tb /mnt/spirit-8tb/ollama-models
  run_readonly du -sh /mnt/spirit-8tb/ollama-models
  curl_timed "Ollama tags, no restart" "http://127.0.0.1:11434/api/tags"
  curl_timed "Ollama loaded models, no restart" "http://127.0.0.1:11434/api/ps"
} >"$LOG" 2>&1

echo "$LOG"
