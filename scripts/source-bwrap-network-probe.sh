#!/usr/bin/env bash
set -uo pipefail

cd "$(dirname "$0")/.."
PYTHON_BIN="${SOURCE_PROXY_PYTHON:-./.venv-source-proxy/bin/python}"

echo "== namespace sysctls =="
sysctl kernel.unprivileged_userns_clone user.max_user_namespaces kernel.apparmor_restrict_unprivileged_userns 2>/dev/null || true

echo "== denied default egress =="
"$PYTHON_BIN" -m source_proxy.sandbox.bubblewrap probe-network-deny
DENY_STATUS=$?

echo "== trusted npm registry probe =="
"$PYTHON_BIN" -m source_proxy.sandbox.bubblewrap probe-npm-registry
NPM_STATUS=$?

if [[ "$DENY_STATUS" -eq 0 && "$NPM_STATUS" -eq 0 ]]; then
  exit 0
fi
exit 1
