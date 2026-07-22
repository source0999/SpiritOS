"""Architect-backed production coding path for server-authorized workspaces.

This module deliberately knows nothing about benchmark task IDs, private
oracles, expected patches, or fixture builders.  Its complete authority is the
workspace root and path scope supplied by the resolved target plugin.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from source_proxy.context.canonical_broker import build_context_broker_report
from source_proxy.diagnostics.status_codes import classify_repair_failure
from source_proxy.planning.architect import (
    ArchitectLLMError,
    Block,
    Plan,
    plan_task_deterministically,
    plan_task_with_llm,
)
from source_proxy.planning.plan import ArchitectPlan, task_spec_from_plan
from source_proxy.safety.paths import normalize_repo_path_candidate, path_escapes_workspace
from source_proxy.tasks.long_running import (
    generate_unified_diff_from_content,
    propose_coder_agent_diff_payload_from_plan,
)
from source_proxy.verification.diff import (
    DiffVerificationError,
    git_diff_changed_paths,
    preview_diff_verification,
)


GENERIC_RICH_EXECUTION_PATH = "architect_coder_packet/v1"
_MAX_PREVIEW_ATTEMPTS = 3
_MAX_MULTI_FILE_COUNT = 8
_MAX_MULTI_FILE_CONTENT_CHARS = 120_000


def execute_generic_workspace_rich(
    *,
    task: str,
    workspace_root: Path,
    allowed_paths: tuple[str, ...],
    readable_paths: tuple[str, ...] | None = None,
    model_call: Callable[[str, str], str] | None,
    architect_model_call: Callable[[str, str], str] | None = None,
    coder_model_call: Callable[[str, str], str] | None = None,
    reviewer_model_call: Callable[[str, str], str] | None = None,
    model_alias: str,
    canonical_context: Mapping[str, Any] | None = None,
    architect_task_id: str | None = None,
    plan_ready_callback: (
        Callable[[ArchitectPlan], Mapping[str, Any] | None] | None
    ) = None,
) -> dict[str, Any]:
    """Plan, inspect, code, review, and validate one scoped model-authored diff."""

    root = workspace_root.resolve()
    architect_call = architect_model_call or model_call
    coder_call = coder_model_call or model_call
    scope = tuple(_normalize_scope_path(value) for value in allowed_paths)
    scope = tuple(value for value in scope if value)
    read_scope = tuple(
        value
        for value in (
            _normalize_scope_path(item)
            for item in (readable_paths or allowed_paths)
        )
        if value
    )
    base_diagnostics: dict[str, Any] = {
        "execution_path": GENERIC_RICH_EXECUTION_PATH,
        "architect_status": "not_started",
        "planner_status": "not_started",
        "repository_inspection": "not_started",
        "allowed_paths": list(scope),
        "readable_paths": list(read_scope),
        "changed_files": [],
        "attempts": [],
        "reviewer_model_call_required": False,
        "reviewer_model_call_count_expected": 0,
    }
    if architect_call is None or coder_call is None:
        return _blocked_result(
            "generic_workspace_model_alias_unavailable",
            "The configured local model alias is unavailable.",
            base_diagnostics,
            stage="routing",
        )
    if not scope:
        return _blocked_result(
            "generic_workspace_allowed_scope_missing",
            "The server-authorized workspace path scope is empty.",
            base_diagnostics,
            stage="scope",
        )

    task_id = str(architect_task_id or "").strip() or (
        "generic-plan-"
        + hashlib.sha256(
            f"{root}\n{task}".encode("utf-8", errors="replace")
        ).hexdigest()[:24]
    )
    deterministic = plan_task_deterministically(
        task,
        task_id,
        root,
        allowed_paths=read_scope,
    )
    if isinstance(deterministic, Block):
        base_diagnostics.update(
            {
                "architect_status": "blocked",
                "planner_status": "blocked",
                "architect_reason": deterministic.reason,
            }
        )
        return _blocked_result(
            deterministic.reason,
            "The deterministic architect rejected the requested target or scope.",
            base_diagnostics,
            stage="architect",
        )

    try:
        if isinstance(deterministic, Plan):
            plan = deterministic.plan
            planning_mode = "deterministic"
        else:
            plan = plan_task_with_llm(
                task,
                task_id,
                root,
                llm_call=architect_call,
                allowed_paths=read_scope,
            )
            planning_mode = "local_model"
    except ArchitectLLMError as error:
        base_diagnostics.update(
            {
                "architect_status": "blocked",
                "planner_status": "blocked",
                "architect_reason": error.reason_code,
            }
        )
        return _blocked_result(
            error.reason_code,
            str(error),
            base_diagnostics,
            stage="architect",
        )

    plan_error = _validate_plan_scope(
        plan,
        root=root,
        allowed_paths=scope,
        readable_paths=read_scope,
    )
    if plan_error:
        base_diagnostics.update(
            {
                "architect_status": "blocked",
                "planner_status": "blocked",
                "architect_reason": plan_error,
            }
        )
        return _blocked_result(
            plan_error,
            "The architect plan is outside the server-authorized workspace scope.",
            base_diagnostics,
            stage="architect",
        )

    # The canonical orchestrator uses this exact plan as its authoritative
    # planner output before the first coder provider call.  Keeping the hook
    # here avoids a second, unaccounted architect call and guarantees that the
    # semantic reviewer later binds the proposal to the plan that actually
    # shaped the coder prompt.
    if plan_ready_callback is not None:
        refreshed_context = plan_ready_callback(plan)
        if isinstance(refreshed_context, Mapping):
            canonical_context = refreshed_context
    planner_context_report = _build_context_report(
        plan,
        allowed_paths=read_scope,
        existing=canonical_context,
        coder_prompt_sha256=None,
    )
    if planner_context_report.get("go_eligible") is not True:
        base_diagnostics["canonical_context_broker"] = planner_context_report
        return _blocked_result(
            "generic_workspace_context_not_go_eligible",
            "; ".join(
                str(value)
                for value in planner_context_report.get("required_context_blockers", [])
            )
            or "Canonical context was not eligible for planner consumption.",
            base_diagnostics,
            stage="context",
        )
    workspace_context_text, workspace_context_manifest = _render_scoped_workspace_context(
        root,
        read_scope,
    )
    context_text = "\n".join(
        part
        for part in (
            _render_current_context(plan, planner_context_report),
            workspace_context_text,
        )
        if part
    )[:24_000]
    context_text_sha256 = hashlib.sha256(context_text.encode("utf-8")).hexdigest()
    context_report = planner_context_report
    base_diagnostics.update(
        {
            "architect_status": "completed",
            "planner_status": "completed",
            "architect_mode": planning_mode,
            "architect_plan_id": plan.plan_id,
            "architect_plan_sha256": _sha256_json(plan.to_dict()),
            "architect_target": plan.coder_packet.target_file.path,
            "acceptance_criteria": [
                {
                    "id": item.id,
                    "description": item.description,
                    "kind": item.kind,
                }
                for item in plan.coder_packet.acceptance_criteria
            ],
            "repository_inspection": "architect_context_slices_ready",
            "context_manifest": [
                {
                    "path": item.path,
                    "kind": item.kind,
                    "sha256": item.sha256,
                    "line_range": list(item.line_range),
                }
                for item in plan.coder_packet.context_slices
            ],
            "scoped_workspace_context_manifest": workspace_context_manifest,
            "canonical_context_broker": context_report,
            "canonical_context_report_hash": context_report.get(
                "canonical_report_hash"
            ),
            "rendered_context_sha256": context_text_sha256,
        }
    )
    previous_signature = ""
    feedback: list[str] | None = None
    final_result: dict[str, Any] | None = None
    observed_coder_prompts: list[str] = []
    multi_file_requested = _task_requests_multi_file_capability(task)
    base_diagnostics["multi_file_capability_requested"] = multi_file_requested

    def observed_coder_call(prompt: str, alias: str) -> str:
        observed_coder_prompts.append(hashlib.sha256(prompt.encode("utf-8")).hexdigest())
        return coder_call(prompt, alias)

    for attempt_index in range(1, _MAX_PREVIEW_ATTEMPTS + 1):
        attempt_strategy = {
            1: "architect_packet_initial",
            2: "preview_feedback_repair",
            3: "constrained_minimal_rewrite",
        }[attempt_index]
        if multi_file_requested:
            result = _propose_multi_file_diff(
                plan=plan,
                workspace_root=root,
                allowed_paths=scope,
                context_text=context_text,
                model_call=observed_coder_call,
                model_alias=model_alias,
                feedback=feedback,
                strategy=attempt_strategy,
            )
        else:
            result = propose_coder_agent_diff_payload_from_plan(
                architect_plan=plan,
                workspace_root=root,
                llm_call=observed_coder_call,
                model_alias=model_alias,
                reviewer_feedback=feedback,
                force_live_model=True,
                canonical_context=planner_context_report,
                canonical_context_text=context_text,
            )
        if observed_coder_prompts:
            context_report = _build_context_report(
                plan,
                allowed_paths=scope,
                existing=canonical_context,
                coder_prompt_sha256=observed_coder_prompts[-1],
            )
            base_diagnostics["canonical_context_broker"] = context_report
            base_diagnostics["canonical_context_report_hash"] = context_report.get(
                "canonical_report_hash"
            )
            base_diagnostics["coder_rendered_prompt_sha256"] = observed_coder_prompts[-1]
        diagnostics = _mapping(result.get("coder_diagnostics"))
        proposed_diff = str(result.get("proposed_diff") or "")
        changed_files = _diff_files(proposed_diff, root=root)
        attempt: dict[str, Any] = {
            "attempt_index": attempt_index,
            "strategy": attempt_strategy,
            "feedback": list(feedback or []),
            "proposed_diff_sha256": hashlib.sha256(
                proposed_diff.encode("utf-8", errors="replace")
            ).hexdigest(),
            "changed_files": changed_files,
            "coder_reason_code": str(
                result.get("reason_code") or result.get("reasonCode") or ""
            ),
            "coder_validation_status": str(
                diagnostics.get("validation_status") or ""
            ),
            "failure_class": None,
            "failure_kind": None,
            "failure_classification": None,
        }
        base_diagnostics["attempts"].append(attempt)
        if not proposed_diff.strip():
            reason_code = attempt["coder_reason_code"] or "generic_workspace_coder_no_diff"
            failure = diagnostics.get("failure_classification")
            if not isinstance(failure, Mapping):
                failure = classify_repair_failure(
                    diagnostic_code=reason_code,
                    stage="coder",
                    reason=reason_code,
                ).to_dict()
            attempt["failure_classification"] = dict(failure)
            attempt["failure_class"] = failure.get("failure_class")
            attempt["failure_kind"] = failure.get("failure_kind")
            if not bool(result.get("coder_blocked") or result.get("coderBlocked")):
                final_result = result
                break
            feedback = [
                f"{reason_code}: {result.get('blocked_reason') or result.get('blockedReason') or reason_code}"
            ]
            signature = _attempt_signature(
                context_manifest=base_diagnostics["context_manifest"],
                proposed_diff_sha256=attempt["proposed_diff_sha256"],
                feedback=feedback,
                strategy=attempt["strategy"],
            )
            attempt["evidence_strategy_signature"] = signature
            if signature == previous_signature or attempt_index >= _MAX_PREVIEW_ATTEMPTS:
                return _blocked_result(
                    "generic_workspace_coder_repair_exhausted",
                    "; ".join(feedback[:8]),
                    base_diagnostics,
                    stage="coder",
                )
            previous_signature = signature
            continue
        scope_error = _validate_diff_scope(changed_files, scope, root=root)
        if scope_error:
            return _blocked_result(
                scope_error,
                "The coder proposed a file outside the server-authorized scope.",
                base_diagnostics,
                stage="scope",
            )
        try:
            task_spec = task_spec_from_plan(plan).to_dict()
            if multi_file_requested:
                task_spec.update(
                    {
                        "task_type": "create_file_bundle",
                        "allowed_files": [
                            value.rstrip("/") + "/**" if value.endswith("/") else value
                            for value in scope
                        ],
                    }
                )
            preview = preview_diff_verification(
                proposed_diff,
                task_text=task,
                architect_plan=plan,
                task_spec=task_spec,
                route_type="local_route",
                reviewer_llm_call=reviewer_model_call,
                workspace_root=root,
            )
        except DiffVerificationError as error:
            preview = {
                "status": "blocked",
                "blocked_reasons": [
                    {
                        "reason_code": "preview_diff_verification_error",
                        "details": str(error),
                    }
                ],
            }
        llm_review_report = preview.get("llm_review_report")
        reviewer_call_required = bool(
            isinstance(llm_review_report, Mapping)
            and llm_review_report
            and llm_review_report.get("skipped") is not True
        )
        attempt["reviewer_model_call_required"] = reviewer_call_required
        if reviewer_call_required:
            base_diagnostics["reviewer_model_call_required"] = True
            base_diagnostics["reviewer_model_call_count_expected"] = (
                int(base_diagnostics["reviewer_model_call_count_expected"]) + 1
            )
        attempt["preview_status"] = str(preview.get("status") or "unknown")
        attempt["preview_sha256"] = _sha256_json(preview)
        attempt["blocked_reasons"] = _preview_feedback(preview)
        if preview.get("status") == "blocked":
            first_reason = next(
                (
                    str(reason.get("reason_code") or "")
                    for reason in preview.get("blocked_reasons", [])
                    if isinstance(reason, Mapping)
                    and str(reason.get("reason_code") or "").strip()
                ),
                "preview_verification_blocked",
            )
            failure_stage = (
                "reviewer"
                if isinstance(preview.get("review_report"), Mapping)
                and preview["review_report"].get("findings")
                else "verifier"
            )
            failure = classify_repair_failure(
                diagnostic_code=first_reason,
                stage=failure_stage,
                reason="; ".join(attempt["blocked_reasons"][:8]),
            ).to_dict()
            attempt["failure_classification"] = failure
            attempt["failure_class"] = failure["failure_class"]
            attempt["failure_kind"] = failure["failure_kind"]
        if preview.get("status") != "blocked":
            check = subprocess.run(
                ["git", "apply", "--check", "--recount", "-"],
                input=proposed_diff,
                text=True,
                cwd=root,
                capture_output=True,
                check=False,
                timeout=15,
            )
            attempt["git_apply_check"] = {
                "passed": check.returncode == 0,
                "exit_code": check.returncode,
                "output_tail": (check.stderr or check.stdout or "")[-1200:],
            }
            if check.returncode == 0:
                final_result = result
                base_diagnostics["changed_files"] = changed_files
                break
            preview = {
                "status": "blocked",
                "blocked_reasons": [
                    {
                        "reason_code": "diff_apply_check_failed",
                        "details": (check.stderr or check.stdout or "git apply --check failed")[-1200:],
                    }
                ],
            }
            attempt["blocked_reasons"] = _preview_feedback(preview)
            failure = classify_repair_failure(
                diagnostic_code="diff_apply_check_failed",
                stage="verifier",
                reason="; ".join(attempt["blocked_reasons"][:8]),
            ).to_dict()
            attempt["failure_classification"] = failure
            attempt["failure_class"] = failure["failure_class"]
            attempt["failure_kind"] = failure["failure_kind"]

        feedback = _preview_feedback(preview)
        signature = _attempt_signature(
            context_manifest=base_diagnostics["context_manifest"],
            proposed_diff_sha256=attempt["proposed_diff_sha256"],
            feedback=feedback,
            strategy=attempt["strategy"],
        )
        attempt["evidence_strategy_signature"] = signature
        if signature == previous_signature or attempt_index >= _MAX_PREVIEW_ATTEMPTS:
            return _blocked_result(
                "generic_workspace_preview_repair_exhausted",
                "; ".join(feedback[:8]) or "Preview verification remained blocked.",
                base_diagnostics,
                stage="verifier",
            )
        previous_signature = signature

    if final_result is None:
        return _blocked_result(
            "generic_workspace_coder_attempts_exhausted",
            "The bounded architect/coder attempts did not produce a safe diff.",
            base_diagnostics,
            stage="coder",
        )
    result_diagnostics = _mapping(final_result.get("coder_diagnostics"))
    result_diagnostics.update(base_diagnostics)
    result_diagnostics["execution_path"] = GENERIC_RICH_EXECUTION_PATH
    result_diagnostics["model_response_format"] = str(
        result_diagnostics.get("structured_output_mode") or "replacement_content"
    )
    final_result["coder_diagnostics"] = result_diagnostics
    final_result["coderDiagnostics"] = result_diagnostics
    final_result["execution_path"] = GENERIC_RICH_EXECUTION_PATH
    return final_result


def _task_requests_multi_file_capability(task: str) -> bool:
    """Recognize ordinary requests whose stated outcome inherently spans files.

    This is deliberately semantic and contains no benchmark IDs, fixture names,
    package names, or expected answers.  A single-file request continues through
    the established replacement-content packet; only an explicit cross-file
    request selects the atomic bundle output contract.
    """

    normalized = " ".join(str(task or "").lower().split())
    patterns = (
        r"\b(?:add|write|include|create)\b.{0,100}\btests?\b",
        r"\btests?\b.{0,100}\b(?:add|write|include|create|implementation|function)\b",
        r"\b(?:both|all)\s+(?:callers|implementations|modules|endpoints|files)\b",
        r"\bduplicat(?:e|ed|ion)\b.{0,120}\b(?:shared|common|helper|both|callers)\b",
        r"\b(?:shared|common)\s+(?:service\s+)?helper\b.{0,120}\b(?:callers|both|replace|update)\b",
        r"\bmultiple\s+files?\b",
    )
    return any(re.search(pattern, normalized) for pattern in patterns)


def _propose_multi_file_diff(
    *,
    plan: ArchitectPlan,
    workspace_root: Path,
    allowed_paths: tuple[str, ...],
    context_text: str,
    model_call: Callable[[str, str], str],
    model_alias: str,
    feedback: list[str] | None,
    strategy: str,
) -> dict[str, Any]:
    packet = plan.coder_packet
    prompt = "\n".join(
        [
            "You are the SpiritOS Coder executing an Architect-owned multi-file packet.",
            "Implement the task atomically. Read the current source state before editing.",
            "Attempt strategy: " + strategy,
            "Return exactly one JSON object and no markdown or prose:",
            '{"files":[{"path":"repo/relative/file.py","content":"complete replacement content"}]}',
            f"You may return between 1 and {_MAX_MULTI_FILE_COUNT} files.",
            "Include only files that must change. Preserve unrelated behavior.",
            "Do not delete files, use absolute paths, traverse directories, or touch symlinks.",
            "Authorized paths or prefixes: " + json.dumps(list(allowed_paths)),
            "Architect primary target: " + packet.target_file.path,
            "Acceptance criteria:",
            *[
                f"- {criterion.id} [{criterion.kind}]: {criterion.description}"
                for criterion in packet.acceptance_criteria
            ],
            "Original task:",
            plan.source_task,
            "Reviewer/verifier feedback from the previous rejected attempt:",
            *(feedback or ["- none"]),
            "Current server-scoped repository context:",
            context_text,
        ]
    )
    raw = str(model_call(prompt, model_alias) or "")
    files, parse_error = _parse_generic_file_bundle(raw)
    diagnostics: dict[str, Any] = {
        "generation_source": "model",
        "execution_mode": "architect_multi_file_packet",
        "structured_output_mode": "json_file_bundle",
        "validation_status": "pending",
        "raw_response_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "changed_files": [],
    }
    if parse_error:
        diagnostics["validation_status"] = "generic_workspace_multi_file_parse_failed"
        diagnostics["parse_error_message"] = parse_error
        return _multi_file_blocked(
            "generic_workspace_multi_file_parse_failed",
            parse_error,
            diagnostics,
            target=packet.target_file.path,
        )
    assert files is not None
    chunks: list[str] = []
    changed_files: list[str] = []
    total_chars = 0
    seen: set[str] = set()
    for file in files:
        raw_path = str(file.get("path") or "")
        content = file.get("content")
        normalized = _normalize_scope_path(raw_path)
        if (
            not normalized
            or raw_path.startswith(("/", "\\"))
            or "\\" in raw_path
            or normalized in seen
            or not _path_resolves_in_scope(workspace_root, normalized, allowed_paths)
        ):
            return _multi_file_blocked(
                "generic_workspace_multi_file_scope_violation",
                f"Rejected unsafe, duplicate, or unauthorized path: {raw_path}",
                diagnostics,
                target=packet.target_file.path,
            )
        if not isinstance(content, str) or not content or "\x00" in content:
            return _multi_file_blocked(
                "generic_workspace_multi_file_content_invalid",
                f"Replacement content is empty or invalid for {normalized}.",
                diagnostics,
                target=packet.target_file.path,
            )
        total_chars += len(content)
        if total_chars > _MAX_MULTI_FILE_CONTENT_CHARS:
            return _multi_file_blocked(
                "generic_workspace_multi_file_content_too_large",
                "The replacement bundle exceeded the bounded content limit.",
                diagnostics,
                target=packet.target_file.path,
            )
        if normalized.endswith(".py"):
            try:
                compile(content, normalized, "exec")
            except SyntaxError as error:
                return _multi_file_blocked(
                    "generic_workspace_multi_file_python_syntax_invalid",
                    f"{normalized}: {error.msg}",
                    diagnostics,
                    target=packet.target_file.path,
                )
        seen.add(normalized)
        chunk = generate_unified_diff_from_content(
            workspace_root,
            normalized,
            content,
        )
        if chunk:
            chunks.append(chunk)
            changed_files.append(normalized)
    if packet.target_file.path not in changed_files:
        return _multi_file_blocked(
            "generic_workspace_multi_file_primary_target_missing",
            "The bundle did not change the Architect primary target.",
            diagnostics,
            target=packet.target_file.path,
        )
    diff = "".join(chunks)
    if not diff:
        return _multi_file_blocked(
            "generic_workspace_multi_file_no_changes",
            "The replacement bundle matched the current source state.",
            diagnostics,
            target=packet.target_file.path,
        )
    diagnostics.update(
        {
            "validation_status": "generic_workspace_multi_file_diff_ready",
            "changed_files": changed_files,
            "file_count": len(changed_files),
        }
    )
    return {
        "proposed_diff": diff,
        "target": packet.target_file.path,
        "changed_files": changed_files,
        "coder_blocked": False,
        "coderBlocked": False,
        "reason_code": "generic_workspace_multi_file_diff_ready",
        "reasonCode": "generic_workspace_multi_file_diff_ready",
        "coder_diagnostics": diagnostics,
        "coderDiagnostics": diagnostics,
        "execution_path": GENERIC_RICH_EXECUTION_PATH,
    }


def _parse_generic_file_bundle(
    raw: str,
) -> tuple[list[dict[str, str]] | None, str]:
    stripped = str(raw or "").strip()
    fenced = re.fullmatch(
        r"```(?:json)?[ \t]*\n(?P<payload>.*?)(?:\n)?```",
        stripped,
        flags=re.DOTALL | re.IGNORECASE,
    )
    payload_text = fenced.group("payload") if fenced else stripped
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as error:
        return None, f"Coder response was not valid file-bundle JSON: {error.msg}"
    if not isinstance(payload, dict) or set(payload) != {"files"}:
        return None, "Coder response must contain only the files field."
    raw_files = payload.get("files")
    if (
        not isinstance(raw_files, list)
        or not raw_files
        or len(raw_files) > _MAX_MULTI_FILE_COUNT
    ):
        return None, f"files must contain 1..{_MAX_MULTI_FILE_COUNT} entries."
    files: list[dict[str, str]] = []
    for index, item in enumerate(raw_files):
        if not isinstance(item, dict) or set(item) != {"path", "content"}:
            return None, f"files[{index}] must contain exactly path and content."
        path = item.get("path")
        content = item.get("content")
        if not isinstance(path, str) or not isinstance(content, str):
            return None, f"files[{index}] path and content must be strings."
        files.append({"path": path, "content": content})
    return files, ""


def _multi_file_blocked(
    reason_code: str,
    reason: str,
    diagnostics: Mapping[str, Any],
    *,
    target: str,
) -> dict[str, Any]:
    payload = dict(diagnostics)
    payload["validation_status"] = reason_code
    return {
        "proposed_diff": "",
        "target": target,
        "changed_files": [],
        "coder_blocked": True,
        "coderBlocked": True,
        "blocked_reason": reason,
        "blockedReason": reason,
        "reason_code": reason_code,
        "reasonCode": reason_code,
        "coder_diagnostics": payload,
        "coderDiagnostics": payload,
        "execution_path": GENERIC_RICH_EXECUTION_PATH,
    }


def _render_scoped_workspace_context(
    root: Path,
    allowed_paths: tuple[str, ...],
) -> tuple[str, list[dict[str, Any]]]:
    listed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        capture_output=True,
        check=False,
        timeout=15,
    )
    if listed.returncode:
        return "", []
    remaining = 12_000
    sections = ["ADDITIONAL CURRENT AUTHORIZED FILES:"]
    manifest: list[dict[str, Any]] = []
    for path in listed.stdout.decode("utf-8", errors="strict").split("\0"):
        if not path or not _path_resolves_in_scope(root, path, allowed_paths):
            continue
        candidate = root / path
        if not candidate.is_file() or candidate.is_symlink():
            continue
        raw = candidate.read_bytes()
        content = raw.decode("utf-8", errors="replace")
        manifest.append(
            {
                "path": path,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "size": len(raw),
            }
        )
        rendered = f"--- {path} ---\n{content[:3_000]}\n"
        if len(rendered) > remaining:
            continue
        sections.append(rendered)
        remaining -= len(rendered)
    return "\n".join(sections) if manifest else "", manifest


def _attempt_signature(
    *,
    context_manifest: Any,
    proposed_diff_sha256: str,
    feedback: list[str],
    strategy: str,
) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "current_context": context_manifest,
                "diff_sha256": proposed_diff_sha256,
                "feedback": feedback,
                "strategy": strategy,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _validate_plan_scope(
    plan: ArchitectPlan,
    *,
    root: Path,
    allowed_paths: tuple[str, ...],
    readable_paths: tuple[str, ...] | None = None,
) -> str:
    packet = plan.coder_packet
    target = _normalize_scope_path(packet.target_file.path)
    if packet.operation not in {"edit", "create"}:
        return "generic_workspace_architect_operation_unsupported"
    if not _path_resolves_in_scope(root, target, allowed_paths):
        return "generic_workspace_architect_target_outside_scope"
    candidate = root / target
    if candidate.is_symlink():
        return "generic_workspace_architect_target_symlink"
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return "generic_workspace_architect_target_outside_root"
    if packet.operation == "edit" and not candidate.is_file():
        return "generic_workspace_architect_edit_target_missing"
    for context_slice in packet.context_slices:
        if not _path_allowed(
            context_slice.path,
            readable_paths or allowed_paths,
        ):
            return "generic_workspace_architect_context_outside_scope"
    return ""


def _build_context_report(
    plan: ArchitectPlan,
    *,
    allowed_paths: tuple[str, ...],
    existing: Mapping[str, Any] | None,
    coder_prompt_sha256: str | None,
) -> dict[str, Any]:
    sources: list[dict[str, Any]] = []
    for raw in (existing or {}).get("sources_considered", []):
        if not isinstance(raw, Mapping):
            continue
        source = dict(raw)
        source["consumed"] = False
        packet = source.get("packet")
        if source.get("selected") is True and source.get("included") is True:
            if not isinstance(packet, Mapping) or not packet:
                source["selected"] = False
                source["included"] = False
            else:
                packet_json = json.dumps(
                    dict(packet),
                    sort_keys=True,
                    separators=(",", ":"),
                    default=str,
                )
                source["packet"] = {
                    "bounded_context": packet_json[:4_000],
                    "packet_sha256": hashlib.sha256(packet_json.encode("utf-8")).hexdigest(),
                    "truncated": len(packet_json) > 4_000,
                }
        sources.append(source)
    sources = [
        source
        for source in sources
        if str(source.get("source") or "") != "architect_repository_context"
    ]
    sources.append(
        {
            "source": "architect_repository_context",
            "considered": True,
            "status": "used",
            "reason": "architect_selected_current_scoped_source",
            "required": True,
            "selected": True,
            "included": True,
            "consumed": False,
            "packet": {
                "plan_id": plan.plan_id,
                "target": plan.coder_packet.target_file.path,
                "allowed_paths": list(allowed_paths),
                "context_slices": [
                    {
                        "path": item.path,
                        "kind": item.kind,
                        "sha256": item.sha256,
                        "line_range": list(item.line_range),
                    }
                    for item in plan.coder_packet.context_slices
                ],
            },
        }
    )
    selected = [
        str(source.get("source") or "")
        for source in sources
        if source.get("selected") is True and source.get("included") is True
    ]
    acknowledgements: dict[str, dict[str, Any]] = {
        "planner": {
            "applicable": True,
            "acknowledged": True,
            "sources": selected,
            "evidence": "architect_selected_server_scoped_repository_context",
            "reason": "planner_built_current_scoped_context_manifest",
        },
    }
    applicable_consumers = ["planner"]
    if coder_prompt_sha256:
        acknowledgements["coder"] = {
            "applicable": True,
            "acknowledged": True,
            "sources": selected,
            "evidence": f"rendered_context_sha256:{coder_prompt_sha256}",
            "reason": "coder_consumed_current_scoped_context_before_generation",
        }
        applicable_consumers.append("coder")
    return build_context_broker_report(
        sources,
        downstream_consumers=acknowledgements,
        applicable_consumers=applicable_consumers,
    )


def _render_current_context(
    plan: ArchitectPlan,
    context_report: Mapping[str, Any],
) -> str:
    sections = [
        "CURRENT SERVER-SCOPED SOURCE STATE (read before editing):",
    ]
    for item in plan.coder_packet.context_slices:
        sections.extend(
            [
                f"--- {item.path} ({item.kind}; sha256={item.sha256}) ---",
                item.content,
            ]
        )
    for source in context_report.get("sources_considered", []):
        if not isinstance(source, Mapping):
            continue
        if str(source.get("source") or "") == "architect_repository_context":
            continue
        if source.get("selected") is not True or source.get("included") is not True:
            continue
        packet = source.get("packet")
        bounded = str(packet.get("bounded_context") or "") if isinstance(packet, Mapping) else ""
        if not bounded:
            continue
        sections.extend(
            [
                f"--- selected context packet: {source.get('source')} ---",
                bounded,
            ]
        )
    sections.extend(
        [
            "CANONICAL CONTEXT MANIFEST:",
            json.dumps(
                {
                    "selected_sources": context_report.get("selected_sources", []),
                    "target": plan.coder_packet.target_file.path,
                },
                sort_keys=True,
            ),
        ]
    )
    return "\n".join(sections)[:24_000]


def _blocked_result(
    reason_code: str,
    reason: str,
    diagnostics: Mapping[str, Any],
    *,
    stage: str,
) -> dict[str, Any]:
    classification = classify_repair_failure(
        diagnostic_code=reason_code,
        stage=stage,
        reason=reason,
        details={"diagnostic_code": reason_code, "stage": stage},
    ).to_dict()
    payload_diagnostics = dict(diagnostics)
    payload_diagnostics.update(
        {
            "validation_status": reason_code,
            "failure_class": classification["failure_class"],
            "failure_classification": classification,
            "failure_kind": classification["failure_kind"],
            "failure_stage": stage,
            "diagnostic_code": reason_code,
            "generation_source": "model"
            if payload_diagnostics.get("attempts")
            else "non_model",
        }
    )
    return {
        "proposed_diff": "",
        "target": str(payload_diagnostics.get("architect_target") or ""),
        "coder_blocked": True,
        "coderBlocked": True,
        "blocked_reason": reason,
        "blockedReason": reason,
        "reason_code": reason_code,
        "reasonCode": reason_code,
        "coder_diagnostics": payload_diagnostics,
        "coderDiagnostics": payload_diagnostics,
        "execution_path": GENERIC_RICH_EXECUTION_PATH,
    }


def _preview_feedback(preview: Mapping[str, Any]) -> list[str]:
    feedback: list[str] = []
    review = preview.get("review_report")
    if isinstance(review, Mapping):
        for finding in review.get("findings", []):
            if not isinstance(finding, Mapping):
                continue
            finding_id = str(finding.get("id") or "reviewer_rejection")
            details = str(finding.get("details") or "")
            feedback.append(f"{finding_id}: {details}".strip(": "))
    for reason in preview.get("blocked_reasons", []):
        if not isinstance(reason, Mapping):
            continue
        code = str(reason.get("reason_code") or "verification_blocked")
        details = str(reason.get("details") or reason.get("summary") or "")
        rendered = f"{code}: {details}".strip(": ")
        if rendered not in feedback:
            feedback.append(rendered)
    return feedback or ["verification_blocked: no structured detail was returned"]


def _diff_files(diff: str, *, root: Path) -> list[str]:
    try:
        return git_diff_changed_paths(diff, workspace_root=root)
    except DiffVerificationError:
        return []


def _validate_diff_scope(
    changed_files: list[str],
    allowed_paths: tuple[str, ...],
    *,
    root: Path,
) -> str:
    if not changed_files:
        return "generic_workspace_changed_files_missing"
    if any(
        not _path_resolves_in_scope(root, path, allowed_paths)
        for path in changed_files
    ):
        return "generic_workspace_scope_violation"
    return ""


def _path_allowed(path: str, allowed_paths: tuple[str, ...]) -> bool:
    normalized = _normalize_scope_path(path)
    if not normalized or path_escapes_workspace(normalized):
        return False
    return any(
        normalized == allowed.rstrip("/")
        or normalized.startswith(allowed.rstrip("/") + "/")
        for allowed in allowed_paths
    )


def _path_resolves_in_scope(
    root: Path,
    path: str,
    allowed_paths: tuple[str, ...],
) -> bool:
    normalized = _normalize_scope_path(path)
    if not _path_allowed(normalized, allowed_paths):
        return False
    candidate = root.resolve()
    for part in Path(normalized).parts:
        candidate = candidate / part
        if candidate.is_symlink():
            return False
    resolved = candidate.resolve()
    try:
        resolved_relative = resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return False
    return _path_allowed(resolved_relative, allowed_paths)


def _normalize_scope_path(value: str) -> str:
    return normalize_repo_path_candidate(str(value or ""))


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode(
            "utf-8"
        )
    ).hexdigest()
