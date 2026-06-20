#!/usr/bin/env bash
set -euo pipefail

cd /home/source/SpiritOS

echo "Plan 2/6 operator check"

ROOT="docs/source-proxy-human-brain-full-live-integration-pivot-20260619"
PLAN_DIR="$ROOT/plan-02"
ARTIFACTS="$PLAN_DIR/artifacts"

for file in \
  "$PLAN_DIR/plan.md" \
  "$PLAN_DIR/status.md" \
  "$PLAN_DIR/status.json" \
  "$PLAN_DIR/gate-manifest.template.json" \
  "$PLAN_DIR/operator-check.sh" \
  "$PLAN_DIR/plan-closeout.md" \
  "$PLAN_DIR/plan-closeout.json" \
  "$ARTIFACTS/2.0-preflight.md" \
  "$ARTIFACTS/2.0-plan1-carryforward-check.md" \
  "$ARTIFACTS/2.1.1-mac-worker-inventory.md" \
  "$ARTIFACTS/phase-2.1-closeout.md" \
  "$ARTIFACTS/2.2.1-research-inventory.md" \
  "$ARTIFACTS/phase-2.2-closeout.md" \
  "$ARTIFACTS/2.3.1-specialist-inventory.md" \
  "$ARTIFACTS/phase-2.3-closeout.md" \
  "$ARTIFACTS/2.4-task-a-proof.md" \
  "$ARTIFACTS/2.4-task-b-proof.md" \
  "$ARTIFACTS/2.4-task-c-proof.md" \
  "$ARTIFACTS/phase-2.4-closeout.md" \
  "$ARTIFACTS/2.5.1-evidence-budget.md"; do
  test -f "$file" || { echo "FAIL missing $file"; exit 1; }
done

python3 -m json.tool "$PLAN_DIR/status.json" >/dev/null
python3 -m json.tool "$PLAN_DIR/gate-manifest.template.json" >/dev/null
python3 -m json.tool "$PLAN_DIR/plan-closeout.json" >/dev/null

python3 - <<'PY'
import json
from pathlib import Path

closeout = json.loads(Path("docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-02/plan-closeout.json").read_text())
if closeout.get("verdict") not in {"GO", "NEEDS_FIX", "BLOCKED_HUMAN", "BLOCKED_ENV"}:
    raise SystemExit("invalid Plan 2 verdict")
for key in ["mac", "research", "specialists", "acceptance_tasks", "safety"]:
    if key not in closeout:
        raise SystemExit(f"missing closeout key: {key}")
for family in ["mac", "research", "specialists"]:
    text = json.dumps(closeout.get(family, {}))
    if "trace_id" not in text or "consumer" not in text:
        raise SystemExit(f"missing causal trace/consumer proof in {family}")
print("json ok")
PY

PLAN1_OUTPUT="$(mktemp)"
set +e
bash "$ROOT/plan-01/operator-check.sh" >"$PLAN1_OUTPUT" 2>&1
PLAN1_STATUS=$?
set -e
if [ "$PLAN1_STATUS" -ne 0 ]; then
  if ! grep -q "FAIL Plan 2 artifacts are present" "$PLAN1_OUTPUT"; then
    cat "$PLAN1_OUTPUT"
    echo "FAIL Plan 1 carryforward check regressed"
    exit 1
  fi
  echo "Plan 1 carryforward PASS except expected historical Plan 2 artifact guard"
else
  echo "Plan 1 operator check PASS"
fi

grep -R -n "record_subsystem_integration_result" source_proxy/tasks/long_running.py >/dev/null
grep -R -n "CURRENT_RESEARCH_HANDLER_VERSION" source_proxy/decision/current_research.py >/dev/null
grep -R -n "SPECIALIST_INTEGRATION_VERSION" source_proxy/decision/specialist_integration.py >/dev/null
grep -R -n "requires_human_first_write" src/lib/mac-worker >/dev/null

if find "$ROOT/plan-03" -path "*/artifacts/*" -print 2>/dev/null | grep -q .; then
  echo "FAIL Plan 3 artifacts are present"
  exit 1
fi

git status --branch --short --untracked-files=normal
echo "PASS Plan 2/6 operator check"
