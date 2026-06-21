#!/usr/bin/env bash
# F08 operator check — plan-stage. Live gates activate when source edited.
set -euo pipefail
STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F08"
echo "F08 operator check"

test -f "$STAGE_DIR/acceptance-contract.json"
test -f "$STAGE_DIR/holdout-manifest.json"
python3 -c "import json;[json.load(open('$STAGE_DIR/'+f)) for f in ['acceptance-contract.json','holdout-manifest.json','status.json']]"
echo "  [OK] contract artifacts present and parse"

python3 - <<'PY'
import json
d=json.load(open('docs/spiritos-full-repo-cleanup-20260621/F08/acceptance-contract.json'))
req={"health_success","compressed=true","tokens_saved>0"}
assert set(d["headroom_active_requires_all_three"])==req, "Headroom-active proofs misfrozen"
print("  [OK] Headroom-active requires all 3 proofs (health+compressed+tokens)")
PY

echo "F08 operator check: PASS (plan-stage)"
exit 0
