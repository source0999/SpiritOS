from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from pathlib import Path
import subprocess
from typing import Any


LOCAL_COMMIT_PROPOSAL_MODEL_PHASE = "Plan 9 Phase 9.1: Commit proposal model"
HUMAN_APPROVED_LOCAL_COMMIT_PHASE = "Plan 9 Phase 9.1: Human-approved local commit"
HUMAN_APPROVED_LOCAL_COMMIT_PERMISSION_PHRASE = (
    "Approve Cartographer Integrated Control Master Plan 9/10 Human Approved Local Commit."
)
AUTO_SAFE_LOCAL_COMMIT_PHASE = "Plan 9 Phase 9.1: Auto local commit blocked"
AUTO_SAFE_LOCAL_COMMIT_PREFIXES: tuple[str, ...] = (
    "docs/cartographer-live-receipts/",
    "docs/cartographer-receipts/",
    "docs/cartographer-evidence/",
    "docs/cartographer-daily-driver-autonomy-plan-",
)

LOCAL_COMMIT_PROPOSAL_STATUSES: tuple[str, ...] = (
    "proposed",
    "blocked",
    "approved_later_phase",
)

LOCAL_COMMIT_DIRTY_TREE_EXPECTATIONS: tuple[str, ...] = (
    "exact_files_only",
    "clean_except_exact_files",
)

LOCAL_COMMIT_REQUIRED_FIELDS: tuple[str, ...] = (
    "proposal_id",
    "exact_file_list",
    "exact_commit_message",
    "verification_result",
    "rollback_command",
    "expected_head",
    "branch",
    "dirty_tree_expectation",
    "blocked_files",
    "status",
    "task_ids",
    "receipt_paths",
    "approval_token_id",
    "created_at",
)

FORBIDDEN_LOCAL_COMMIT_AUTHORITIES: tuple[str, ...] = (
    "git_add",
    "git_add_all",
    "commit",
    "push",
    "merge",
    "branch",
    "worktree",
    "stash",
    "clean",
    "reset",
    "checkout",
    "file_write",
    "command_execution",
    "approval_token_minting",
    "self_approval",
    "api_mutation",
    "durable_storage",
)


@dataclasses.dataclass(frozen=True)
class LocalCommitVerificationResult:
    status: str
    checks: tuple[str, ...]
    checked_at: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class LocalCommitProposal:
    proposal_id: str
    exact_file_list: tuple[str, ...]
    exact_commit_message: str
    verification_result: dict[str, Any]
    rollback_command: str
    expected_head: str
    branch: str
    dirty_tree_expectation: str
    blocked_files: tuple[str, ...]
    status: str
    task_ids: tuple[str, ...]
    receipt_paths: tuple[str, ...]
    approval_token_id: str
    created_at: str
    model_only: bool = True
    proposal_only: bool = True
    commit_enabled: bool = False
    staging_enabled: bool = False
    push_enabled: bool = False
    command_authority_granted: bool = False
    git_mutation_authority_granted: bool = False
    file_write_authority_granted: bool = False
    api_mutation_available: bool = False
    durable_storage_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class LocalCommitProposalValidation:
    status: str
    accepted: bool
    blocked: bool
    reasons: tuple[str, ...]
    proposal_id: str | None
    exact_file_list: tuple[str, ...] | None
    exact_commit_message: str | None
    rollback_command: str | None
    verification_checks: tuple[str, ...]
    expected_head: str | None
    branch: str | None
    dirty_tree_expectation: str | None
    blocked_files: tuple[str, ...] | None
    proposal_status: str | None
    task_ids: tuple[str, ...] | None
    receipt_paths: tuple[str, ...] | None
    approval_token_id: str | None
    validated_at: str
    proposal_receipt: dict[str, Any] | None
    model_only: bool = True
    proposal_only: bool = True
    commit_enabled: bool = False
    staging_enabled: bool = False
    push_enabled: bool = False
    command_authority_granted: bool = False
    git_mutation_authority_granted: bool = False
    file_write_authority_granted: bool = False
    api_mutation_available: bool = False
    durable_storage_available: bool = False
    no_execution_guarantee: str = (
        "Plan 9 Phase 9.1 validates local commit proposals as data only. It "
        "does not stage files, invoke staging commands, commit, push, merge, branch, "
        "create worktrees, stash, clean, reset, checkout, write files, run "
        "commands, mint approval tokens, self-approve, expose mutation APIs, "
        "or persist proposals."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class HumanApprovedLocalCommitResult:
    phase: str
    status: str
    committed: bool
    blocked: bool
    reasons: tuple[str, ...]
    proposal_id: str | None
    exact_file_list: tuple[str, ...]
    exact_commit_message: str | None
    expected_head: str | None
    new_head: str | None
    rollback_command: str | None
    task_ids: tuple[str, ...]
    receipt_paths: tuple[str, ...]
    approval_token_id: str | None
    committed_at: str
    human_approval_required: bool = True
    exact_file_list_only: bool = True
    broad_staging_allowed: bool = False
    push_enabled: bool = False
    branch_enabled: bool = False
    worktree_enabled: bool = False
    stash_enabled: bool = False
    clean_enabled: bool = False
    reset_enabled: bool = False
    checkout_enabled: bool = False
    api_mutation_available: bool = False
    self_approval_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class AutoSafeLocalCommitResult:
    phase: str
    status: str
    auto_committed: bool
    blocked: bool
    reasons: tuple[str, ...]
    proposal_id: str | None
    exact_file_list: tuple[str, ...]
    exact_commit_message: str | None
    expected_head: str | None
    new_head: str | None
    rollback_command: str | None
    task_ids: tuple[str, ...]
    receipt_paths: tuple[str, ...]
    approval_token_id: str | None
    committed_at: str
    soak_promoted: bool
    exact_file_list_only: bool = True
    safe_docs_evidence_receipts_only: bool = True
    source_files_allowed: bool = False
    broad_staging_allowed: bool = False
    push_enabled: bool = False
    branch_enabled: bool = False
    worktree_enabled: bool = False
    stash_enabled: bool = False
    clean_enabled: bool = False
    reset_enabled: bool = False
    checkout_enabled: bool = False
    api_mutation_available: bool = False
    self_approval_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_local_commit_proposal_model_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Integrated Control Master Plan 9/10",
        "phase": LOCAL_COMMIT_PROPOSAL_MODEL_PHASE,
        "status": "model-only",
        "proposal_statuses": LOCAL_COMMIT_PROPOSAL_STATUSES,
        "dirty_tree_expectations": LOCAL_COMMIT_DIRTY_TREE_EXPECTATIONS,
        "required_fields": LOCAL_COMMIT_REQUIRED_FIELDS,
        "forbidden_authorities": FORBIDDEN_LOCAL_COMMIT_AUTHORITIES,
        "proposal_only": True,
        "commit_enabled": False,
        "staging_enabled": False,
        "push_enabled": False,
        "command_authority_granted": False,
        "git_mutation_authority_granted": False,
        "file_write_authority_granted": False,
        "api_mutation_available": False,
        "durable_storage_available": False,
        "proposal_receipt_available": True,
        "safe_next_action": "Model exact commit proposals only; require exact human approval before local commit test-fixture execution.",
    }


def validate_local_commit_proposal(
    proposal: Any,
    *,
    expected_approval_token_id: str,
    now: datetime | None = None,
) -> LocalCommitProposalValidation:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []
    expected_approval_token_id = expected_approval_token_id.strip() if expected_approval_token_id else ""
    if not expected_approval_token_id:
        reasons.append("missing_expected_approval_token_id")

    payload = _proposal_payload(proposal)
    if payload is None:
        reasons.append("malformed_local_commit_proposal")
        return _validation(
            reasons=reasons,
            current_time=current_time,
            proposal_id=None,
            exact_file_list=None,
            exact_commit_message=None,
            rollback_command=None,
            verification_result=None,
            expected_head=None,
            branch=None,
            dirty_tree_expectation=None,
            blocked_files=None,
            proposal_status=None,
            task_ids=None,
            receipt_paths=None,
            approval_token_id=None,
        )

    for field in LOCAL_COMMIT_REQUIRED_FIELDS:
        if field not in payload:
            reasons.append(f"missing_required_field:{field}")

    proposal_id = _string_field(payload, "proposal_id", reasons)
    exact_file_list = _exact_file_tuple_field(payload, "exact_file_list", reasons)
    exact_commit_message = _string_field(payload, "exact_commit_message", reasons)
    verification_result = _verification_result(payload.get("verification_result"), reasons)
    rollback_command = _string_field(payload, "rollback_command", reasons)
    expected_head = _string_field(payload, "expected_head", reasons)
    branch = _string_field(payload, "branch", reasons)
    dirty_tree_expectation = _string_field(payload, "dirty_tree_expectation", reasons)
    blocked_files = _exact_file_tuple_field(payload, "blocked_files", reasons)
    proposal_status = _string_field(payload, "status", reasons)
    task_ids = _string_tuple_field(payload, "task_ids", reasons)
    receipt_paths = _exact_file_tuple_field(payload, "receipt_paths", reasons)
    approval_token_id = _string_field(payload, "approval_token_id", reasons)
    created_at = _datetime_field(payload, "created_at", reasons, required=True)

    if exact_file_list == ():
        reasons.append("missing_exact_file_list")
    if receipt_paths == ():
        reasons.append("missing_receipt_paths")
    if task_ids == ():
        reasons.append("missing_task_ids")
    if proposal_status and proposal_status not in LOCAL_COMMIT_PROPOSAL_STATUSES:
        reasons.append("unknown_proposal_status")
    if dirty_tree_expectation and dirty_tree_expectation not in LOCAL_COMMIT_DIRTY_TREE_EXPECTATIONS:
        reasons.append("unknown_dirty_tree_expectation")
    if proposal_status == "approved_later_phase":
        reasons.append("approval_status_not_allowed_in_phase_9_1")
    if approval_token_id and approval_token_id != expected_approval_token_id:
        reasons.append("wrong_approval_token")
    if exact_commit_message and "\n" in exact_commit_message:
        reasons.append("commit_message_must_be_exact_single_line")
    if exact_commit_message and exact_commit_message.lower().strip() in {"wip", "update", "changes"}:
        reasons.append("commit_message_too_vague")
    if rollback_command and not rollback_command.startswith("git revert "):
        reasons.append("rollback_command_must_be_git_revert")
    if expected_head and len(expected_head) < 7:
        reasons.append("expected_head_too_short")
    if verification_result is not None and verification_result.get("status") != "passed":
        reasons.append("verification_not_passed")
    if exact_file_list is not None and receipt_paths is not None:
        missing_receipt_paths = set(receipt_paths) - set(exact_file_list)
        if missing_receipt_paths:
            reasons.append("receipt_paths_must_be_in_exact_file_list")
    if exact_file_list is not None and blocked_files is not None:
        blocked_overlap = set(exact_file_list).intersection(blocked_files)
        if blocked_overlap:
            reasons.append("blocked_file_in_exact_file_list")
    if created_at is not None and created_at > current_time:
        reasons.append("created_at_in_future")

    return _validation(
        reasons=reasons,
        current_time=current_time,
        proposal_id=proposal_id,
        exact_file_list=exact_file_list,
        exact_commit_message=exact_commit_message,
        rollback_command=rollback_command,
        verification_result=verification_result,
        expected_head=expected_head,
        branch=branch,
        dirty_tree_expectation=dirty_tree_expectation,
        blocked_files=blocked_files,
        proposal_status=proposal_status,
        task_ids=task_ids,
        receipt_paths=receipt_paths,
        approval_token_id=approval_token_id,
    )


def run_human_approved_local_commit(
    proposal: Any,
    *,
    repo_root: str | Path,
    expected_approval_token_id: str,
    human_approval_phrase: str,
    now: datetime | None = None,
) -> HumanApprovedLocalCommitResult:
    current_time = now or datetime.now(UTC)
    validation = validate_local_commit_proposal(
        proposal,
        expected_approval_token_id=expected_approval_token_id,
        now=current_time,
    )
    reasons = list(validation.reasons)
    if human_approval_phrase != HUMAN_APPROVED_LOCAL_COMMIT_PERMISSION_PHRASE:
        reasons.append("missing_exact_human_approval_phrase")

    root = Path(repo_root).resolve()
    if not root.exists() or not root.is_dir():
        reasons.append("invalid_repo_root")

    exact_file_list = validation.exact_file_list or ()
    for exact_file in exact_file_list:
        if _path_escapes_repo(root, exact_file):
            reasons.append("exact_file_outside_repo")

    if reasons:
        return _human_commit_result(
            reasons=reasons,
            current_time=current_time,
            validation=validation,
            exact_file_list=exact_file_list,
            new_head=None,
        )

    reasons, new_head = _execute_exact_local_commit(root, validation, exact_file_list, reasons)
    return _human_commit_result(
        reasons=reasons,
        current_time=current_time,
        validation=validation,
        exact_file_list=exact_file_list,
        new_head=new_head,
    )


def run_auto_safe_local_commit(
    proposal: Any,
    *,
    repo_root: str | Path,
    expected_approval_token_id: str,
    soak_promoted: bool,
    now: datetime | None = None,
) -> AutoSafeLocalCommitResult:
    current_time = now or datetime.now(UTC)
    validation = validate_local_commit_proposal(
        proposal,
        expected_approval_token_id=expected_approval_token_id,
        now=current_time,
    )
    reasons = list(validation.reasons)
    reasons.append("auto_local_commit_requires_exact_human_approval")
    if not soak_promoted:
        reasons.append("auto_local_commit_requires_soak_promotion")

    root = Path(repo_root).resolve()
    if not root.exists() or not root.is_dir():
        reasons.append("invalid_repo_root")

    exact_file_list = validation.exact_file_list or ()
    for exact_file in exact_file_list:
        if _path_escapes_repo(root, exact_file):
            reasons.append("exact_file_outside_repo")
        if not _is_auto_safe_local_commit_file(exact_file):
            reasons.append("unsafe_auto_commit_file_class")

    return _auto_commit_result(
        reasons=reasons,
        current_time=current_time,
        validation=validation,
        exact_file_list=exact_file_list,
        new_head=None,
        soak_promoted=soak_promoted,
    )


def _validation(
    *,
    reasons: list[str],
    current_time: datetime,
    proposal_id: str | None,
    exact_file_list: tuple[str, ...] | None,
    exact_commit_message: str | None,
    rollback_command: str | None,
    verification_result: dict[str, Any] | None,
    expected_head: str | None,
    branch: str | None,
    dirty_tree_expectation: str | None,
    blocked_files: tuple[str, ...] | None,
    proposal_status: str | None,
    task_ids: tuple[str, ...] | None,
    receipt_paths: tuple[str, ...] | None,
    approval_token_id: str | None,
) -> LocalCommitProposalValidation:
    blocked_reasons = tuple(_dedupe(reasons))
    accepted = not blocked_reasons
    verification_checks = _verification_checks(verification_result)
    return LocalCommitProposalValidation(
        status="accepted" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        reasons=blocked_reasons,
        proposal_id=proposal_id,
        exact_file_list=exact_file_list,
        exact_commit_message=exact_commit_message,
        rollback_command=rollback_command,
        verification_checks=verification_checks,
        expected_head=expected_head,
        branch=branch,
        dirty_tree_expectation=dirty_tree_expectation,
        blocked_files=blocked_files,
        proposal_status=proposal_status,
        task_ids=task_ids,
        receipt_paths=receipt_paths,
        approval_token_id=approval_token_id,
        validated_at=_format_utc(current_time),
        proposal_receipt=_local_commit_proposal_receipt(
            status="accepted" if accepted else "blocked",
            reasons=blocked_reasons,
            proposal_id=proposal_id,
            exact_file_list=exact_file_list,
            exact_commit_message=exact_commit_message,
            rollback_command=rollback_command,
            verification_checks=verification_checks,
            expected_head=expected_head,
            branch=branch,
            dirty_tree_expectation=dirty_tree_expectation,
            blocked_files=blocked_files,
            task_ids=task_ids,
            receipt_paths=receipt_paths,
            approval_token_id=approval_token_id,
            validated_at=_format_utc(current_time),
        ),
    )


def _proposal_payload(proposal: Any) -> dict[str, Any] | None:
    if isinstance(proposal, LocalCommitProposal):
        return proposal.to_dict()
    if isinstance(proposal, dict):
        return proposal
    return None


def _verification_result(value: Any, reasons: list[str]) -> dict[str, Any] | None:
    if isinstance(value, LocalCommitVerificationResult):
        value = value.to_dict()
    if not isinstance(value, dict):
        reasons.append("invalid_verification_result")
        return None
    status = value.get("status")
    checks = value.get("checks")
    checked_at = value.get("checked_at")
    if not isinstance(status, str) or not status.strip():
        reasons.append("invalid_verification_status")
    if not isinstance(checks, (list, tuple)) or not checks:
        reasons.append("missing_verification_checks")
    elif any(not isinstance(check, str) or not check.strip() for check in checks):
        reasons.append("invalid_verification_check")
    if _datetime_value(checked_at) is None:
        reasons.append("invalid_verification_checked_at")
    return value


def _verification_checks(value: dict[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(value, dict):
        return ()
    checks = value.get("checks")
    if not isinstance(checks, (list, tuple)):
        return ()
    return tuple(check.strip() for check in checks if isinstance(check, str) and check.strip())


def _local_commit_proposal_receipt(
    *,
    status: str,
    reasons: tuple[str, ...],
    proposal_id: str | None,
    exact_file_list: tuple[str, ...] | None,
    exact_commit_message: str | None,
    rollback_command: str | None,
    verification_checks: tuple[str, ...],
    expected_head: str | None,
    branch: str | None,
    dirty_tree_expectation: str | None,
    blocked_files: tuple[str, ...] | None,
    task_ids: tuple[str, ...] | None,
    receipt_paths: tuple[str, ...] | None,
    approval_token_id: str | None,
    validated_at: str,
) -> dict[str, Any]:
    exact_files = exact_file_list or ()
    return {
        "schema_version": "cartographer.local_commit_proposal_receipt.v1",
        "proposal_id": proposal_id,
        "status": status,
        "reasons": reasons,
        "exact_file_list": exact_files,
        "exact_file_count": len(exact_files),
        "exact_commit_message": exact_commit_message,
        "verification_checks": verification_checks,
        "rollback_command": rollback_command,
        "expected_head": expected_head,
        "branch": branch,
        "dirty_tree_expectation": dirty_tree_expectation,
        "blocked_files": blocked_files or (),
        "task_ids": task_ids or (),
        "receipt_paths": receipt_paths or (),
        "approval_token_id": approval_token_id,
        "validated_at": validated_at,
        "proposal_only": True,
        "staging_performed": False,
        "commit_performed": False,
        "push_performed": False,
        "branch_or_worktree_created": False,
        "broad_staging_allowed": False,
        "command_execution_performed": False,
        "git_mutation_performed": False,
        "file_write_performed": False,
        "approval_token_consumed": False,
        "self_approval_allowed": False,
        "durable_storage_performed": False,
    }


def _string_field(payload: dict[str, Any], field: str, reasons: list[str]) -> str | None:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        reasons.append(f"invalid_{field}")
        return None
    return value.strip()


def _string_tuple_field(payload: dict[str, Any], field: str, reasons: list[str]) -> tuple[str, ...] | None:
    value = payload.get(field)
    if not isinstance(value, (list, tuple)):
        reasons.append(f"invalid_{field}")
        return None
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            reasons.append(f"invalid_{field}_entry")
            continue
        items.append(item.strip())
    if len(set(items)) != len(items):
        reasons.append(f"duplicate_{field}_entry")
    return tuple(items)


def _exact_file_tuple_field(payload: dict[str, Any], field: str, reasons: list[str]) -> tuple[str, ...] | None:
    value = payload.get(field)
    if not isinstance(value, (list, tuple)):
        reasons.append(f"invalid_{field}")
        return None
    files: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            reasons.append(f"invalid_{field}_entry")
            continue
        path = item.strip()
        if _is_broad_file_scope(path):
            reasons.append(f"broad_{field}_entry")
        files.append(path)
    if len(set(files)) != len(files):
        reasons.append(f"duplicate_{field}_entry")
    return tuple(files)


def _is_broad_file_scope(path: str) -> bool:
    return (
        path.startswith("/")
        or path.endswith("/")
        or path in {".", ".."}
        or path.startswith("../")
        or "/../" in path
        or "\\" in path
        or "*" in path
        or "?" in path
        or "[" in path
        or "]" in path
    )


def _path_escapes_repo(root: Path, exact_file: str) -> bool:
    try:
        resolved = (root / exact_file).resolve()
        resolved.relative_to(root)
    except ValueError:
        return True
    return False


def _is_auto_safe_local_commit_file(exact_file: str) -> bool:
    return exact_file.endswith(".md") and exact_file.startswith(AUTO_SAFE_LOCAL_COMMIT_PREFIXES)


@dataclasses.dataclass(frozen=True)
class _GitResult:
    ok: bool
    stdout: str
    stderr: str


def _git(root: Path, *args: str) -> _GitResult:
    completed = subprocess.run(
        ("git", *args),
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return _GitResult(
        ok=completed.returncode == 0,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _execute_exact_local_commit(
    root: Path,
    validation: LocalCommitProposalValidation,
    exact_file_list: tuple[str, ...],
    reasons: list[str],
) -> tuple[list[str], str | None]:
    head = _git(root, "rev-parse", "--verify", "HEAD")
    if not head.ok:
        reasons.append("cannot_read_expected_head")
        return reasons, None
    current_head = head.stdout.strip()
    if current_head != validation.expected_head:
        reasons.append("expected_head_mismatch")
        return reasons, None

    stage_result = _git(root, "add", "--", *exact_file_list)
    if not stage_result.ok:
        reasons.append("exact_file_stage_failed")
        return reasons, None

    staged_result = _git(root, "diff", "--cached", "--name-only")
    if not staged_result.ok:
        reasons.append("cannot_verify_staged_exact_file_list")
        return reasons, None
    staged_files = tuple(line.strip() for line in staged_result.stdout.splitlines() if line.strip())
    if tuple(sorted(staged_files)) != tuple(sorted(exact_file_list)):
        reasons.append("staged_files_do_not_match_exact_file_list")
        return reasons, None

    commit_result = _git(root, "commit", "-m", validation.exact_commit_message or "")
    if not commit_result.ok:
        reasons.append("local_commit_failed")
        return reasons, None

    new_head_result = _git(root, "rev-parse", "--verify", "HEAD")
    if not new_head_result.ok:
        reasons.append("cannot_read_new_head")
        return reasons, None
    return reasons, new_head_result.stdout.strip()


def _human_commit_result(
    *,
    reasons: list[str],
    current_time: datetime,
    validation: LocalCommitProposalValidation,
    exact_file_list: tuple[str, ...],
    new_head: str | None,
) -> HumanApprovedLocalCommitResult:
    blocked_reasons = tuple(_dedupe(reasons))
    committed = not blocked_reasons and new_head is not None
    return HumanApprovedLocalCommitResult(
        phase=HUMAN_APPROVED_LOCAL_COMMIT_PHASE,
        status="committed" if committed else "blocked",
        committed=committed,
        blocked=not committed,
        reasons=blocked_reasons,
        proposal_id=validation.proposal_id,
        exact_file_list=exact_file_list,
        exact_commit_message=validation.exact_commit_message,
        expected_head=validation.expected_head,
        new_head=new_head,
        rollback_command=f"git revert {new_head}" if committed else None,
        task_ids=validation.task_ids or (),
        receipt_paths=validation.receipt_paths or (),
        approval_token_id=validation.approval_token_id,
        committed_at=_format_utc(current_time),
    )


def _auto_commit_result(
    *,
    reasons: list[str],
    current_time: datetime,
    validation: LocalCommitProposalValidation,
    exact_file_list: tuple[str, ...],
    new_head: str | None,
    soak_promoted: bool,
) -> AutoSafeLocalCommitResult:
    blocked_reasons = tuple(_dedupe(reasons))
    committed = not blocked_reasons and new_head is not None
    return AutoSafeLocalCommitResult(
        phase=AUTO_SAFE_LOCAL_COMMIT_PHASE,
        status="committed" if committed else "blocked",
        auto_committed=committed,
        blocked=not committed,
        reasons=blocked_reasons,
        proposal_id=validation.proposal_id,
        exact_file_list=exact_file_list,
        exact_commit_message=validation.exact_commit_message,
        expected_head=validation.expected_head,
        new_head=new_head,
        rollback_command=f"git revert {new_head}" if committed else None,
        task_ids=validation.task_ids or (),
        receipt_paths=validation.receipt_paths or (),
        approval_token_id=validation.approval_token_id,
        committed_at=_format_utc(current_time),
        soak_promoted=soak_promoted,
    )


def _datetime_field(
    payload: dict[str, Any],
    field: str,
    reasons: list[str],
    *,
    required: bool,
) -> datetime | None:
    value = payload.get(field)
    parsed = _datetime_value(value)
    if parsed is None and required:
        reasons.append(f"invalid_{field}")
    return parsed


def _datetime_value(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def _dedupe(reasons: list[str]) -> list[str]:
    return list(dict.fromkeys(reasons))


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
