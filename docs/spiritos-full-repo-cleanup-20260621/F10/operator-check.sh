#!/usr/bin/env bash
# F10 operator check - plan-stage. Live gates activate after F01-F09 are GO.
set -euo pipefail

STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F10"
echo "F10 operator check"

for f in plan.md status.md status.json acceptance-contract.json holdout-manifest.json increment-manifest.md evidence-summary.md codex-review-report.md next-stage-handoff.md; do
  test -s "$STAGE_DIR/$f"
done
test -s "$STAGE_DIR/evidence/.gitkeep"
echo "  [OK] required files present"

python3 - <<'PY'
import json
from pathlib import Path

stage = Path("docs/spiritos-full-repo-cleanup-20260621/F10")
contract = json.loads((stage / "acceptance-contract.json").read_text())
holdout = json.loads((stage / "holdout-manifest.json").read_text())
status = json.loads((stage / "status.json").read_text())

assert status["stage"] == "F10"
assert status["status"] == "NOT_STARTED"
assert status["terminal_state_on_GO"].startswith("READY_FOR_SECONDARY_REVIEW")
assert contract["stage"] == "F10"
assert holdout["stage"] == "F10"

required_battery = {
    "B-TAX",
    "B-FAILCLASS",
    "B-AC-NEG",
    "B-PARITY",
    "B-BS-DRY",
    "B-NO-API",
    "B-PD-HOLD",
    "B-RECEIPT",
    "B-TRACE",
    "B-APPLY-RECOV",
    "B-PY-FOCUSED",
    "B-PY-BROADER",
    "B-LINT",
    "B-TC",
    "B-BUILD",
    "B-CODING",
    "B-SMOKE",
    "B-PLAN2-OP",
    "B-PLAN3-OP",
    "B-HEADROOM",
    "B-PROTECTED",
    "B-DIRTY",
    "B-DIFFCHECK",
    "B-TAILOR",
}
actual_battery = {item["id"] for item in contract["battery"]}
missing = required_battery - actual_battery
assert not missing, f"missing battery items: {sorted(missing)}"

required_holdouts = {
    "HOLD-F10-TAILOR-WHOLE",
    "HOLD-F10-NOAPI-WHOLE",
    "HOLD-F10-RECEIPT-E2E",
    "HOLD-F10-CONTRACT-HASH",
    "HOLD-F10-PROTECTED-WHOLE",
    "HOLD-F10-CROSS-STAGE-FALLBACK",
    "HOLD-F10-NO-STAMPED-PASS",
}
actual_holdouts = {item["id"] for item in holdout["generic_checks"]}
missing_holdouts = required_holdouts - actual_holdouts
assert not missing_holdouts, f"missing holdouts: {sorted(missing_holdouts)}"

required_deps = {f"F{i:02d}" for i in range(1, 10)}
assert set(contract["dependencies"]) == required_deps
assert set(status["dependencies_satisfied"]) == required_deps

for forbidden in ["Set A", "Set B", "Set C"]:
    assert forbidden not in contract.get("terminal_action_on_GO", "")

print("  [OK] F10 battery, holdouts, dependencies, and terminal stop are frozen")
PY

echo "F10 operator check: PASS (plan-stage)"
exit 0
