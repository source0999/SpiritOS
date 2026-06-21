#!/usr/bin/env bash
# F09 operator check — plan-stage. Live gates activate when source edited.
set -euo pipefail
STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F09"
echo "F09 operator check"

test -f "$STAGE_DIR/acceptance-contract.json"
test -f "$STAGE_DIR/holdout-manifest.json"
python3 -c "import json;[json.load(open('$STAGE_DIR/'+f)) for f in ['acceptance-contract.json','holdout-manifest.json','status.json']]"
echo "  [OK] contract artifacts present and parse"

python3 - <<'PY'
import json
d=json.load(open('docs/spiritos-full-repo-cleanup-20260621/F09/acceptance-contract.json"))
req={"typed_request_result","timeout","attempt_count","failure_classification_F1","evidence_reference","redacted_logs","ownership_metadata"}
assert set(d["adapter_contract_fields"])==req, f"adapter contract fields mismatch: missing={req-set(d['adapter_contract_fields'])}"
print("  [OK] 7-field adapter contract frozen")
PY

echo "F09 operator check: PASS (plan-stage)"
exit 0
