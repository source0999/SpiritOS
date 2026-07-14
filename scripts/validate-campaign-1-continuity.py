#!/usr/bin/env python3
"""Fail closed when Campaign 1 cannot resume from committed control-plane state."""
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ.get("SPIRITOS_CAMPAIGN1_CONTINUITY_ROOT", Path(__file__).resolve().parents[1]))
PLAN = ROOT / "docs/architecture/campaign-1-plan.md"
LEDGER = ROOT / "docs/architecture/campaign-1-ledger.md"
STATE = ROOT / "docs/architecture/campaign-1-state.json"
REQUIRED_STATE_FIELDS = {"schema", "campaign_id", "plan_path", "ledger_path", "base_commit", "branch", "recorded_head", "current_phase", "current_increment", "completed_gate_ids", "partial_gate_ids", "next_gate_id", "protected_heads", "allowed_mutable_root", "dirty_state_policy", "valid_stop_reasons", "go_eligible", "last_verified_at"}


def git(directory: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(directory), *args], text=True).strip()


def main() -> int:
    failures: list[str] = []
    for path in (PLAN, LEDGER, STATE):
        if not path.is_file(): failures.append(f"missing:{path.relative_to(ROOT)}")
    if failures:
        print("CAMPAIGN_1_CONTINUITY_INVALID"); print("\n".join(failures)); return 1
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print("CAMPAIGN_1_CONTINUITY_INVALID"); print(f"state_json_invalid:{error.msg}"); return 1
    ledger, plan = LEDGER.read_text(encoding="utf-8"), PLAN.read_text(encoding="utf-8")
    head, branch = git(ROOT, "rev-parse", "HEAD"), git(ROOT, "branch", "--show-current")
    missing_fields = sorted(REQUIRED_STATE_FIELDS - set(state))
    if missing_fields: failures.append("checkpoint_fields_missing:" + ",".join(missing_fields))
    if state.get("schema") != "spiritos-campaign-1-state/v1": failures.append("state_schema_mismatch")
    if state.get("campaign_id") != "spiritos-campaign-1" or "spiritos-campaign-1" not in ledger.lower() or "Campaign 1" not in plan: failures.append("campaign_identity_mismatch")
    if state.get("plan_path") != "docs/architecture/campaign-1-plan.md" or state.get("ledger_path") != "docs/architecture/campaign-1-ledger.md" or "campaign-1-plan.md" not in ledger: failures.append("control_plane_link_mismatch")
    if state.get("branch") != branch: failures.append("branch_mismatch")
    if state.get("recorded_head") != head or head not in ledger: failures.append("recorded_head_mismatch")
    if state.get("current_phase") != "Phase 1" or "Phase: **Phase 1**" not in ledger: failures.append("obsolete_phase")
    if state.get("next_gate_id") in state.get("completed_gate_ids", []): failures.append("next_gate_already_complete")
    if state.get("next_gate_id") not in ledger: failures.append("next_gate_not_recorded")
    if "_worktrees/" not in ledger or "_worktrees/" not in plan or "borrowed" not in ledger.lower(): failures.append("borrowed_worktree_policy_missing")
    roots = {
        "source_proxy": Path(os.environ.get("SPIRITOS_CAMPAIGN1_SOURCE_PROXY_ROOT", "/home/source/SpiritOS-source-proxy-20260711")),
        "spiritflix": Path(os.environ.get("SPIRITOS_CAMPAIGN1_SPIRITFLIX_ROOT", "/home/source/SpiritOS")),
        "architecture_audit": Path(os.environ.get("SPIRITOS_CAMPAIGN1_ARCHITECTURE_AUDIT_ROOT", "/home/source/SpiritOS/.codex-worktrees/spiritos-architecture-audit-20260712")),
    }
    for key, path in roots.items():
        try: actual = git(path, "rev-parse", "HEAD")
        except subprocess.CalledProcessError:
            failures.append(f"protected_head_unreadable:{key}"); continue
        if state.get("protected_heads", {}).get(key) != actual: failures.append(f"protected_head_mismatch:{key}")
    operator_files = [ROOT / "src/app/v1/operator/session/route.ts", ROOT / "src/lib/coding/operator-approval-session.ts"]
    if any(path.exists() for path in operator_files) and "operator-session" not in ledger: failures.append("operator_session_checkpoint_missing")
    if state.get("go_eligible") and state.get("partial_gate_ids"): failures.append("premature_final_verdict")
    if "GO eligibility: `false`" not in ledger and state.get("go_eligible") is False: failures.append("ledger_go_eligibility_mismatch")
    if failures:
        print("CAMPAIGN_1_CONTINUITY_INVALID"); print("\n".join(failures)); return 1
    print("CAMPAIGN_1_CONTINUITY_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
