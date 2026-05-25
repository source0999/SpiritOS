from __future__ import annotations

from datetime import datetime, timezone
from fnmatch import fnmatchcase
from hashlib import sha256
from pathlib import Path
import subprocess
from typing import Any

from source_proxy.cartographer.component_mapper import map_paths
from source_proxy.cartographer.git_status import read_git_status_for_project, read_git_statuses
from source_proxy.cartographer.models import CommitProposal, GitStatus, ProposalRecord
from source_proxy.cartographer.proposals import list_proposals


COMMIT_READY_STATES = {"applied", "commit_pending"}
RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "blocked": 3, "unknown": 4}
REQUIRED_COMMIT_CHECKS = [
    "git_diff_check",
    "blueprint_metadata_validation",
    "cartographer_pytest",
]
LEVEL_3_PROPOSAL_VERSION = "cartographer.level_3.commit_proposal.v1"
LEVEL_3_ENDPOINT = "/v1/cartographer/level-3-commit-proposals"
FORBIDDEN_FILE_PATTERNS = (
    ".env*",
    "**/.env*",
    "certificates/**",
    "**/certificates/**",
    "**/*secret*",
    "**/*token*",
    "**/*credential*",
    "**/*password*",
    "**/*private-key*",
    "**/*.pem",
    "**/*.key",
    "**/*.p12",
    "**/*.pfx",
    "node_modules/**",
    "**/node_modules/**",
    ".next/**",
    "**/.next/**",
    "dist/**",
    "**/dist/**",
    "build/**",
    "**/build/**",
    "coverage/**",
    "**/coverage/**",
    ".pytest_cache/**",
    "**/.pytest_cache/**",
    "__pycache__/**",
    "**/__pycache__/**",
    "*.sqlite",
    "*.sqlite3",
    "*.db",
    "*.db-shm",
    "*.db-wal",
    "package-lock.json",
    "npm-shrinkwrap.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "bun.lockb",
)
CONFIG_FILE_PATTERNS = (
    "package.json",
    "tsconfig*.json",
    "next.config.*",
    "vite.config.*",
    "vitest.config.*",
    "eslint.config.*",
    ".eslintrc*",
)
BINARY_FILE_SUFFIXES = (
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".tgz",
    ".7z",
    ".mp4",
    ".mov",
    ".woff",
    ".woff2",
    ".ttf",
)


def build_commit_proposals() -> list[CommitProposal]:
    statuses = read_git_statuses()
    if not statuses:
        cwd = Path.cwd()
        if (cwd / ".git").exists():
            statuses = [read_git_status_for_project(project_id=cwd.name.lower(), root=cwd)]
    git_by_project = {
        status.project_id: status
        for status in statuses
        if status.project_id and status.available
    }
    proposals: list[CommitProposal] = []
    claimed_files_by_project: dict[str, set[str]] = {}
    for proposal in list_proposals():
        if proposal.status not in COMMIT_READY_STATES:
            continue
        git_status = git_by_project.get(proposal.project_id)
        if not git_status:
            continue
        files = _commit_files(proposal, git_status)
        if not files:
            continue
        proposals.append(_commit_proposal(proposal, files, git_status))
        claimed_files_by_project.setdefault(proposal.project_id, set()).update(files)

    for project_id, git_status in git_by_project.items():
        claimed_files = claimed_files_by_project.get(project_id, set())
        remaining_files = [
            _normalize_repo_path(path)
            for path in git_status.changed_files
            if _normalize_repo_path(path) not in claimed_files
        ]
        proposals.extend(_dirty_tree_commit_proposals(git_status, remaining_files))

    return proposals


def build_level_3_commit_proposal_preview(
    *,
    level_2_readiness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    statuses = read_git_statuses()
    if not statuses:
        cwd = Path.cwd()
        if (cwd / ".git").exists():
            statuses = [read_git_status_for_project(project_id=cwd.name.lower(), root=cwd)]

    base_proposals = build_commit_proposals()
    status_by_project = {
        status.project_id or "unknown": status
        for status in statuses
        if status.project_id and status.available
    }
    receipts = [
        _level_3_receipt(proposal, status_by_project.get(proposal.project_id))
        for proposal in base_proposals
    ]
    forbidden_files = sorted(
        {
            path
            for receipt in receipts
            for path in receipt["forbidden_files_detected"]
        }
    )
    unknown_files = sorted(
        {
            path
            for receipt in receipts
            if receipt["file_bundle"] == "unknown_or_mixed"
            for path in receipt["included_files"]
        }
    )
    proposed_bundles = [
        receipt
        for receipt in receipts
        if not receipt["blockers"]
    ]
    blocked_bundles = [
        receipt
        for receipt in receipts
        if receipt["blockers"]
    ]
    docs_apply_enabled = (
        bool(level_2_readiness.get("docs_apply_enabled"))
        if isinstance(level_2_readiness, dict)
        else False
    )
    level_2_blockers = [
        str(blocker.get("code"))
        for blocker in (level_2_readiness or {}).get("blockers", [])
        if isinstance(blocker, dict) and blocker.get("code")
    ]
    readiness_blockers = [
        "level_2_apply_blocked"
        for _ in [None]
        if not docs_apply_enabled
    ]
    if forbidden_files:
        readiness_blockers.append("forbidden_files_detected")
    if unknown_files:
        readiness_blockers.append("unknown_files_require_manual_classification")
    return {
        "status": "observing",
        "level": 3,
        "mode": "human_approved_local_commit_proposals",
        "proposal_version": LEVEL_3_PROPOSAL_VERSION,
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "endpoint": LEVEL_3_ENDPOINT,
        "level_2_docs_apply_enabled": docs_apply_enabled,
        "level_2_blockers": level_2_blockers,
        "level_3_activation_blocked": bool(readiness_blockers),
        "activation_blockers": readiness_blockers,
        "commit_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "branch_creation_allowed": False,
        "branch_delete_allowed": False,
        "stash_allowed": False,
        "cleanup_allowed": False,
        "self_approval_allowed": False,
        "self_promotion_allowed": False,
        "creates_push_queue_item": False,
        "proposal_count": len(receipts),
        "proposed_bundle_count": len(proposed_bundles),
        "blocked_bundle_count": len(blocked_bundles),
        "forbidden_files": forbidden_files,
        "unknown_files": unknown_files,
        "proposed_bundles": proposed_bundles,
        "blocked_bundles": blocked_bundles,
        "commit_proposals": receipts,
        "recommended_next_action": (
            "resolve Level 2 readiness blockers before Level 3 commit execution"
            if not docs_apply_enabled
            else "review proposed bundles; commit execution remains disabled until a later approved implementation"
        ),
    }


def build_level_3_commit_approval_preview(
    *,
    proposal_id: str,
    approval_id: str | None,
    approved_by: str | None,
    exact_file_list: list[str],
    proposed_commit_title: str,
    proposed_commit_body: str,
    git_head_at_creation: str | None = None,
    dirty_tree_fingerprint: str | None = None,
    check_results: list[dict[str, Any]] | None = None,
    approved_deleted_files: list[str] | None = None,
) -> dict[str, Any]:
    proposals_payload = build_level_3_commit_proposal_preview(level_2_readiness=None)
    proposals = [
        proposal
        for proposal in proposals_payload["commit_proposals"]
        if proposal["proposal_id"] == proposal_id
    ]
    proposal = proposals[0] if proposals else None
    blockers: list[str] = []
    if proposal is None:
        blockers.append("proposal_not_found")
    if not approval_id:
        blockers.append("approval_id_required")
    if not approved_by:
        blockers.append("approved_by_required")
    if str(approved_by or "").strip().lower() == "cartographer":
        blockers.append("cartographer_self_approval_blocked")

    normalized_files = sorted(dict.fromkeys(_normalize_repo_path(path) for path in exact_file_list))
    expected_files = sorted(proposal["included_files"]) if proposal else []
    if proposal is not None and normalized_files != expected_files:
        blockers.append("exact_file_list_mismatch")
    if proposal is not None and proposed_commit_title != proposal["proposed_commit_title"]:
        blockers.append("commit_title_mismatch")
    if proposal is not None and proposed_commit_body != proposal["proposed_commit_body"]:
        blockers.append("commit_body_mismatch")
    current_head = str(proposal["git_head_at_creation"] or "") if proposal else ""
    supplied_head = str(git_head_at_creation or "").strip()
    if proposal is not None and supplied_head and supplied_head != current_head:
        blockers.append("git_head_mismatch")
    current_fingerprint = str(proposal["dirty_tree_fingerprint"]) if proposal else ""
    supplied_fingerprint = str(dirty_tree_fingerprint or "").strip()
    if proposal is not None and supplied_fingerprint and supplied_fingerprint != current_fingerprint:
        blockers.append("dirty_tree_fingerprint_mismatch")
    if proposal is not None and proposal["blockers"]:
        blockers.extend(str(blocker) for blocker in proposal["blockers"])
    if proposal is not None and proposal["forbidden_files_detected"]:
        blockers.append("forbidden_files_detected")
    if proposal is not None and proposal["sensitive_files_detected"]:
        blockers.append("sensitive_files_detected")
    check_blockers = _level_3_check_blockers(proposal, check_results or [])
    blockers.extend(check_blockers)
    deletion_blockers = _level_3_deletion_blockers(proposal, approved_deleted_files or [])
    blockers.extend(deletion_blockers)

    unique_blockers = list(dict.fromkeys(blockers))
    approval_validated = proposal is not None and not unique_blockers
    return {
        "status": "approval_preview",
        "level": 3,
        "mode": "human_approval_gate_preview",
        "proposal_id": proposal_id,
        "proposal_found": proposal is not None,
        "approval_required": True,
        "approval_id": approval_id,
        "approved_by": approved_by,
        "approval_validated": approval_validated,
        "approved_at": None,
        "exact_file_list": normalized_files,
        "expected_file_list": expected_files,
        "git_head_at_creation": proposal["git_head_at_creation"] if proposal else None,
        "supplied_git_head_at_creation": git_head_at_creation,
        "dirty_tree_fingerprint": proposal["dirty_tree_fingerprint"] if proposal else None,
        "supplied_dirty_tree_fingerprint": dirty_tree_fingerprint,
        "current_branch": proposal["current_branch"] if proposal else None,
        "proposed_commit_title": proposed_commit_title,
        "proposed_commit_body": proposed_commit_body,
        "required_check_commands": proposal["related_test_commands"] if proposal else [],
        "check_results": check_results or [],
        "checks_validated": not check_blockers,
        "deleted_files": proposal["deleted_files"] if proposal else [],
        "approved_deleted_files": [
            _normalize_repo_path(path) for path in (approved_deleted_files or [])
        ],
        "deletions_validated": not deletion_blockers,
        "blockers": unique_blockers,
        "commit_allowed": False,
        "commit_enabled": False,
        "commit_execution_enabled": False,
        "push_allowed": False,
        "creates_push_queue_item": False,
        "proposal_stale": any(
            blocker in unique_blockers
            for blocker in ("git_head_mismatch", "dirty_tree_fingerprint_mismatch")
        ),
        "actions_taken": False,
        "next_step": (
            "approval fields validate, but commit execution is not implemented for Level 3 yet"
            if approval_validated
            else "resolve approval preview blockers before requesting Level 3 commit execution"
        ),
    }


def build_level_3_commit_execution_block(
    *,
    proposal_id: str,
    approval_id: str | None,
    approved_by: str | None,
    exact_file_list: list[str] | None = None,
    proposed_commit_title: str = "",
    proposed_commit_body: str = "",
    git_head_at_creation: str | None = None,
    dirty_tree_fingerprint: str | None = None,
    check_results: list[dict[str, Any]] | None = None,
    approved_deleted_files: list[str] | None = None,
    level_2_readiness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    proposal, git_status = _find_level_3_proposal_with_status(proposal_id)
    blockers: list[str] = []
    if not bool((level_2_readiness or {}).get("docs_apply_enabled")):
        blockers.append("level_2_safe_dependency")

    approval_preview = build_level_3_commit_approval_preview(
        proposal_id=proposal_id,
        approval_id=approval_id,
        approved_by=approved_by,
        exact_file_list=exact_file_list or [],
        proposed_commit_title=proposed_commit_title,
        proposed_commit_body=proposed_commit_body,
        git_head_at_creation=git_head_at_creation,
        dirty_tree_fingerprint=dirty_tree_fingerprint,
        check_results=check_results or [],
        approved_deleted_files=approved_deleted_files or [],
    )
    blockers.extend(str(blocker) for blocker in approval_preview["blockers"])
    if not git_head_at_creation:
        blockers.append("git_head_at_creation_required")
    if not dirty_tree_fingerprint:
        blockers.append("dirty_tree_fingerprint_required")
    if proposal is not None and git_status is None:
        blockers.append("git_status_unavailable")

    normalized_files = [_normalize_repo_path(path) for path in (exact_file_list or [])]
    if any(_is_forbidden_level_3_path(path) for path in normalized_files):
        blockers.append("forbidden_files_detected")
    if any(_is_sensitive_path(path) for path in normalized_files):
        blockers.append("sensitive_files_detected")
    if proposal is not None and proposal["file_bundle"] == "unknown_or_mixed":
        blockers.append("unknown_or_mixed_files_block_approval")
    if git_status is not None:
        staged = {_normalize_repo_path(path) for path in git_status.staged_files}
        unapproved_staged = sorted(staged.difference(normalized_files))
        if unapproved_staged:
            blockers.append("unrelated_staged_files_block_commit")
    else:
        unapproved_staged = []

    unique_blockers = list(dict.fromkeys(blockers))
    if unique_blockers:
        return _level_3_commit_execution_receipt(
            status="blocked",
            proposal_id=proposal_id,
            approval_id=approval_id,
            approved_by=approved_by,
            proposal=proposal,
            git_status=git_status,
            blockers=unique_blockers,
            approval_preview=approval_preview,
            committed_files=[],
            commit_sha=None,
        )

    assert proposal is not None
    assert git_status is not None
    root = Path(str(git_status.root))
    head_before = _git_stdout_or_blocker(root, "rev-parse", "HEAD")
    if head_before["blocker"]:
        return _level_3_commit_execution_receipt(
            status="blocked",
            proposal_id=proposal_id,
            approval_id=approval_id,
            approved_by=approved_by,
            proposal=proposal,
            git_status=git_status,
            blockers=[head_before["blocker"]],
            approval_preview=approval_preview,
            committed_files=[],
            commit_sha=None,
        )
    add_result = _git(root, "add", "--", *normalized_files)
    if add_result.returncode != 0:
        return _level_3_commit_execution_receipt(
            status="blocked",
            proposal_id=proposal_id,
            approval_id=approval_id,
            approved_by=approved_by,
            proposal=proposal,
            git_status=git_status,
            blockers=["explicit_file_staging_failed"],
            approval_preview=approval_preview,
            committed_files=[],
            commit_sha=None,
            command_error=add_result.stderr.strip() or add_result.stdout.strip(),
        )
    staged_after = _git_stdout_or_blocker(root, "diff", "--cached", "--name-only")
    staged_files_after = sorted(
        _normalize_repo_path(path)
        for path in staged_after["stdout"].splitlines()
        if path.strip()
    )
    if staged_after["blocker"] or staged_files_after != sorted(normalized_files):
        return _level_3_commit_execution_receipt(
            status="blocked",
            proposal_id=proposal_id,
            approval_id=approval_id,
            approved_by=approved_by,
            proposal=proposal,
            git_status=git_status,
            blockers=[staged_after["blocker"] or "staged_file_bundle_mismatch"],
            approval_preview=approval_preview,
            committed_files=[],
            commit_sha=None,
        )
    command = [
        "commit",
        "-m",
        proposed_commit_title,
        "-m",
        proposed_commit_body or "Approved by Cartographer Level 3.",
        "--",
        *normalized_files,
    ]
    commit_result = _git(root, *command)
    if commit_result.returncode != 0:
        return _level_3_commit_execution_receipt(
            status="blocked",
            proposal_id=proposal_id,
            approval_id=approval_id,
            approved_by=approved_by,
            proposal=proposal,
            git_status=git_status,
            blockers=["git_commit_failed"],
            approval_preview=approval_preview,
            committed_files=[],
            commit_sha=None,
            command_error=commit_result.stderr.strip() or commit_result.stdout.strip(),
        )
    commit_sha = _git_stdout_or_blocker(root, "rev-parse", "HEAD")
    committed_files = _git_stdout_or_blocker(root, "show", "--name-only", "--format=", "HEAD")
    return _level_3_commit_execution_receipt(
        status="committed",
        proposal_id=proposal_id,
        approval_id=approval_id,
        approved_by=approved_by,
        proposal=proposal,
        git_status=git_status,
        blockers=[],
        approval_preview=approval_preview,
        committed_files=[
            _normalize_repo_path(path)
            for path in committed_files["stdout"].splitlines()
            if path.strip()
        ],
        commit_sha=commit_sha["stdout"].strip() or None,
        head_before=head_before["stdout"].strip(),
    )


def _level_3_commit_execution_receipt(
    *,
    status: str,
    proposal_id: str,
    approval_id: str | None,
    approved_by: str | None,
    proposal: dict[str, Any] | None,
    git_status: GitStatus | None,
    blockers: list[str],
    approval_preview: dict[str, Any],
    committed_files: list[str],
    commit_sha: str | None,
    head_before: str | None = None,
    command_error: str | None = None,
) -> dict[str, Any]:
    commit_created = status == "committed" and bool(commit_sha)
    head_before_value = head_before or (git_status.head_sha if git_status else None)
    receipt_id = _level_3_execution_receipt_id(
        proposal_id=proposal_id,
        approval_id=approval_id,
        head_before=head_before_value,
        head_after=commit_sha,
        blockers=blockers,
    )
    return {
        "receipt_version": "cartographer.level_3.local_commit_receipt.v1",
        "receipt_id": receipt_id,
        "status": status,
        "level": 3,
        "mode": "approved_local_commit_executor",
        "proposal_id": proposal_id,
        "proposal_found": proposal is not None,
        "approval_id": approval_id,
        "approved_by": approved_by,
        "approved_at": None,
        "executed_by": "cartographer",
        "approval_validated": approval_preview["approval_validated"],
        "blockers": list(dict.fromkeys(blockers)),
        "validation_summary": {
            "approval_validated": approval_preview["approval_validated"],
            "checks_validated": approval_preview["checks_validated"],
            "deletions_validated": approval_preview["deletions_validated"],
            "head_validated": "git_head_mismatch" not in blockers and bool(head_before_value),
            "dirty_tree_fingerprint_validated": (
                "dirty_tree_fingerprint_mismatch" not in blockers
                and bool(approval_preview["dirty_tree_fingerprint"])
            ),
            "forbidden_paths_blocked": "forbidden_files_detected" not in blockers,
            "sensitive_paths_blocked": "sensitive_files_detected" not in blockers,
            "unclassified_files_blocked": "unknown_or_mixed_files_block_approval" not in blockers,
        },
        "commit_allowed": commit_created,
        "commit_enabled": commit_created,
        "commit_execution_enabled": False,
        "commit_created": commit_created,
        "commit_sha": commit_sha,
        "head_before": head_before_value,
        "head_after": commit_sha,
        "current_branch": git_status.branch if git_status else None,
        "committed_files": committed_files,
        "approved_files": proposal["included_files"] if proposal else [],
        "approved_deleted_files": approval_preview["approved_deleted_files"],
        "excluded_dirty_files": proposal["excluded_files"] if proposal else [],
        "required_checks": approval_preview["required_check_commands"],
        "check_results": approval_preview["check_results"],
        "push_allowed": False,
        "push_enabled": False,
        "push_created": False,
        "creates_push_queue_item": False,
        "branch_creation_allowed": False,
        "merge_allowed": False,
        "stash_allowed": False,
        "cleanup_allowed": False,
        "branch_created": False,
        "merge_created": False,
        "stash_created": False,
        "cleanup_performed": False,
        "actions_taken": commit_created,
        "rollback_command": _rollback_command(),
        "rollback_requires_human_approval": True,
        "rollback_performed": False,
        "command_summary": {
            "stage": "git add -- <approved-files>" if commit_created else None,
            "commit": "git commit -m <title> -m <body> -- <approved-files>" if commit_created else None,
            "push": None,
            "branch": None,
            "merge": None,
            "stash": None,
            "cleanup": None,
        },
        "command_error": command_error,
        "next_step": (
            "Local commit created; push remains disabled."
            if commit_created
            else "Resolve blockers before requesting Level 3 local commit execution."
        ),
    }


def _level_3_execution_receipt_id(
    *,
    proposal_id: str,
    approval_id: str | None,
    head_before: str | None,
    head_after: str | None,
    blockers: list[str],
) -> str:
    key = "|".join(
        [
            proposal_id,
            approval_id or "",
            head_before or "",
            head_after or "",
            ",".join(sorted(blockers)),
        ]
    )
    return f"level-3-local-commit-receipt-{sha256(key.encode('utf-8')).hexdigest()[:12]}"


def _find_level_3_proposal_with_status(
    proposal_id: str,
) -> tuple[dict[str, Any] | None, GitStatus | None]:
    statuses = read_git_statuses()
    if not statuses:
        cwd = Path.cwd()
        if (cwd / ".git").exists():
            statuses = [read_git_status_for_project(project_id=cwd.name.lower(), root=cwd)]
    status_by_project = {
        status.project_id or "unknown": status
        for status in statuses
        if status.project_id and status.available
    }
    for proposal in build_commit_proposals():
        status = status_by_project.get(proposal.project_id)
        receipt = _level_3_receipt(proposal, status)
        if receipt["proposal_id"] == proposal_id:
            return receipt, status
    return None, None


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired as error:
        return subprocess.CompletedProcess(
            ["git", *args],
            returncode=124,
            stdout="",
            stderr=str(error),
        )


def _git_stdout_or_blocker(root: Path, *args: str) -> dict[str, str | None]:
    result = _git(root, *args)
    if result.returncode != 0:
        return {"stdout": result.stdout, "blocker": "git_command_failed"}
    return {"stdout": result.stdout, "blocker": None}


def _level_3_deletion_blockers(
    proposal: dict[str, Any] | None,
    approved_deleted_files: list[str],
) -> list[str]:
    if proposal is None:
        return []
    deleted = sorted(_normalize_repo_path(path) for path in proposal["deleted_files"])
    if not deleted:
        return []
    approved = sorted(_normalize_repo_path(path) for path in approved_deleted_files)
    if approved != deleted:
        return ["explicit_deletion_approval_required"]
    return []


def _level_3_check_blockers(
    proposal: dict[str, Any] | None,
    check_results: list[dict[str, Any]],
) -> list[str]:
    if proposal is None:
        return []
    required = [str(command) for command in proposal["related_test_commands"]]
    if not required:
        return []
    if not check_results:
        return ["required_checks_missing"]

    by_command = {
        str(result.get("command")): str(result.get("status")).lower()
        for result in check_results
        if isinstance(result, dict) and result.get("command")
    }
    missing = [command for command in required if command not in by_command]
    failed = [
        command
        for command in required
        if by_command.get(command) not in {"passed", "ok", "success"}
    ]
    blockers: list[str] = []
    if missing:
        blockers.append("required_checks_missing")
    if failed:
        blockers.append("required_checks_failed")
    return blockers


def _commit_files(proposal: ProposalRecord, git_status: GitStatus) -> list[str]:
    changed = {_normalize_repo_path(path) for path in git_status.changed_files}
    proposed = [_normalize_repo_path(path) for path in proposal.proposed_files]
    if proposed:
        return [path for path in proposed if path in changed]
    return sorted(changed)


def _commit_proposal(
    proposal: ProposalRecord,
    files: list[str],
    git_status: GitStatus,
) -> CommitProposal:
    component, risk = _component_and_risk(files)
    purpose = _purpose_for_files(files)
    staged_files, unstaged_files, untracked_files = _status_buckets(files, git_status)
    excluded_files = _excluded_files(files, git_status)
    verification_status, verification_checks, verification_blockers = _proposal_verification(proposal)
    commit_blockers = [*_commit_blockers(risk), *verification_blockers]
    return CommitProposal(
        commit_proposal_id=_commit_proposal_id(proposal, files),
        project_id=proposal.project_id,
        source_proposal_id=proposal.proposal_id,
        status="commit_pending",
        suggested_message=_suggested_message(proposal),
        story=_story_for_group(component, risk, purpose),
        group_key=_group_key(component, risk, purpose),
        group_reason=_group_reason(component, risk, purpose),
        files=files,
        included_files=files,
        excluded_files=excluded_files,
        reason=(
            f"Proposal {proposal.proposal_id} is {proposal.status}; "
            "package reviewed files into a commit only after approval."
        ),
        component=component,
        risk=risk,
        diff_summary=_diff_summary(git_status, files),
        required_checks=REQUIRED_COMMIT_CHECKS,
        verification_status=verification_status,
        verification_checks=verification_checks,
        audit_state="commit_not_created",
        rollback_command=_rollback_command(),
        stronger_confirmation_required=_stronger_confirmation_required(risk),
        commit_blocked=bool(commit_blockers),
        commit_blockers=commit_blockers,
        generated=False,
        staged_files=staged_files,
        unstaged_files=unstaged_files,
        untracked_files=untracked_files,
        editable=True,
        requires_approval=True,
        commit_enabled=False,
        action_taken=False,
    )


def _dirty_tree_commit_proposals(
    git_status: GitStatus,
    changed_files: list[str],
) -> list[CommitProposal]:
    grouped: dict[tuple[str, str, str], list[str]] = {}
    for path in sorted(dict.fromkeys(changed_files)):
        component, risk = _component_and_risk([path])
        purpose = _purpose_for_path(path)
        grouped.setdefault((component, risk, purpose), []).append(path)

    proposals: list[CommitProposal] = []
    for (component, risk, purpose), files in sorted(grouped.items()):
        staged_files, unstaged_files, untracked_files = _status_buckets(files, git_status)
        excluded_files = _excluded_files(files, git_status)
        commit_blockers = _commit_blockers(risk)
        proposals.append(
            CommitProposal(
                commit_proposal_id=_dirty_commit_proposal_id(
                    git_status.project_id or "unknown",
                    component,
                    risk,
                    purpose,
                    files,
                ),
                project_id=git_status.project_id or "unknown",
                source_proposal_id="dirty-tree",
                status="commit_pending",
                suggested_message=_dirty_tree_message(component, risk, purpose),
                story=_story_for_group(component, risk, purpose),
                group_key=_group_key(component, risk, purpose),
                group_reason=_group_reason(component, risk, purpose),
                files=files,
                included_files=files,
                excluded_files=excluded_files,
                reason=(
                    "Dirty tree files are grouped by component, risk, and purpose; "
                    "stage and commit only after explicit approval."
                ),
                component=component,
                risk=risk,
        diff_summary=_diff_summary(git_status, files),
        required_checks=REQUIRED_COMMIT_CHECKS,
        verification_status="manual_dirty_tree_review_required",
        verification_checks=[],
        audit_state="commit_not_created",
                rollback_command=_rollback_command(),
                stronger_confirmation_required=_stronger_confirmation_required(risk),
                commit_blocked=bool(commit_blockers),
                commit_blockers=commit_blockers,
                generated=True,
                staged_files=staged_files,
                unstaged_files=unstaged_files,
                untracked_files=untracked_files,
                editable=True,
                requires_approval=True,
                commit_enabled=False,
                action_taken=False,
            )
        )
    return proposals


def _level_3_receipt(
    proposal: CommitProposal,
    git_status: GitStatus | None,
) -> dict[str, Any]:
    included_files = [_normalize_repo_path(path) for path in proposal.included_files]
    excluded_files = [_normalize_repo_path(path) for path in proposal.excluded_files]
    deleted_files = _deleted_files(git_status, included_files)
    sensitive_files = [
        path for path in included_files if _is_sensitive_path(path)
    ]
    forbidden_files = [
        path for path in included_files if _is_forbidden_level_3_path(path)
    ]
    file_bundle = _level_3_bundle_for_files(included_files)
    blockers = list(dict.fromkeys([
        *proposal.commit_blockers,
        *(["unknown_or_mixed_files_block_approval"] if file_bundle == "unknown_or_mixed" else []),
        *(["forbidden_files_detected"] if forbidden_files else []),
        *(["sensitive_files_detected"] if sensitive_files else []),
    ]))
    title = proposal.suggested_message or "chore(cartographer): review local commit bundle"
    return {
        "level": 3,
        "proposal_id": proposal.commit_proposal_id,
        "proposal_version": LEVEL_3_PROPOSAL_VERSION,
        "created_at": _generated_at(),
        "created_by": "cartographer",
        "current_branch": git_status.branch if git_status else None,
        "git_head_at_creation": git_status.head_sha if git_status else None,
        "dirty_tree_summary": _level_3_dirty_tree_summary(git_status),
        "dirty_tree_fingerprint": _dirty_tree_fingerprint(git_status),
        "proposed_commit_title": title,
        "proposed_commit_body": _level_3_commit_body(proposal, file_bundle, blockers),
        "file_bundle": file_bundle,
        "included_files": included_files,
        "excluded_files": excluded_files,
        "deleted_files": deleted_files,
        "sensitive_files_detected": sensitive_files,
        "forbidden_files_detected": forbidden_files,
        "rationale_by_file": {
            path: _rationale_for_file(path, file_bundle, proposal)
            for path in included_files
        },
        "related_test_commands": _related_test_commands(file_bundle, included_files),
        "manual_check_commands": [
            "git status -sb",
            "git diff --name-status",
            "git diff --check",
        ],
        "risk_level": proposal.risk,
        "blockers": blockers,
        "approval_required": True,
        "approval_id": None,
        "approved_by": None,
        "approved_at": None,
        "commit_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "branch_creation_allowed": False,
        "stash_allowed": False,
        "cleanup_allowed": False,
        "creates_push_queue_item": False,
        "rollback_command": proposal.rollback_command or _rollback_command(),
        "expected_status_after_commit": "approved files committed locally; unrelated dirty files remain untouched",
        "source_proposal_id": proposal.source_proposal_id,
        "group_key": proposal.group_key,
        "group_reason": proposal.group_reason,
        "diff_summary": proposal.diff_summary,
        "required_checks": proposal.required_checks,
        "commit_enabled": False,
        "action_taken": False,
    }


def _level_3_dirty_tree_summary(git_status: GitStatus | None) -> dict[str, Any]:
    if git_status is None:
        return {
            "available": False,
            "dirty": False,
            "changed_file_count": 0,
            "staged_file_count": 0,
            "unstaged_file_count": 0,
            "untracked_file_count": 0,
        }
    return {
        "available": git_status.available,
        "dirty": git_status.dirty,
        "changed_file_count": len(git_status.changed_files),
        "staged_file_count": len(git_status.staged_files),
        "unstaged_file_count": len(git_status.unstaged_files),
        "untracked_file_count": len(git_status.untracked_files),
        "changed_files": [_normalize_repo_path(path) for path in git_status.changed_files],
    }


def _dirty_tree_fingerprint(git_status: GitStatus | None) -> str | None:
    if git_status is None:
        return None
    parts = [
        git_status.project_id or "",
        git_status.branch or "",
        git_status.head_sha or "",
        ",".join(sorted(_normalize_repo_path(path) for path in git_status.changed_files)),
        ",".join(sorted(_normalize_repo_path(path) for path in git_status.staged_files)),
        ",".join(sorted(_normalize_repo_path(path) for path in git_status.unstaged_files)),
        ",".join(sorted(_normalize_repo_path(path) for path in git_status.untracked_files)),
    ]
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _level_3_bundle_for_files(files: list[str]) -> str:
    bundles = {_level_3_bundle_for_file(path) for path in files}
    if not bundles:
        return "unknown_or_mixed"
    if "forbidden_or_sensitive" in bundles:
        return "forbidden_or_sensitive"
    if len(bundles) == 1:
        return next(iter(bundles))
    if bundles <= {"cartographer_level_3", "cartographer_level_3_plan"}:
        return "cartographer_level_3"
    return "unknown_or_mixed"


def _level_3_bundle_for_file(path: str) -> str:
    normalized = _normalize_repo_path(path)
    lowered = normalized.lower()
    if _is_forbidden_level_3_path(normalized):
        return "forbidden_or_sensitive"
    if normalized == "docs/cartographer-level-1-autonomy-plan.md":
        return "cartographer_level_1"
    if normalized == "docs/cartographer-level-2-autonomy-plan.md":
        return "cartographer_level_2"
    if normalized == "docs/cartographer-level-3-autonomy-plan.md":
        return "cartographer_level_3_plan"
    if (
        lowered.startswith("source_proxy/cartographer/")
        or lowered == "source_proxy/api/cartographer.py"
        or lowered.startswith("source_proxy/tests/test_cartographer")
    ):
        return "cartographer_level_3"
    if lowered.startswith("scout/src/scout/"):
        return "scout_backend"
    if (
        lowered.startswith("src/components/dashboard/")
        or lowered.startswith("src/lib/scout")
        or lowered.startswith("src/app/api/scout/")
    ):
        return "scout_dashboard"
    if lowered.startswith("src/components/coding/"):
        return "coding_cockpit"
    if lowered.endswith(".md") or lowered.startswith("docs/"):
        return "docs_only"
    if lowered in {
        "cartographerbeta.md",
        "cartogrpaherplanauto.md",
        "codingagentoverhaul.md",
        "masteroverhual.md",
        "post-v1-diag.md",
        "productionproxy.md",
        "spiritblueprinter.md",
        "scoutrefinemint.md",
    }:
        return "old_plan_cleanup"
    return "unknown_or_mixed"


def _is_forbidden_level_3_path(path: str) -> bool:
    normalized = _normalize_repo_path(path)
    lowered = normalized.lower()
    if (
        not normalized
        or normalized.startswith("/")
        or normalized.startswith("~")
        or any(segment == ".." for segment in normalized.split("/"))
    ):
        return True
    if any(fnmatchcase(lowered, pattern.lower()) for pattern in FORBIDDEN_FILE_PATTERNS):
        return True
    if any(fnmatchcase(lowered, pattern.lower()) for pattern in CONFIG_FILE_PATTERNS):
        return True
    return lowered.endswith(BINARY_FILE_SUFFIXES)


def _is_sensitive_path(path: str) -> bool:
    lowered = _normalize_repo_path(path).lower()
    return any(
        marker in lowered
        for marker in ("secret", "token", "credential", "password", ".env", "private-key")
    )


def _deleted_files(git_status: GitStatus | None, files: list[str]) -> list[str]:
    if git_status is None or not git_status.root:
        return []
    result = subprocess.run(
        ["git", "diff", "--name-status", "--", *files],
        cwd=git_status.root,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    deleted: list[str] = []
    for line in result.stdout.splitlines():
        status, _separator, path = line.partition("\t")
        if status.startswith("D") and path:
            deleted.append(_normalize_repo_path(path))
    return sorted(dict.fromkeys(deleted))


def _level_3_commit_body(
    proposal: CommitProposal,
    file_bundle: str,
    blockers: list[str],
) -> str:
    lines = [
        proposal.story or "Cartographer Level 3 commit proposal.",
        "",
        f"Bundle: {file_bundle}",
        f"Risk: {proposal.risk}",
        f"Files: {len(proposal.included_files)}",
    ]
    if blockers:
        lines.append(f"Blocked until: {', '.join(blockers)}")
    return "\n".join(lines)


def _rationale_for_file(path: str, file_bundle: str, proposal: CommitProposal) -> str:
    return (
        f"{path} is grouped in {file_bundle} because it shares the "
        f"{proposal.component} component and {proposal.risk} risk profile for this review bundle."
    )


def _related_test_commands(file_bundle: str, files: list[str]) -> list[str]:
    commands = ["git diff --check"]
    if file_bundle.startswith("cartographer_level_"):
        commands.extend(
            [
                'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_3 or commit"',
                "PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py",
            ]
        )
    elif file_bundle == "scout_backend":
        commands.append("PYTHONPATH=. .venv/bin/python -m pytest scout/src/scout/tests")
    elif file_bundle in {"scout_dashboard", "coding_cockpit"}:
        commands.append("npm test")
    elif any(path.endswith(".py") for path in files):
        commands.append("PYTHONPATH=. .venv/bin/python -m pytest")
    return list(dict.fromkeys(commands))


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _suggested_message(proposal: ProposalRecord) -> str:
    if proposal.type == "starter_blueprint_pack":
        return "docs(cartographer): add starter blueprint pack"
    if proposal.component and proposal.component != "unknown":
        return f"docs({proposal.component}): apply cartographer blueprint update"
    return "docs(cartographer): apply approved blueprint update"


def _commit_proposal_id(proposal: ProposalRecord, files: list[str]) -> str:
    key = "|".join([proposal.project_id, proposal.proposal_id, ",".join(files)])
    return f"commit-prop-{sha256(key.encode('utf-8')).hexdigest()[:12]}"


def _dirty_commit_proposal_id(
    project_id: str,
    component: str,
    risk: str,
    purpose: str,
    files: list[str],
) -> str:
    key = "|".join([project_id, component, risk, purpose, ",".join(files)])
    return f"commit-prop-{sha256(key.encode('utf-8')).hexdigest()[:12]}"


def _component_and_risk(files: list[str]) -> tuple[str, str]:
    components, unmapped = map_paths(files)
    if components:
        component = components[0].component_id
        risks: list[str] = []
        for item in components:
            risks.extend(item.matched_path_risks.values())
        if not risks:
            risks = [component.risk for component in components]
    else:
        component = "unknown"
        risks = [item.risk for item in unmapped] or ["unknown"]
    return component, _max_risk(risks)


def _status_buckets(
    files: list[str],
    git_status: GitStatus,
) -> tuple[list[str], list[str], list[str]]:
    staged = {_normalize_repo_path(item) for item in git_status.staged_files}
    unstaged = {_normalize_repo_path(item) for item in git_status.unstaged_files}
    untracked = {_normalize_repo_path(item) for item in git_status.untracked_files}
    return (
        [path for path in files if path in staged],
        [path for path in files if path in unstaged],
        [path for path in files if path in untracked],
    )


def _excluded_files(files: list[str], git_status: GitStatus) -> list[str]:
    included = {_normalize_repo_path(path) for path in files}
    return [
        _normalize_repo_path(path)
        for path in git_status.changed_files
        if _normalize_repo_path(path) not in included
    ]


def _diff_summary(git_status: GitStatus, files: list[str]) -> str:
    if not git_status.root:
        return f"{len(files)} file(s) selected for commit preview."
    result = subprocess.run(
        ["git", "diff", "--stat", "--", *files],
        cwd=git_status.root,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = result.stdout.strip()
    if output:
        return output
    if any(path in {_normalize_repo_path(item) for item in git_status.untracked_files} for path in files):
        return f"{len(files)} untracked file(s) selected for commit preview."
    return f"{len(files)} file(s) selected for commit preview."


def _commit_blockers(risk: str) -> list[str]:
    if risk == "unknown":
        return ["unknown_files_require_manual_classification"]
    if risk == "blocked":
        return ["blocked_files_cannot_be_committed_by_cartographer"]
    return []


def _proposal_verification(proposal: ProposalRecord) -> tuple[str, list[dict[str, object]], list[str]]:
    verification = proposal.post_apply_verification
    if not isinstance(verification, dict):
        return "missing", [], ["post_apply_verification_missing"]

    status = str(verification.get("status") or "unknown")
    checks = [
        check
        for check in verification.get("checks", [])
        if isinstance(check, dict)
    ]
    blockers: list[str] = []
    if status != "verified":
        blockers.append(
            "post_apply_verification_failed"
            if status in {"failed", "verification_failed"}
            else "post_apply_verification_incomplete"
        )
    if bool(verification.get("commit_proposal_blocked")):
        blockers.extend(
            str(item)
            for item in verification.get("commit_blockers", [])
            if item
        )
    return status, checks, list(dict.fromkeys(blockers))


def _stronger_confirmation_required(risk: str) -> bool:
    return risk in {"high", "blocked", "unknown"}


def _rollback_command() -> str:
    return "git reset --soft HEAD~1"


def _purpose_for_path(path: str) -> str:
    lowered = path.lower()
    if "soak-log" in lowered or "/soak-logs/" in lowered:
        return "soak"
    if lowered.startswith("docs/") or lowered.startswith("_blueprints/") or lowered.endswith(".md"):
        return "docs"
    if "/tests/" in lowered or "/__tests__/" in lowered or lowered.endswith(".test.ts") or lowered.endswith("_test.py"):
        return "test"
    return "code"


def _purpose_for_files(files: list[str]) -> str:
    purposes = sorted({_purpose_for_path(path) for path in files})
    if len(purposes) == 1:
        return purposes[0]
    return "mixed"


def _group_key(component: str, risk: str, purpose: str) -> str:
    return f"{component}:{risk}:{purpose}"


def _group_reason(component: str, risk: str, purpose: str) -> str:
    return (
        f"Grouped as {component} {purpose} work with {risk} risk so review can keep "
        "unrelated commit stories separate before approval."
    )


def _story_for_group(component: str, risk: str, purpose: str) -> str:
    if risk in {"high", "blocked"}:
        return f"{_display_component(component)} safety hardening"
    if purpose == "soak":
        return f"{_display_component(component)} soak evidence"
    if purpose == "docs":
        return f"{_display_component(component)} docs/runbook update"
    if purpose == "test":
        return f"{_display_component(component)} test fix"
    if purpose == "mixed":
        return f"{_display_component(component)} reviewed change set"
    return f"{_display_component(component)} implementation update"


def _dirty_tree_message(component: str, risk: str, purpose: str) -> str:
    scope = _commit_scope(component)
    prefix = "docs" if purpose in {"docs", "soak"} else "test" if purpose == "test" else "feat"
    if purpose == "soak":
        return f"chore({scope}): record soak snapshot"
    if risk in {"high", "blocked"}:
        return f"chore({scope}): isolate {risk}-risk changes"
    return f"{prefix}({scope}): update {component.replace('-', ' ')}"


def _commit_scope(component: str) -> str:
    if component in {"blueprint-system", "cartographer-api-bridge"}:
        return "cartographer"
    return component.replace("_", "-") or "work"


def _display_component(component: str) -> str:
    if component == "unknown":
        return "Unknown file"
    return component.replace("-", " ").replace("_", " ").title()


def _max_risk(risks: list[str]) -> str:
    return max(risks, key=lambda risk: RISK_ORDER.get(risk, RISK_ORDER["unknown"]))


def _normalize_repo_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    if normalized.startswith("a/") or normalized.startswith("b/"):
        normalized = normalized[2:]
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized
