#!/usr/bin/env bash
# F01 operator check — runnable, deterministic pass/fail.
# Run from the cleanup worktree root. Exit 0 = pass.
# NOTE: this script is a plan-stage stub; the REAL assertions are activated
# when F01 source exists. It validates the frozen contract artifacts parse and
# that the planned target files are absent (so we know implementation hasn't
# started). Once F01 is implemented, replace the "planned-absent" checks with
# the live gates from acceptance-contract.json.

set -euo pipefail

STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F01"

echo "F01 operator check"

# 1. Frozen contract artifacts exist and parse
test -f "$STAGE_DIR/acceptance-contract.json"
test -f "$STAGE_DIR/holdout-manifest.json"
python3 -c "import json,json,sys; [json.load(open('$STAGE_DIR/'+f)) for f in ['acceptance-contract.json','holdout-manifest.json','status.json']]"
echo "  [OK] contract artifacts present and parse"

# 2. 19 classes are exactly the frozen set in the contract
python3 - <<'PY'
import json
d=json.load(open('docs/spiritos-full-repo-cleanup-20260621/F01/acceptance-contract.json'))
expected={"TECHNICAL_FAILURE","ENVIRONMENT_FAILURE","SERVICE_UNAVAILABLE","BRIDGE_INTEGRATION_FAILURE","ROUTING_FAILURE","TOOL_FAILURE","SEARCH_PROVIDER_EMPTY","SEARCH_PROVIDER_FAILURE","MODEL_CAPABILITY_LIMIT","MODEL_FORMATTING_FAILURE","LOCAL_MODEL_INSUFFICIENT","API_ESCALATION_RECOMMENDED","POLICY_BLOCKED","HUMAN_APPROVAL_REQUIRED","EVIDENCE_MISSING","VALIDATOR_FAILURE","PROMPT_AMBIGUITY","RESOURCE_PRESSURE","UNKNOWN_NEEDS_INVESTIGATION"}
got=set(d["failure_classes_frozen"])
assert got==expected, f"failure class set mismatch: missing={expected-got} extra={got-expected}"
assert len(got)==19
print("  [OK] 19 failure classes frozen exactly")
PY

# 3. Planned-target-absence checks (pre-implementation)
#    status_codes.py must not exist yet (created in F01). If it exists, F01
#    already started — then this check is replaced by live gates at exec time.
if [ -f source_proxy/diagnostics/status_codes.py ]; then
  echo "  [INFO] status_codes.py exists — F01 implementation in progress; run live gates instead"
  # Live gate: every class constructible
  python -m pytest -q source_proxy/tests/test_status_codes.py
else
  echo "  [OK] status_codes.py absent (planned; F01 not yet implemented)"
fi

# 4. Anti-cheat: no benchmark-ID branch in plan artifacts themselves
if grep -rE '\bA[1259]\b|Set A|4R[0-9]' "$STAGE_DIR/acceptance-contract.json" "$STAGE_DIR/holdout-manifest.json" 2>/dev/null | grep -vi 'regression\|historical\|A2/A5/A9' ; then
  echo "  [WARN] possible benchmark token in contract (review context)"
fi

echo "F01 operator check: PASS (plan-stage)"
exit 0
