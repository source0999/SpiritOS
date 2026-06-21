#!/usr/bin/env bash
set -euo pipefail

ROOT="${SPIRITOS_ROOT:-$HOME/SpiritOS}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=runtime-port-guard.sh
source "$SCRIPT_DIR/runtime-port-guard.sh"
LOG="${SPIRITFLIX_STABLE_WATCHDOG_LOG:-$HOME/spiritflix-stable-3001-watchdog.log}"
WORKDIR="${SPIRITFLIX_STABLE_WORKDIR:-/tmp/spiritos-spiritflix-stable-3001}"
PORT="${SPIRITFLIX_STABLE_PORT:-3001}"
HEALTH_URL="${SPIRITFLIX_STABLE_HEALTH_URL:-http://127.0.0.1:3001/spiritflix}"
RESTART_DELAY="${SPIRITFLIX_STABLE_RESTART_DELAY:-8}"
HEALTH_INTERVAL="${SPIRITFLIX_STABLE_HEALTH_INTERVAL:-30}"
HEALTH_FAILURE_LIMIT="${SPIRITFLIX_STABLE_HEALTH_FAILURE_LIMIT:-3}"

log() {
  printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "$LOG"
}

health_check() {
  local code
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 12 "$HEALTH_URL" 2>/dev/null || echo 000)"
  [[ "$code" =~ ^[23] ]]
}

if [[ ! -d "$WORKDIR" ]]; then
  log "missing SpiritFlix stable workdir: $WORKDIR"
  exit 1
fi

cd "$WORKDIR"
log "SpiritFlix stable watchdog starting on :$PORT ($WORKDIR)"

while true; do
  port_pids="$(listener_pids_on_port "$PORT")"
  if [[ -n "$port_pids" ]]; then
    while IFS= read -r pid; do
      [[ -z "$pid" ]] && continue
      kill -TERM "$pid" 2>/dev/null || true
    done <<< "$port_pids"
    wait_for_port_free "$PORT" 8 || true
  fi

  log "starting SpiritFlix stable: npm run start -- -H 0.0.0.0 -p $PORT"
  npm run start -- -H 0.0.0.0 -p "$PORT" >> "${WORKDIR}.log" 2>> "${WORKDIR}.err.log" &
  app_pid=$!
  failures=0

  while kill -0 "$app_pid" 2>/dev/null; do
    if health_check; then
      failures=0
    else
      failures=$((failures + 1))
      log "SpiritFlix :$PORT health failed $failures/$HEALTH_FAILURE_LIMIT"
      if (( failures >= HEALTH_FAILURE_LIMIT )); then
        log "SpiritFlix :$PORT unreachable; restarting"
        kill -TERM "$app_pid" 2>/dev/null || true
        wait_for_port_free "$PORT" 5 || true
        kill -KILL "$app_pid" 2>/dev/null || true
        break
      fi
    fi
    sleep "$HEALTH_INTERVAL"
  done

  if kill -0 "$app_pid" 2>/dev/null; then
    :
  else
    wait "$app_pid" || true
    log "SpiritFlix :$PORT exited; restarting in ${RESTART_DELAY}s"
  fi
  sleep "$RESTART_DELAY"
done
