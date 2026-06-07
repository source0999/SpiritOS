#!/usr/bin/env bash
set -euo pipefail

ROOT="${SPIRIT_ROOT:-$(pwd)}"
cd "$ROOT"

FRONTEND_URL="${SPIRIT_FRONTEND_URL:-https://10.0.0.186:3000}"
PROXY_URL="${SPIRIT_PROXY_URL:-https://10.0.0.186:8787}"
STORE="${SPIRIT_CODING_RUNS_STORE:-data/coding-runs.json}"

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
printf 'root=%s\nstore=%s\nfrontend=%s\nproxy=%s\n' "$ROOT" "$STORE" "$FRONTEND_URL" "$PROXY_URL"

section "durable run store"
node - "$STORE" <<'NODE'
const fs = require("fs");
const storePath = process.argv[2];
const terminal = new Set(["completed", "failed", "timed_out", "cancelled", "cleared", "reverted"]);
const inFlight = new Set(["pending", "running"]);
function violations(run) {
  const rows = Array.isArray(run.rows) ? run.rows : [];
  const running = rows.filter((row) => inFlight.has(row.status));
  const completedRows = rows.filter((row) => !inFlight.has(row.status) && row.result_label !== "RUNNING").length;
  const out = [];
  if (running.length > 1) out.push(`multiple_running_rows:${running.map((row) => row.prompt_id).join(",")}`);
  if ((run.completed_count ?? 0) < completedRows) out.push(`completed_count_below_rows:${run.completed_count}<${completedRows}`);
  if ((run.completed_count ?? 0) > (run.requested_count ?? 0)) out.push(`completed_count_above_requested:${run.completed_count}>${run.requested_count}`);
  if (terminal.has(run.status) && run.status !== "cleared" && run.status !== "cancelled" && running.length) {
    out.push(`terminal_run_has_running_row:${run.status}:${running.map((row) => row.prompt_id).join(",")}`);
  }
  if (run.status === "completed" && (run.completed_count ?? 0) < (run.requested_count ?? 0)) {
    out.push(`completed_status_before_full_count:${run.completed_count}/${run.requested_count}`);
  }
  if (run.status === "cleared" && run.current_prompt_id) out.push(`cleared_run_keeps_current_prompt:${run.current_prompt_id}`);
  if (running.length === 1 && run.current_prompt_id !== running[0].prompt_id) {
    out.push(`current_prompt_not_running_row:${run.current_prompt_id ?? "none"}!=${running[0].prompt_id}`);
  }
  return out;
}
if (!fs.existsSync(storePath)) {
  console.log(JSON.stringify({ exists: false, active: null, recent: [] }, null, 2));
  process.exit(0);
}
const payload = JSON.parse(fs.readFileSync(storePath, "utf8"));
const runs = Array.isArray(payload.runs) ? payload.runs : [];
const recent = runs.slice(0, 5).map((run) => ({
  run_id: run.run_id,
  status: run.status,
  completed_count: run.completed_count,
  requested_count: run.requested_count,
  current_prompt_id: run.current_prompt_id,
  last_write_decision: run.last_write_decision ?? null,
  invariant_violations: run.invariant_violations ?? violations(run),
  rows: (run.rows ?? []).map((row) => ({
    prompt_id: row.prompt_id,
    status: row.status,
    result_label: row.result_label,
    reason_code: row.reason_code,
    owner_kind: row.owner_kind ?? null,
    write_source: row.write_source ?? null,
  })),
  write_debug_tail: (run.write_debug ?? []).slice(-8),
}));
console.log(JSON.stringify({
  exists: true,
  active: recent.find((run) => !terminal.has(run.status)) ?? null,
  recent,
}, null, 2));
NODE

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
