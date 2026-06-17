#!/usr/bin/env bash
set -euo pipefail

ROOT="${SPIRITOS_ROOT:-$HOME/SpiritOS}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=runtime-port-guard.sh
source "$SCRIPT_DIR/runtime-port-guard.sh"
LOG="${SOURCE_PROXY_LAN_WATCHDOG_LOG:-$HOME/source-proxy-lan-watchdog.log}"
HEALTH_URL="${SOURCE_PROXY_LAN_HEALTH_URL:-https://127.0.0.1:8787/healthcheck}"
RESTART_DELAY="${SOURCE_PROXY_LAN_RESTART_DELAY:-8}"
HEALTH_INTERVAL="${SOURCE_PROXY_LAN_HEALTH_INTERVAL:-30}"
HEALTH_FAILURE_LIMIT="${SOURCE_PROXY_LAN_HEALTH_FAILURE_LIMIT:-3}"
HEALTH_CURL_TIMEOUT="${SOURCE_PROXY_LAN_HEALTH_CURL_TIMEOUT:-20}"

log() {
  printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "$LOG"
}

health_check() {
  local code
  code="$(curl -k -sS -o /dev/null -w '%{http_code}' --max-time "$HEALTH_CURL_TIMEOUT" "$HEALTH_URL" 2>/dev/null || echo 000)"
  [[ "$code" =~ ^[23] ]]
}

cd "$ROOT" || exit 1
log "Source Proxy LAN watchdog starting (health=$HEALTH_URL)"

while true; do
  port_pids="$(listener_pids_on_port 8787)"
  if [[ -n "$port_pids" ]]; then
    while IFS= read -r pid; do
      [[ -z "$pid" ]] && continue
      kill -TERM "$pid" 2>/dev/null || true
    done <<< "$port_pids"
    wait_for_port_free 8787 8 || true
  fi

  log "starting Source Proxy: npm run proxy:https:lan"
  npm run proxy:https:lan 2>&1 | tee -a ~/source-proxy-https-lan.log &
  app_pid=$!
  failures=0

  while kill -0 "$app_pid" 2>/dev/null; do
    if health_check; then
      failures=0
    else
      failures=$((failures + 1))
      log "proxy :8787 health failed $failures/$HEALTH_FAILURE_LIMIT"
      if (( failures >= HEALTH_FAILURE_LIMIT )); then
        log "proxy :8787 unreachable; restarting"
        kill -TERM "$app_pid" 2>/dev/null || true
        wait_for_port_free 8787 5 || true
        pkill -f "uvicorn source_proxy.main:app.*8787" 2>/dev/null || true
        break
      fi
    fi
    sleep "$HEALTH_INTERVAL"
  done

  if ! kill -0 "$app_pid" 2>/dev/null; then
    wait "$app_pid" || true
    log "proxy :8787 exited; restarting in ${RESTART_DELAY}s"
  fi
  sleep "$RESTART_DELAY"
done
