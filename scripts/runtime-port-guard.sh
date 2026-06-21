#!/usr/bin/env bash
# ── Runtime port guard ───────────────────────────────────────────────
# tmux-managed production dev ports. Agents/smoke scripts must not kill these.

PROTECTED_RUNTIME_PORTS=(3000 8787 3001)
SPIRITFLIX_ADMIN_SMOKE_PORTS=(3020 3030)
ORPHAN_NEXT_DEV_PORTS=(3020 3027 3030)

is_protected_runtime_port() {
  local port="$1"
  local p
  for p in "${PROTECTED_RUNTIME_PORTS[@]}"; do
    if [[ "$p" == "$port" ]]; then
      return 0
    fi
  done
  return 1
}

is_spiritos_lan_dev_args() {
  local args="$1"
  [[ "$args" == *"next dev"* ]] && [[ "$args" == *"3000"* ]] && [[ "$args" == *"experimental-https"* ]]
}

is_spiritos_lan_listener_pid() {
  local pid="$1"
  local args port_line
  args="$(ps -p "$pid" -o args= 2>/dev/null || true)"
  [[ -z "$args" ]] && return 1
  if is_spiritos_lan_dev_args "$args"; then
    return 0
  fi
  if [[ "$args" == *"next-server"* ]]; then
    port_line="$(ss -ltnp 2>/dev/null | grep "pid=$pid" | grep ':3000 ' || true)"
    [[ -n "$port_line" ]] && return 0
  fi
  if [[ "$args" == *"spiritos-lan-watchdog"* ]]; then
    return 0
  fi
  return 1
}

is_spiritos_lan_tree_pid() {
  local pid="$1"
  local depth=0
  while [[ -n "$pid" && "$pid" != "1" && depth -lt 10 ]]; do
    if is_spiritos_lan_listener_pid "$pid"; then
      return 0
    fi
    pid="$(ps -p "$pid" -o ppid= 2>/dev/null | tr -d ' ')"
    depth=$((depth + 1))
  done
  return 1
}

listener_pids_on_port() {
  local port="$1"
  lsof -ti "tcp:${port}" 2>/dev/null || true
}

kill_pids_gracefully() {
  local signal="${1:-TERM}"
  shift
  local pid
  for pid in "$@"; do
    [[ -z "$pid" ]] && continue
    kill "-$signal" "$pid" 2>/dev/null || true
  done
}

# Kill listeners on comma-separated ports. Skips protected ports unless FORCE=1.
kill_listeners_on_ports() {
  local ports_csv="${1:-}"
  local force="${SPIRITOS_RUNTIME_PORT_FORCE:-0}"
  local port pid port_pids

  IFS=',' read -r -a ports <<< "$ports_csv"
  for port in "${ports[@]}"; do
    [[ -z "$port" ]] && continue
    if [[ "$force" != "1" ]] && is_protected_runtime_port "$port"; then
      printf 'refusing to kill protected runtime port %s (tmux-managed; use npm run lan:restart)\n' "$port" >&2
      continue
    fi
    port_pids="$(listener_pids_on_port "$port")"
    [[ -z "$port_pids" ]] && continue
    while IFS= read -r pid; do
      [[ -z "$pid" ]] && continue
      kill -TERM "$pid" 2>/dev/null || true
    done <<< "$port_pids"
  done
}

kill_spiritos_lan_listener_tree() {
  local pid="$1"
  local signal="${2:-TERM}"
  local current="$pid"
  local depth=0
  local args

  while [[ -n "$current" && "$current" != "1" && depth -lt 12 ]]; do
    kill "-$signal" "$current" 2>/dev/null || true
    pkill "-$signal" -P "$current" 2>/dev/null || true
    args="$(ps -p "$current" -o args= 2>/dev/null || true)"
    if is_spiritos_lan_dev_args "$args"; then
      break
    fi
    current="$(ps -p "$current" -o ppid= 2>/dev/null | tr -d ' ')"
    depth=$((depth + 1))
  done
}

kill_spiritos_lan_listeners() {
  local pid port_pids
  port_pids="$(listener_pids_on_port 3000)"
  [[ -z "$port_pids" ]] && return 0
  while IFS= read -r pid; do
    [[ -z "$pid" ]] && continue
    if is_spiritos_lan_tree_pid "$pid"; then
      kill_spiritos_lan_listener_tree "$pid" TERM
    else
      printf 'refusing to kill foreign listener on :3000 pid=%s\n' "$pid" >&2
    fi
  done <<< "$port_pids"
  # Orphaned next dev parents can survive listener-only kills and block restarts.
  pkill -TERM -f "next dev -H 0.0.0.0 --webpack -p 3000 --experimental-https" 2>/dev/null || true
}

force_kill_spiritos_lan_listeners() {
  local pid port_pids
  port_pids="$(listener_pids_on_port 3000)"
  [[ -z "$port_pids" ]] && return 0
  while IFS= read -r pid; do
    [[ -z "$pid" ]] && continue
    if is_spiritos_lan_tree_pid "$pid"; then
      kill_spiritos_lan_listener_tree "$pid" KILL
    fi
  done <<< "$port_pids"
  pkill -KILL -f "next dev -H 0.0.0.0 --webpack -p 3000 --experimental-https" 2>/dev/null || true
}

cleanup_orphan_next_smoke_ports() {
  local port pid port_pids
  for port in "${ORPHAN_NEXT_DEV_PORTS[@]}"; do
    port_pids="$(listener_pids_on_port "$port")"
    [[ -z "$port_pids" ]] && continue
    printf 'cleaning orphan next dev listener(s) on :%s pid(s): %s\n' "$port" "${port_pids//$'\n'/ }" >&2
    while IFS= read -r pid; do
      [[ -z "$pid" ]] && continue
      kill -TERM "$pid" 2>/dev/null || true
      pkill -TERM -P "$pid" 2>/dev/null || true
    done <<< "$port_pids"
  done
  pkill -f "next dev -H 127.0.0.1 --port 3020" 2>/dev/null || true
  pkill -f "next dev -H 127.0.0.1 --port 3030" 2>/dev/null || true
  sleep 1
  for port in "${ORPHAN_NEXT_DEV_PORTS[@]}"; do
    port_pids="$(listener_pids_on_port "$port")"
    [[ -z "$port_pids" ]] && continue
    while IFS= read -r pid; do
      [[ -z "$pid" ]] && continue
      kill -KILL "$pid" 2>/dev/null || true
      pkill -KILL -P "$pid" 2>/dev/null || true
    done <<< "$port_pids"
  done
  pkill -KILL -f "next dev -H 127.0.0.1 --port 3020" 2>/dev/null || true
  pkill -KILL -f "next dev -H 127.0.0.1 --port 3030" 2>/dev/null || true
}

wait_for_port_free() {
  local port="$1"
  local attempts="${2:-8}"
  local _ attempt
  for ((attempt = 1; attempt <= attempts; attempt++)); do
    if [[ -z "$(listener_pids_on_port "$port")" ]]; then
      return 0
    fi
    sleep 1
  done
  return 1
}
