#!/usr/bin/env bash
set -euo pipefail
cd /home/source/SpiritOS

ROOT="docs/source-proxy-human-brain-full-live-integration-pivot-20260619"
PLAN_DIR="$ROOT/plan-03"
ART="$PLAN_DIR/artifacts"
RAW="/home/source/spiritos-evidence/plan-03/plan3-disposable-proof.json"

echo "Plan 3/6 operator check"

set +e
bash "$ROOT/plan-02/operator-check.sh" >/tmp/plan3-plan2-operator.out 2>&1
PLAN2_STATUS=$?
set -e
if [ "$PLAN2_STATUS" -ne 0 ]; then
  if grep -q "FAIL Plan 3 artifacts are present" /tmp/plan3-plan2-operator.out \
    && grep -q "json ok" /tmp/plan3-plan2-operator.out; then
    echo "Plan 2 carryforward PASS except expected historical Plan 3 artifact guard"
  else
    cat /tmp/plan3-plan2-operator.out
    echo "FAIL Plan 2 operator check did not pass"
    exit 1
  fi
else
  grep -q "PASS Plan 2/6 operator check" /tmp/plan3-plan2-operator.out || {
    cat /tmp/plan3-plan2-operator.out
    echo "FAIL Plan 2 operator check did not report PASS"
    exit 1
  }
fi

for f in \
  "$PLAN_DIR/status.md" \
  "$PLAN_DIR/status.json" \
  "$PLAN_DIR/plan-closeout.md" \
  "$PLAN_DIR/plan-closeout.json" \
  "$ART/2-durable-state-machine.md" \
  "$ART/3-policy-gates.md" \
  "$ART/4-retry-timeout-failure.md" \
  "$ART/5-recovery-proof.md" \
  "$ART/6-verifier-driven-repair-loop.md" \
  "$ART/8-task-a-policy-proof.md" \
  "$ART/8-task-b-recovery-proof.md" \
  "$ART/8-task-c-repair-proof.md" \
  "$ART/plan3-proof-summary.json" \
  "$RAW"; do
  test -f "$f" || { echo "FAIL missing $f"; exit 1; }
done

python3 -m json.tool "$PLAN_DIR/status.json" >/dev/null
python3 -m json.tool "$PLAN_DIR/plan-closeout.json" >/dev/null
python3 -m json.tool "$ART/plan3-proof-summary.json" >/dev/null
python3 -m json.tool "$RAW" >/dev/null

python3 - <<'PY'
import json
from pathlib import Path

closeout = json.loads(Path("docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/plan-closeout.json").read_text())
summary = json.loads(Path("docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/artifacts/plan3-proof-summary.json").read_text())
raw = json.loads(Path("/home/source/spiritos-evidence/plan-03/plan3-disposable-proof.json").read_text())

required_closeout = {
    "verdict": "GO",
    "plan_2_carryforward": "PASS",
    "durable_state": "INTEGRATED_LIVE",
    "policy_gates": "INTEGRATED_LIVE",
    "retry_timeout_failure": "INTEGRATED_LIVE",
    "recovery": "INTEGRATED_LIVE",
    "repair_loop": "INTEGRATED_LIVE",
    "task_a_policy": "PASS",
    "task_b_recovery": "PASS",
    "task_c_repair": "PASS",
    "operator_check": "PASS",
    "focused_tests": "PASS",
}
for key, expected in required_closeout.items():
    actual = closeout.get(key)
    if actual != expected:
        raise SystemExit(f"FAIL closeout {key}={actual!r}, expected {expected!r}")

fake_flags = [
    "preview_go_detected",
    "advisory_go_detected",
    "status_only_go_detected",
    "repair_suggestion_only_go_detected",
    "recovery_not_tested_go_detected",
    "policy_doc_only_go_detected",
    "unconsumed_output_go_detected",
    "plan_4_started",
]
for key in fake_flags:
    if closeout.get(key) is not False:
        raise SystemExit(f"FAIL fake-go flag {key} is not false")

if raw.get("production_mutation") is not False:
    raise SystemExit("FAIL raw proof reports production mutation")
if raw.get("repair_file_final") != "<main>fixed</main>\n":
    raise SystemExit("FAIL repair proof was not actually applied")

expect = {
    "policy_task": "policy_blocked",
    "recovery_task": "worker_dispatched",
    "retry_task": "failed_needs_human",
    "repair_task": "verified",
}
for key, expected_status in expect.items():
    state = raw[key]
    if state.get("current_status") != expected_status:
        raise SystemExit(f"FAIL {key} status {state.get('current_status')!r}")
    traces = {event.get("trace_id") for event in state.get("causal_events_json", [])}
    if state.get("trace_id") not in traces:
        raise SystemExit(f"FAIL {key} trace_id is not present in causal events")

event_sets = {key: {event.get("event_type") for event in raw[key].get("causal_events_json", [])} for key in expect}
if "policy" not in event_sets["policy_task"]:
    raise SystemExit("FAIL policy proof has no policy event")
if "recovery" not in event_sets["recovery_task"]:
    raise SystemExit("FAIL recovery proof has no recovery event")
if not ({"retry", "failure"} <= event_sets["retry_task"]):
    raise SystemExit("FAIL retry proof lacks retry/failure events")
if not ({"repair", "verification"} <= event_sets["repair_task"]):
    raise SystemExit("FAIL repair proof lacks repair/verification events")

if summary.get("raw_evidence") != "/home/source/spiritos-evidence/plan-03/plan3-disposable-proof.json":
    raise SystemExit("FAIL summary raw evidence path mismatch")
PY

if find "$PLAN_DIR/../plan-04" -path "*/artifacts/*" -print | grep .; then
  echo "FAIL Plan 4 artifacts exist"
  exit 1
fi

if grep -R -E '"(preview_go_detected|advisory_go_detected|status_only_go_detected|repair_suggestion_only_go_detected|recovery_not_tested_go_detected|policy_doc_only_go_detected|unconsumed_output_go_detected|plan_4_started)"[[:space:]]*:[[:space:]]*true' "$PLAN_DIR" >/dev/null 2>&1; then
  echo "FAIL forbidden fake-GO true flag found in Plan 3 closeout"
  exit 1
fi

echo "PASS Plan 3/6 operator check"
