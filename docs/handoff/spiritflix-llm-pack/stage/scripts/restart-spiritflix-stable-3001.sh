#!/usr/bin/env bash
set -euo pipefail

ROOT="${SPIRITOS_ROOT:-$HOME/SpiritOS}"
WORKDIR="${SPIRITFLIX_STABLE_WORKDIR:-/tmp/spiritos-spiritflix-stable-3001}"
PORT="${SPIRITFLIX_STABLE_PORT:-3001}"

if [[ ! -d "$WORKDIR" ]]; then
  printf 'SpiritFlix stable workdir missing: %s\n' "$WORKDIR" >&2
  exit 1
fi

printf 'Restarting SpiritFlix stable on :%s only. SpiritOS :3000 and proxy :8787 are left untouched.\n' "$PORT"

tmux kill-session -t spiritflix-stable-3001 2>/dev/null || true
pkill -f "spiritflix-stable-watchdog.sh" 2>/dev/null || true

port_pids="$(lsof -ti "tcp:${PORT}" 2>/dev/null || true)"
if [[ -n "$port_pids" ]]; then
  printf 'terminating stale port %s pid(s): %s\n' "$PORT" "${port_pids//$'\n'/ }"
  printf '%s\n' "$port_pids" | xargs -r kill -TERM
fi
sleep 2
port_pids="$(lsof -ti "tcp:${PORT}" 2>/dev/null || true)"
if [[ -n "$port_pids" ]]; then
  printf '%s\n' "$port_pids" | xargs -r kill -KILL
fi

chmod +x "$ROOT/scripts/spiritflix-stable-watchdog.sh"
tmux new-session -d -s spiritflix-stable-3001 "cd '$WORKDIR' && bash '$ROOT/scripts/spiritflix-stable-watchdog.sh'"

sleep "${SPIRITFLIX_STABLE_RESTART_WAIT:-15}"
tmux ls || true
ss -ltnp | grep -E ":${PORT}" || true
curl -sS -o /dev/null -w 'spiritflix :%s -> %{http_code}\n' --max-time 20 "http://127.0.0.1:${PORT}/spiritflix" || true
