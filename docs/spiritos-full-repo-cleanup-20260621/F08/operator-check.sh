#!/usr/bin/env bash
set -euo pipefail
STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F08"
echo "F08 operator check"
python3 - <<'PY'
import hashlib, json
from pathlib import Path
stage=Path('docs/spiritos-full-repo-cleanup-20260621/F08')
status=json.loads((stage/'status.json').read_text())
for name in ['acceptance-contract.json','holdout-manifest.json','status.json']:
    json.loads((stage/name).read_text())
assert status.get('acceptance_contract_sha256') == hashlib.sha256((stage/'acceptance-contract.json').read_bytes()).hexdigest()
assert status.get('holdout_manifest_sha256') == hashlib.sha256((stage/'holdout-manifest.json').read_bytes()).hexdigest()
needles=['pkill','killall','npm install','pip install','python3 -m venv','Cursor must be killed']
for rel in ['scripts/context/headroom-check.sh','scripts/headroom-proxy-dev.sh','scripts/context/verify-repomix-context.sh']:
    text=Path(rel).read_text()
    hits=[needle for needle in needles if needle in text]
    assert not hits, f'{rel}: {hits}'
    assert '->' in text or rel != 'scripts/context/verify-repomix-context.sh'
print('  [OK] no package install, Cursor kill, or false Headroom tokens in scripts')
PY
bash -n scripts/context/headroom-check.sh
bash -n scripts/headroom-proxy-dev.sh
bash -n scripts/context/verify-repomix-context.sh
printf '  [OK] shell syntax checks pass
'
python3 - <<'PY'
import subprocess
allowed={'scripts/context/headroom-check.sh','scripts/headroom-proxy-dev.sh','scripts/context/verify-repomix-context.sh','docs/spiritos-full-repo-cleanup-20260621/cleanup-state.json'}
allowed_prefixes={'docs/spiritos-full-repo-cleanup-20260621/F08/'}
result=subprocess.run(['git','diff','--name-only','HEAD'], check=True, capture_output=True, text=True)
untracked=subprocess.run(['git','ls-files','--others','--exclude-standard'], check=True, capture_output=True, text=True)
paths=sorted({line.strip() for blob in (result.stdout, untracked.stdout) for line in blob.splitlines() if line.strip()})
bad=[p for p in paths if p not in allowed and not any(p.startswith(prefix) for prefix in allowed_prefixes)]
assert not bad, f'non-F8 paths changed: {bad}'
print('  [OK] changed paths are F8-scoped')
PY
git diff --check
printf '  [OK] git diff --check
'
echo "F08 operator check: PASS"
