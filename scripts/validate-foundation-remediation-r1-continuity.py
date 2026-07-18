#!/usr/bin/env python3
"""Validate the Foundation Remediation R1 control-plane checkpoint.

This validator intentionally checks Git and protected refs instead of trusting the
machine state to attest to its own continuity.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any


EXPECTED_SCHEMA = "spiritos-foundation-remediation-r1-state/v1"
EXPECTED_ID = "spiritos-foundation-remediation-r1"
EXPECTED_BASE = "2b8ead66578d7f7053c01cb987e011b763c1c03d"
EXPECTED_BRANCH = "codex/spiritos-foundation-remediation-r1-20260717"
EXPECTED_PATHS = {
    "goal_path": "docs/architecture/foundation-remediation-r1-goal.md",
    "plan_path": "docs/architecture/foundation-remediation-r1-plan.md",
    "ledger_path": "docs/architecture/foundation-remediation-r1-ledger.md",
    "authority_inventory_path": "docs/architecture/foundation-remediation-r1-authority-inventory.md",
    "evidence_index_path": "docs/architecture/foundation-remediation-r1-evidence-index.md",
    "test_profiles_path": "docs/architecture/foundation-remediation-r1-test-profiles.json",
}
STATE_RELATIVE = "docs/architecture/foundation-remediation-r1-state.json"
REQUIRED_SCRIPT_PATHS = {
    "scripts/foundation-remediation-r1-completion.py",
    "scripts/test-foundation-remediation-r1-completion.py",
    "scripts/validate-foundation-remediation-r1-authority.py",
    "scripts/validate-foundation-remediation-r1-continuity.py",
    "scripts/validate-foundation-remediation-r1-evidence.py",
    "scripts/validate-foundation-remediation-r1-test-profiles.py",
}
EXPECTED_PROTECTED_HEADS = {
    "source_proxy": "594d66ef8280953af767a273d7c91be765d1a6eb",
    "spiritflix": "5fde4ae064d471e1133e00d6bf25fb5aecb5d196",
    "architecture_audit": "05612d2ae358bc01b6ef997243137649f8d65f14",
    "campaign_1_terminal": "8a20473c2260bc132e595c64230d3fdfc9fef97f",
    "campaign_2_engineering_terminal": EXPECTED_BASE,
    "campaign_3_design_terminal": "4aec510409e8bb82386190af9fa8f666efcbc63e",
}
PROTECTED_REFS = {
    "source_proxy": "refs/heads/codex/source-proxy-structural-milestone-20260711",
    "spiritflix": "refs/heads/codex/spiritflix-smart-scan-identity-fix",
    "architecture_audit": "refs/heads/codex/spiritos-architecture-audit-20260712",
    "campaign_1_terminal": "refs/heads/codex/spiritos-campaign-1-foundation-20260712",
    "campaign_2_engineering_terminal": "refs/heads/codex/spiritos-campaign-2-core-coding-os-20260716",
    "campaign_3_design_terminal": "refs/heads/codex/spiritos-campaign-3-core-design-lane-20260717",
}
EXPECTED_PROTECTED_REF_TIPS = {
    **EXPECTED_PROTECTED_HEADS,
    # Campaign 2 advanced after its historical engineering terminal. Both the
    # terminal object and the exact branch tip observed at R1 start are pinned.
    "campaign_2_engineering_terminal": "39de31bb73cb4a910281705259b35a6d42a0726c",
}
REQUIRED_STATE_FIELDS = {
    "schema",
    "remediation_id",
    *EXPECTED_PATHS,
    "base_commit",
    "branch",
    "worktree",
    "recorded_head",
    "checkpoint_commit_policy",
    "current_phase",
    "current_increment",
    "completed_gate_ids",
    "partial_gate_ids",
    "next_gate_id",
    "terminal_gate_id",
    "gate_dependency_order",
    "protected_heads",
    "historical_claims",
    "validator_status",
    "terminal_evidence",
    "valid_stop_reasons",
    "go_eligible",
    "closeout",
}


def run_git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=check,
    )


def git_text(root: Path, *args: str) -> str:
    return run_git(root, *args).stdout.strip()


def load_state(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, f"state_unreadable_or_malformed:{error}"
    if not isinstance(payload, dict):
        return None, "state_not_object"
    return payload, None


def registered_worktree_head(root: Path) -> str | None:
    current_path: Path | None = None
    for line in git_text(root, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            current_path = Path(line.removeprefix("worktree ")).resolve()
        elif line.startswith("HEAD ") and current_path == root.resolve():
            return line.removeprefix("HEAD ").strip()
    return None


def terminal_candidate(state: dict[str, Any]) -> bool:
    closeout = state.get("closeout")
    return bool(
        state.get("go_eligible") is True
        or "r1_complete" in (state.get("completed_gate_ids") or [])
        or (isinstance(closeout, dict) and closeout.get("status") == "complete")
    )


def validate_terminal_git_binding(
    root: Path,
    state: dict[str, Any],
    head: str,
    failures: list[str],
) -> None:
    status = run_git(root, "status", "--porcelain=v1", "--untracked-files=all", check=False)
    if status.returncode != 0:
        failures.append("terminal_worktree_status_unreadable")
    elif status.stdout:
        failures.append("terminal_worktree_not_globally_clean")

    evidence = state.get("terminal_evidence")
    if not isinstance(evidence, dict):
        failures.append("terminal_evidence_missing_for_git_binding")
        return
    source = evidence.get("source_commit")
    tag = evidence.get("tag_name")
    if not isinstance(source, str) or len(source) != 40:
        failures.append("terminal_authority_source_commit_invalid")
        return
    if not isinstance(tag, str) or not tag:
        failures.append("terminal_authority_tag_name_invalid")
        return
    if run_git(root, "cat-file", "-e", f"{source}^{{commit}}", check=False).returncode != 0:
        failures.append("terminal_authority_source_commit_unreadable")
        return
    tag_type = run_git(root, "cat-file", "-t", f"refs/tags/{tag}", check=False)
    if tag_type.returncode != 0 or tag_type.stdout.strip() != "tag":
        failures.append("terminal_authority_tag_not_annotated")
        return
    target = run_git(root, "rev-parse", f"refs/tags/{tag}^{{}}", check=False)
    if target.returncode != 0 or target.stdout.strip() != head:
        failures.append("terminal_authority_tag_target_mismatch")
        return
    if source == head or run_git(
        root, "merge-base", "--is-ancestor", source, head, check=False
    ).returncode != 0:
        failures.append("terminal_authority_source_not_precloseout_ancestor")
    authority_diff = run_git(
        root,
        "diff",
        "--quiet",
        source,
        head,
        "--",
        "source_proxy",
        "scripts/approval-authority.py",
        "src/lib/coding",
        check=False,
    )
    if authority_diff.returncode != 0:
        failures.append("terminal_authority_source_tag_tree_mismatch")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(os.environ.get("SPIRITOS_FOUNDATION_R1_ROOT", Path(__file__).resolve().parents[1])),
    )
    args = parser.parse_args()
    root = args.root.resolve()
    state_path = root / STATE_RELATIVE
    ledger_path = root / EXPECTED_PATHS["ledger_path"]
    failures: list[str] = []

    state, error = load_state(state_path)
    if error:
        print("FOUNDATION_REMEDIATION_R1_CONTINUITY_INVALID")
        print(error)
        return 1
    assert state is not None

    missing_fields = sorted(REQUIRED_STATE_FIELDS - set(state))
    if missing_fields:
        failures.append("state_fields_missing:" + ",".join(missing_fields))
    if state.get("schema") != EXPECTED_SCHEMA:
        failures.append("state_schema_mismatch")
    if state.get("remediation_id") != EXPECTED_ID:
        failures.append("remediation_identity_mismatch")
    for field, relative in EXPECTED_PATHS.items():
        if state.get(field) != relative:
            failures.append(f"control_plane_path_mismatch:{field}")
    for relative in sorted({*EXPECTED_PATHS.values(), STATE_RELATIVE, *REQUIRED_SCRIPT_PATHS}):
        path = root / relative
        if not path.is_file():
            failures.append(f"control_plane_file_missing:{relative}")
            continue
        if run_git(root, "ls-files", "--error-unmatch", relative, check=False).returncode != 0:
            failures.append(f"control_plane_file_untracked:{relative}")
        if run_git(root, "diff", "--quiet", "--", relative, check=False).returncode != 0:
            failures.append(f"control_plane_file_dirty:{relative}")
        if run_git(root, "diff", "--cached", "--quiet", "--", relative, check=False).returncode != 0:
            failures.append(f"control_plane_file_staged:{relative}")

    try:
        head = git_text(root, "rev-parse", "HEAD")
        branch = git_text(root, "branch", "--show-current")
    except subprocess.CalledProcessError as error_obj:
        failures.append(f"git_identity_unreadable:{error_obj}")
        head = ""
        branch = ""
    if branch != EXPECTED_BRANCH or state.get("branch") != branch:
        failures.append("branch_mismatch")
    if state.get("base_commit") != EXPECTED_BASE:
        failures.append("base_commit_mismatch")
    if run_git(root, "cat-file", "-e", f"{EXPECTED_BASE}^{{commit}}", check=False).returncode != 0:
        failures.append("base_commit_unreadable")
    elif head and run_git(root, "merge-base", "--is-ancestor", EXPECTED_BASE, head, check=False).returncode != 0:
        failures.append("base_commit_not_ancestor")
    if terminal_candidate(state):
        validate_terminal_git_binding(root, state, head, failures)

    configured_worktree = state.get("worktree")
    if not isinstance(configured_worktree, str) or Path(configured_worktree).resolve() != root:
        failures.append("worktree_identity_mismatch")
    registered_head = registered_worktree_head(root)
    if registered_head != head:
        failures.append("registered_worktree_mismatch")

    recorded = state.get("recorded_head")
    recorded_valid = isinstance(recorded, str) and recorded == head
    if not recorded_valid and state.get("checkpoint_commit_policy") == "parent_of_atomic_checkpoint" and head:
        parent = git_text(root, "rev-parse", "HEAD^")
        checkpoint_files = set(
            git_text(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines()
        )
        atomic_files = {
            "docs/architecture/foundation-remediation-r1-state.json",
            "docs/architecture/foundation-remediation-r1-ledger.md",
        }
        recorded_valid = recorded == parent and atomic_files.issubset(checkpoint_files)
    if not recorded_valid:
        failures.append("recorded_head_mismatch")
    if ledger_path.is_file() and isinstance(recorded, str):
        ledger = ledger_path.read_text(encoding="utf-8")
        if recorded not in ledger and recorded[:12] not in ledger:
            failures.append("recorded_head_not_in_ledger")

    protected = state.get("protected_heads")
    if protected != EXPECTED_PROTECTED_HEADS:
        failures.append("protected_head_inventory_mismatch")
    for name, expected in EXPECTED_PROTECTED_HEADS.items():
        if run_git(root, "cat-file", "-e", f"{expected}^{{commit}}", check=False).returncode != 0:
            failures.append(f"protected_commit_unreadable:{name}")
            continue
        ref = PROTECTED_REFS[name]
        result = run_git(root, "rev-parse", "--verify", ref, check=False)
        if result.returncode != 0:
            failures.append(f"protected_ref_unreadable:{name}")
            continue
        actual = result.stdout.strip()
        expected_tip = EXPECTED_PROTECTED_REF_TIPS[name]
        if actual != expected_tip:
            failures.append(f"protected_ref_mismatch:{name}")
        if name == "campaign_2_engineering_terminal" and run_git(
            root, "merge-base", "--is-ancestor", expected, actual, check=False
        ).returncode != 0:
            failures.append(f"protected_ref_lost_terminal:{name}")

    gate_order = state.get("gate_dependency_order")
    completed = state.get("completed_gate_ids")
    partial = state.get("partial_gate_ids")
    if not isinstance(gate_order, list) or gate_order[-1:] != ["r1_complete"]:
        failures.append("gate_dependency_order_invalid")
    if not isinstance(completed, list) or not isinstance(partial, list):
        failures.append("gate_progress_invalid")
    elif set(completed) & set(partial):
        failures.append("gate_progress_overlap")

    if failures:
        print("FOUNDATION_REMEDIATION_R1_CONTINUITY_INVALID")
        print("\n".join(sorted(set(failures))))
        return 1
    print("FOUNDATION_REMEDIATION_R1_CONTINUITY_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
