#!/usr/bin/env bash
# F01 operator check - live F1 gates.
set -euo pipefail

STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F01"
PYTHON_BIN="${PYTHON_BIN:-/home/source/SpiritOS/.venv-source-proxy/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="python3"
fi

echo "F01 operator check"

# 1. Frozen contract artifacts exist and parse.
test -s "$STAGE_DIR/acceptance-contract.json"
test -s "$STAGE_DIR/holdout-manifest.json"
test -s "$STAGE_DIR/status.json"
python3 -c "import json; [json.load(open('$STAGE_DIR/'+f)) for f in ['acceptance-contract.json','holdout-manifest.json','status.json']]"
echo "  [OK] contract artifacts present and parse"

# 2. 19 classes are exactly the frozen set in contract and implementation.
"$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path
from source_proxy.diagnostics.status_codes import FailureClass
contract=json.load(open('docs/spiritos-full-repo-cleanup-20260621/F01/acceptance-contract.json'))
expected=set(contract['failure_classes_frozen'])
actual={item.value for item in FailureClass}
assert actual==expected, f"failure class set mismatch: missing={expected-actual} extra={actual-expected}"
assert len(actual)==19
assert Path('source_proxy/diagnostics/status_codes.py').is_file()
print('  [OK] taxonomy module implements frozen 19 classes')
PY

# 3. F1 focused behavior tests.
"$PYTHON_BIN" -m pytest -q source_proxy/tests/test_status_codes.py
"$PYTHON_BIN" -m pytest -q source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_model_lanes.py source_proxy/tests/test_model_lane_observability.py source_proxy/tests/test_model_lane_preview_api.py source_proxy/tests/test_decision_api_request_reset.py
echo "  [OK] F1 focused tests pass"

# 4. Changed paths must stay inside F1 scope.
python3 - <<'PY'
import subprocess, sys
allowed = {
    'source_proxy/diagnostics/status_codes.py',
    'source_proxy/decision/model_lanes.py',
    'source_proxy/api/decision.py',
    'source_proxy/tests/test_status_codes.py',
    'docs/spiritos-full-repo-cleanup-20260621/cleanup-state.json',
}
allowed_prefixes = {'docs/spiritos-full-repo-cleanup-20260621/F01/'}
result = subprocess.run(['git','diff','--name-only','HEAD'], check=True, capture_output=True, text=True)
paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
bad = [p for p in paths if p not in allowed and not any(p.startswith(prefix) for prefix in allowed_prefixes)]
assert not bad, f"non-F1 paths changed: {bad}"
protected = [p for p in paths if p.startswith(('src/components/spiritflix/','src/lib/spiritflix','scripts/media/','services/jellyfin/'))]
assert not protected, f"protected media/Jellyfin paths changed: {protected}"
print('  [OK] changed paths are F1-scoped')
PY

# 5. Anti-cheat and frozen-field checks.
if git diff -- source_proxy/diagnostics/status_codes.py source_proxy/decision/model_lanes.py source_proxy/api/decision.py | grep -E '^\+.*(A2|A5|A9|Set A|4R|fake_go_detected[[:space:]]*=|fake_go_detected.*False|default PASS)' >/tmp/f01-forbidden-grep.txt; then
  cat /tmp/f01-forbidden-grep.txt
  echo "  [FAIL] forbidden benchmark/default-pass/fake_go_detected edit token in runtime diff"
  exit 1
fi
if git diff -- source_proxy src scripts _blueprints services | grep -E '^diff --git a/(src/components/spiritflix/|src/lib/spiritflix|scripts/media/|services/jellyfin/)' >/tmp/f01-protected-grep.txt; then
  cat /tmp/f01-protected-grep.txt
  echo "  [FAIL] protected path changed"
  exit 1
fi
echo "  [OK] anti-cheat/protected-path scans pass"

# 6. Diff hygiene.
git diff --check
echo "  [OK] git diff --check"

echo "F01 operator check: PASS"
exit 0
