#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${SOURCE_PROXY_BOOTSTRAP_PYTHON:-python3}"
VENV_DIR="${SOURCE_PROXY_VENV:-.venv-source-proxy}"
VENV_PYTHON="$VENV_DIR/bin/python"

echo "== Source proxy bootstrap =="
echo "Repo: $ROOT"

echo
echo "== Node environment =="
node --version
npm --version
npm install

echo
echo "== Python environment =="
"$PYTHON_BIN" --version
if ! "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import ensurepip
import venv
PY
then
  PY_VERSION="$("$PYTHON_BIN" - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)"
  cat >&2 <<EOF
Python venv support is not installed for $PYTHON_BIN.

On Debian/Ubuntu, install it with:
  sudo apt update
  sudo apt install -y python${PY_VERSION}-venv

Then rerun:
  npm run proxy:bootstrap
EOF
  exit 1
fi
"$PYTHON_BIN" -m venv "$VENV_DIR"
"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -r requirements.txt

echo
echo "== Compatibility probe =="
"$VENV_PYTHON" - <<'PY'
import importlib.metadata as metadata
import fastapi
import litellm
import pynvml

print("fastapi", fastapi.__version__)
print("litellm", metadata.version("litellm"))
print("pynvml ready")
PY

echo
echo "Bootstrap complete."
