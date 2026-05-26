from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from source_proxy.codex.adapter import (
    CodexEnvelopeError,
    CodexExecutionEnvelope,
    build_codex_cli_status,
    build_codex_command,
    validate_codex_envelope,
)
from source_proxy.safety.paths import (
    normalize_repo_path_candidate,
    unsafe_target_finding,
)
from source_proxy.tasks.long_running import generate_unified_diff_from_content
from source_proxy.verification.diff import DiffVerificationError, preview_diff_verification

router = APIRouter(prefix="/v1/coding")

ALLOWED_CODEX_MODES = {"readonly", "proposal"}
BLOCKED_CODEX_MODES = {"apply", "commit", "push"}
BOUNDED_DIFF_PREVIEW_ALLOWED_TASK_IDS = {f"CG-{index:03d}" for index in range(1, 6)}
BOUNDED_DIFF_PREVIEW_TARGET = "src/lib/coding/workflow-progress-copy.ts"
BOUNDED_DIFF_PREVIEW_PROMPT = "tighten one preview-only helper phrase for clearer coding progress evidence"
BOUNDED_DIFF_PREVIEW_OLD_PHRASE = "Read-only preview passed."
BOUNDED_DIFF_PREVIEW_NEW_PHRASE = (
    "Read-only preview passed. Human review remains required before apply."
)


class CodexAdapterRequest(BaseModel):
    task: str = Field(min_length=1, max_length=20_000)
    target_file: str | None = None
    allowed_files: list[str] = Field(default_factory=list, max_length=50)
    mode: str = Field(default="readonly", max_length=32)
    sandbox_policy: str = Field(default="read-only", max_length=64)
    timeout_seconds: int = Field(default=300, ge=1, le=3600)


class BoundedDiffPreviewRequest(BaseModel):
    task_id: str = Field(min_length=1, max_length=64)
    prompt: str = Field(min_length=1, max_length=20_000)
    target_files: list[str] = Field(default_factory=list, min_length=1, max_length=5)
    allowed_files: list[str] = Field(default_factory=list, min_length=1, max_length=5)
    micro_batch: str | None = Field(default=None, max_length=128)


@router.post("/codex")
async def codex_adapter(request: CodexAdapterRequest) -> dict[str, Any]:
    try:
        return build_codex_adapter_preview(request)
    except CodexEnvelopeError as error:
        raise HTTPException(
            status_code=400,
            detail=_blocked_error_detail(str(error), error.reason_code),
        ) from error
    except ValueError as error:
        reason_code = getattr(error, "reason_code", "codex_request_invalid")
        raise HTTPException(
            status_code=400,
            detail=_blocked_error_detail(str(error), reason_code),
        ) from error


@router.post("/bounded-diff-preview")
async def bounded_diff_preview(request: BoundedDiffPreviewRequest) -> dict[str, Any]:
    return build_bounded_diff_preview(request)


def build_codex_adapter_preview(request: CodexAdapterRequest) -> dict[str, Any]:
    mode = request.mode.strip().lower()
    if mode in BLOCKED_CODEX_MODES:
        raise _request_error(f"Codex mode {mode!r} is blocked.", "codex_mode_blocked")
    if mode not in ALLOWED_CODEX_MODES:
        raise _request_error(f"Codex mode {mode!r} is not supported.", "codex_mode_unsupported")

    workspace = Path.cwd().resolve()
    allowed_files = tuple(_normalize_and_validate_repo_path(path, workspace) for path in request.allowed_files)
    target_file = _normalize_optional_target(request.target_file, workspace)
    if mode == "proposal" and not allowed_files:
        raise _request_error("Proposal mode requires allowed_files.", "codex_proposal_missing_allowed_files")
    if target_file and target_file not in allowed_files and mode == "proposal":
        raise _request_error("Proposal target_file must be present in allowed_files.", "codex_target_not_allowed")

    output_dir = Path(tempfile.gettempdir()) / "spiritos-source-proxy-codex"
    prompt_file = output_dir / "request-prompt.md"
    output_file = output_dir / "last-message.md"
    envelope = CodexExecutionEnvelope(
        workspace=workspace,
        task_id="source-proxy-codex-route-preview",
        prompt_file=prompt_file,
        output_file=output_file,
        output_dir=output_dir,
        allowed_files=allowed_files,
        blocked_files=(),
        sandbox=request.sandbox_policy,
        timeout_seconds=request.timeout_seconds,
    )
    envelope_validation = validate_codex_envelope(envelope)
    if not envelope_validation["ok"]:
        reason = envelope_validation["blocked_reasons"][0]["reason_code"]
        raise CodexEnvelopeError("Codex execution envelope is not safe.", str(reason))

    command_preview = build_codex_command(envelope)
    codex_status = build_codex_cli_status()
    authority = _no_authority_payload()
    return {
        "service": "source-proxy",
        "route": "codex_adapter",
        "mode": mode,
        "status": "config_blocked",
        "execution_state": "config_blocked",
        "reason_code": "codex_route_live_execution_not_enabled",
        "message": (
            "Codex route validation is available, but server-side live execution "
            "is not enabled in this increment."
        ),
        "live_execution": {
            "enabled": False,
            "reason_code": "codex_route_live_execution_not_enabled",
            "allowed_modes": sorted(ALLOWED_CODEX_MODES),
            "blocked_modes": sorted(BLOCKED_CODEX_MODES),
            "readonly_contract": "validate envelope and return command preview only",
            "proposal_contract": "validate target_file and allowed_files, then return command preview only",
        },
        "target_file": target_file,
        "allowed_files": list(allowed_files),
        "sandbox_policy": request.sandbox_policy,
        "timeout_seconds": request.timeout_seconds,
        "command_preview": command_preview,
        "envelope_validation": envelope_validation,
        "codex_cli_status": codex_status,
        "authority": authority,
        "would_run_task": False,
        "changed_files": [],
        "proposal_ready": mode == "proposal",
        "preview_ready": mode == "readonly",
        "approval_authority": authority["approval_authority"],
        "apply_authority": authority["apply_authority"],
        "commit_authority": authority["commit_authority"],
        "push_authority": authority["push_authority"],
    }


def build_bounded_diff_preview(request: BoundedDiffPreviewRequest) -> dict[str, Any]:
    workspace = Path.cwd().resolve()
    task_id = request.task_id.strip().upper()
    prompt = request.prompt.strip()

    try:
        target_files = [_normalize_and_validate_repo_path(path, workspace) for path in request.target_files]
        allowed_files = [_normalize_and_validate_repo_path(path, workspace) for path in request.allowed_files]
    except ValueError as error:
        return _bounded_preview_packet(
            task_id=task_id,
            prompt=prompt,
            target_files=[],
            allowed_files=[],
            reason_code=getattr(error, "reason_code", "bounded_preview_invalid_path"),
            receipt_class="blocked_safety",
        )

    base_packet = {
        "task_id": task_id,
        "prompt": prompt,
        "target_files": target_files,
        "allowed_files": allowed_files,
    }
    reason_code = _bounded_preview_request_block_reason(
        task_id=task_id,
        prompt=prompt,
        target_files=target_files,
        allowed_files=allowed_files,
    )
    if reason_code:
        return _bounded_preview_packet(
            **base_packet,
            reason_code=reason_code,
            receipt_class="blocked_safety" if reason_code != "backend_diff_generation_gap" else "route_gap_not_ready",
        )

    target_path = workspace / BOUNDED_DIFF_PREVIEW_TARGET
    if not target_path.is_file():
        return _bounded_preview_packet(
            **base_packet,
            reason_code="target_unresolved",
            receipt_class="route_gap_not_ready",
        )

    current_content = target_path.read_text(encoding="utf-8", errors="replace")
    replacement_content = _bounded_preview_replacement_content(current_content)
    if replacement_content is None:
        return _bounded_preview_packet(
            **base_packet,
            reason_code="backend_diff_generation_gap",
            receipt_class="route_gap_not_ready",
        )

    unified_diff = generate_unified_diff_from_content(
        workspace,
        BOUNDED_DIFF_PREVIEW_TARGET,
        replacement_content,
    )
    if not unified_diff.strip():
        return _bounded_preview_packet(
            **base_packet,
            reason_code="backend_diff_generation_gap",
            receipt_class="route_gap_not_ready",
        )

    changed_files = _changed_files_from_unified_diff(unified_diff)
    unexpected_files = [path for path in changed_files if path not in allowed_files]
    if unexpected_files:
        return _bounded_preview_packet(
            **base_packet,
            changed_files=changed_files,
            unified_diff=unified_diff,
            reason_code="allowed_files_mismatch",
            receipt_class="blocked_safety",
            unexpected_files=len(unexpected_files),
        )
    if changed_files != [BOUNDED_DIFF_PREVIEW_TARGET]:
        return _bounded_preview_packet(
            **base_packet,
            changed_files=changed_files,
            unified_diff=unified_diff,
            reason_code="backend_diff_generation_gap",
            receipt_class="route_gap_not_ready",
        )

    try:
        verification = preview_diff_verification(
            unified_diff,
            route_type="bounded-diff-preview",
            task_text=prompt,
            task_spec={
                "allowed_files": allowed_files,
                "forbidden_files": [],
                "risk_tier": "low",
                "schema_version": 1,
                "source": "source_proxy_bounded_diff_preview_cg001_cg005",
                "target": BOUNDED_DIFF_PREVIEW_TARGET,
                "task_type": "modify_existing_file",
                "verification": [],
            },
        )
    except DiffVerificationError as error:
        return _bounded_preview_packet(
            **base_packet,
            changed_files=changed_files,
            unified_diff=unified_diff,
            reason_code=error.reason_code,
            receipt_class="blocked_safety",
            unsafe_failures=0,
        )

    if verification.get("status") == "blocked":
        blocked_reasons = verification.get("blocked_reasons")
        reason = _first_reason_code(blocked_reasons) or "diff_validation_failed"
        return _bounded_preview_packet(
            **base_packet,
            changed_files=changed_files,
            unified_diff=unified_diff,
            reason_code=reason,
            receipt_class="blocked_safety",
        )

    return _bounded_preview_packet(
        **base_packet,
        changed_files=changed_files,
        unified_diff=unified_diff,
        reason_code="preview_ready",
        receipt_class="productive_preview",
    )


def _normalize_optional_target(path: str | None, workspace: Path) -> str | None:
    if path is None:
        return None
    return _normalize_and_validate_repo_path(path, workspace)


def _normalize_and_validate_repo_path(path: str, workspace: Path) -> str:
    normalized = normalize_repo_path_candidate(path)
    if not normalized:
        raise _request_error("Path must be non-empty.", "codex_empty_path")
    finding = unsafe_target_finding(normalized, workspace_root=workspace)
    if finding is not None:
        raise _request_error(finding.message, f"codex_{finding.reason_code}")
    return normalized


def _request_error(message: str, reason_code: str) -> ValueError:
    error = ValueError(message)
    error.reason_code = reason_code  # type: ignore[attr-defined]
    return error


def _no_authority_payload() -> dict[str, bool]:
    return {
        "approval_authority": False,
        "apply_authority": False,
        "commit_authority": False,
        "push_authority": False,
    }


def _no_execution_payload() -> dict[str, bool]:
    return {
        "preview_only": True,
        "apply_authority": False,
        "commit_authority": False,
        "push_authority": False,
        "provider_call_made": False,
        "queue_worker_started": False,
        "shell_command_started": False,
        "hidden_execution_started": False,
        "human_review_required": True,
    }


def _blocked_error_detail(message: str, reason_code: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "error": message,
        "reason_code": reason_code,
        **_no_authority_payload(),
    }


def _bounded_preview_packet(
    *,
    task_id: str,
    prompt: str,
    target_files: list[str],
    allowed_files: list[str],
    changed_files: list[str] | None = None,
    unified_diff: str = "",
    reason_code: str,
    receipt_class: str,
    unsafe_failures: int = 0,
    unexpected_files: int = 0,
) -> dict[str, Any]:
    changed = changed_files or []
    return {
        "task_id": task_id,
        "prompt": prompt,
        "target_files": target_files,
        "allowed_files": allowed_files,
        "changed_files": changed,
        "unified_diff": unified_diff,
        "diff_present": bool(unified_diff.strip()) and receipt_class == "productive_preview",
        **_no_execution_payload(),
        "unsafe_failures": unsafe_failures,
        "unexpected_files": unexpected_files,
        "reason_code": reason_code,
        "receipt_class": receipt_class,
    }


def _bounded_preview_request_block_reason(
    *,
    task_id: str,
    prompt: str,
    target_files: list[str],
    allowed_files: list[str],
) -> str | None:
    if task_id not in BOUNDED_DIFF_PREVIEW_ALLOWED_TASK_IDS:
        return "backend_diff_generation_gap"
    if target_files != [BOUNDED_DIFF_PREVIEW_TARGET]:
        return "target_unresolved"
    if allowed_files != [BOUNDED_DIFF_PREVIEW_TARGET]:
        return "allowed_files_mismatch"
    normalized_prompt = " ".join(prompt.lower().split())
    if BOUNDED_DIFF_PREVIEW_PROMPT not in normalized_prompt:
        return "backend_diff_generation_gap"
    import re

    action_prompt = re.sub(r"\bdo not\b[^.]*[.]", "", normalized_prompt)
    action_prompt = re.sub(r"\bno\b[^.]*[.]", "", action_prompt)
    for pattern, reason_code in _bounded_preview_forbidden_prompt_patterns():
        if pattern.search(action_prompt):
            return reason_code
    return None


def _bounded_preview_forbidden_prompt_patterns() -> tuple[tuple[Any, str], ...]:
    import re

    return (
        (re.compile(r"\bgit\s+(?:commit|push|stash|reset|clean|checkout|restore)\b"), "git_mutation_request"),
        (re.compile(r"\b(?:commit|push|stash|reset|clean|checkout|restore)\s+(?:the|these|my|changes)\b"), "git_mutation_request"),
        (re.compile(r"\b(?:run|start|execute|invoke)\s+(?:a\s+)?(?:shell|terminal|command)\b"), "shell_request"),
        (re.compile(r"\b(?:call|invoke|use|run)\s+(?:a\s+)?(?:provider|model|api)\b"), "provider_request"),
        (re.compile(r"\b(?:start|run|enqueue|spawn)\s+(?:a\s+)?(?:queue|worker|background)\b"), "queue_worker_request"),
        (re.compile(r"\b(?:activate|start|run)\s+(?:cartographer|live map|soak)\b"), "cartographer_activation_request"),
        (re.compile(r"\bdesign\s+apply\b|\bapply\s+design\b"), "design_apply_request"),
        (re.compile(r"\bapproval[-_\s]?token\b"), "approval_token_request"),
    )


def _bounded_preview_replacement_content(current_content: str) -> str | None:
    if BOUNDED_DIFF_PREVIEW_NEW_PHRASE in current_content:
        return None
    if BOUNDED_DIFF_PREVIEW_OLD_PHRASE not in current_content:
        return None
    return current_content.replace(
        BOUNDED_DIFF_PREVIEW_OLD_PHRASE,
        BOUNDED_DIFF_PREVIEW_NEW_PHRASE,
        1,
    )


def _changed_files_from_unified_diff(unified_diff: str) -> list[str]:
    changed: list[str] = []
    for raw_line in unified_diff.splitlines():
        path = ""
        if raw_line.startswith("diff --git "):
            parts = raw_line.split()
            if len(parts) >= 4:
                path = parts[3]
        elif raw_line.startswith("+++ "):
            path = raw_line[4:].split("\t", 1)[0].strip()
        if not path:
            continue
        normalized = normalize_repo_path_candidate(path, strip_diff_prefix=True)
        if normalized and normalized not in changed:
            changed.append(normalized)
    return changed


def _first_reason_code(blocked_reasons: Any) -> str | None:
    if not isinstance(blocked_reasons, list):
        return None
    for reason in blocked_reasons:
        if isinstance(reason, dict) and isinstance(reason.get("reason_code"), str):
            return reason["reason_code"]
    return None
