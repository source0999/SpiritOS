#!/usr/bin/env bash
set -euo pipefail
cd /home/source/SpiritOS
echo "Plan 6/6 - Reliability and Daily-Driver Promotion"
ROOT="docs/source-proxy-human-brain-full-live-integration-pivot-20260619"
PLAN_DIR="$ROOT/plan-06"
for f in plan.md status.md status.json gate-manifest.template.json operator-check.sh next-plan-handoff.md new-chat-start.md; do
  test -f "$PLAN_DIR/$f" || { echo "FAIL missing $PLAN_DIR/$f"; exit 1; }
done
python3 -m json.tool "$PLAN_DIR/status.json" >/dev/null
python3 -m json.tool "$PLAN_DIR/gate-manifest.template.json" >/dev/null
python3 -m json.tool "$PLAN_DIR/plan6-live-fail-closed-reliability-proof-20260626.json" >/dev/null
python3 -m json.tool "$PLAN_DIR/plan6-mac-dell-dispatch-proof-20260626.json" >/dev/null
python3 -m json.tool "$PLAN_DIR/plan6-supervised-daily-driver-trial-proof-20260626.json" >/dev/null
test -f "$PLAN_DIR/phase-6-5-supervised-daily-driver-trial-20260626.md"
test -f "$PLAN_DIR/plan6-daily-driver-promotion-decision-20260626.md"
python3 -m json.tool "$ROOT/status.json" >/dev/null

# Plan 6 partial-candidate addendum checks
test -f "$PLAN_DIR/plan6-partial-candidate-targeted-fixes-addendum-20260627.md"
test -f "$PLAN_DIR/plan6-additional-productive-soak-decision-20260627.md"
python3 -m json.tool "$PLAN_DIR/plan6-addendum-approval-records-20260627.json" >/dev/null
python3 -m json.tool "$PLAN_DIR/plan6-additional-productive-soak-proof-20260627.json" >/dev/null
python3 -m json.tool "$PLAN_DIR/plan6-conditional-hardening-operator-approval-20260627.json" >/dev/null
python3 -m json.tool "$PLAN_DIR/plan6-conditional-hardening-verifier-20260627.json" >/dev/null
test -f "$PLAN_DIR/plan6-conditional-candidate-hardening-closeout-20260627.md"
python3 - "$PLAN_DIR" <<'PY'
import json
import sys
from pathlib import Path

plan_dir = Path(sys.argv[1])
status = json.loads((plan_dir / "status.json").read_text(encoding="utf-8"))
approval = json.loads((plan_dir / "plan6-addendum-approval-records-20260627.json").read_text(encoding="utf-8"))
proof = json.loads((plan_dir / "plan6-additional-productive-soak-proof-20260627.json").read_text(encoding="utf-8"))
manifest = json.loads((plan_dir / "plan6-conditional-hardening-operator-approval-20260627.json").read_text(encoding="utf-8"))
verifier = json.loads((plan_dir / "plan6-conditional-hardening-verifier-20260627.json").read_text(encoding="utf-8"))

def expect(condition, message):
    if not condition:
        raise SystemExit(f"FAIL {message}")

expect(status.get("status") == "PLAN6_CONDITIONAL_CANDIDATE_HARDENING_COMPLETE", "status is not current hardening state")
expect(status.get("daily_driver_promotion_recommendation") == "CONDITIONAL_DAILY_DRIVER_CANDIDATE", "recommendation mismatch")
expect(status.get("full_daily_driver_promotion") == "NOT_APPROVED", "full promotion must remain denied")
expect(status.get("plan7_status") in {"NOT_STARTED_NOT_AUTHORIZED", "NOT_STARTED / NOT_AUTHORIZED"}, "Plan 7 status mismatch")
expect(status.get("next_plan_authorized") is False, "next plan must not be authorized")
expect(status.get("forbidden_paths_touched") is False, "forbidden paths touched flag must be false")
expect(status.get("package_or_env_changed") is False, "package/env changed flag must be false")
expect(status.get("generated_xml_or_repomix_changed") is False, "generated XML/repomix flag must be false")
expect(len(approval.get("records", [])) == 5, "addendum approval record count must be 5")
expect(len(proof.get("task_results", [])) == 5, "addendum soak task count must be 5")
expect(all(task.get("post_restore_blocked_apply_probe", {}).get("blocked") is True for task in proof["task_results"]), "all post-restore probes must be blocked")
expect(all(task.get("forbidden_state_scan") == [] for task in proof["task_results"]), "all forbidden_state_scan arrays must be empty")
expect(manifest.get("operator_decision_source") == "Britton chat approval for conditional hardening + closeout", "hardening manifest source mismatch")
expect(manifest.get("full_daily_driver_go") == "NOT_APPROVED", "manifest full GO mismatch")
expect(manifest.get("plan7_authorization") == "NOT_AUTHORIZED", "manifest Plan 7 authorization mismatch")
expect(verifier.get("final_recommendation") == "CONDITIONAL_DAILY_DRIVER_CANDIDATE", "verifier recommendation mismatch")
expect(verifier.get("full_daily_driver_go") == "NOT_APPROVED", "verifier full GO mismatch")
PY
if grep -R -E "preview_only_completion|advisory_only_completion|read_only_completion" "$PLAN_DIR/status.md" >/dev/null 2>&1; then
  echo "FAIL forbidden completion flag in status"
  exit 1
fi
git status --short
if find "$ROOT" -type d -empty -print | grep .; then
  echo "FAIL empty planning directories present"
  exit 1
fi
echo "PASS Plan 6/6 operator planning check"
