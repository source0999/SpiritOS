#!/usr/bin/env bash
set -euo pipefail

cd /home/source/SpiritOS

echo "Plan 2/6 operator check"

ROOT="docs/source-proxy-human-brain-full-live-integration-pivot-20260619"
PLAN_DIR="$ROOT/plan-02"
ARTIFACTS="$PLAN_DIR/artifacts"
CONTINUATION="$PLAN_DIR/continuation-hardline"

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
  "$ARTIFACTS/2.5.1-evidence-budget.md" \
  "$CONTINUATION/0-preflight.md" \
  "$CONTINUATION/1-hardline-classifier.md" \
  "$CONTINUATION/2.3-mac-live-write-proof.md" \
  "$CONTINUATION/3.1-searxng-provider-truth.md" \
  "$CONTINUATION/4.3-specialist-live-proof.md" \
  "$CONTINUATION/5-coding-shell-surface-proof.md" \
  "$CONTINUATION/7-test-results.md" \
  "$CONTINUATION/9-final-hardline-verdict.md"; do
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
for key in ["hardline_summary", "mac", "research", "specialists", "acceptance_tasks", "coding_shell", "safety"]:
    if key not in closeout:
        raise SystemExit(f"missing closeout key: {key}")
for family in ["mac", "research", "specialists"]:
    text = json.dumps(closeout.get(family, {}))
    if "trace_id" not in text or "consumer" not in text:
        raise SystemExit(f"missing causal trace/consumer proof in {family}")
if closeout["research"].get("status") != "INTEGRATED_LIVE":
    raise SystemExit("current research is not live-integrated")
if closeout["research"].get("local_fallback_used") is not False:
    raise SystemExit("current research fallback boundary missing")
if closeout["mac"].get("status") == "INTEGRATED_LIVE" and closeout["mac"].get("mac_write_performed") is not True:
    raise SystemExit("Mac GO claimed without real write proof")
if closeout["specialists"].get("status") == "INTEGRATED_LIVE":
    if closeout["specialists"].get("gemma") in {"failed", "blocked", "timeout", "error"}:
        raise SystemExit("specialist GO claimed with failed Gemma lane")
    if closeout["specialists"].get("hermes") in {"failed", "blocked", "timeout", "error"}:
        raise SystemExit("specialist GO claimed with failed Hermes lane")
if closeout.get("verdict") == "GO":
    required = [
        closeout["mac"].get("status"),
        closeout["research"].get("status"),
        closeout["specialists"].get("status"),
    ]
    if required != ["INTEGRATED_LIVE", "INTEGRATED_LIVE", "INTEGRATED_LIVE"]:
        raise SystemExit("Plan 2 GO claimed without all required live integrations")
    if closeout["hardline_summary"].get("go_allowed") is not True:
        raise SystemExit("Plan 2 GO claimed while hardline go_allowed is false")
else:
    if closeout["hardline_summary"].get("go_allowed") is not False:
        raise SystemExit("non-GO verdict must keep hardline go_allowed false")
print("json ok")
PY

PLAN1_OUTPUT="$(mktemp)"
trap 'rm -f "$PLAN1_OUTPUT"' EXIT
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
grep -R -n "finish_subsystem_integration_result" source_proxy/tasks/long_running.py >/dev/null
grep -R -n "CURRENT_RESEARCH_HANDLER_VERSION" source_proxy/decision/current_research.py >/dev/null
grep -R -n "SPECIALIST_INTEGRATION_VERSION" source_proxy/decision/specialist_integration.py >/dev/null
grep -R -n "MODEL_LANE_FAILURE_STATUSES" source_proxy/decision/specialist_integration.py >/dev/null
grep -R -n "HARDLINE_STATUS_VERSION" source_proxy/decision/hardline_integration.py >/dev/null
grep -R -n "mac_isolated_write_proof" source_proxy/decision/mac_integration.py >/dev/null
grep -R -n "requires_human_first_write" src/lib/mac-worker >/dev/null
grep -R -n "Plan 2 subsystem truth" src/components/coding/CodingCockpitShell.tsx >/dev/null

if find "$ROOT/plan-03" -path "*/artifacts/*" -print 2>/dev/null | grep -q .; then
  echo "FAIL Plan 3 artifacts are present"
  exit 1
fi

git status --branch --short --untracked-files=normal
echo "PASS Plan 2/6 operator check"
