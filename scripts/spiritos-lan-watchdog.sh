#!/usr/bin/env bash
set -uo pipefail

ROOT="${SPIRITOS_ROOT:-$HOME/SpiritOS}"
LOG="${SPIRITOS_LAN_WATCHDOG_LOG:-$HOME/spiritos-dev-lan-watchdog.log}"
DEV_LOG="${SPIRITOS_LAN_DEV_LOG:-$HOME/spiritos-dev-lan.log}"
RESTART_DELAY="${SPIRITOS_LAN_RESTART_DELAY:-5}"
HEALTH_URL="${SPIRITOS_LAN_HEALTH_URL:-https://127.0.0.1:3000/coding}"
FRONTEND_SCRIPT="${SPIRITOS_LAN_FRONTEND_SCRIPT:-dev:https:lan}"
HEALTH_INTERVAL="${SPIRITOS_LAN_HEALTH_INTERVAL:-15}"
HEALTH_STARTUP_GRACE="${SPIRITOS_LAN_HEALTH_STARTUP_GRACE:-75}"
HEALTH_FAILURE_LIMIT="${SPIRITOS_LAN_HEALTH_FAILURE_LIMIT:-3}"

log() {
  printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "$LOG"
}

snapshot() {
  {
    echo "== snapshot $(date -Is) =="
    echo "-- tmux --"
    tmux ls 2>&1 || true
    echo "-- ports --"
    ss -ltnp 2>/dev/null | grep -E ':3000|:8787|:22|:11434' || true
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
}

stop_frontend_processes() {
  local pid="${1:-}"
  local port_pids
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    log "terminating frontend pid $pid"
    kill -TERM "$pid" 2>/dev/null || true
  fi
  port_pids="$(lsof -ti tcp:3000 2>/dev/null || true)"
  if [[ -n "$port_pids" ]]; then
    log "terminating stale port 3000 pid(s): ${port_pids//$'\n'/ }"
    printf '%s\n' "$port_pids" | xargs -r kill -TERM
  fi
  for _ in 1 2 3 4 5; do
    if [[ -z "$(lsof -ti tcp:3000 2>/dev/null || true)" ]]; then
      break
    fi
    sleep 1
  done
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    log "killing frontend pid $pid"
    kill -KILL "$pid" 2>/dev/null || true
  fi
  port_pids="$(lsof -ti tcp:3000 2>/dev/null || true)"
  if [[ -n "$port_pids" ]]; then
    log "killing stale port 3000 pid(s): ${port_pids//$'\n'/ }"
    printf '%s\n' "$port_pids" | xargs -r kill -KILL
  fi
  for _ in 1 2 3 4 5; do
    if [[ -z "$(lsof -ti tcp:3000 2>/dev/null || true)" ]]; then
      return 0
    fi
    sleep 1
  done
  log "warning: port 3000 still occupied after cleanup"
}

health_check() {
  curl -k -fsS -I --max-time 8 "$HEALTH_URL" >/dev/null 2>&1
}

cd "$ROOT" || {
  log "cannot cd to $ROOT"
  exit 1
}

log "watchdog starting in $ROOT"
snapshot

while true; do
  stop_frontend_processes ""
  clean_next_dev_cache
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
    log "frontend exited with status $status"
    snapshot
  fi

  if [[ "${SPIRITOS_LAN_WATCHDOG_ONCE:-}" == "1" ]]; then
    exit "$status"
  fi
  log "restarting frontend in ${RESTART_DELAY}s"
  sleep "$RESTART_DELAY"
done
