#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
PYTHON_BIN="${SOURCE_PROXY_PYTHON:-./.venv-source-proxy/bin/python}"

exec "$PYTHON_BIN" -m source_proxy.sandbox.bubblewrap probe-home
