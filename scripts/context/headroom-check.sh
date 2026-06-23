#!/usr/bin/env bash
# ── Headroom proxy reachability check ───────────────────────────────
set -euo pipefail

HOST="${HEADROOM_HOST:-127.0.0.1}"
PORT="${HEADROOM_PORT:-8797}"
BASE="${HEADROOM_BASE_URL:-http://${HOST}:${PORT}}"
BASE="${BASE%/}"

echo "Headroom proxy check: ${BASE}/health"

if curl -fsS --max-time 3 "${BASE}/health" >/dev/null 2>&1; then
  echo "headroom_health_success: true"
  echo "headroom_proxy_reachable: true"
  echo "headroom_active_contract: health_success_required_before_compression_claim"
  echo "hint: npm run context:source-proxy-min may use Headroom only when compressed=true and tokens_saved>0"
  exit 0
fi

echo "headroom_health_success: false"
echo "headroom_proxy_reachable: false"
echo "headroom_active_contract: inactive_until_health_success"
echo "hint: start with npm run headroom:proxy in another terminal if the Linux-native binary already exists"
echo "fallback: tree-sitter profile only; do not label as Headroom-compressed"
exit 1
