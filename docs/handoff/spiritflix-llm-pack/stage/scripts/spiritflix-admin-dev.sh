#!/usr/bin/env bash
# ── SpiritFlix admin smoke dev ───────────────────────────────────────
# Temporary localhost Next dev for /spiritflix/admin browser smoke.
# NEVER touches tmux-managed ports 3000, 8787, or 3001.

set -euo pipefail

ROOT="${SPIRITOS_ROOT:-$HOME/SpiritOS}"
PORT="${SPIRITFLIX_ADMIN_DEV_PORT:-3030}"
LOG="${SPIRITFLIX_ADMIN_DEV_LOG:-$HOME/spiritflix-admin-dev.log}"
ACTION="${1:-start}"

cd "$ROOT"

kill_smoke_ports() {
  local port_pids pid
  for port in 3020 3030; do
    port_pids="$(lsof -ti "tcp:${port}" 2>/dev/null || true)"
    [[ -z "$port_pids" ]] && continue
    printf 'stopping smoke dev on :%s pid(s): %s\n' "$port" "${port_pids//$'\n'/ }"
    while IFS= read -r pid; do
      [[ -z "$pid" ]] && continue
      kill -TERM "$pid" 2>/dev/null || true
    done <<< "$port_pids"
  done
  sleep 1
  for port in 3020 3030; do
    port_pids="$(lsof -ti "tcp:${port}" 2>/dev/null || true)"
    [[ -z "$port_pids" ]] && continue
    while IFS= read -r pid; do
      [[ -z "$pid" ]] && continue
      kill -KILL "$pid" 2>/dev/null || true
    done <<< "$port_pids"
  done
}

case "$ACTION" in
  start)
    kill_smoke_ports
    rm -f .next/dev/lock 2>/dev/null || true
    API_KEY="$(docker exec spirit-jellyfin cat /config/config/system.xml 2>/dev/null | sed -n 's:.*<ApiKey>\([^<]*\)</ApiKey>.*:\1:p' | head -1 || true)"
    printf 'starting SpiritFlix admin smoke dev on 127.0.0.1:%s (production :3000/:8787/:3001 untouched)\n' "$PORT"
    exec env \
      JELLYFIN_API_KEY="${API_KEY:-}" \
      JELLYFIN_URL="${JELLYFIN_URL:-http://127.0.0.1:8096}" \
      npx next dev -H 127.0.0.1 --port "$PORT" --webpack >>"$LOG" 2>&1
    ;;
  stop)
    kill_smoke_ports
    printf 'SpiritFlix admin smoke dev stopped.\n'
    ;;
  *)
    printf 'usage: %s [start|stop]\n' "$0" >&2
    exit 2
    ;;
esac
