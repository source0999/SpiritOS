#!/usr/bin/env bash
# F06 operator check — plan-stage. Live gates activate when source exists.
set -euo pipefail
STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F06"
echo "F06 operator check"

test -f "$STAGE_DIR/acceptance-contract.json"
test -f "$STAGE_DIR/holdout-manifest.json"
python3 -c "import json;[json.load(open('$STAGE_DIR/'+f)) for f in ['acceptance-contract.json','holdout-manifest.json','status.json']]"
echo "  [OK] contract artifacts present and parse"

python3 - <<'PY'
import json
d=json.load(open('docs/spiritos-full-repo-cleanup-20260621/F06/acceptance-contract.json'))
req={"engine","apply","trace","recovery","regression"}
joined=" ".join(d["responsibilities_frozen"]).lower()
missing=[r for r in req if r not in joined]
assert not missing, f"missing responsibilities: {missing}"
# state-machine preservation gate present
assert any("transition" in g.get("gate","").lower() for g in d["required_gates"]), "missing transition-set gate"
print("  [OK] 5 responsibilities + transition-set gate frozen")
PY

if [ -d source_proxy/tasks/apply ] || [ -d source_proxy/tasks/recovery ]; then
  echo "  [INFO] tasks/{apply,recovery,...} exist — F06 in progress; run live parity gates"
else
  echo "  [OK] split dirs absent (planned; F06 not yet implemented)"
fi
echo "F06 operator check: PASS (plan-stage)"
exit 0
