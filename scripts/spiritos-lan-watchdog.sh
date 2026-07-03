#!/usr/bin/env bash
set -uo pipefail

ROOT="${SPIRITOS_ROOT:-$HOME/SpiritOS}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=runtime-port-guard.sh
source "$SCRIPT_DIR/runtime-port-guard.sh"
LOG="${SPIRITOS_LAN_WATCHDOG_LOG:-$HOME/spiritos-dev-lan-watchdog.log}"
DEV_LOG="${SPIRITOS_LAN_DEV_LOG:-$HOME/spiritos-dev-lan.log}"
RESTART_DELAY="${SPIRITOS_LAN_RESTART_DELAY:-8}"
HEALTH_URL="${SPIRITOS_LAN_HEALTH_URL:-https://127.0.0.1:3000/spiritflix}"
FRONTEND_SCRIPT="${SPIRITOS_LAN_FRONTEND_SCRIPT:-dev:https:lan}"
HEALTH_INTERVAL="${SPIRITOS_LAN_HEALTH_INTERVAL:-20}"
HEALTH_STARTUP_GRACE="${SPIRITOS_LAN_HEALTH_STARTUP_GRACE:-180}"
HEALTH_FAILURE_LIMIT="${SPIRITOS_LAN_HEALTH_FAILURE_LIMIT:-5}"
HEALTH_CURL_TIMEOUT="${SPIRITOS_LAN_HEALTH_CURL_TIMEOUT:-15}"
CACHE_CLEAR_EVERY="${SPIRITOS_LAN_CACHE_CLEAR_EVERY:-3}"

export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=1536}"

log() {
  printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "$LOG"
}

snapshot() {
  {
    echo "== snapshot $(date -Is) =="
    echo "-- tmux --"
    tmux ls 2>&1 || true
    echo "-- ports --"
    ss -ltnp 2>/dev/null | grep -E ':3000|:8787|:3001|:22|:11434' || true
    echo "-- node/next processes --"
    ps -eo pid,ppid,stat,pcpu,pmem,rss,etime,cmd --sort=-rss 2>/dev/null | grep -E 'next|node|npm run dev:https:lan' | grep -v grep || true
    echo "-- memory --"
    free -h 2>/dev/null || true
    echo "-- disk --"
    df -h "$ROOT" 2>/dev/null || true
    echo "-- kernel oom hints --"
    dmesg -T 2>/dev/null | grep -Ei 'out of memory|oom-kill|killed process|next-server|node' | tail -n 40 || true
  } >> "$LOG"
}

clean_next_dev_cache() {
  log "clearing Next dev cache before frontend start"
  rm -rf .next/dev/cache .next/cache
  rm -f .next/dev/lock 2>/dev/null || true
}

stop_frontend_processes() {
  local pid="${1:-}"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    log "terminating frontend pid $pid"
    kill -TERM "$pid" 2>/dev/null || true
  fi
  kill_spiritos_lan_listeners
  wait_for_port_free 3000 8 || true
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    log "killing frontend pid $pid"
    kill -KILL "$pid" 2>/dev/null || true
  fi
  force_kill_spiritos_lan_listeners
  wait_for_port_free 3000 5 || true
  local foreign_pids foreign_pid
  foreign_pids="$(listener_pids_on_port 3000)"
  if [[ -n "$foreign_pids" ]]; then
    while IFS= read -r foreign_pid; do
      [[ -z "$foreign_pid" ]] && continue
      log "warning: foreign listener still on :3000 pid=$foreign_pid (watchdog will not kill it)"
    done <<< "$foreign_pids"
    return 1
  fi
}

health_check() {
  local headers code
  headers="$(curl -k -sS -I --max-time "$HEALTH_CURL_TIMEOUT" "$HEALTH_URL" 2>/dev/null || true)"
  if printf '%s' "$headers" | grep -qi 'x-powered-by: next.js'; then
    return 0
  fi
  code="$(curl -k -sS -o /dev/null -w '%{http_code}' --max-time "$HEALTH_CURL_TIMEOUT" "$HEALTH_URL" 2>/dev/null || echo 000)"
  [[ "$code" =~ ^[23] ]]
}

cd "$ROOT" || {
  log "cannot cd to $ROOT"
  exit 1
}

log "watchdog starting in $ROOT (health=$HEALTH_URL grace=${HEALTH_STARTUP_GRACE}s)"
cleanup_orphan_next_smoke_ports
snapshot

restart_count=0
skip_next_cache_clear=0

while true; do
  stop_frontend_processes ""
  if (( skip_next_cache_clear )); then
    log "skipping cache clear after fast-fail restart"
    skip_next_cache_clear=0
    rm -f .next/dev/lock 2>/dev/null || true
  elif (( restart_count % CACHE_CLEAR_EVERY == 0 )); then
    clean_next_dev_cache
  else
    rm -f .next/dev/lock 2>/dev/null || true
  fi
  log "starting frontend: npm run $FRONTEND_SCRIPT"
  npm run "$FRONTEND_SCRIPT" >> "$DEV_LOG" 2>&1 &
  app_pid=$!
  failures=0
  started_at=$(date +%s)

  while kill -0 "$app_pid" 2>/dev/null; do
    now=$(date +%s)
    age=$((now - started_at))
    if (( age < HEALTH_STARTUP_GRACE )); then
      sleep "$HEALTH_INTERVAL"
      continue
    fi
    if health_check; then
      if (( failures > 0 )); then
        log "frontend health recovered after $failures failed check(s)"
      fi
      failures=0
    else
      failures=$((failures + 1))
      log "frontend health check failed $failures/$HEALTH_FAILURE_LIMIT for $HEALTH_URL"
      if (( failures >= HEALTH_FAILURE_LIMIT )); then
        log "frontend is hung or unreachable; restarting"
        snapshot
        stop_frontend_processes "$app_pid"
        break
      fi
    fi
    sleep "$HEALTH_INTERVAL"
  done

  if kill -0 "$app_pid" 2>/dev/null; then
    status=124
  else
    wait "$app_pid"
    status=$?
    if (( status == 1 )) && (( $(date +%s) - started_at < 45 )); then
      log "frontend failed fast (likely EADDRINUSE); force-clearing :3000 listeners"
      force_kill_spiritos_lan_listeners
      wait_for_port_free 3000 15 || true
      skip_next_cache_clear=1
    fi
    log "frontend exited with status $status"
    snapshot
  fi

  restart_count=$((restart_count + 1))

  if [[ "${SPIRITOS_LAN_WATCHDOG_ONCE:-}" == "1" ]]; then
    exit "$status"
  fi
  log "restarting frontend in ${RESTART_DELAY}s (restart_count=$restart_count)"
  sleep "$RESTART_DELAY"
done
