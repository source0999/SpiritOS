#!/usr/bin/env bash
set -euo pipefail

STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F05"
PYTHON_BIN="${PYTHON_BIN:-/home/source/SpiritOS/.venv-source-proxy/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="python3"
fi

echo "F05 operator check"
python3 - <<'PY'
import hashlib, json
from pathlib import Path
stage = Path('docs/spiritos-full-repo-cleanup-20260621/F05')
status = json.loads((stage / 'status.json').read_text())
for name in ['acceptance-contract.json', 'holdout-manifest.json', 'status.json']:
    json.loads((stage / name).read_text())
assert status.get('acceptance_contract_sha256') == hashlib.sha256((stage / 'acceptance-contract.json').read_bytes()).hexdigest()
assert status.get('holdout_manifest_sha256') == hashlib.sha256((stage / 'holdout-manifest.json').read_bytes()).hexdigest()
print('  [OK] frozen contract artifacts parse and hashes match status')
PY

"$PYTHON_BIN" - <<'PY'
from pathlib import Path
from source_proxy.api import decision
from source_proxy.decision.lanes import status_helpers
assert decision._lane_status is status_helpers.lane_status
assert decision._packet_lane_status is status_helpers.packet_lane_status
assert decision._receipt_failure_event is status_helpers.receipt_failure_event
text = Path('source_proxy/api/decision.py').read_text()
for marker in ['@router.post("/route")', '@router.post("/prompt-packet")', '@router.post("/recommend-model")']:
    assert text.count(marker) == 1, marker
print('  [OK] imports are acyclic and public route handlers remain')
PY

"$PYTHON_BIN" -m pytest source_proxy/tests/test_decision_lane_status_helpers.py source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_status_codes.py source_proxy/tests/test_packet_decomposition.py -q
printf '  [OK] F5 focused parity tests and F1-F4 compatibility tests pass
'

python3 - <<'PY'
import subprocess
allowed = {
    'source_proxy/api/decision.py',
    'source_proxy/decision/lanes/__init__.py',
    'source_proxy/decision/lanes/status_helpers.py',
    'source_proxy/tests/test_decision_lane_status_helpers.py',
    'docs/spiritos-full-repo-cleanup-20260621/cleanup-state.json',
}
allowed_prefixes = {'docs/spiritos-full-repo-cleanup-20260621/F05/'}
result = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], check=True, capture_output=True, text=True)
untracked = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], check=True, capture_output=True, text=True)
paths = sorted({line.strip() for blob in (result.stdout, untracked.stdout) for line in blob.splitlines() if line.strip()})
bad = [p for p in paths if p not in allowed and not any(p.startswith(prefix) for prefix in allowed_prefixes)]
assert not bad, f'non-F5 paths changed: {bad}'
protected = [p for p in paths if p.startswith(('src/components/spiritflix/', 'src/lib/spiritflix', 'scripts/media/', 'services/jellyfin/'))]
assert not protected, f'protected media/Jellyfin paths changed: {protected}'
print('  [OK] changed paths are F5-scoped and protected paths are untouched')
PY

git diff --check
printf '  [OK] git diff --check
'

echo "F05 operator check: PASS"
