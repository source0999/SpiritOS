#!/usr/bin/env bash
# ── Headroom proxy reachability check ───────────────────────────────
set -euo pipefail

HOST="${HEADROOM_HOST:-127.0.0.1}"
PORT="${HEADROOM_PORT:-8797}"
BASE="${HEADROOM_BASE_URL:-http://${HOST}:${PORT}}"
BASE="${BASE%/}"

echo "Headroom proxy check: ${BASE}/health"

if curl -fsS --max-time 3 "${BASE}/health" >/dev/null 2>&1; then
  echo "headroom_present: true"
  echo "headroom_proxy_reachable: true"
  echo "hint: npm run context:source-proxy-min will use Headroom when proxy is up"
  exit 0
fi

echo "headroom_present: true (venv/cli may exist)"
echo "headroom_proxy_reachable: false"
echo "hint: start with npm run headroom:proxy in another terminal"
echo "fallback: tight repomix profile still produces uploadable tree-sitter output"
exit 1
