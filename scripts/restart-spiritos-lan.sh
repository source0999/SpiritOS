#!/usr/bin/env bash
set -euo pipefail

ROOT="${SPIRITOS_ROOT:-$HOME/SpiritOS}"

cd "$ROOT"

printf 'Restarting SpiritOS HTTPS LAN app on :3000 only. Source proxy :8787 and SpiritFlix sidecar :3001 are left untouched.\n'

# shellcheck source=runtime-port-guard.sh
source "$ROOT/scripts/runtime-port-guard.sh"
cleanup_orphan_next_smoke_ports

tmux kill-session -t spiritos-lan 2>/dev/null || true
pkill -f "npm run dev:https:lan:watch" 2>/dev/null || true
pkill -f "scripts/spiritos-lan-watchdog.sh" 2>/dev/null || true
port_pids="$(lsof -ti tcp:3000 2>/dev/null || true)"
if [[ -n "$port_pids" ]]; then
  printf 'terminating stale port 3000 pid(s): %s\n' "${port_pids//$'\n'/ }"
  printf '%s\n' "$port_pids" | xargs -r kill -TERM
fi
for _ in 1 2 3 4 5; do
  if [[ -z "$(lsof -ti tcp:3000 2>/dev/null || true)" ]]; then
    break
  fi
  sleep 1
done
port_pids="$(lsof -ti tcp:3000 2>/dev/null || true)"
if [[ -n "$port_pids" ]]; then
  printf 'killing stale port 3000 pid(s): %s\n' "${port_pids//$'\n'/ }"
  printf '%s\n' "$port_pids" | xargs -r kill -KILL
fi
for _ in 1 2 3 4 5; do
  if [[ -z "$(lsof -ti tcp:3000 2>/dev/null || true)" ]]; then
    break
  fi
  sleep 1
done
rm -rf .next
chmod +x scripts/spiritos-lan-watchdog.sh
tmux new-session -d -s spiritos-lan "cd '$ROOT' && npm run dev:https:lan:watch"

sleep "${SPIRITOS_LAN_RESTART_WAIT:-35}"
tmux ls || true
ss -ltnp | grep -E ':3000|:8787|:22|:11434' || true
curl -k -I --max-time 25 https://localhost:3000/coding || true
