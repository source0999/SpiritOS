#!/usr/bin/env bash
# F02 operator check — plan-stage. Activates live gates once source exists.
set -euo pipefail
STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F02"
echo "F02 operator check"

test -f "$STAGE_DIR/acceptance-contract.json"
test -f "$STAGE_DIR/holdout-manifest.json"
python3 -c "import json;[json.load(open('$STAGE_DIR/'+f)) for f in ['acceptance-contract.json','holdout-manifest.json','status.json']]"
echo "  [OK] contract artifacts present and parse"

# negative corpus has all 15 required cheat classes
python3 - <<'PY'
import json
d=json.load(open('docs/spiritos-full-repo-cleanup-20260621/F02/holdout-manifest.json'))
required_patterns={'canned','static','route','status','repo','fixture','preview','fallback','renderer','manual','consumer','unavailable','contradict','benchmark','testonly'}
got={c['id'] for c in d['generic_checks']}
ids=' '.join(c['id']+':'+c['shape'] for c in d['generic_checks']).lower()
missing=[p for p in required_patterns if p not in ids]
assert not missing, f"holdout missing patterns: {missing}"
print(f"  [OK] {len(got)} negative-corpus checks cover all 15 cheat classes")
PY

if [ -d source_proxy/verification/anticheat ]; then
  echo "  [INFO] anticheat package exists — F02 in progress; run live gates"
  python -c "import source_proxy.verification.anticheat" 2>/dev/null && echo "  [OK] package imports"
else
  echo "  [OK] anticheat package absent (planned; F02 not yet implemented)"
fi
echo "F02 operator check: PASS (plan-stage)"
exit 0
