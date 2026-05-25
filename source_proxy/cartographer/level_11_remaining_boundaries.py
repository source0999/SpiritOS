from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class CartographerLevel11BoundaryPacket:
    level: str
    title: str
    status: str
    mode: str
    action_type: str
    target_files: tuple[str, ...]
    allowed_files: tuple[str, ...]
    forbidden_files: tuple[str, ...]
    would_write_files: bool
    would_execute_commands: bool
    authority_granted: bool
    blocked: bool
    blocked_reasons: tuple[str, ...]
    next_increment: str


def build_level_11_docs_only_apply_dry_run_packet(
    *,
    target_docs_files: tuple[str, ...],
    allowed_files: tuple[str, ...],
    forbidden_files: tuple[str, ...],
) -> CartographerLevel11BoundaryPacket:
    reasons = _common_scope_reasons(target_docs_files, allowed_files, forbidden_files)
    if any(not path.startswith("docs/") for path in target_docs_files):
        reasons += ["non_docs_target_in_scope"]

    return _packet(
        level="11.6",
        title="Approved Docs-Only Apply Runtime Dry Run",
        status="docs-only-apply-dry-run-only",
        action_type="approved_docs_only_apply",
        target_files=target_docs_files,
        allowed_files=allowed_files,
        forbidden_files=forbidden_files,
        blocked_reasons=reasons,
        next_increment="Cartographer Level 11.7: Controlled Local Verification Execution Dry Run",
    )


def build_level_11_local_verification_execution_dry_run_packet(
    *,
    command: tuple[str, ...],
    allowed_files: tuple[str, ...],
    forbidden_files: tuple[str, ...],
) -> CartographerLevel11BoundaryPacket:
    reasons: list[str] = []
    if not command:
        reasons += ["missing_command"]
    allowed_command_heads = {"git", "grep", "test"}
    if command and command[0] not in allowed_command_heads:
        reasons += ["command_class_not_preview_allowed"]
    forbidden_terms = {"add", "commit", "push", "merge", "checkout", "stash", "clean", "rm"}
    if any(part in forbidden_terms for part in command):
        reasons += ["mutating_or_git_authority_command_forbidden"]
    if not allowed_files:
        reasons += ["missing_allowed_files"]
    if forbidden_files:
        reasons += ["forbidden_files_declared"]

    return _packet(
        level="11.7",
        title="Controlled Local Verification Execution Dry Run",
        status="local-verification-execution-dry-run-only",
        action_type="controlled_local_verification_execution",
        target_files=command,
        allowed_files=allowed_files,
        forbidden_files=forbidden_files,
        blocked_reasons=reasons,
        next_increment="Cartographer Level 11.8: Rollback And Closeout Receipt Dry Run",
    )


def build_level_11_rollback_closeout_dry_run_packet(
    *,
    closeout_receipt_file: str,
    rollback_reference: str,
    verification_reference: str,
    allowed_files: tuple[str, ...],
    forbidden_files: tuple[str, ...],
) -> CartographerLevel11BoundaryPacket:
    target_files = (closeout_receipt_file,) if closeout_receipt_file else ()
    reasons = _common_scope_reasons(target_files, allowed_files, forbidden_files)
    if not closeout_receipt_file:
        reasons += ["missing_closeout_receipt_file"]
    if closeout_receipt_file and not closeout_receipt_file.startswith("docs/"):
        reasons += ["closeout_receipt_file_outside_docs"]
    if not rollback_reference:
        reasons += ["missing_rollback_reference"]
    if not verification_reference:
        reasons += ["missing_verification_reference"]

    return _packet(
        level="11.8",
        title="Rollback And Closeout Receipt Dry Run",
        status="rollback-closeout-dry-run-only",
        action_type="approved_closeout_receipt_write",
        target_files=target_files,
        allowed_files=allowed_files,
        forbidden_files=forbidden_files,
        blocked_reasons=reasons,
        next_increment="Cartographer Level 11.9: Fail-Closed Safety Regression Gate And Level 12 Access Check",
    )


def build_level_11_closeout_level_12_access_check() -> dict[str, object]:
    return {
        "level": "11.9",
        "title": "Fail-Closed Safety Regression Gate And Level 12 Access Check",
        "status": "level-11-runtime-dry-run-closeout",
        "level_12_access": "requires_explicit_human_verification",
        "authority_granted": False,
        "write_authority_granted": False,
        "local_execution_authority_granted": False,
        "workflow_execution_authority_granted": False,
        "worker_orchestration_authority_granted": False,
        "safe_task_queue_execution_authority_granted": False,
        "autonomy_granted": False,
        "protected_lanes_remain_locked": (
            "proxy_ui_makeover",
            "coding_ui_implementation_wiring",
            "source_proxy_stress_testing",
            "codex_adapter_lane",
        ),
        "next_increment": "Cartographer Level 12.1: Workflow State Schema Runtime Dry Run",
    }


def _common_scope_reasons(
    target_files: tuple[str, ...],
    allowed_files: tuple[str, ...],
    forbidden_files: tuple[str, ...],
) -> list[str]:
    reasons: list[str] = []
    if not target_files:
        reasons += ["missing_target_files"]
    if not allowed_files:
        reasons += ["missing_allowed_files"]
    if not set(target_files).issubset(set(allowed_files)):
        reasons += ["target_files_outside_allowed_files"]
    if set(target_files).intersection(forbidden_files):
        reasons += ["target_files_intersect_forbidden_files"]
    if any(path.startswith(("src/", "source_proxy/api/", "source_proxy/verification/")) for path in target_files):
        reasons += ["protected_path_in_scope"]
    return reasons


def _packet(
    *,
    level: str,
    title: str,
    status: str,
    action_type: str,
    target_files: tuple[str, ...],
    allowed_files: tuple[str, ...],
    forbidden_files: tuple[str, ...],
    blocked_reasons: list[str],
    next_increment: str,
) -> CartographerLevel11BoundaryPacket:
    return CartographerLevel11BoundaryPacket(
        level=level,
        title=title,
        status=status,
        mode="dry_run",
        action_type=action_type,
        target_files=target_files,
        allowed_files=allowed_files,
        forbidden_files=forbidden_files,
        would_write_files=False,
        would_execute_commands=False,
        authority_granted=False,
        blocked=bool(blocked_reasons),
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
        next_increment=next_increment,
    )
