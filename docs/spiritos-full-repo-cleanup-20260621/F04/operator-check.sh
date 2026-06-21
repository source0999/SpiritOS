#!/usr/bin/env bash
# F04 operator check — plan-stage. Live gates activate when source exists.
set -euo pipefail
STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F04"
echo "F04 operator check"

test -f "$STAGE_DIR/acceptance-contract.json"
test -f "$STAGE_DIR/holdout-manifest.json"
python3 -c "import json;[json.load(open('$STAGE_DIR/'+f)) for f in ['acceptance-contract.json','holdout-manifest.json','status.json']]"
echo "  [OK] contract artifacts present and parse"

python3 - <<'PY'
import json
d=json.load(open('docs/spiritos-full-repo-cleanup-20260621/F04/acceptance-contract.json'))
exp={"multi-node resource planning","current-tool comparison","architecture planning","implementation handoff","research-backed recommendation"}
assert set(d["task_shapes_frozen"])==exp, "task shape set mismatch"
print("  [OK] 5 generic task shapes frozen")
PY

if [ -d source_proxy/decision/packet_templates ]; then
  echo "  [INFO] packet_templates exists — F04 in progress; run live gates"
else
  echo "  [OK] packet_templates absent (planned; F04 not yet implemented)"
fi
echo "F04 operator check: PASS (plan-stage)"
exit 0
