from __future__ import annotations

import dataclasses
from datetime import UTC, datetime


APPROVAL_TOKEN_ACTION_TYPES: tuple[str, ...] = (
    "approved_receipt_write",
    "approved_evidence_write",
    "approved_docs_only_apply",
    "controlled_local_verification_execution",
    "approved_rollback_execution",
    "approved_closeout_receipt_write",
)

PROTECTED_APPROVAL_PATH_PREFIXES: tuple[str, ...] = (
    "src/",
    "src/components/coding/",
    "src/lib/coding/",
    "src/app/coding/",
    "source_proxy/api/codex_adapter.py",
    "source_proxy/codex/",
    "source_proxy/testing/runner.py",
    "source_proxy/verification/",
)


@dataclasses.dataclass(frozen=True)
class CartographerLevel11ApprovalToken:
    token_id: str
    run_id: str
    action_type: str
    target_files: tuple[str, ...]
    allowed_files: tuple[str, ...]
    forbidden_files: tuple[str, ...]
    expires_at: str
    max_attempts: int
    rollback_command: str
    verification_command: str
    operator_id: str
    created_at: str
    used_at: str | None = None
    revoked: bool = False


@dataclasses.dataclass(frozen=True)
class CartographerLevel11ApprovalTokenValidation:
    valid_for_dry_run: bool
    action_authority_granted: bool
    write_authority_granted: bool
    local_execution_authority_granted: bool
    blocked_reasons: tuple[str, ...]
    next_required_human_step: str


def build_level_11_approval_token_schema_preview() -> dict[str, object]:
    return {
        "level": "11.2",
        "title": "Approval Token Runtime Schema And Validation Dry Run",
        "status": "schema-validation-dry-run-only",
        "authority_granted": False,
        "write_authority_granted": False,
        "local_execution_authority_granted": False,
        "token_issuance_enabled": False,
        "token_consumption_enabled": False,
        "supported_action_types": APPROVAL_TOKEN_ACTION_TYPES,
        "required_fields": tuple(field.name for field in dataclasses.fields(CartographerLevel11ApprovalToken)),
        "next_increment": "Cartographer Level 11.3: Event Ledger Runtime Model Dry Run",
    }


def validate_level_11_approval_token_dry_run(
    token: CartographerLevel11ApprovalToken,
    *,
    requested_run_id: str,
    requested_action_type: str,
    requested_target_files: tuple[str, ...],
    operator_id: str,
    now: datetime | None = None,
) -> CartographerLevel11ApprovalTokenValidation:
    reasons: list[str] = []
    current_time = now or datetime.now(UTC)

    if not token.token_id:
        reasons.append("missing_token_id")
    if not token.run_id or token.run_id != requested_run_id:
        reasons.append("run_id_mismatch")
    if token.action_type not in APPROVAL_TOKEN_ACTION_TYPES:
        reasons.append("unsupported_action_type")
    if token.action_type != requested_action_type:
        reasons.append("action_type_mismatch")
    if not requested_target_files or token.target_files != requested_target_files:
        reasons.append("target_files_mismatch")
    if not token.allowed_files:
        reasons.append("missing_allowed_files")
    if not set(requested_target_files).issubset(set(token.allowed_files)):
        reasons.append("target_files_outside_allowed_files")
    if set(requested_target_files).intersection(token.forbidden_files):
        reasons.append("target_files_intersect_forbidden_files")
    if any(_is_protected_path(path) for path in (*requested_target_files, *token.target_files)):
        reasons.append("protected_path_in_scope")
    if _is_expired(token.expires_at, current_time):
        reasons.append("token_expired_or_malformed")
    if token.max_attempts < 1:
        reasons.append("invalid_max_attempts")
    if not token.rollback_command:
        reasons.append("missing_rollback_metadata")
    if not token.verification_command:
        reasons.append("missing_verification_metadata")
    if not token.operator_id or token.operator_id == operator_id:
        reasons.append("self_approval_or_missing_external_operator")
    if token.used_at is not None:
        reasons.append("token_already_used")
    if token.revoked:
        reasons.append("token_revoked")

    return CartographerLevel11ApprovalTokenValidation(
        valid_for_dry_run=not reasons,
        action_authority_granted=False,
        write_authority_granted=False,
        local_execution_authority_granted=False,
        blocked_reasons=tuple(reasons),
        next_required_human_step="operator_review_required",
    )


def _is_expired(expires_at: str, now: datetime) -> bool:
    try:
        parsed = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    return parsed <= now


def _is_protected_path(path: str) -> bool:
    normalized = path.strip().lstrip("/")
    return any(
        normalized == prefix.removesuffix("/") or normalized.startswith(prefix)
        for prefix in PROTECTED_APPROVAL_PATH_PREFIXES
    )
