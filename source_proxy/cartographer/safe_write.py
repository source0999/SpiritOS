from __future__ import annotations

import dataclasses
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from source_proxy.cartographer.approval_token_consumption import (
    FORBIDDEN_ACTION_CLASSES,
    preview_approval_token_consumption as _preview_approval_token_consumption,
)
from source_proxy.cartographer.verification_runner import (
    build_verification_result_receipt_summary as _build_verification_result_receipt_summary,
)

SAFE_WRITE_PHASE = "Plan 5 Phase 5.1: Safe Write Classes"
SAFE_WRITE_VERIFICATION_RECEIPT_PHASE = (
    "Plan 6 Phase 6.2: Safe Write Verification Integration"
)
SAFE_WRITE_ACTION_CLASS = "safe_write"
SAFE_WRITE_TRUST_TIER = "tier-1"
SAFE_WRITE_REQUIRED_LANE_ID = "cartographer"
SAFE_WRITE_REQUIRED_LANE_OWNER = "cartographer"
RECEIPT_SUMMARY_LIMIT = 400
REQUIRED_SAFE_WRITE_PROOF_FIELDS: tuple[str, ...] = (
    "active_lane_id",
    "lane_owner",
    "lane_dirty_overlap_status",
    "rollback",
    "verification",
    "expected_head",
    "expected_dirty_tree",
)
REQUIRED_SAFE_WRITE_RECEIPT_FIELDS: tuple[str, ...] = (
    "before_state",
    "target_file",
    "bytes_written",
    "verification_result",
    "rollback_guidance",
    "approval_token_id",
    "event_ids",
)
REQUIRED_VERIFICATION_RECEIPT_FIELDS: tuple[str, ...] = (
    "command_id",
    "argv",
    "exit_code",
    "stdout_summary",
    "stderr_summary",
    "timeout_seconds",
    "status",
    "passed",
    "blocked",
    "reasons",
)
SAFE_WRITE_ALLOWED_PREFIXES: tuple[str, ...] = (
    "docs/",
    "docs/cartographer-live-evidence/",
    "docs/cartographer-live-receipts/",
)

PROTECTED_PATH_PREFIXES: tuple[str, ...] = (
    "source_proxy/",
    "src/app/",
    "src/components/",
    "src/lib/",
    "coding/",
    "/coding/",
    "dashboard/",
    "generated/",
    "public/",
    "assets/",
    "media/",
    "tests/",
    ".next/",
    "node_modules/",
    ".git/",
    "scout/",
    "Scout/",
)

PROTECTED_EXACT_FILES: tuple[str, ...] = (
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "next.config.ts",
    "allowed-dev-origins.ts",
    ".env",
    ".env.local",
    ".env.production",
    "source_proxy/api/cartographer.py",
    "src/app/map/page.tsx",
)

GLOB_MARKERS: tuple[str, ...] = ("*", "?", "[", "]", "{", "}")
PATH_TRAVERSAL_MARKERS: tuple[str, ...] = ("../", "/..", "..\\", "\\..")
MEDIA_FILE_EXTENSIONS: tuple[str, ...] = (
    ".apng",
    ".avif",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".mp3",
    ".mp4",
    ".ogg",
    ".png",
    ".svg",
    ".wav",
    ".webm",
    ".webp",
)


@dataclasses.dataclass(frozen=True)
class SafeWritePreview:
    status: str
    eligible: bool
    blocked: bool
    reasons: tuple[str, ...]
    requested_actor: str
    requested_scope: dict[str, str]
    requested_action_class: str
    requested_files: tuple[str, ...]
    approval_preview: dict[str, Any]
    expected_head: str | None
    current_head: str | None
    kill_switch_active: bool
    preview_only: bool = True
    authority_granted: bool = False
    write_authority_granted: bool = False
    command_authority_granted: bool = False
    workflow_authority_granted: bool = False
    queue_authority_granted: bool = False
    git_authority_granted: bool = False
    safe_write_available: bool = True
    no_mutation_guarantee: str = (
        "Plan 5 Phase 5.1 safe write preview does not mutate files, run "
        "commands, enqueue work, execute workflows, or perform version-control "
        "actions."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class SafeWriteResult:
    status: str
    written: bool
    blocked: bool
    reasons: tuple[str, ...]
    target_file: str
    bytes_written: int
    before_exists: bool
    before_size_bytes: int = 0
    before_sha256: str | None = None
    after_sha256: str | None = None
    rollback_guidance: str = ""
    receipt_metadata_required: bool = True
    rollback_receipt_available: bool = False
    receipt_closeout_ready: bool = False
    safe_write_complete: bool = False
    approval_token_id: str | None = None
    event_ids: tuple[str, ...] = ()
    safe_write_available: bool = True
    authority_granted: bool = False
    write_authority_granted: bool = False
    command_authority_granted: bool = False
    workflow_authority_granted: bool = False
    queue_authority_granted: bool = False
    git_authority_granted: bool = False
    no_git_or_execution_guarantee: str = (
        "Safe write only writes the exact approved file content. It does not "
        "stage, commit, push, branch, create worktrees, stash, clean, reset, "
        "checkout, run commands, execute workflows, or execute queues."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class SafeWriteReceiptCloseoutPreview:
    status: str
    closeout_ready: bool
    blocked: bool
    reasons: tuple[str, ...]
    target_file: str
    bytes_written: int
    before_state: dict[str, Any] | None
    verification_status: str | None
    rollback_guidance: str | None
    approval_token_id: str | None
    event_ids: tuple[str, ...]
    preview_only: bool = True
    authority_granted: bool = False
    write_authority_granted: bool = False
    command_authority_granted: bool = False
    workflow_authority_granted: bool = False
    queue_authority_granted: bool = False
    git_authority_granted: bool = False
    no_closeout_without_receipt_guarantee: str = (
        "Safe write closeout is a metadata preview only. Missing rollback, "
        "verification, approval token, event ids, or before-state receipt data "
        "keeps the write from being marked complete."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_safe_write_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Integrated Control Master Plan 5",
        "phase": SAFE_WRITE_PHASE,
        "status": "safe-write-service-available",
        "safe_write_available": True,
        "preview_available": True,
        "authority_granted": False,
        "write_authority_granted": False,
        "command_authority_granted": False,
        "workflow_authority_granted": False,
        "queue_authority_granted": False,
        "git_authority_granted": False,
        "forbidden_action_classes": FORBIDDEN_ACTION_CLASSES,
        "safe_write_action_class": SAFE_WRITE_ACTION_CLASS,
        "safe_write_trust_tier": SAFE_WRITE_TRUST_TIER,
        "safe_write_required_lane_id": SAFE_WRITE_REQUIRED_LANE_ID,
        "safe_write_required_lane_owner": SAFE_WRITE_REQUIRED_LANE_OWNER,
        "safe_write_allowed_prefixes": SAFE_WRITE_ALLOWED_PREFIXES,
        "protected_path_prefixes": PROTECTED_PATH_PREFIXES,
        "protected_exact_files": PROTECTED_EXACT_FILES,
        "blocked_media_extensions": MEDIA_FILE_EXTENSIONS,
        "required_receipt_fields": REQUIRED_SAFE_WRITE_RECEIPT_FIELDS,
        "required_proof_fields": REQUIRED_SAFE_WRITE_PROOF_FIELDS,
        "required_verification_receipt_fields": REQUIRED_VERIFICATION_RECEIPT_FIELDS,
        "receipt_metadata_required": True,
        "safe_next_action": "Use only with exact human-approved file scope.",
    }


def build_safe_write_verification_receipt_content(
    *,
    title: str,
    safe_write_result: Any,
    verification_result: Any,
    generated_at: datetime,
) -> str:
    safe_write_data = _result_to_dict(safe_write_result)
    verification_data = _result_to_dict(verification_result)
    argv = verification_data.get("argv", ())
    if isinstance(argv, (list, tuple)):
        argv_text = " ".join(str(part) for part in argv)
    else:
        argv_text = str(argv)

    lines = [
        f"# {title.strip() or 'Cartographer Safe Write Verification Receipt'}",
        "",
        f"Plan phase: {SAFE_WRITE_VERIFICATION_RECEIPT_PHASE}",
        f"Generated at: {_format_timestamp(generated_at)}",
        "",
        "## Safe Write",
        "",
        f"- status: `{safe_write_data.get('status', '')}`",
        f"- target file: `{safe_write_data.get('target_file', '')}`",
        f"- written: `{safe_write_data.get('written', False)}`",
        f"- blocked: `{safe_write_data.get('blocked', False)}`",
        f"- bytes written: `{safe_write_data.get('bytes_written', 0)}`",
        "",
        "## Verification",
        "",
        f"- command: `{argv_text}`",
        f"- command id: `{verification_data.get('matched_command_id', '')}`",
        f"- status: `{verification_data.get('status', '')}`",
        f"- executed: `{verification_data.get('executed', False)}`",
        f"- blocked: `{verification_data.get('blocked', False)}`",
        f"- exit code: `{verification_data.get('exit_code', None)}`",
        f"- timeout seconds: `{verification_data.get('timeout_seconds', '')}`",
        f"- reasons: `{', '.join(str(reason) for reason in verification_data.get('reasons', ()))}`",
        "",
        "## Output Summary",
        "",
        "### stdout",
        "",
        "```text",
        _summarize_output(verification_data.get("stdout", "")),
        "```",
        "",
        "### stderr",
        "",
        "```text",
        _summarize_output(verification_data.get("stderr", "")),
        "```",
        "",
        "## Authority Boundary",
        "",
        "- command authority granted: `false`",
        "- workflow authority granted: `false`",
        "- queue authority granted: `false`",
        "- git mutation authority granted: `false`",
        "- commit, push, branch, worktree, stash, clean, reset, and checkout remain unavailable.",
        "",
    ]
    return "\n".join(lines)


def build_safe_write_receipt_metadata(
    *,
    safe_write_result: Any,
    verification_result: Any,
    before_state: dict[str, Any],
    rollback_guidance: str,
    approval_token_id: str,
    event_ids: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    safe_write_data = _result_to_dict(safe_write_result)
    return {
        "before_state": before_state if isinstance(before_state, dict) else {},
        "target_file": safe_write_data.get("target_file", ""),
        "bytes_written": safe_write_data.get("bytes_written", 0),
        "verification_result": _build_verification_result_receipt_summary(
            verification_result,
        ),
        "rollback_guidance": rollback_guidance,
        "approval_token_id": approval_token_id,
        "event_ids": list(event_ids) if isinstance(event_ids, (list, tuple)) else [],
    }


def preview_safe_write_receipt_closeout(
    safe_write_result: Any,
    receipt_metadata: dict[str, Any] | None,
) -> SafeWriteReceiptCloseoutPreview:
    safe_write_data = _result_to_dict(safe_write_result)
    metadata = receipt_metadata if isinstance(receipt_metadata, dict) else {}
    reasons: list[str] = []

    if not isinstance(receipt_metadata, dict):
        reasons.append("missing_receipt_metadata")
    for field in REQUIRED_SAFE_WRITE_RECEIPT_FIELDS:
        if field not in metadata:
            reasons.append(f"missing_receipt_field:{field}")

    before_state = metadata.get("before_state")
    if "before_state" in metadata and not isinstance(before_state, dict):
        reasons.append("malformed_receipt_field:before_state")

    target_file = _normalize_single_file(str(metadata.get("target_file", "")))
    if "target_file" in metadata and not target_file:
        reasons.append("malformed_receipt_field:target_file")

    bytes_written = metadata.get("bytes_written")
    if "bytes_written" in metadata and not isinstance(bytes_written, int):
        reasons.append("malformed_receipt_field:bytes_written")

    verification_result = metadata.get("verification_result")
    verification_data = _result_to_dict(verification_result)
    if "verification_result" in metadata and not verification_data:
        reasons.append("malformed_receipt_field:verification_result")
    verification_status = verification_data.get("status")
    for field in REQUIRED_VERIFICATION_RECEIPT_FIELDS:
        if verification_data and field not in verification_data:
            reasons.append(f"missing_verification_receipt_field:{field}")
    if verification_data:
        for field in ("command_id", "status"):
            if not _normalize_context_string(verification_data.get(field)):
                reasons.append(f"malformed_verification_receipt_field:{field}")
        if not isinstance(verification_data.get("argv"), (list, tuple)):
            reasons.append("malformed_verification_receipt_field:argv")
        for field in ("stdout_summary", "stderr_summary"):
            if field in verification_data and not isinstance(verification_data.get(field), str):
                reasons.append(f"malformed_verification_receipt_field:{field}")
    if verification_data and verification_status != "passed":
        reasons.append("verification_not_passed")
    if verification_data and verification_data.get("passed") is not True:
        reasons.append("verification_not_passed")
    if verification_data and verification_data.get("blocked") is True:
        reasons.append("verification_blocked")

    rollback_guidance = metadata.get("rollback_guidance")
    normalized_rollback = rollback_guidance.strip() if isinstance(rollback_guidance, str) else ""
    if "rollback_guidance" in metadata and not normalized_rollback:
        reasons.append("malformed_receipt_field:rollback_guidance")

    approval_token_id = metadata.get("approval_token_id")
    normalized_approval_token_id = (
        approval_token_id.strip() if isinstance(approval_token_id, str) else ""
    )
    if "approval_token_id" in metadata and not normalized_approval_token_id:
        reasons.append("malformed_receipt_field:approval_token_id")

    event_ids = _normalize_requested_files(metadata.get("event_ids", ()))
    if "event_ids" in metadata and not event_ids:
        reasons.append("malformed_receipt_field:event_ids")

    if safe_write_data.get("written") is not True:
        reasons.append("write_not_completed")
    if safe_write_data.get("blocked") is True:
        reasons.append("write_blocked")

    result_target_file = _normalize_single_file(str(safe_write_data.get("target_file", "")))
    if target_file and result_target_file and target_file != result_target_file:
        reasons.append("receipt_target_mismatch")

    result_bytes = safe_write_data.get("bytes_written")
    if isinstance(bytes_written, int) and isinstance(result_bytes, int):
        if bytes_written != result_bytes:
            reasons.append("receipt_bytes_written_mismatch")

    reasons = _dedupe(reasons)
    closeout_ready = not reasons
    return SafeWriteReceiptCloseoutPreview(
        status="ready" if closeout_ready else "blocked",
        closeout_ready=closeout_ready,
        blocked=not closeout_ready,
        reasons=tuple(reasons),
        target_file=target_file or result_target_file,
        bytes_written=bytes_written if isinstance(bytes_written, int) else 0,
        before_state=before_state if isinstance(before_state, dict) else None,
        verification_status=verification_status if isinstance(verification_status, str) else None,
        rollback_guidance=normalized_rollback or None,
        approval_token_id=normalized_approval_token_id or None,
        event_ids=event_ids,
    )


def preview_safe_write_request(
    payload: Any,
    *,
    requested_actor: str,
    requested_scope: dict[str, str],
    requested_action_class: str,
    requested_files: list[str] | tuple[str, ...],
    consumption_context: dict[str, Any] | None,
    current_head: str | None = None,
    dirty_tree_matches_expected: bool = True,
    kill_switch_active: bool = False,
    now: datetime | None = None,
) -> SafeWritePreview:
    approval_preview = _preview_approval_token_consumption(
        payload,
        requested_actor=requested_actor,
        requested_scope=requested_scope,
        requested_action_class=requested_action_class,
        requested_files=requested_files,
        consumption_context=consumption_context,
        current_head=current_head,
        kill_switch_active=kill_switch_active,
        now=now,
    )

    normalized_files = _normalize_requested_files(requested_files)
    reasons = [f"approval:{reason}" for reason in approval_preview.reasons]
    reasons.extend(_path_policy_reasons(normalized_files, consumption_context))
    reasons.extend(_proof_policy_reasons(consumption_context))

    if requested_action_class != SAFE_WRITE_ACTION_CLASS:
        reasons.append("wrong_action_class")

    context = consumption_context if isinstance(consumption_context, dict) else {}
    if context.get("trust_tier") != SAFE_WRITE_TRUST_TIER:
        reasons.append("wrong_trust_tier")

    if not dirty_tree_matches_expected:
        reasons.append("dirty_tree_mismatch")

    reasons = _dedupe(reasons)
    eligible = approval_preview.eligible and not reasons

    return SafeWritePreview(
        status="eligible" if eligible else "blocked",
        eligible=eligible,
        blocked=not eligible,
        reasons=tuple(reasons),
        requested_actor=approval_preview.requested_actor,
        requested_scope=approval_preview.requested_scope,
        requested_action_class=approval_preview.requested_action_class,
        requested_files=normalized_files,
        approval_preview=approval_preview.to_dict(),
        expected_head=approval_preview.expected_head,
        current_head=approval_preview.current_head,
        kill_switch_active=approval_preview.kill_switch_active,
    )


def execute_safe_write_request(
    payload: Any,
    *,
    requested_actor: str,
    requested_scope: dict[str, str],
    target_file: str,
    content: str,
    consumption_context: dict[str, Any] | None,
    workspace_root: Path,
    current_head: str | None = None,
    dirty_tree_matches_expected: bool = True,
    kill_switch_active: bool = False,
    now: datetime | None = None,
) -> SafeWriteResult:
    preview = preview_safe_write_request(
        payload,
        requested_actor=requested_actor,
        requested_scope=requested_scope,
        requested_action_class=SAFE_WRITE_ACTION_CLASS,
        requested_files=[target_file],
        consumption_context=consumption_context,
        current_head=current_head,
        dirty_tree_matches_expected=dirty_tree_matches_expected,
        kill_switch_active=kill_switch_active,
        now=now,
    )
    if not isinstance(content, str):
        return _blocked_result(target_file, (*preview.reasons, "malformed_content"))
    if preview.blocked:
        return _blocked_result(target_file, preview.reasons)

    normalized_target = _normalize_single_file(target_file)
    resolved_root = workspace_root.resolve()
    resolved_target = (resolved_root / normalized_target).resolve()
    if not _is_within_root(resolved_target, resolved_root):
        return _blocked_result(normalized_target, (*preview.reasons, "target_outside_workspace"))

    before_exists = resolved_target.exists()
    before_bytes = resolved_target.read_bytes() if before_exists else b""
    resolved_target.parent.mkdir(parents=True, exist_ok=True)
    resolved_target.write_text(content, encoding="utf-8")
    after_bytes = content.encode("utf-8")
    return SafeWriteResult(
        status="written",
        written=True,
        blocked=False,
        reasons=(),
        target_file=normalized_target,
        bytes_written=len(after_bytes),
        before_exists=before_exists,
        before_size_bytes=len(before_bytes),
        before_sha256=_sha256_bytes(before_bytes) if before_exists else None,
        after_sha256=_sha256_bytes(after_bytes),
        rollback_guidance=_rollback_guidance(
            target_file=normalized_target,
            before_exists=before_exists,
        ),
    )


def _path_policy_reasons(
    requested_files: tuple[str, ...],
    consumption_context: dict[str, Any] | None,
) -> list[str]:
    reasons: list[str] = []
    context = consumption_context if isinstance(consumption_context, dict) else {}
    allowed_files = set(_normalize_requested_files(context.get("exact_allowed_files", ())))
    forbidden_files = set(_normalize_requested_files(context.get("exact_forbidden_files", ())))

    for file_path in requested_files:
        if file_path.startswith("/"):
            reasons.append("absolute_path_blocked")
        if _has_path_traversal(file_path):
            reasons.append("path_traversal_blocked")
        if _has_broad_glob(file_path):
            reasons.append("broad_glob_blocked")
        if _is_broad_directory_target(file_path):
            reasons.append("broad_directory_blocked")
        if _is_media_write(file_path):
            reasons.append("media_write_blocked")
        if _is_protected_path(file_path):
            reasons.append("protected_path_blocked")
        if file_path.startswith("docs/") and file_path not in allowed_files:
            reasons.append("unapproved_docs_blocked")
        if file_path in forbidden_files:
            reasons.append("forbidden_file_blocked")
        if not _is_allowed_safe_write_path(file_path, allowed_files):
            reasons.append("unsafe_write_class_blocked")

    return reasons


def _proof_policy_reasons(consumption_context: dict[str, Any] | None) -> list[str]:
    reasons: list[str] = []
    context = consumption_context if isinstance(consumption_context, dict) else {}

    for field in REQUIRED_SAFE_WRITE_PROOF_FIELDS:
        if field not in context:
            reasons.append(f"missing_safe_write_proof:{field}")

    active_lane_id = _normalize_context_string(context.get("active_lane_id"))
    lane_owner = _normalize_context_string(context.get("lane_owner"))
    dirty_overlap_status = _normalize_context_string(context.get("lane_dirty_overlap_status"))
    rollback = _normalize_context_string(context.get("rollback"))
    verification = _normalize_context_string(context.get("verification"))

    if "active_lane_id" in context and active_lane_id != SAFE_WRITE_REQUIRED_LANE_ID:
        reasons.append("wrong_active_lane")
    if "lane_owner" in context and lane_owner != SAFE_WRITE_REQUIRED_LANE_OWNER:
        reasons.append("wrong_lane_owner")
    if "lane_dirty_overlap_status" in context and dirty_overlap_status != "clear":
        reasons.append("dirty_overlap_not_clear")
    if "rollback" in context and not rollback:
        reasons.append("missing_rollback_guidance")
    if "verification" in context and not verification:
        reasons.append("missing_verification_plan")

    return reasons


def _normalize_requested_files(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        text = item.strip().replace("\\", "/")
        if text:
            normalized.append(text)
    return tuple(normalized)


def _has_path_traversal(file_path: str) -> bool:
    return file_path == ".." or any(marker in file_path for marker in PATH_TRAVERSAL_MARKERS)


def _has_broad_glob(file_path: str) -> bool:
    return any(marker in file_path for marker in GLOB_MARKERS)


def _is_broad_directory_target(file_path: str) -> bool:
    return file_path in {"docs", "docs/"} or file_path.endswith("/")


def _is_media_write(file_path: str) -> bool:
    return file_path.lower().endswith(MEDIA_FILE_EXTENSIONS)


def _is_protected_path(file_path: str) -> bool:
    if file_path in PROTECTED_EXACT_FILES:
        return True
    return any(file_path.startswith(prefix) for prefix in PROTECTED_PATH_PREFIXES)


def _is_allowed_safe_write_path(file_path: str, allowed_files: set[str]) -> bool:
    if file_path not in allowed_files:
        return False
    if any(file_path.startswith(prefix) for prefix in SAFE_WRITE_ALLOWED_PREFIXES):
        return True
    return file_path.startswith("docs/")


def _normalize_single_file(value: str) -> str:
    files = _normalize_requested_files([value])
    return files[0] if files else ""


def _normalize_context_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _is_within_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _rollback_guidance(*, target_file: str, before_exists: bool) -> str:
    if before_exists:
        return (
            f"Restore {target_file} from the operator-reviewed before-state "
            "content and verify the recorded before_sha256."
        )
    return f"Delete {target_file} after operator approval to restore the absent before-state."


def _blocked_result(target_file: str, reasons: tuple[str, ...]) -> SafeWriteResult:
    return SafeWriteResult(
        status="blocked",
        written=False,
        blocked=True,
        reasons=tuple(_dedupe(list(reasons))),
        target_file=_normalize_single_file(target_file),
        bytes_written=0,
        before_exists=False,
    )


def _result_to_dict(value: Any) -> dict[str, Any]:
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict") and callable(value.to_dict):
        result = value.to_dict()
        if isinstance(result, dict):
            return result
    return {}


def _format_timestamp(value: datetime) -> str:
    if not isinstance(value, datetime):
        return ""
    return value.isoformat().replace("+00:00", "Z")


def _summarize_output(value: Any) -> str:
    if not isinstance(value, str) or not value:
        return ""
    if len(value) <= RECEIPT_SUMMARY_LIMIT:
        return value
    return f"{value[:RECEIPT_SUMMARY_LIMIT]}... [truncated]"


def _dedupe(reasons: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        deduped.append(reason)
    return deduped
