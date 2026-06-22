#!/usr/bin/env bash
set -euo pipefail

STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F04"
PYTHON_BIN="${PYTHON_BIN:-/home/source/SpiritOS/.venv-source-proxy/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="python3"
fi

echo "F04 operator check"

test -f "$STAGE_DIR/acceptance-contract.json"
test -f "$STAGE_DIR/holdout-manifest.json"
test -f "$STAGE_DIR/status.json"
python3 - <<'PY'
import hashlib, json
from pathlib import Path
stage = Path('docs/spiritos-full-repo-cleanup-20260621/F04')
status = json.loads((stage / 'status.json').read_text())
for name in ['acceptance-contract.json', 'holdout-manifest.json', 'status.json']:
    json.loads((stage / name).read_text())
expected = {
    'acceptance_contract_sha256': hashlib.sha256((stage / 'acceptance-contract.json').read_bytes()).hexdigest(),
    'holdout_manifest_sha256': hashlib.sha256((stage / 'holdout-manifest.json').read_bytes()).hexdigest(),
}
for key, digest in expected.items():
    assert status.get(key) == digest, f'{key} mismatch: status={status.get(key)} actual={digest}'
print('  [OK] frozen contract artifacts parse and hashes match status')
PY

"$PYTHON_BIN" - <<'PY'
from source_proxy.decision.packet_decomposition import decompose_task, supported_task_shapes
for shape in supported_task_shapes():
    result = decompose_task(f'fresh holdout for {shape}', task_shape=shape, evidence_ids=('ev-operator',))
    assert result.validation_status == 'pass'
    assert result.local_only is True
    assert result.provider_call_performed is False
    assert len(result.sub_packets) >= 3
print('  [OK] generic local decomposition validates for all task shapes')
PY

"$PYTHON_BIN" -m pytest source_proxy/tests/test_packet_decomposition.py source_proxy/tests/test_brain_switch_contract.py source_proxy/tests/test_status_codes.py source_proxy/tests/test_anticheat_registry.py -q
printf '  [OK] F4 focused tests and F1-F3 compatibility tests pass
'

python3 - <<'PY'
from pathlib import Path
needles = ('A2', 'A5', 'A9', 'Set A', '4R', '4R7')
for path in [
    Path('source_proxy/decision/packet_decomposition.py'),
    Path('source_proxy/decision/prompt_packet.py'),
    Path('source_proxy/api/decision.py'),
]:
    text = path.read_text(errors='ignore')
    hits = [needle for needle in needles if needle in text]
    assert not hits, f'benchmark labels in production {path}: {hits}'
print('  [OK] no named benchmark labels in F4 production code')
PY

python3 - <<'PY'
import subprocess
allowed = {
    'source_proxy/api/decision.py',
    'source_proxy/decision/prompt_packet.py',
    'source_proxy/decision/packet_decomposition.py',
    'source_proxy/decision/packet_templates/__init__.py',
    'source_proxy/tests/test_packet_decomposition.py',
    'docs/spiritos-full-repo-cleanup-20260621/cleanup-state.json',
}
allowed_prefixes = {'docs/spiritos-full-repo-cleanup-20260621/F04/'}
result = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], check=True, capture_output=True, text=True)
untracked = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], check=True, capture_output=True, text=True)
paths = sorted({line.strip() for blob in (result.stdout, untracked.stdout) for line in blob.splitlines() if line.strip()})
bad = [p for p in paths if p not in allowed and not any(p.startswith(prefix) for prefix in allowed_prefixes)]
assert not bad, f'non-F4 paths changed: {bad}'
protected = [p for p in paths if p.startswith(('src/components/spiritflix/', 'src/lib/spiritflix', 'scripts/media/', 'services/jellyfin/'))]
assert not protected, f'protected media/Jellyfin paths changed: {protected}'
print('  [OK] changed paths are F4-scoped and protected paths are untouched')
PY

git diff --check
printf '  [OK] git diff --check
'

echo "F04 operator check: PASS"
