#!/usr/bin/env bash
set -euo pipefail
STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F07"
echo "F07 operator check"
python3 - <<'PY'
import hashlib, json
from pathlib import Path
stage=Path('docs/spiritos-full-repo-cleanup-20260621/F07')
status=json.loads((stage/'status.json').read_text())
for name in ['acceptance-contract.json','holdout-manifest.json','status.json']:
    json.loads((stage/name).read_text())
assert status.get('acceptance_contract_sha256') == hashlib.sha256((stage/'acceptance-contract.json').read_bytes()).hexdigest()
assert status.get('holdout_manifest_sha256') == hashlib.sha256((stage/'holdout-manifest.json').read_bytes()).hexdigest()
page=Path('src/app/coding/page.tsx').read_text()
registry=Path('src/lib/coding/shell-registry.ts').read_text()
test=Path('src/lib/coding/__tests__/shell-registry.test.ts').read_text()
assert 'CodingCockpitShell' in page and 'activeCodingShell' in page
assert 'data-coding-shell-id={activeCodingShell.id}' in page
assert 'coding-cockpit-shell' in registry and 'status: "active"' in registry and 'route: "/coding"' in registry
assert 'coding-command-center-shell' in registry and 'status: "experimental"' in registry
assert 'do not delete' in registry.lower() or 'do not delete' in test.lower()
print('  [OK] /coding active shell and alternate-shell registry are statically verified')
PY
python3 - <<'PY'
import subprocess
allowed={'src/app/coding/page.tsx','src/lib/coding/shell-registry.ts','src/lib/coding/__tests__/shell-registry.test.ts','docs/spiritos-full-repo-cleanup-20260621/cleanup-state.json'}
allowed_prefixes={'docs/spiritos-full-repo-cleanup-20260621/F07/'}
result=subprocess.run(['git','diff','--name-only','HEAD'], check=True, capture_output=True, text=True)
untracked=subprocess.run(['git','ls-files','--others','--exclude-standard'], check=True, capture_output=True, text=True)
paths=sorted({line.strip() for blob in (result.stdout, untracked.stdout) for line in blob.splitlines() if line.strip()})
bad=[p for p in paths if p not in allowed and not any(p.startswith(prefix) for prefix in allowed_prefixes)]
assert not bad, f'non-F7 paths changed: {bad}'
print('  [OK] changed paths are F7-scoped')
PY
git diff --check
printf '  [OK] git diff --check
'
echo "F07 operator check: PASS"
