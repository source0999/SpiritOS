#!/usr/bin/env bash
set -euo pipefail

# STABLE SpiritFlix serving mode for :3000.
# This runs a production Next build and serves it with `next start`, so repo
# writes from upload watchdogs, worker receipts, generated reports, or normal
# editing do not trigger browser reloads. Use `npm run spiritflix:admin:dev`
# on its separate port when fast-refresh editing is needed.

ROOT="${SPIRITOS_ROOT:-$(pwd)}"
PORT="${SPIRITFLIX_PROD_PORT:-3000}"
INTERNAL_PORT="${SPIRITFLIX_PROD_INTERNAL_PORT:-3002}"
SESSION="${SPIRITFLIX_PROD_TMUX_SESSION:-spiritos-lan}"
LOG_FILE="${SPIRITFLIX_PROD_LOG_FILE:-.codex-next-3000.log}"

cd "$ROOT"

printf 'Building SpiritFlix production bundle for :%s from %s\n' "$PORT" "$ROOT"
npx next build

printf 'Starting SpiritFlix production server on :%s. Source proxy :8787 and SpiritFlix sidecar :3001 are left untouched.\n' "$PORT"
printf 'Next production upstream will run on 127.0.0.1:%s behind the local HTTPS wrapper.\n' "$INTERNAL_PORT"

tmux kill-session -t "$SESSION" 2>/dev/null || true
pkill -f "npm run dev:https:lan:watch" 2>/dev/null || true
pkill -f "scripts/spiritos-lan-watchdog.sh" 2>/dev/null || true

port_pids="$(lsof -ti "tcp:${PORT}" 2>/dev/null || true)"
if [[ -n "$port_pids" ]]; then
  printf 'terminating stale port %s pid(s): %s\n' "$PORT" "${port_pids//$'\n'/ }"
  printf '%s\n' "$port_pids" | xargs -r kill -TERM
fi
for _ in 1 2 3 4 5; do
  if [[ -z "$(lsof -ti "tcp:${PORT}" 2>/dev/null || true)" ]]; then
    break
  fi
  sleep 1
done
port_pids="$(lsof -ti "tcp:${PORT}" 2>/dev/null || true)"
if [[ -n "$port_pids" ]]; then
  printf 'killing stale port %s pid(s): %s\n' "$PORT" "${port_pids//$'\n'/ }"
  printf '%s\n' "$port_pids" | xargs -r kill -KILL
fi

internal_pids="$(lsof -ti "tcp:${INTERNAL_PORT}" 2>/dev/null || true)"
if [[ -n "$internal_pids" ]]; then
  printf 'terminating stale internal port %s pid(s): %s\n' "$INTERNAL_PORT" "${internal_pids//$'\n'/ }"
  printf '%s\n' "$internal_pids" | xargs -r kill -TERM
fi
for _ in 1 2 3 4 5; do
  if [[ -z "$(lsof -ti "tcp:${INTERNAL_PORT}" 2>/dev/null || true)" ]]; then
    break
  fi
  sleep 1
done
internal_pids="$(lsof -ti "tcp:${INTERNAL_PORT}" 2>/dev/null || true)"
if [[ -n "$internal_pids" ]]; then
  printf 'killing stale internal port %s pid(s): %s\n' "$INTERNAL_PORT" "${internal_pids//$'\n'/ }"
  printf '%s\n' "$internal_pids" | xargs -r kill -KILL
fi

: > "$LOG_FILE"
tmux new-session -d -s "$SESSION" "cd '$ROOT' && npx next start -H 127.0.0.1 -p '$INTERNAL_PORT' >> '$LOG_FILE' 2>&1 & next_pid=\$!; node ./scripts/spiritflix-prod-https-proxy.mjs --port '$PORT' --target-port '$INTERNAL_PORT' --key ./certificates/spirit-dev-key.pem --cert ./certificates/spirit-dev.pem >> '$LOG_FILE' 2>&1; proxy_status=\$?; kill \$next_pid 2>/dev/null || true; wait \$next_pid 2>/dev/null || true; exit \$proxy_status"

sleep "${SPIRITFLIX_PROD_START_WAIT:-12}"
tmux ls || true
ss -ltnp | grep -E ":${PORT}|:${INTERNAL_PORT}|:8787|:3001|:22" || true
status="$(curl -sk -o /dev/null -w '%{http_code}' --max-time 25 "https://127.0.0.1:${PORT}/spiritflix" || true)"
printf 'spiritflix :%s -> %s\n' "$PORT" "$status"
printf 'Production log: %s/%s\n' "$ROOT" "$LOG_FILE"
if [[ "$status" != "200" ]]; then
  printf 'SpiritFlix production health check failed. Recent log:\n' >&2
  tail -80 "$LOG_FILE" >&2 || true
  exit 1
fi
