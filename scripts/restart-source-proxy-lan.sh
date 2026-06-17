#!/usr/bin/env bash
set -euo pipefail

ROOT="${SPIRITOS_ROOT:-$HOME/SpiritOS}"

cd "$ROOT"

printf 'Restarting Source Proxy HTTPS LAN on :8787 only. SpiritOS frontend :3000 and SpiritFlix :3001 are left untouched.\n'

tmux kill-session -t source-proxy-lan 2>/dev/null || true
pkill -f "source-proxy-lan-watchdog.sh" 2>/dev/null || true
pkill -f "scripts/source-proxy-dev.mjs --https --lan" 2>/dev/null || true

port_pids="$(lsof -ti tcp:8787 2>/dev/null || true)"
if [[ -n "$port_pids" ]]; then
  printf 'terminating stale port 8787 pid(s): %s\n' "${port_pids//$'\n'/ }"
  printf '%s\n' "$port_pids" | xargs -r kill -TERM
fi
for _ in 1 2 3 4 5; do
  if [[ -z "$(lsof -ti tcp:8787 2>/dev/null || true)" ]]; then
    break
  fi
  sleep 1
done
port_pids="$(lsof -ti tcp:8787 2>/dev/null || true)"
if [[ -n "$port_pids" ]]; then
  printf 'killing stale port 8787 pid(s): %s\n' "${port_pids//$'\n'/ }"
  printf '%s\n' "$port_pids" | xargs -r kill -KILL
fi

tmux new-session -d -s source-proxy-lan "cd '$ROOT' && bash ./scripts/source-proxy-lan-watchdog.sh"

sleep "${SPIRITOS_PROXY_RESTART_WAIT:-12}"
tmux ls || true
ss -ltnp | grep -E ':3000|:8787|:3001' || true
curl -k -sS --max-time 15 https://localhost:8787/v1/self/status | head -c 400 || true
printf '\n'
