#!/usr/bin/env bash
set -euo pipefail

# ── Headroom proxy (8797) ───────────────────────────────────────────
# Source Proxy owns 8787. Headroom gets its own lane so compress() stops
# talking to the wrong service and silently "saving" zero tokens.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${HEADROOM_PORT:-8797}"
HOST="${HEADROOM_HOST:-127.0.0.1}"
VENV="${ROOT}/.venv-headroom"

resolve_headroom() {
  if command -v headroom >/dev/null 2>&1; then
    command -v headroom
    return 0
  fi
  if [[ -x "${VENV}/bin/headroom" ]]; then
    echo "${VENV}/bin/headroom"
    return 0
  fi
  return 1
}

if ! HEADROOM_BIN="$(resolve_headroom)"; then
  echo "Headroom CLI not found in PATH or ${VENV}/bin/headroom."
  echo "Install or repair the Linux-native Headroom venv out of band, then rerun this script."
  echo "No package install was attempted by this launcher."
  exit 1
fi

echo "Starting Headroom proxy on http://${HOST}:${PORT}"
echo "Then run: npm run context:source-proxy-min"
exec "${HEADROOM_BIN}" proxy --host "$HOST" --port "$PORT"
