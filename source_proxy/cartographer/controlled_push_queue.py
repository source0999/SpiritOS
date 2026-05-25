from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from pathlib import Path
import subprocess
from typing import Any


PUSH_PROPOSAL_ONLY_PHASE = "Plan 9 Phase 9.2: Push proposal only"
HUMAN_APPROVED_DEDICATED_BRANCH_PUSH_PHASE = "Plan 9 Phase 9.2: Human-approved dedicated branch push blocked"
HUMAN_APPROVED_DEDICATED_BRANCH_PUSH_PERMISSION_PHRASE = (
    "Approve Cartographer Integrated Control Master Plan 9/10 Human Approved Dedicated Branch Push."
)
PUSH_RECEIPT_AND_ROLLBACK_GUIDANCE_PHASE = "Plan 9 Phase 9.3: Push receipt and rollback guidance"
ISOLATED_BRANCH_AUTO_PUSH_DECISION_GATE_PHASE = (
    "Plan 9 Phase 9.4: Auto-push promotion gate"
)

PUSH_PROPOSAL_REQUIRED_FIELDS: tuple[str, ...] = (
    "proposal_id",
    "remote",
    "branch",
    "upstream",
    "ahead_count",
    "behind_count",
    "local_commits",
    "commit_sha",
    "clean_status",
    "exact_file_lineage",
    "verification",
    "verification_receipts",
    "rollback_guidance",
    "approval_token_id",
    "risk",
    "created_at",
)

PUSH_PROPOSAL_RISK_LEVELS: tuple[str, ...] = (
    "low",
    "requires_review",
    "blocked",
)

PROTECTED_BASE_BRANCHES: tuple[str, ...] = ("main", "master", "trunk")

FORBIDDEN_PUSH_AUTHORITIES: tuple[str, ...] = (
    "push",
    "force_push",
    "tag_push",
    "main_branch_push",
    "merge",
    "branch_creation",
    "worktree_creation",
    "stash",
    "clean",
    "reset",
    "checkout",
    "command_execution",
    "approval_token_minting",
    "self_approval",
    "api_mutation",
    "durable_storage",
)


@dataclasses.dataclass(frozen=True)
class PushProposalVerification:
    status: str
    checks: tuple[str, ...]
    checked_at: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class PushProposal:
    proposal_id: str
    remote: str
    branch: str
    upstream: str
    ahead_count: int
    behind_count: int
    local_commits: tuple[str, ...]
    commit_sha: str
    clean_status: str
    exact_file_lineage: tuple[str, ...]
    verification: dict[str, Any]
    verification_receipts: tuple[str, ...]
    rollback_guidance: str
    approval_token_id: str
    risk: str
    created_at: str
    proposal_only: bool = True
    push_enabled: bool = False
    force_push_enabled: bool = False
    tag_push_enabled: bool = False
    merge_enabled: bool = False
    command_authority_granted: bool = False
    api_mutation_available: bool = False
    durable_storage_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class PushProposalValidation:
    status: str
    accepted: bool
    blocked: bool
    reasons: tuple[str, ...]
    proposal_id: str | None
    remote: str | None
    branch: str | None
    upstream: str | None
    ahead_count: int | None
    behind_count: int | None
    local_commits: tuple[str, ...] | None
    commit_sha: str | None
    clean_status: str | None
    exact_file_lineage: tuple[str, ...] | None
    verification_receipts: tuple[str, ...] | None
    approval_token_id: str | None
    risk: str | None
    validated_at: str
    proposal_receipt: dict[str, Any] | None
    proposal_only: bool = True
    push_enabled: bool = False
    force_push_enabled: bool = False
    tag_push_enabled: bool = False
    merge_enabled: bool = False
    command_authority_granted: bool = False
    api_mutation_available: bool = False
    durable_storage_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class HumanApprovedDedicatedBranchPushResult:
    phase: str
    status: str
    pushed: bool
    blocked: bool
    reasons: tuple[str, ...]
    proposal_id: str | None
    remote: str | None
    branch: str | None
    commit_sha: str | None
    clean_status: str | None
    exact_file_lineage: tuple[str, ...]
    approval_token_id: str | None
    pushed_at: str
    human_approval_required: bool = True
    exact_commit_sha_required: bool = True
    dedicated_branch_only: bool = True
    push_to_main_enabled: bool = False
    force_push_enabled: bool = False
    tag_push_enabled: bool = False
    merge_enabled: bool = False
    broad_push_enabled: bool = False
    branch_creation_enabled: bool = False
    worktree_enabled: bool = False
    stash_enabled: bool = False
    clean_enabled: bool = False
    reset_enabled: bool = False
    checkout_enabled: bool = False
    self_approval_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class PushReceiptAndRollbackGuidance:
    phase: str
    receipt_id: str
    status: str
    proposal_id: str | None
    remote: str | None
    branch: str | None
    commit_sha: str | None
    exact_file_lineage: tuple[str, ...]
    approval_token_id: str | None
    pushed_at: str | None
    generated_at: str
    rollback_guidance: str
    operator_next_steps: tuple[str, ...]
    safety_boundaries: tuple[str, ...]
    evidence: dict[str, Any]
    durable_storage_written: bool = False
    push_performed_by_receipt_builder: bool = False
    force_push_allowed: bool = False
    tag_push_allowed: bool = False
    main_branch_push_allowed: bool = False
    auto_push_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class IsolatedBranchAutoPushDecisionGate:
    phase: str
    decision_id: str
    status: str
    candidate: bool
    blocked: bool
    reasons: tuple[str, ...]
    proposal_id: str | None
    remote: str | None
    branch: str | None
    commit_sha: str | None
    exact_file_lineage: tuple[str, ...]
    approval_token_id: str | None
    decided_at: str
    required_inputs: tuple[str, ...]
    safety_boundaries: tuple[str, ...]
    next_authority_required: str
    auto_push_enabled: bool = False
    push_performed: bool = False
    push_to_main_enabled: bool = False
    force_push_enabled: bool = False
    tag_push_enabled: bool = False
    broad_push_enabled: bool = False
    self_approval_allowed: bool = False
    durable_storage_written: bool = False
    api_mutation_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_push_proposal_only_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Integrated Control Master Plan 9/10",
        "phase": PUSH_PROPOSAL_ONLY_PHASE,
        "status": "proposal-only",
        "required_fields": PUSH_PROPOSAL_REQUIRED_FIELDS,
        "risk_levels": PUSH_PROPOSAL_RISK_LEVELS,
        "forbidden_authorities": FORBIDDEN_PUSH_AUTHORITIES,
        "protected_base_branches": PROTECTED_BASE_BRANCHES,
        "proposal_only": True,
        "push_enabled": False,
        "force_push_enabled": False,
        "tag_push_enabled": False,
        "merge_enabled": False,
        "command_authority_granted": False,
        "api_mutation_available": False,
        "durable_storage_available": False,
        "proposal_receipt_available": True,
        "safe_next_action": "Preview exact push proposals only; keep push runtime blocked until later explicit promotion.",
    }


def validate_push_proposal(
    proposal: Any,
    *,
    expected_approval_token_id: str,
    now: datetime | None = None,
) -> PushProposalValidation:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []
    expected_approval_token_id = expected_approval_token_id.strip() if expected_approval_token_id else ""
    if not expected_approval_token_id:
        reasons.append("missing_expected_approval_token_id")

    payload = _proposal_payload(proposal)
    if payload is None:
        reasons.append("malformed_push_proposal")
        return _validation(
            reasons=reasons,
            current_time=current_time,
            proposal_id=None,
            remote=None,
            branch=None,
            upstream=None,
            ahead_count=None,
            behind_count=None,
            local_commits=None,
            commit_sha=None,
            clean_status=None,
            exact_file_lineage=None,
            verification_receipts=None,
            approval_token_id=None,
            risk=None,
        )

    for field in PUSH_PROPOSAL_REQUIRED_FIELDS:
        if field not in payload:
            reasons.append(f"missing_required_field:{field}")

    proposal_id = _string_field(payload, "proposal_id", reasons)
    remote = _string_field(payload, "remote", reasons)
    branch = _string_field(payload, "branch", reasons)
    upstream = _string_field(payload, "upstream", reasons)
    ahead_count = _int_field(payload, "ahead_count", reasons)
    behind_count = _int_field(payload, "behind_count", reasons)
    local_commits = _string_tuple_field(payload, "local_commits", reasons)
    commit_sha = _string_field(payload, "commit_sha", reasons)
    clean_status = _string_field(payload, "clean_status", reasons)
    exact_file_lineage = _exact_file_tuple_field(payload, "exact_file_lineage", reasons)
    verification = _verification(payload.get("verification"), reasons)
    verification_receipts = _exact_file_tuple_field(payload, "verification_receipts", reasons)
    rollback_guidance = _string_field(payload, "rollback_guidance", reasons)
    approval_token_id = _string_field(payload, "approval_token_id", reasons)
    risk = _string_field(payload, "risk", reasons)
    created_at = _datetime_field(payload, "created_at", reasons)

    if remote and remote != "origin":
        reasons.append("remote_must_be_exact_origin")
    if branch and branch in PROTECTED_BASE_BRANCHES:
        reasons.append("protected_base_branch_not_allowed_in_phase_9_2")
    if branch and not branch.startswith("cartographer/"):
        reasons.append("branch_must_be_dedicated_cartographer_branch")
    if upstream and branch and upstream != f"origin/{branch}":
        reasons.append("upstream_must_match_origin_branch")
    if ahead_count is not None and ahead_count < 0:
        reasons.append("ahead_count_must_not_be_negative")
    if behind_count is not None and behind_count != 0:
        reasons.append("behind_count_must_be_zero")
    if local_commits == ():
        reasons.append("missing_local_commits")
    if commit_sha and not _is_full_sha(commit_sha):
        reasons.append("commit_sha_must_be_full_hex_sha")
    if commit_sha and local_commits is not None and commit_sha not in local_commits:
        reasons.append("commit_sha_must_be_in_local_commits")
    if clean_status and clean_status != "clean":
        reasons.append("clean_status_required")
    if exact_file_lineage == ():
        reasons.append("missing_exact_file_lineage")
    if verification_receipts == ():
        reasons.append("missing_verification_receipts")
    if verification is not None and verification.get("status") != "passed":
        reasons.append("verification_not_passed")
    if rollback_guidance and "force" in rollback_guidance.lower():
        reasons.append("rollback_guidance_must_not_recommend_force")
    if approval_token_id and approval_token_id != expected_approval_token_id:
        reasons.append("wrong_approval_token")
    if risk and risk not in PUSH_PROPOSAL_RISK_LEVELS:
        reasons.append("unknown_push_risk")
    if risk == "blocked":
        reasons.append("blocked_risk_cannot_be_pushed")
    if created_at is not None and created_at > current_time:
        reasons.append("created_at_in_future")

    return _validation(
        reasons=reasons,
        current_time=current_time,
        proposal_id=proposal_id,
        remote=remote,
        branch=branch,
        upstream=upstream,
        ahead_count=ahead_count,
        behind_count=behind_count,
        local_commits=local_commits,
        commit_sha=commit_sha,
        clean_status=clean_status,
        exact_file_lineage=exact_file_lineage,
        verification_receipts=verification_receipts,
        approval_token_id=approval_token_id,
        risk=risk,
        verification_checks=_verification_checks(verification),
    )


def run_human_approved_dedicated_branch_push(
    proposal: Any,
    *,
    repo_root: str | Path,
    expected_approval_token_id: str,
    human_approval_phrase: str,
    now: datetime | None = None,
) -> HumanApprovedDedicatedBranchPushResult:
    current_time = now or datetime.now(UTC)
    validation = validate_push_proposal(
        proposal,
        expected_approval_token_id=expected_approval_token_id,
        now=current_time,
    )
    reasons = list(validation.reasons)
    if human_approval_phrase != HUMAN_APPROVED_DEDICATED_BRANCH_PUSH_PERMISSION_PHRASE:
        reasons.append("missing_exact_human_approval_phrase")

    root = Path(repo_root).resolve()
    if not root.exists() or not root.is_dir():
        reasons.append("invalid_repo_root")

    if reasons:
        return _human_push_result(
            reasons=reasons,
            current_time=current_time,
            validation=validation,
        )

    head = _git(root, "rev-parse", "--verify", "HEAD")
    if not head.ok or head.stdout.strip() != validation.commit_sha:
        reasons.append("commit_sha_mismatch")
        return _human_push_result(
            reasons=reasons,
            current_time=current_time,
            validation=validation,
        )

    status = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
    if not status.ok or status.stdout.strip():
        reasons.append("working_tree_not_clean")
        return _human_push_result(
            reasons=reasons,
            current_time=current_time,
            validation=validation,
        )

    remote = validation.remote or ""
    branch = validation.branch or ""
    commit_sha = validation.commit_sha or ""
    push = _git(root, "push", remote, f"{commit_sha}:refs/heads/{branch}")
    if not push.ok:
        reasons.append("dedicated_branch_push_failed")

    return _human_push_result(
        reasons=reasons,
        current_time=current_time,
        validation=validation,
    )


def build_push_receipt_and_rollback_guidance(
    push_result: Any,
    *,
    proposal: Any | None = None,
    now: datetime | None = None,
) -> PushReceiptAndRollbackGuidance:
    current_time = now or datetime.now(UTC)
    result_payload = _push_result_payload(push_result)
    proposal_payload = _proposal_payload(proposal) if proposal is not None else None

    proposal_id = _payload_string(result_payload, "proposal_id") or _payload_string(proposal_payload, "proposal_id")
    remote = _payload_string(result_payload, "remote") or _payload_string(proposal_payload, "remote")
    branch = _payload_string(result_payload, "branch") or _payload_string(proposal_payload, "branch")
    commit_sha = _payload_string(result_payload, "commit_sha") or _payload_string(proposal_payload, "commit_sha")
    approval_token_id = _payload_string(result_payload, "approval_token_id") or _payload_string(proposal_payload, "approval_token_id")
    pushed_at = _payload_string(result_payload, "pushed_at")
    exact_file_lineage = _payload_tuple(result_payload, "exact_file_lineage") or _payload_tuple(proposal_payload, "exact_file_lineage")
    pushed = bool(result_payload.get("pushed")) if isinstance(result_payload, dict) else False
    status = "pushed" if pushed else "blocked"
    reasons = _payload_tuple(result_payload, "reasons")
    rollback_guidance = _rollback_guidance_for_receipt(
        status=status,
        remote=remote,
        branch=branch,
        commit_sha=commit_sha,
        reasons=reasons,
    )
    return PushReceiptAndRollbackGuidance(
        phase=PUSH_RECEIPT_AND_ROLLBACK_GUIDANCE_PHASE,
        receipt_id=_push_receipt_id(proposal_id=proposal_id, commit_sha=commit_sha, status=status),
        status=status,
        proposal_id=proposal_id,
        remote=remote,
        branch=branch,
        commit_sha=commit_sha,
        exact_file_lineage=exact_file_lineage,
        approval_token_id=approval_token_id,
        pushed_at=pushed_at,
        generated_at=_format_utc(current_time),
        rollback_guidance=rollback_guidance,
        operator_next_steps=_operator_next_steps(status=status),
        safety_boundaries=(
            "do_not_force_push",
            "do_not_push_tags",
            "do_not_push_main_master_or_trunk",
            "do_not_merge_or_rebase_automatically",
            "require_new_human_approval_for_followup_push",
        ),
        evidence={
            "result_status": result_payload.get("status") if isinstance(result_payload, dict) else None,
            "result_reasons": reasons,
            "exact_file_lineage": exact_file_lineage,
            "proposal_status": proposal_payload.get("status") if isinstance(proposal_payload, dict) else None,
        },
    )


def build_isolated_branch_auto_push_decision_gate(
    proposal: Any,
    *,
    expected_approval_token_id: str,
    soak_passed: bool,
    receipt_available: bool,
    rollback_guidance_available: bool,
    policy_approval_id: str,
    now: datetime | None = None,
) -> IsolatedBranchAutoPushDecisionGate:
    current_time = now or datetime.now(UTC)
    validation = validate_push_proposal(
        proposal,
        expected_approval_token_id=expected_approval_token_id,
        now=current_time,
    )
    reasons = list(validation.reasons)
    if not soak_passed:
        reasons.append("auto_push_requires_completed_soak")
    if not receipt_available:
        reasons.append("auto_push_requires_push_receipt")
    if not rollback_guidance_available:
        reasons.append("auto_push_requires_rollback_guidance")
    if not policy_approval_id.strip():
        reasons.append("auto_push_requires_explicit_policy_approval")
    if validation.branch and not validation.branch.startswith("cartographer/"):
        reasons.append("auto_push_requires_isolated_cartographer_branch")
    if validation.remote and validation.remote != "origin":
        reasons.append("auto_push_requires_exact_origin_remote")
    if validation.clean_status and validation.clean_status != "clean":
        reasons.append("auto_push_requires_clean_status")

    candidate = not reasons
    reasons.append("auto_push_runtime_not_promoted_in_plan_9")
    blocked_reasons = tuple(dict.fromkeys(reasons))
    return IsolatedBranchAutoPushDecisionGate(
        phase=ISOLATED_BRANCH_AUTO_PUSH_DECISION_GATE_PHASE,
        decision_id=_auto_push_decision_id(
            proposal_id=validation.proposal_id,
            commit_sha=validation.commit_sha,
            status="candidate" if candidate else "blocked",
        ),
        status="blocked_pending_later_promotion" if candidate else "blocked",
        candidate=candidate,
        blocked=True,
        reasons=blocked_reasons,
        proposal_id=validation.proposal_id,
        remote=validation.remote,
        branch=validation.branch,
        commit_sha=validation.commit_sha,
        exact_file_lineage=validation.exact_file_lineage or (),
        approval_token_id=validation.approval_token_id,
        decided_at=_format_utc(current_time),
        required_inputs=(
            "passed_soak_window",
            "push_receipt_available",
            "rollback_guidance_available",
            "exact_origin_remote",
            "isolated_cartographer_branch",
            "full_commit_sha",
            "clean_status",
            "explicit_policy_approval_id",
        ),
        safety_boundaries=(
            "decision_gate_does_not_push",
            "auto_push_runtime_remains_disabled_in_plan_9",
            "plan_9_auto_push_stays_blocked",
            "no_push_to_main_master_or_trunk",
            "no_force_push",
            "no_tag_push",
            "no_broad_push",
            "no_self_approval",
        ),
        next_authority_required="A later explicit promotion plan is required before any isolated branch auto-push runtime can exist.",
    )


def _validation(
    *,
    reasons: list[str],
    current_time: datetime,
    proposal_id: str | None,
    remote: str | None,
    branch: str | None,
    upstream: str | None,
    ahead_count: int | None,
    behind_count: int | None,
    local_commits: tuple[str, ...] | None,
    commit_sha: str | None,
    clean_status: str | None,
    exact_file_lineage: tuple[str, ...] | None,
    verification_receipts: tuple[str, ...] | None,
    approval_token_id: str | None,
    risk: str | None,
    verification_checks: tuple[str, ...] = (),
) -> PushProposalValidation:
    blocked_reasons = tuple(dict.fromkeys(reasons))
    accepted = not blocked_reasons
    validated_at = _format_utc(current_time)
    return PushProposalValidation(
        status="accepted" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        reasons=blocked_reasons,
        proposal_id=proposal_id,
        remote=remote,
        branch=branch,
        upstream=upstream,
        ahead_count=ahead_count,
        behind_count=behind_count,
        local_commits=local_commits,
        commit_sha=commit_sha,
        clean_status=clean_status,
        exact_file_lineage=exact_file_lineage,
        verification_receipts=verification_receipts,
        approval_token_id=approval_token_id,
        risk=risk,
        validated_at=validated_at,
        proposal_receipt=_push_proposal_receipt(
            status="accepted" if accepted else "blocked",
            reasons=blocked_reasons,
            proposal_id=proposal_id,
            remote=remote,
            branch=branch,
            upstream=upstream,
            ahead_count=ahead_count,
            behind_count=behind_count,
            local_commits=local_commits,
            commit_sha=commit_sha,
            clean_status=clean_status,
            exact_file_lineage=exact_file_lineage,
            verification_checks=verification_checks,
            verification_receipts=verification_receipts,
            approval_token_id=approval_token_id,
            risk=risk,
            validated_at=validated_at,
        ),
    )


def _proposal_payload(proposal: Any) -> dict[str, Any] | None:
    if isinstance(proposal, PushProposal):
        return proposal.to_dict()
    if isinstance(proposal, dict):
        return proposal
    return None


def _push_result_payload(push_result: Any) -> dict[str, Any]:
    if isinstance(push_result, HumanApprovedDedicatedBranchPushResult):
        return push_result.to_dict()
    if isinstance(push_result, dict):
        return push_result
    return {}


def _payload_string(payload: dict[str, Any] | None, field: str) -> str | None:
    if not isinstance(payload, dict):
        return None
    value = payload.get(field)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _payload_tuple(payload: dict[str, Any] | None, field: str) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        return ()
    value = payload.get(field)
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item.strip() for item in value if isinstance(item, str) and item.strip())


def _string_field(payload: dict[str, Any], field: str, reasons: list[str]) -> str | None:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        reasons.append(f"invalid_{field}")
        return None
    return value.strip()


def _int_field(payload: dict[str, Any], field: str, reasons: list[str]) -> int | None:
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        reasons.append(f"invalid_{field}")
        return None
    return value


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


def _verification(value: Any, reasons: list[str]) -> dict[str, Any] | None:
    if isinstance(value, PushProposalVerification):
        value = value.to_dict()
    if not isinstance(value, dict):
        reasons.append("invalid_verification")
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


def _push_proposal_receipt(
    *,
    status: str,
    reasons: tuple[str, ...],
    proposal_id: str | None,
    remote: str | None,
    branch: str | None,
    upstream: str | None,
    ahead_count: int | None,
    behind_count: int | None,
    local_commits: tuple[str, ...] | None,
    commit_sha: str | None,
    clean_status: str | None,
    exact_file_lineage: tuple[str, ...] | None,
    verification_checks: tuple[str, ...],
    verification_receipts: tuple[str, ...] | None,
    approval_token_id: str | None,
    risk: str | None,
    validated_at: str,
) -> dict[str, Any]:
    file_lineage = exact_file_lineage or ()
    commits = local_commits or ()
    return {
        "schema_version": "cartographer.push_proposal_receipt.v1",
        "proposal_id": proposal_id,
        "status": status,
        "reasons": reasons,
        "remote": remote,
        "branch": branch,
        "upstream": upstream,
        "ahead_count": ahead_count,
        "behind_count": behind_count,
        "local_commits": commits,
        "local_commit_count": len(commits),
        "commit_sha": commit_sha,
        "clean_status": clean_status,
        "exact_file_lineage": file_lineage,
        "exact_file_lineage_count": len(file_lineage),
        "verification_checks": verification_checks,
        "verification_receipts": verification_receipts or (),
        "approval_token_id": approval_token_id,
        "risk": risk,
        "validated_at": validated_at,
        "proposal_only": True,
        "push_performed": False,
        "force_push_performed": False,
        "tag_push_performed": False,
        "merge_performed": False,
        "branch_or_worktree_created": False,
        "command_execution_performed": False,
        "git_mutation_performed": False,
        "approval_token_consumed": False,
        "self_approval_allowed": False,
        "provider_call_performed": False,
        "durable_storage_performed": False,
    }


def _datetime_field(payload: dict[str, Any], field: str, reasons: list[str]) -> datetime | None:
    parsed = _datetime_value(payload.get(field))
    if parsed is None:
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


def _is_full_sha(value: str) -> bool:
    return len(value) == 40 and all(character in "0123456789abcdefABCDEF" for character in value)


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


def _human_push_result(
    *,
    reasons: list[str],
    current_time: datetime,
    validation: PushProposalValidation,
) -> HumanApprovedDedicatedBranchPushResult:
    blocked_reasons = tuple(dict.fromkeys(reasons))
    pushed = not blocked_reasons
    return HumanApprovedDedicatedBranchPushResult(
        phase=HUMAN_APPROVED_DEDICATED_BRANCH_PUSH_PHASE,
        status="pushed" if pushed else "blocked",
        pushed=pushed,
        blocked=not pushed,
        reasons=blocked_reasons,
        proposal_id=validation.proposal_id,
        remote=validation.remote,
        branch=validation.branch,
        commit_sha=validation.commit_sha,
        clean_status=validation.clean_status,
        exact_file_lineage=validation.exact_file_lineage or (),
        approval_token_id=validation.approval_token_id,
        pushed_at=_format_utc(current_time),
    )


def _push_receipt_id(*, proposal_id: str | None, commit_sha: str | None, status: str) -> str:
    proposal_part = proposal_id or "unknown-proposal"
    sha_part = commit_sha[:12] if commit_sha else "unknown-sha"
    return f"push-receipt-{proposal_part}-{sha_part}-{status}"


def _auto_push_decision_id(*, proposal_id: str | None, commit_sha: str | None, status: str) -> str:
    proposal_part = proposal_id or "unknown-proposal"
    sha_part = commit_sha[:12] if commit_sha else "unknown-sha"
    return f"auto-push-decision-{proposal_part}-{sha_part}-{status}"


def _rollback_guidance_for_receipt(
    *,
    status: str,
    remote: str | None,
    branch: str | None,
    commit_sha: str | None,
    reasons: tuple[str, ...],
) -> str:
    if status != "pushed":
        return (
            "No remote rollback is required because the push did not complete. "
            f"Resolve blockers first: {', '.join(reasons) if reasons else 'unknown_blocker'}."
        )
    return (
        f"Remote {remote or 'unknown-remote'} branch {branch or 'unknown-branch'} now points at "
        f"{commit_sha or 'unknown-sha'}. If this push is wrong, do not force-push or delete the "
        "branch automatically; revert locally, run verification again, and request a new exact "
        "human-approved push proposal."
    )


def _operator_next_steps(*, status: str) -> tuple[str, ...]:
    if status == "pushed":
        return (
            "review_remote_branch",
            "open_pull_request_if_appropriate",
            "record_any_followup_as_new_exact_proposal",
        )
    return (
        "review_blockers",
        "do_not_retry_push_without_new_exact_approval",
        "rerun_required_verification_after_fixes",
    )


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
