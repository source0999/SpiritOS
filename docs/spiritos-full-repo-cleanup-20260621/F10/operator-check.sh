#!/usr/bin/env bash
set -euo pipefail
STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F10"
PYTHON_BIN="${PYTHON_BIN:-/home/source/SpiritOS/.venv-source-proxy/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then PYTHON_BIN="python3"; fi
echo "F10 operator check"
python3 - <<'PY'
import hashlib, json
from pathlib import Path
root=Path('docs/spiritos-full-repo-cleanup-20260621')
stage=root/'F10'
status=json.loads((stage/'status.json').read_text())
assert status['status'] == 'READY_FOR_GLM_SECONDARY_AUDIT'
assert status['verdict'] == 'READY_FOR_GLM_SECONDARY_AUDIT'
assert status['acceptance_contract_sha256'] == hashlib.sha256((stage/'acceptance-contract.json').read_bytes()).hexdigest()
assert status['holdout_manifest_sha256'] == hashlib.sha256((stage/'holdout-manifest.json').read_bytes()).hexdigest()
for i in range(1,10):
    data=json.loads((root/f'F{i:02d}'/'status.json').read_text())
    assert data.get('status') == 'INTERNAL_GO_PENDING_SECONDARY_REVIEW', i
assert (stage/'secondary-review-handoff.md').is_file()
state=json.loads((root/'cleanup-state.json').read_text())
assert state['ready_for_secondary_review'] is True
assert state['secondary_review_completed'] is False
assert state['old_plan_resumed'] is False
assert state['current_stage'] == 'SECONDARY_REVIEW'
print('  [OK] F10 status/state/handoff ready for secondary audit')
PY
"$PYTHON_BIN" -m pytest source_proxy/tests/test_status_codes.py source_proxy/tests/test_anticheat_registry.py source_proxy/tests/test_brain_switch_contract.py source_proxy/tests/test_packet_decomposition.py source_proxy/tests/test_decision_lane_status_helpers.py source_proxy/tests/test_long_running_engine_state.py source_proxy/tests/test_worker_tool_adapters.py -q
printf '  [OK] focused backend requalification tests pass
'
git diff --check
printf '  [OK] git diff --check
'
echo "F10 operator check: PASS"
