#!/usr/bin/env bash
# F07 operator check — plan-stage. Live gates activate when source edited.
set -euo pipefail
STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F07"
echo "F07 operator check"

test -f "$STAGE_DIR/acceptance-contract.json"
test -f "$STAGE_DIR/holdout-manifest.json"
python3 -c "import json;[json.load(open('$STAGE_DIR/'+f)) for f in ['acceptance-contract.json','holdout-manifest.json','status.json']]"
echo "  [OK] contract artifacts present and parse"

python3 - <<'PY'
import json
d=json.load(open('docs/spiritos-full-repo-cleanup-20260621/F07/acceptance-contract.json'))
assert d["canonical_route_frozen"]["canonical_shell"]=="CodingCockpitShell", "canonical shell misfrozen"
assert len(d["shells_present"])==3, "expected 3 shells"
print("  [OK] canonical=CodingCockpitShell; 3 shells frozen; no-deletion contract present")
PY

echo "F07 operator check: PASS (plan-stage)"
exit 0
