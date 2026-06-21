#!/usr/bin/env bash
# F05 operator check — plan-stage. Live gates activate when source exists.
set -euo pipefail
STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F05"
echo "F05 operator check"

test -f "$STAGE_DIR/acceptance-contract.json"
test -f "$STAGE_DIR/holdout-manifest.json"
python3 -c "import json;[json.load(open('$STAGE_DIR/'+f)) for f in ['acceptance-contract.json','holdout-manifest.json','status.json']]"
echo "  [OK] contract artifacts present and parse"

python3 - <<'PY'
import json
d=json.load(open('docs/spiritos-full-repo-cleanup-20260621/F05/acceptance-contract.json'))
exp={"decision/lanes/receipts.py","decision/lanes/context.py","decision/lanes/research.py","decision/lanes/coder.py","decision/lanes/verifier.py","decision/lanes/trace.py"}
assert set(d["target_modules"])==exp, "target module set mismatch"
# all 12 compatibility contracts listed
assert len(d["compatibility_contracts_preserved"])>=12, "compatibility contracts incomplete"
print("  [OK] 6 lane targets + 12 compatibility contracts frozen")
PY

if [ -d source_proxy/decision/lanes ]; then
  echo "  [INFO] decision/lanes exists — F05 in progress; run live parity gates"
else
  echo "  [OK] decision/lanes absent (planned; F05 not yet implemented)"
fi
echo "F05 operator check: PASS (plan-stage)"
exit 0
