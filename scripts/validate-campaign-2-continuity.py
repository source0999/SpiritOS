#!/usr/bin/env python3
"""Fail closed when Campaign 2 control-plane state cannot be resumed."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(os.environ.get("SPIRITOS_CAMPAIGN2_CONTINUITY_ROOT", Path(__file__).resolve().parents[1]))
PLAN = ROOT / "docs/architecture/campaign-2-plan.md"
LEDGER = ROOT / "docs/architecture/campaign-2-ledger.md"
STATE = ROOT / "docs/architecture/campaign-2-state.json"
REQUIRED_FIELDS = {
    "schema", "campaign_id", "plan_path", "ledger_path", "base_commit", "branch",
    "recorded_head", "checkpoint_commit_policy", "current_phase", "current_increment",
    "completed_gate_ids", "partial_gate_ids", "next_gate_id", "protected_heads",
    "allowed_mutable_root", "valid_stop_reasons", "go_eligible", "closeout",
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def main() -> int:
    failures: list[str] = []
    for path in (PLAN, LEDGER, STATE):
        if not path.is_file():
            failures.append(f"missing:{path.relative_to(ROOT)}")
    if failures:
        print("CAMPAIGN_2_CONTINUITY_INVALID", *failures, sep="\n")
        return 1
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print("CAMPAIGN_2_CONTINUITY_INVALID", f"state_json_invalid:{error.msg}", sep="\n")
        return 1
    ledger = LEDGER.read_text(encoding="utf-8")
    missing = sorted(REQUIRED_FIELDS - set(state))
    if missing:
        failures.append("checkpoint_fields_missing:" + ",".join(missing))
    if state.get("schema") != "spiritos-campaign-2-state/v1" or state.get("campaign_id") != "spiritos-campaign-2":
        failures.append("campaign_identity_mismatch")
    if state.get("plan_path") != "docs/architecture/campaign-2-plan.md" or state.get("ledger_path") != "docs/architecture/campaign-2-ledger.md":
        failures.append("control_plane_link_mismatch")
    if state.get("branch") != git("branch", "--show-current"):
        failures.append("branch_mismatch")
    checkpoint_files = set(git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines())
    atomic = {"docs/architecture/campaign-2-state.json", "docs/architecture/campaign-2-ledger.md"}.issubset(checkpoint_files)
    recorded = state.get("recorded_head")
    valid_recorded = recorded == git("rev-parse", "HEAD")
    if not valid_recorded and state.get("checkpoint_commit_policy") == "parent_of_atomic_checkpoint" and atomic:
        valid_recorded = recorded == git("rev-parse", "HEAD^")
    if not isinstance(recorded, str) or not valid_recorded or recorded[:8] not in ledger:
        failures.append("recorded_head_mismatch")
    completed = state.get("completed_gate_ids")
    if not isinstance(completed, list) or state.get("next_gate_id") in completed:
        failures.append("gate_progress_invalid")
    if state.get("go_eligible") is False and "GO eligibility: `false`" not in ledger:
        failures.append("ledger_go_eligibility_mismatch")
    for key, path in {
        "source_proxy": "/home/source/SpiritOS-source-proxy-20260711",
        "spiritflix": "/home/source/SpiritOS",
        "architecture_audit": "/home/source/SpiritOS/.codex-worktrees/spiritos-architecture-audit-20260712",
        "campaign_1_terminal": "/home/source/SpiritOS-campaign-1-20260712",
    }.items():
        try:
            actual = subprocess.check_output(["git", "-C", path, "rev-parse", "HEAD"], text=True).strip()
        except subprocess.CalledProcessError:
            failures.append(f"protected_head_unreadable:{key}")
            continue
        if state.get("protected_heads", {}).get(key) != actual:
            failures.append(f"protected_head_mismatch:{key}")
    if failures:
        print("CAMPAIGN_2_CONTINUITY_INVALID", *failures, sep="\n")
        return 1
    print("CAMPAIGN_2_CONTINUITY_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
