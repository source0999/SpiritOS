#!/usr/bin/env bash
# F02 operator check - live F2 gates.
set -euo pipefail

STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F02"
PYTHON_BIN="${PYTHON_BIN:-/home/source/SpiritOS/.venv-source-proxy/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="python3"
fi

echo "F02 operator check"

test -s "$STAGE_DIR/acceptance-contract.json"
test -s "$STAGE_DIR/holdout-manifest.json"
test -s "$STAGE_DIR/status.json"
python3 -c "import json; [json.load(open('$STAGE_DIR/'+f)) for f in ['acceptance-contract.json','holdout-manifest.json','status.json']]"
echo "  [OK] contract artifacts present and parse"

"$PYTHON_BIN" - <<'PY'
from pathlib import Path
from source_proxy.verification.anticheat import detector_registry, run_anticheat_detectors
registry = detector_registry()
assert Path('source_proxy/verification/anticheat').is_dir()
assert len(registry.detector_ids) >= 15
report = run_anticheat_detectors({'canned_output': True})
assert report.status == 'fail'
assert any(v.violation_code == 'canned_output_detected' for v in report.violations)
print('  [OK] anticheat package imports and registry detects canned output')
PY

"$PYTHON_BIN" -m pytest -q source_proxy/tests/test_anticheat_registry.py
"$PYTHON_BIN" -m pytest -q source_proxy/tests/test_status_codes.py
echo "  [OK] F2 focused tests pass"

python3 - <<'PY'
import subprocess
allowed_exact = {
    'source_proxy/tests/test_anticheat_registry.py',
    'docs/spiritos-full-repo-cleanup-20260621/cleanup-state.json',
    'docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py',
}
allowed_prefixes = {
    'source_proxy/verification/anticheat/',
    'docs/spiritos-full-repo-cleanup-20260621/F02/',
}
result = subprocess.run(['git','diff','--name-only','HEAD'], check=True, capture_output=True, text=True)
paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
bad = [p for p in paths if p not in allowed_exact and not any(p.startswith(prefix) for prefix in allowed_prefixes)]
assert not bad, f'non-F2 paths changed: {bad}'
protected = [p for p in paths if p.startswith(('src/components/spiritflix/','src/lib/spiritflix','scripts/media/','services/jellyfin/'))]
assert not protected, f'protected media/Jellyfin paths changed: {protected}'
legacy = [p for p in paths if p in {'source_proxy/verification/contracts.py','source_proxy/verification/deterministic.py','source_proxy/verification/diff.py','source_proxy/verification/__init__.py'}]
assert not legacy, f'legacy verification module modified: {legacy}'
print('  [OK] changed paths are F2-scoped and legacy verification modules unchanged')
PY

if git diff -- source_proxy/verification/anticheat docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py | grep -E '^\+.*fake_go_detected[[:space:]]*=[[:space:]]*False|^\+.*fake_go_detected=False|^\+.*default PASS|^\+.*hardcode.*success' >/tmp/f02-forbidden-grep.txt; then
  cat /tmp/f02-forbidden-grep.txt
  echo "  [FAIL] forbidden fake_go/default-pass/hardcoded-success edit"
  exit 1
fi
if git diff -- source_proxy src scripts _blueprints services | grep -E '^diff --git a/(src/components/spiritflix/|src/lib/spiritflix|scripts/media/|services/jellyfin/)' >/tmp/f02-protected-grep.txt; then
  cat /tmp/f02-protected-grep.txt
  echo "  [FAIL] protected path changed"
  exit 1
fi
echo "  [OK] anti-cheat/protected-path scans pass"

git diff --check
echo "  [OK] git diff --check"

echo "F02 operator check: PASS"
exit 0
