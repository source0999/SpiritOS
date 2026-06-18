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
  run_readonly ss -ltnp
  run_readonly systemctl status ollama docker --no-pager
  run_readonly docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
  run_readonly tmux ls
  curl_timed "Source Proxy docs liveness, no restart" "https://127.0.0.1:8787/docs"
  curl_timed "Source Proxy OpenAPI liveness, no restart" "https://127.0.0.1:8787/openapi.json"
  curl_timed "Next HTTPS admin liveness, no restart" "https://127.0.0.1:3000/spiritflix/admin"
  curl_timed "Ollama tags, no restart" "http://127.0.0.1:11434/api/tags"
  curl_timed "Ollama loaded models, no restart" "http://127.0.0.1:11434/api/ps"
} >"$LOG" 2>&1

echo "$LOG"
