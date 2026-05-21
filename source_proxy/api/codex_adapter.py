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
from source_proxy.safety.paths import normalize_repo_path_candidate, unsafe_target_finding

router = APIRouter(prefix="/v1/coding")

ALLOWED_CODEX_MODES = {"readonly", "proposal"}
BLOCKED_CODEX_MODES = {"apply", "commit", "push"}


class CodexAdapterRequest(BaseModel):
    task: str = Field(min_length=1, max_length=20_000)
    target_file: str | None = None
    allowed_files: list[str] = Field(default_factory=list, max_length=50)
    mode: str = Field(default="readonly", max_length=32)
    sandbox_policy: str = Field(default="read-only", max_length=64)
    timeout_seconds: int = Field(default=300, ge=1, le=3600)


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


def _blocked_error_detail(message: str, reason_code: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "error": message,
        "reason_code": reason_code,
        **_no_authority_payload(),
    }
