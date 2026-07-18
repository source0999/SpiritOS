#!/usr/bin/env bash
set -euo pipefail

ROOT="${SPIRIT_ROOT:-$(pwd)}"
cd "$ROOT"

FRONTEND_URL="${SPIRIT_FRONTEND_URL:-https://10.0.0.186:3000}"
PROXY_URL="${SPIRIT_PROXY_URL:-https://10.0.0.186:8787}"

section() {
  printf '\n== %s ==\n' "$1"
}

curl_probe() {
  local label="$1"
  local url="$2"
  local out="/tmp/spirit-coding-debug-${label//[^A-Za-z0-9_.-]/_}.json"
  local code
  code="$(curl -k -sS -o "$out" -w "%{http_code}" "$url" 2>/tmp/spirit-coding-debug-curl.err || true)"
  printf '%s %s\n' "$label" "${code:-curl_failed}"
  if [ -s "$out" ]; then
    head -c 2000 "$out"
    printf '\n'
  elif [ -s /tmp/spirit-coding-debug-curl.err ]; then
    head -c 400 /tmp/spirit-coding-debug-curl.err
    printf '\n'
  fi
}

section "coding sync snapshot"
date -Is
printf 'root=%s\nfrontend=%s\nproxy=%s\n' "$ROOT" "$FRONTEND_URL" "$PROXY_URL"

section "durable run authority"
printf '%s\n' 'Source Proxy long_running_tasks.sqlite3 is authoritative.'
printf '%s\n' 'data/coding-runs.json is a retired, ignored pre-R1 cache and is not inspected.'

section "agent-lab baseline"
node <<'NODE'
const fs = require("fs");
const path = require("path");
const roots = ["src/app/agent-lab", "src/components/agent-lab", "src/lib/agent-lab", "src/app/api/agent-lab", "tests/agent-lab"];
const files = [];
for (const root of roots) {
  if (!fs.existsSync(root)) continue;
  const stack = [root];
  while (stack.length) {
    const current = stack.pop();
    const stat = fs.statSync(current);
    if (stat.isDirectory()) {
      for (const name of fs.readdirSync(current)) stack.push(path.join(current, name));
    } else {
      files.push(current.replaceAll("\\", "/"));
    }
  }
}
console.log(JSON.stringify({ clean: files.length === 0, files: files.sort() }, null, 2));
NODE

section "git scoped status"
git status --short -- src/lib/coding src/components/coding src/app/v1/coding scripts/debug-coding-sync-state.sh src/app/agent-lab src/components/agent-lab src/lib/agent-lab src/app/api/agent-lab tests/agent-lab || true

section "runner/browser processes"
ps -ef | grep -E 'coder-frontend-acceptance|chromium_headless|chrome-headless|playwright|node /tmp' | grep -v grep || true

section "frontend route probes"
curl_probe "frontend-coding" "$FRONTEND_URL/coding"
curl_probe "active-run" "$FRONTEND_URL/v1/coding/runs/active"
curl_probe "recent-runs" "$FRONTEND_URL/v1/coding/runs/recent"
curl_probe "long-running-route-shape" "$FRONTEND_URL/v1/tasks/long-running"
curl_probe "prompt-packet-route-shape" "$FRONTEND_URL/v1/decisions/prompt-packet"

section "proxy health"
curl_probe "proxy-self-status" "$PROXY_URL/v1/self/status"

section "tmux log tails"
if command -v tmux >/dev/null 2>&1; then
  for pane in spiritos-lan source-proxy-lan; do
    printf -- '-- %s --\n' "$pane"
    tmux capture-pane -t "$pane" -p -S -80 2>/dev/null || true
  done
else
  echo "tmux unavailable"
fi
