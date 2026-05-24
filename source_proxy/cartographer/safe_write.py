from __future__ import annotations

import dataclasses
from datetime import datetime
from pathlib import Path
from typing import Any

from source_proxy.cartographer.approval_token_consumption import (
    FORBIDDEN_ACTION_CLASSES,
    preview_approval_token_consumption as _preview_approval_token_consumption,
)

SAFE_WRITE_PHASE = "Plan 3 Phase 2: Safe Write Service"
SAFE_WRITE_VERIFICATION_RECEIPT_PHASE = (
    "Plan 4 Phase 4: Verification Receipt Attached To Safe Write"
)
SAFE_WRITE_ACTION_CLASS = "safe_write"
SAFE_WRITE_TRUST_TIER = "tier-1"
RECEIPT_SUMMARY_LIMIT = 400
SAFE_WRITE_ALLOWED_PREFIXES: tuple[str, ...] = (
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
        "Plan 3 Phase 2 safe write preview does not mutate files, run "
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


def build_safe_write_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Daily Driver Autonomy Roadmap Plan 3",
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
        "safe_write_allowed_prefixes": SAFE_WRITE_ALLOWED_PREFIXES,
        "protected_path_prefixes": PROTECTED_PATH_PREFIXES,
        "protected_exact_files": PROTECTED_EXACT_FILES,
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
    resolved_target.parent.mkdir(parents=True, exist_ok=True)
    resolved_target.write_text(content, encoding="utf-8")
    return SafeWriteResult(
        status="written",
        written=True,
        blocked=False,
        reasons=(),
        target_file=normalized_target,
        bytes_written=len(content.encode("utf-8")),
        before_exists=before_exists,
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
        if _is_protected_path(file_path):
            reasons.append("protected_path_blocked")
        if file_path.startswith("docs/") and file_path not in allowed_files:
            reasons.append("unapproved_docs_blocked")
        if file_path in forbidden_files:
            reasons.append("forbidden_file_blocked")
        if not _is_allowed_safe_write_path(file_path, allowed_files):
            reasons.append("unsafe_write_class_blocked")

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


def _is_within_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


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
