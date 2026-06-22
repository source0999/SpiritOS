#!/usr/bin/env bash
set -euo pipefail
STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F09"
PYTHON_BIN="${PYTHON_BIN:-/home/source/SpiritOS/.venv-source-proxy/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then PYTHON_BIN="python3"; fi
echo "F09 operator check"
python3 - <<'PY'
import hashlib, json
from pathlib import Path
stage=Path('docs/spiritos-full-repo-cleanup-20260621/F09')
status=json.loads((stage/'status.json').read_text())
for name in ['acceptance-contract.json','holdout-manifest.json','status.json']:
    json.loads((stage/name).read_text())
assert status.get('acceptance_contract_sha256') == hashlib.sha256((stage/'acceptance-contract.json').read_bytes()).hexdigest()
assert status.get('holdout_manifest_sha256') == hashlib.sha256((stage/'holdout-manifest.json').read_bytes()).hexdigest()
print('  [OK] frozen contract artifacts parse and hashes match status')
PY
"$PYTHON_BIN" -m pytest source_proxy/tests/test_worker_tool_adapters.py source_proxy/tests/test_decision_lane_status_helpers.py source_proxy/tests/test_status_codes.py source_proxy/tests/test_long_running_engine_state.py -q
printf '  [OK] F9 focused adapter and compatibility tests pass
'
"$PYTHON_BIN" -m py_compile source_proxy/decision/worker_tool_adapters.py source_proxy/api/decision.py
printf '  [OK] changed Python modules compile
'
python3 - <<'PY'
import subprocess
allowed={'source_proxy/api/decision.py','source_proxy/decision/worker_tool_adapters.py','source_proxy/tests/test_worker_tool_adapters.py','docs/spiritos-full-repo-cleanup-20260621/cleanup-state.json'}
allowed_prefixes={'docs/spiritos-full-repo-cleanup-20260621/F09/'}
result=subprocess.run(['git','diff','--name-only','HEAD'], check=True, capture_output=True, text=True)
untracked=subprocess.run(['git','ls-files','--others','--exclude-standard'], check=True, capture_output=True, text=True)
paths=sorted({line.strip() for blob in (result.stdout, untracked.stdout) for line in blob.splitlines() if line.strip()})
bad=[p for p in paths if p not in allowed and not any(p.startswith(prefix) for prefix in allowed_prefixes)]
assert not bad, f'non-F9 paths changed: {bad}'
print('  [OK] changed paths are F9-scoped')
PY
git diff --check
printf '  [OK] git diff --check
'
echo "F09 operator check: PASS"
