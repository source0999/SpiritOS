#!/usr/bin/env bash
set -euo pipefail
cd /home/source/SpiritOS

ROOT="docs/source-proxy-human-brain-full-live-integration-pivot-20260619"
PLAN_DIR="$ROOT/plan-03"
ART="$PLAN_DIR/artifacts"
RAW="/home/source/spiritos-evidence/plan-03-3x10-dryrun/stage-2/plan3-stage2-disposable-proof.json"

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
    "verdict": "PLAN_3_STAGE_2_NEEDS_FIX_PATCH_COMPLETE_PENDING_HUMAN_REVIEW",
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

if closeout.get("stage_2_completed") is not True:
    raise SystemExit("FAIL Stage 2 completion not recorded")
if closeout.get("stage_3_started") is not False:
    raise SystemExit("FAIL Stage 3 start must be false")
if closeout.get("battery_3x10_run") is not False:
    raise SystemExit("FAIL 3x10 battery must not be run")

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

def event_types(state):
    return {event.get("event_type") for event in state.get("causal_events_json", [])}

def require_consumer(state, label):
    latest = state.get("latest_consumer_event_id")
    consumer = state.get("consumer_event_id")
    if not latest:
        raise SystemExit(f"FAIL {label} proof missing latest_consumer_event_id")
    if not consumer:
        raise SystemExit(f"FAIL {label} proof missing consumer_event_id")
    if latest != consumer:
        raise SystemExit(f"FAIL {label} consumer_event_id does not match latest_consumer_event_id")
    if not state.get("consumer_subsystem"):
        raise SystemExit(f"FAIL {label} proof missing consumer_subsystem")
    match = None
    for event in state.get("causal_events_json", []):
        if event.get("event_id") == latest and event.get("event_type") == "consumer":
            match = event
            break
    if match is None:
        raise SystemExit(f"FAIL {label} consumer event missing")
    if match.get("trace_id") != state.get("trace_id"):
        raise SystemExit(f"FAIL {label} consumer event not in same trace")

policy = raw["policy_task"]
policy_events = event_types(policy)
if "policy" not in policy_events:
    raise SystemExit("FAIL policy proof has no policy event")
if policy.get("policy_decision") not in {"policy_blocked", "blocked_human"}:
    raise SystemExit("FAIL policy proof missing blocked policy decision")
if policy.get("mutation_prevented") is not True:
    raise SystemExit("FAIL policy proof missing mutation_prevented=true")
if not policy.get("blocked_action"):
    raise SystemExit("FAIL policy proof missing blocked action")
require_consumer(policy, "policy")

recovery = raw["recovery_task"]
recovery_events = event_types(recovery)
if "recovery" not in recovery_events:
    raise SystemExit("FAIL recovery proof has no recovery event")
if recovery.get("duplicate_action_prevented") is not True:
    raise SystemExit("FAIL recovery duplicate action prevention missing")
require_consumer(recovery, "recovery")

retry_events = event_types(raw["retry_task"])
if not ({"retry", "failure"} <= retry_events):
    raise SystemExit("FAIL retry proof lacks retry/failure events")

repair = raw["repair_task"]
repair_events = event_types(repair)
if "failure" not in repair_events:
    raise SystemExit("FAIL repair proof missing explicit verifier failure event")
if "repair" not in repair_events:
    raise SystemExit("FAIL repair proof missing repair event")
if "verification" not in repair_events:
    raise SystemExit("FAIL repair proof missing reverify event")
if not repair.get("latest_repair_failure_event_id"):
    raise SystemExit("FAIL repair proof missing latest_repair_failure_event_id")
if not repair.get("latest_repair_event_id"):
    raise SystemExit("FAIL repair proof missing latest_repair_event_id")
if not repair.get("latest_reverify_event_id"):
    raise SystemExit("FAIL repair proof missing latest_reverify_event_id")
repair_attempt_count = int(repair.get("repair_attempt_count") or 0)
max_repair_attempts = int(repair.get("max_repair_attempts") or 0)
if repair_attempt_count < 1:
    raise SystemExit("FAIL repair attempt count missing")
if max_repair_attempts < 1 or repair_attempt_count > max_repair_attempts:
    raise SystemExit("FAIL repair attempt count missing or unbounded")
if repair.get("current_status") not in {"verified", "failed_needs_human"}:
    raise SystemExit("FAIL repair final result missing")
require_consumer(repair, "repair")

if summary.get("raw_evidence") != "/home/source/spiritos-evidence/plan-03-3x10-dryrun/stage-2/plan3-stage2-disposable-proof.json":
    raise SystemExit("FAIL summary raw evidence path mismatch")
PY

if find "$PLAN_DIR/../plan-04" -path "*/artifacts/*" -print | grep .; then
  echo "FAIL Plan 4 artifacts exist"
  exit 1
fi

if grep -E '"(preview_go_detected|advisory_go_detected|status_only_go_detected|repair_suggestion_only_go_detected|recovery_not_tested_go_detected|policy_doc_only_go_detected|unconsumed_output_go_detected|plan_4_started)"[[:space:]]*:[[:space:]]*true' \
  "$PLAN_DIR/status.json" \
  "$PLAN_DIR/plan-closeout.json" \
  "$ART/plan3-proof-summary.json" >/dev/null 2>&1; then
  echo "FAIL forbidden fake-GO true flag found in current Plan 3 closeout"
  exit 1
fi

echo "PASS Plan 3/6 operator check"
