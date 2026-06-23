#!/usr/bin/env bash
set -euo pipefail

STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F06"
PYTHON_BIN="${PYTHON_BIN:-/home/source/SpiritOS/.venv-source-proxy/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="python3"
fi

echo "F06 operator check"
python3 - <<'PY'
import hashlib, json
from pathlib import Path
stage=Path('docs/spiritos-full-repo-cleanup-20260621/F06')
status=json.loads((stage/'status.json').read_text())
for name in ['acceptance-contract.json','holdout-manifest.json','status.json']:
    json.loads((stage/name).read_text())
assert status.get('acceptance_contract_sha256') == hashlib.sha256((stage/'acceptance-contract.json').read_bytes()).hexdigest()
assert status.get('holdout_manifest_sha256') == hashlib.sha256((stage/'holdout-manifest.json').read_bytes()).hexdigest()
print('  [OK] frozen contract artifacts parse and hashes match status')
PY

"$PYTHON_BIN" - <<'PY'
from source_proxy.tasks import long_running
from source_proxy.tasks.engine import state
assert long_running._append_unique_steps is state.append_unique_steps
assert long_running._has_approved_execution is state.has_approved_execution
assert long_running._terminal_or_waiting_statuses is state.terminal_or_waiting_statuses
assert long_running._task_blocker_reason_code is state.task_blocker_reason_code
assert long_running._task_queue_title is state.task_queue_title
print('  [OK] long_running aliases extracted state helpers without circular import')
PY

"$PYTHON_BIN" -m pytest source_proxy/tests/test_long_running_engine_state.py source_proxy/tests/test_long_running_tasks.py::LongRunningTaskTrackerTests::test_create_and_poll_task_without_execution source_proxy/tests/test_long_running_tasks.py::LongRunningTaskTrackerTests::test_list_long_running_tasks_returns_read_only_queue_items source_proxy/tests/test_long_running_tasks.py::LongRunningTaskTrackerTests::test_create_blocks_second_live_write_task_on_same_scope source_proxy/tests/test_long_running_tasks.py::LongRunningTaskTrackerTests::test_task_payload_lists_multi_worker_lanes_as_evidence_only -q
printf '  [OK] F6 state/readback parity tests pass
'

python3 - <<'PY'
import subprocess
allowed={
 'source_proxy/tasks/long_running.py',
 'source_proxy/tasks/engine/__init__.py',
 'source_proxy/tasks/engine/state.py',
 'source_proxy/tests/test_long_running_engine_state.py',
 'docs/spiritos-full-repo-cleanup-20260621/cleanup-state.json',
}
allowed_prefixes={'docs/spiritos-full-repo-cleanup-20260621/F06/'}
result=subprocess.run(['git','diff','--name-only','HEAD'], check=True, capture_output=True, text=True)
untracked=subprocess.run(['git','ls-files','--others','--exclude-standard'], check=True, capture_output=True, text=True)
paths=sorted({line.strip() for blob in (result.stdout, untracked.stdout) for line in blob.splitlines() if line.strip()})
bad=[p for p in paths if p not in allowed and not any(p.startswith(prefix) for prefix in allowed_prefixes)]
assert not bad, f'non-F6 paths changed: {bad}'
protected=[p for p in paths if p.startswith(('src/components/spiritflix/','src/lib/spiritflix','scripts/media/','services/jellyfin/'))]
assert not protected, f'protected media/Jellyfin paths changed: {protected}'
print('  [OK] changed paths are F6-scoped and protected paths are untouched')
PY

git diff --check
printf '  [OK] git diff --check
'

echo "F06 operator check: PASS"
