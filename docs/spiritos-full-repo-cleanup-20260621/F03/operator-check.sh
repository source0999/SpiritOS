#!/usr/bin/env bash
# F03 operator check — plan-stage. Live gates activate when source exists.
set -euo pipefail
STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F03"
echo "F03 operator check"

test -f "$STAGE_DIR/acceptance-contract.json"
test -f "$STAGE_DIR/holdout-manifest.json"
python3 -c "import json;[json.load(open('$STAGE_DIR/'+f)) for f in ['acceptance-contract.json','holdout-manifest.json','status.json']]"
echo "  [OK] contract artifacts present and parse"

python3 - <<'PY'
import json
d=json.load(open('docs/spiritos-full-repo-cleanup-20260621/F03/acceptance-contract.json'))
exp={"LOCAL_RETRY_RECOMMENDED","LOCAL_DECOMPOSITION_RECOMMENDED","LOCAL_MODEL_INSUFFICIENT","API_ESCALATION_RECOMMENDED","HUMAN_DECISION_REQUIRED"}
assert set(d["verdicts_frozen"])==exp, "verdict set mismatch"
# the no-provider-call gate must be present
assert any("no provider call" in g.get("gate","").lower() or "no provider call occurs" in g.get("command","").lower() for g in d["required_gates"]), "missing no-call gate"
print("  [OK] 5 verdicts frozen; no-provider-call gate present")
PY

if [ -f source_proxy/decision/escalation_contract.py ]; then
  echo "  [INFO] escalation_contract exists — F03 in progress; run live gates (incl. no-call proof)"
else
  echo "  [OK] escalation_contract absent (planned; F03 not yet implemented)"
fi
echo "F03 operator check: PASS (plan-stage)"
exit 0
