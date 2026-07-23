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

from source_proxy.context.canonical_broker import (
    ARCHITECT_REPOSITORY_CONTEXT_SOURCE,
    build_context_broker_report,
    derived_architect_context_authority,
    is_derived_architect_context_source,
)
from source_proxy.diagnostics.status_codes import classify_repair_failure
from source_proxy.decision.proposal_task import effective_planning_task_text
from source_proxy.planning.architect import (
    ArchitectLLMError,
    Block,
    Plan,
    plan_task_deterministically,
    plan_task_with_llm,
)
from source_proxy.planning.plan import (
    ArchitectPlan,
    review_intent_paths_from_plan,
    review_task_spec_from_plan,
    task_requests_shared_helper_artifact,
    task_requests_test_artifact,
)
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
_BOUNDED_CONTEXT_PACKET_SCHEMA = "source-proxy-bounded-context-packet/v1"


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
    prevalidated_plan: ArchitectPlan | None = None,
    plan_ready_callback: (
        Callable[
            [ArchitectPlan, Mapping[str, Any]],
            Mapping[str, Any] | None,
        ]
        | None
    ) = None,
    coder_ready_callback: (
        Callable[
            [ArchitectPlan, Mapping[str, Any], str],
            Mapping[str, Any] | None,
        ]
        | None
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
    if coder_call is None or (prevalidated_plan is None and architect_call is None):
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
    if prevalidated_plan is not None:
        if not isinstance(prevalidated_plan, ArchitectPlan) or (
            prevalidated_plan.task_id != task_id
        ):
            return _blocked_result(
                "generic_workspace_prevalidated_plan_identity_mismatch",
                "The server-owned fallback plan did not match this exact task.",
                base_diagnostics,
                stage="architect",
            )
        plan = prevalidated_plan
        planning_mode = "server_persisted_plan_reuse"
    else:
        deterministic = plan_task_deterministically(
            task,
            task_id,
            root,
            allowed_paths=scope,
            readable_paths=read_scope,
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
                    allowed_paths=scope,
                    readable_paths=read_scope,
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

    multi_file_requested = _task_requests_multi_file_capability(task)

    try:
        workspace_context_text, workspace_context_manifest = (
            _render_scoped_workspace_context(
                root,
                read_scope,
            )
        )
    except RuntimeError as error:
        return _blocked_result(
            "generic_workspace_repository_index_unavailable",
            str(error),
            base_diagnostics,
            stage="context",
        )
    staged_planner_context_report = _build_context_report(
        plan,
        allowed_paths=read_scope,
        existing=canonical_context,
        scoped_workspace_context=workspace_context_text,
        scoped_workspace_context_manifest=workspace_context_manifest,
    )
    if prevalidated_plan is not None:
        if plan_ready_callback is not None or coder_ready_callback is None:
            base_diagnostics["canonical_context_broker"] = (
                staged_planner_context_report
            )
            return _blocked_result(
                "generic_workspace_reused_plan_callback_contract_invalid",
                "A reused server plan requires only the coder dispatch callback.",
                base_diagnostics,
                stage="context",
            )
        reuse_error = _validate_coder_context_report(
            staged_planner_context_report,
            canonical_context or {},
        )
        if reuse_error:
            base_diagnostics["canonical_context_broker"] = dict(
                canonical_context or {}
            )
            return _blocked_result(
                "generic_workspace_reused_plan_context_invalid",
                reuse_error,
                base_diagnostics,
                stage="context",
            )
        planner_context_report = json.loads(
            json.dumps(dict(canonical_context or {}), sort_keys=True, default=str)
        )
    else:
        planner_context_report = staged_planner_context_report
        if (plan_ready_callback is None) != (coder_ready_callback is None):
            base_diagnostics["canonical_context_broker"] = planner_context_report
            return _blocked_result(
                "generic_workspace_context_callback_pair_incomplete",
                "Planner-ready and coder-ready context callbacks must be supplied together.",
                base_diagnostics,
                stage="context",
            )

        if planner_context_report.get("go_eligible") is not True and not (
            plan_ready_callback is not None
            and _is_staged_planner_context_report(planner_context_report)
        ):
            base_diagnostics["canonical_context_broker"] = planner_context_report
            return _blocked_result(
                "generic_workspace_context_not_go_eligible",
                "; ".join(
                    str(value)
                    for value in planner_context_report.get(
                        "required_context_blockers", []
                    )
                )
                or "Canonical context was not eligible for planner consumption.",
                base_diagnostics,
                stage="context",
            )

        # The first hook persists the exact expanded report and Architect plan.
        # It deliberately does not claim that Coder ran; the second hook is
        # invoked only from the real provider-call boundary below.
        refreshed_context = (
            plan_ready_callback(plan, planner_context_report)
            if plan_ready_callback is not None
            else planner_context_report
        )
        if not isinstance(refreshed_context, Mapping):
            base_diagnostics["canonical_context_broker"] = planner_context_report
            return _blocked_result(
                "generic_workspace_context_refresh_missing",
                "The canonical orchestrator did not return the persisted context report.",
                base_diagnostics,
                stage="context",
            )
        refresh_error = _validate_persisted_planner_context_report(
            planner_context_report,
            refreshed_context,
        )
        if refresh_error:
            base_diagnostics["canonical_context_broker"] = dict(refreshed_context)
            return _blocked_result(
                refresh_error,
                "The persisted context report did not bind the exact adapter source material.",
                base_diagnostics,
                stage="context",
            )
        planner_context_report = json.loads(
            json.dumps(dict(refreshed_context), sort_keys=True, default=str)
        )
        canonical_context = planner_context_report
    context_text = _bound_coder_context_text(planner_context_report)
    if context_text is None:
        base_diagnostics["canonical_context_broker"] = planner_context_report
        return _blocked_result(
            "generic_workspace_bound_coder_context_missing",
            "The persisted Architect source did not retain the exact rendered coder context.",
            base_diagnostics,
            stage="context",
        )
    context_text_sha256 = hashlib.sha256(context_text.encode("utf-8")).hexdigest()
    context_report: Mapping[str, Any] = planner_context_report
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
                    "line_range": list(item.line_range or ()),
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
    coder_context_ready = False
    coder_context_error = ""
    coder_callback_exception: BaseException | None = None
    coder_provider_exception: Exception | None = None
    base_diagnostics["multi_file_capability_requested"] = multi_file_requested

    def observed_coder_call(prompt: str, alias: str) -> str:
        nonlocal context_report, coder_context_ready, coder_context_error
        nonlocal coder_callback_exception, coder_provider_exception
        prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        if coder_callback_exception is not None or coder_context_error:
            return _context_callback_block_response(
                coder_context_error
                or "generic_workspace_coder_context_callback_failed"
            )
        if coder_ready_callback is not None and not coder_context_ready:
            try:
                refreshed_context = coder_ready_callback(
                    plan,
                    planner_context_report,
                    prompt_sha256,
                )
            except Exception as error:  # re-raised outside model wrappers
                coder_callback_exception = error
                return _context_callback_block_response(
                    "generic_workspace_coder_context_callback_failed"
                )
            if not isinstance(refreshed_context, Mapping):
                coder_context_error = "generic_workspace_coder_context_refresh_missing"
                return _context_callback_block_response(coder_context_error)
            coder_context_error = _validate_coder_context_report(
                planner_context_report,
                refreshed_context,
            )
            if coder_context_error:
                return _context_callback_block_response(coder_context_error)
            context_report = json.loads(
                json.dumps(dict(refreshed_context), sort_keys=True, default=str)
            )
            coder_context_ready = True
            base_diagnostics["canonical_context_broker"] = context_report
            base_diagnostics["canonical_context_report_hash"] = context_report.get(
                "canonical_report_hash"
            )
        observed_coder_prompts.append(prompt_sha256)
        try:
            return coder_call(prompt, alias)
        except Exception as error:  # noqa: BLE001 - normalized at provider boundary
            coder_provider_exception = error
            return _context_callback_block_response(
                "generic_workspace_coder_provider_failed"
            )

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
        if coder_callback_exception is not None:
            raise coder_callback_exception
        if coder_context_error:
            return _blocked_result(
                coder_context_error,
                "The coder-ready context acknowledgement did not bind the persisted planner material.",
                base_diagnostics,
                stage="context",
            )
        if observed_coder_prompts:
            bindings = [
                {
                    "schema_version": "source-proxy-coder-context-binding/v1",
                    "call_index": index,
                    "canonical_context_report_hash": context_report.get(
                        "canonical_report_hash"
                    ),
                    "rendered_prompt_sha256": prompt_sha256,
                    "selected_sources": list(
                        context_report.get("selected_sources") or []
                    ),
                    "consumed_sources": list(
                        context_report.get("consumed_sources") or []
                    ),
                    "consumed": True,
                }
                for index, prompt_sha256 in enumerate(
                    observed_coder_prompts,
                    start=1,
                )
            ]
            base_diagnostics["coder_context_bindings"] = bindings
            base_diagnostics["coder_context_binding"] = bindings[-1]
            base_diagnostics["coder_rendered_prompt_sha256"] = (
                observed_coder_prompts[-1]
            )
        if coder_provider_exception is not None:
            provider_reason = str(
                getattr(coder_provider_exception, "reason_code", "") or ""
            )
            if provider_reason == "target_plugin_model_execution_budget_exhausted":
                reason_code = "coder_model_execution_budget_exhausted"
            elif _is_timeout_exception(coder_provider_exception):
                reason_code = "coder_model_timeout"
            else:
                reason_code = "coder_model_router_error"
            failure = classify_repair_failure(
                diagnostic_code=reason_code,
                stage="coder",
                reason=type(coder_provider_exception).__name__,
                details={
                    "diagnostic_code": reason_code,
                    "stage": "coder",
                    "exception_type": type(coder_provider_exception).__name__,
                },
            ).to_dict()
            base_diagnostics["attempts"].append(
                {
                    "attempt_index": attempt_index,
                    "strategy": attempt_strategy,
                    "feedback": list(feedback or []),
                    "proposed_diff_sha256": hashlib.sha256(b"").hexdigest(),
                    "changed_files": [],
                    "coder_reason_code": reason_code,
                    "coder_validation_status": reason_code,
                    "failure_class": failure["failure_class"],
                    "failure_kind": failure["failure_kind"],
                    "failure_classification": failure,
                    "provider_exception_type": type(
                        coder_provider_exception
                    ).__name__,
                }
            )
            base_diagnostics["provider_exception_type"] = type(
                coder_provider_exception
            ).__name__
            return _blocked_result(
                reason_code,
                (
                    "The authorized local Coder call exceeded its bounded provider timeout."
                    if reason_code == "coder_model_timeout"
                    else "The authorized local Coder route failed before returning usable output."
                ),
                base_diagnostics,
                stage="coder",
            )
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
            review_artifact_snapshots = _build_review_artifact_snapshots(
                root,
                changed_files,
            )
        except RuntimeError as error:
            return _blocked_result(
                "generic_workspace_review_snapshot_unavailable",
                str(error),
                base_diagnostics,
                stage="reviewer",
            )
        base_diagnostics["review_artifact_snapshots"] = (
            review_artifact_snapshots
        )
        base_diagnostics["review_artifact_snapshots_sha256"] = (
            _canonical_review_artifact_snapshots_sha256(
                review_artifact_snapshots
            )
        )
        try:
            task_spec = review_task_spec_from_plan(
                plan,
                changed_files,
                authorized_paths=scope,
                artifact_snapshots=review_artifact_snapshots,
            ).to_dict()
            base_diagnostics["review_task_spec"] = task_spec
            base_diagnostics["review_task_spec_sha256"] = _sha256_json(task_spec)
            preview = preview_diff_verification(
                proposed_diff,
                task_text=task,
                architect_plan=plan,
                task_spec=task_spec,
                route_type="local_route",
                reviewer_llm_call=reviewer_model_call,
                workspace_root=root,
                review_attempt_id=f"{plan.plan_id}:preview:{attempt_index}",
                review_artifact_snapshots=review_artifact_snapshots,
            )
        except (DiffVerificationError, ValueError) as error:
            preview = {
                "status": "blocked",
                "blocked_reasons": [
                    {
                        "reason_code": (
                            "preview_diff_verification_error"
                            if isinstance(error, DiffVerificationError)
                            else "review_task_spec_unrequested_changed_file"
                        ),
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

    if task_requests_test_artifact(task) or task_requests_shared_helper_artifact(task):
        return True

    normalized = " ".join(str(task or "").lower().split())
    patterns = (
        r"\b(?:both|all)\s+(?:callers|implementations|modules|endpoints|files)\b",
        r"\bmultiple\s+files?\b",
    )
    return any(re.search(pattern, normalized) for pattern in patterns)


def _multi_file_capability_prompt_lines(plan: ArchitectPlan) -> list[str]:
    task = effective_planning_task_text(plan.source_task)
    lines: list[str] = []
    if task_requests_test_artifact(task):
        lines.append(
            "- Focused-test capability: at most one conventional test artifact that imports or directly references the primary target module."
        )
    if task_requests_shared_helper_artifact(task):
        lines.append(
            "- Shared-helper capability: at most one new helper file beside the two exact task-intended source artifacts, with their same extension."
        )
    return lines


def _build_review_artifact_snapshots(
    root: Path,
    changed_files: list[str],
) -> dict[str, dict[str, object]]:
    snapshots: dict[str, dict[str, object]] = {}
    total_chars = 0
    resolved_root = root.resolve()
    for path in changed_files:
        candidate = resolved_root
        for part in Path(path).parts:
            candidate = candidate / part
            if candidate.is_symlink():
                raise RuntimeError("review snapshot path traverses a symlink")
        try:
            candidate.resolve().relative_to(resolved_root)
        except ValueError as error:
            raise RuntimeError("review snapshot path escapes workspace") from error
        try:
            exists = candidate.is_file()
            if candidate.exists() and not exists:
                raise RuntimeError("review snapshot path is not a regular file")
            remaining = 1_000_000 - total_chars
            if exists and candidate.stat().st_size > remaining:
                raise RuntimeError("review snapshot content exceeds bounded budget")
            if exists:
                # Recheck the budget while reading so a file that grows after
                # stat cannot force an unbounded allocation or decode.
                with candidate.open(
                    "r",
                    encoding="utf-8",
                    errors="replace",
                    newline=None,
                ) as stream:
                    content = stream.read(remaining + 1)
            else:
                content = ""
        except OSError as error:
            raise RuntimeError("review snapshot path could not be read") from error
        total_chars += len(content)
        if total_chars > 1_000_000:
            raise RuntimeError("review snapshot content exceeds bounded budget")
        snapshots[path] = {
            "schema_version": "coding.review-artifact-snapshot/v1",
            "path": path,
            "exists": exists,
            "content": content,
            "content_sha256": hashlib.sha256(
                content.encode("utf-8")
            ).hexdigest(),
        }
    return snapshots


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
    exact_intended_paths = [
        path
        for path in review_intent_paths_from_plan(plan)
        if _path_allowed(path, allowed_paths)
    ]
    capability_lines = _multi_file_capability_prompt_lines(plan)
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
            "Exact task-intended artifacts: " + json.dumps(exact_intended_paths),
            "Every returned file must be in that exact list or satisfy one bounded capability below.",
            *(capability_lines or ["- No additional artifact capability is authorized."]),
            "Architect primary target: " + packet.target_file.path,
            "Acceptance criteria:",
            f"- target-file [scope]: The primary target {packet.target_file.path} must change.",
            *[
                f"- {criterion.id} [{criterion.kind}]: {criterion.description}"
                for criterion in packet.acceptance_criteria
                if criterion.id != "target-file"
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
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        cwd=root,
        capture_output=True,
        check=False,
        timeout=15,
    )
    if listed.returncode:
        raise RuntimeError(
            "The authorized Git file index could not be read for context binding."
        )
    rendered_context = "ADDITIONAL CURRENT AUTHORIZED FILES:\n"
    remaining = 12_000 - len(rendered_context)
    manifest: list[dict[str, Any]] = []
    for path in listed.stdout.decode("utf-8", errors="strict").split("\0"):
        if not path or not _path_resolves_in_scope(root, path, allowed_paths):
            continue
        candidate = root / path
        if not candidate.is_file() or candidate.is_symlink():
            continue
        raw = candidate.read_bytes()
        content = raw.decode("utf-8", errors="replace")
        rendered = f"--- {path} ---\n{content[:3_000]}\n"
        if len(rendered) > remaining:
            continue
        rendered_start = len(rendered_context)
        rendered_context += rendered
        rendered_end = len(rendered_context)
        manifest.append(
            {
                "path": path,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "size": len(raw),
                "rendered_sha256": hashlib.sha256(
                    rendered.encode("utf-8")
                ).hexdigest(),
                "rendered_chars": len(rendered),
                "truncated": len(content) > 3_000,
                "rendered_start": rendered_start,
                "rendered_end": rendered_end,
            }
        )
        remaining -= len(rendered)
    return rendered_context if manifest else "", manifest


def _attempt_signature(
    *,
    context_manifest: Any,
    proposed_diff_sha256: str,
    feedback: list[str],
    strategy: str,
) -> str:
    del strategy
    return hashlib.sha256(
        json.dumps(
            {
                "current_context": context_manifest,
                "diff_sha256": proposed_diff_sha256,
                "feedback": feedback,
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
    target_exists = candidate.is_file()
    if target_exists is not packet.target_file.exists:
        return "generic_workspace_architect_target_state_mismatch"
    current_target_sha256 = (
        hashlib.sha256(candidate.read_bytes()).hexdigest()
        if target_exists
        else None
    )
    if current_target_sha256 != packet.target_file.sha256_before:
        return "generic_workspace_architect_target_hash_mismatch"
    for context_slice in packet.context_slices:
        effective_read_scope = readable_paths or allowed_paths
        if not _path_resolves_in_scope(
            root,
            context_slice.path,
            effective_read_scope,
        ):
            return "generic_workspace_architect_context_outside_scope"
        context_candidate = root / context_slice.path
        if not context_candidate.is_file() or context_candidate.is_symlink():
            return "generic_workspace_architect_context_missing"
        current_content = context_candidate.read_text(
            encoding="utf-8",
            errors="replace",
        )
        if (
            context_slice.sha256
            != hashlib.sha256(context_slice.content.encode("utf-8")).hexdigest()
            or context_slice.content != current_content
        ):
            return "generic_workspace_architect_context_hash_mismatch"
    return ""


def _build_context_report(
    plan: ArchitectPlan,
    *,
    allowed_paths: tuple[str, ...],
    existing: Mapping[str, Any] | None,
    scoped_workspace_context: str,
    scoped_workspace_context_manifest: list[dict[str, Any]],
) -> dict[str, Any]:
    sources: list[dict[str, Any]] = []
    for raw in (existing or {}).get("sources_considered", []):
        if not isinstance(raw, Mapping):
            continue
        source = dict(raw)
        source["consumed"] = False
        packet = source.get("packet")
        if source.get("selected") is True and source.get("included") is True:
            source["packet"] = _normalize_selected_context_packet(packet)
        elif not isinstance(packet, Mapping):
            source["packet"] = {}
        sources.append(source)
    sources = [
        source
        for source in sources
        if not is_derived_architect_context_source(source)
    ]
    sources.append(
        {
            "source": ARCHITECT_REPOSITORY_CONTEXT_SOURCE,
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
                            "line_range": list(item.line_range or ()),
                    }
                    for item in plan.coder_packet.context_slices
                ],
                "scoped_workspace_context": scoped_workspace_context,
                "scoped_workspace_context_manifest": json.loads(
                    json.dumps(
                        scoped_workspace_context_manifest,
                        sort_keys=True,
                        default=str,
                    )
                ),
                "scoped_workspace_context_sha256": hashlib.sha256(
                    scoped_workspace_context.encode("utf-8")
                ).hexdigest(),
                "scoped_workspace_context_char_count": len(
                    scoped_workspace_context
                ),
            },
            "authority": derived_architect_context_authority(),
        }
    )
    selected = [
        str(source.get("source") or "")
        for source in sources
        if source.get("selected") is True and source.get("included") is True
    ]
    # This is deliberately staged as unacknowledged.  The adapter can assemble
    # the late-bound packet, but only the server-owned callback may attest that
    # the planner lane validated it and durably persisted the exact plan.
    acknowledgements: dict[str, dict[str, Any]] = {}
    report = build_context_broker_report(
        sources,
        downstream_consumers=acknowledgements,
        applicable_consumers=("planner",),
    )
    rendered_coder_context = "\n".join(
        part
        for part in (
            _render_current_context(plan, report),
            scoped_workspace_context,
        )
        if part
    )[:24_000]
    architect_packet = sources[-1]["packet"]
    architect_packet.update(
        {
            "rendered_coder_context": rendered_coder_context,
            "rendered_coder_context_sha256": hashlib.sha256(
                rendered_coder_context.encode("utf-8")
            ).hexdigest(),
            "rendered_coder_context_char_count": len(rendered_coder_context),
        }
    )
    report = build_context_broker_report(
        sources,
        downstream_consumers=acknowledgements,
        applicable_consumers=("planner",),
    )
    for field_name in ("task_id", "trace_id", "explicit_target", "finalized"):
        if field_name in (existing or {}):
            report[field_name] = (existing or {})[field_name]
    return report


def _is_staged_planner_context_report(report: Mapping[str, Any]) -> bool:
    """Recognize the sole NO-GO state permitted before the server callback."""

    selected_sources = [
        source
        for source in report.get("sources_considered", [])
        if isinstance(source, Mapping)
        and source.get("selected") is True
        and source.get("included") is True
    ]
    expected_blockers: list[str] = []
    for source in selected_sources:
        source_name = str(source.get("source") or "")
        if source.get("required") is True:
            expected_blockers.append(
                f"required_context_unacknowledged:{source_name}:planner"
            )
        expected_blockers.append(
            f"selected_context_unacknowledged:{source_name}:planner"
        )
    planner = (report.get("downstream_acknowledgements") or {}).get("planner")
    coder = (report.get("downstream_acknowledgements") or {}).get("coder")
    return bool(
        selected_sources
        and report.get("canonical") is True
        and report.get("go_eligible") is False
        and list(report.get("required_context_blockers") or []) == expected_blockers
        and list(report.get("applicable_consumers") or []) == ["planner"]
        and isinstance(planner, Mapping)
        and planner.get("applicable") is True
        and planner.get("acknowledged") is False
        and list(planner.get("sources") or []) == []
        and isinstance(coder, Mapping)
        and coder.get("applicable") is False
        and coder.get("acknowledged") is False
    )


def _bound_coder_context_text(report: Mapping[str, Any]) -> str | None:
    architect_sources = [
        source
        for source in report.get("sources_considered", [])
        if isinstance(source, Mapping)
        and str(source.get("source") or "")
        == ARCHITECT_REPOSITORY_CONTEXT_SOURCE
    ]
    if len(architect_sources) != 1:
        return None
    packet = architect_sources[0].get("packet")
    rendered = (
        packet.get("rendered_coder_context")
        if isinstance(packet, Mapping)
        else None
    )
    return rendered if isinstance(rendered, str) and rendered else None


def _normalize_selected_context_packet(packet: Any) -> dict[str, Any]:
    """Bound non-empty packets once while preserving an empty packet's truth."""

    if not isinstance(packet, Mapping) or not packet:
        return {}
    bounded_context = packet.get("bounded_context")
    packet_sha256 = packet.get("packet_sha256")
    bounded_context_sha256 = packet.get("bounded_context_sha256")
    truncated = packet.get("truncated")
    expected_keys = {
        "schema_version",
        "bounded_context",
        "packet_sha256",
        "bounded_context_sha256",
        "truncated",
    }
    if (
        set(packet) == expected_keys
        and packet.get("schema_version") == _BOUNDED_CONTEXT_PACKET_SCHEMA
        and isinstance(bounded_context, str)
        and len(bounded_context) <= 4_000
        and isinstance(packet_sha256, str)
        and re.fullmatch(r"[0-9a-f]{64}", packet_sha256) is not None
        and isinstance(bounded_context_sha256, str)
        and re.fullmatch(r"[0-9a-f]{64}", bounded_context_sha256) is not None
        and bounded_context_sha256
        == hashlib.sha256(bounded_context.encode("utf-8")).hexdigest()
        and isinstance(truncated, bool)
        and (
            (truncated and len(bounded_context) == 4_000)
            or (
                not truncated
                and packet_sha256
                == hashlib.sha256(bounded_context.encode("utf-8")).hexdigest()
            )
        )
    ):
        return json.loads(json.dumps(dict(packet), sort_keys=True, default=str))
    packet_json = json.dumps(
        dict(packet),
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    bounded_context = packet_json[:4_000]
    return {
        "schema_version": _BOUNDED_CONTEXT_PACKET_SCHEMA,
        "bounded_context": bounded_context,
        "packet_sha256": hashlib.sha256(packet_json.encode("utf-8")).hexdigest(),
        "bounded_context_sha256": hashlib.sha256(
            bounded_context.encode("utf-8")
        ).hexdigest(),
        "truncated": len(packet_json) > 4_000,
    }


def _context_source_material_sha256(report: Mapping[str, Any]) -> str:
    sources: list[dict[str, Any]] = []
    for raw in report.get("sources_considered", []):
        if not isinstance(raw, Mapping):
            continue
        sources.append(
            {
                "source": str(raw.get("source") or ""),
                "considered": raw.get("considered") is not False,
                "status": str(raw.get("status") or ""),
                "reason": str(raw.get("reason") or ""),
                "required": raw.get("required") is True,
                "selected": raw.get("selected") is True,
                "included": raw.get("included") is True,
                "packet": (
                    dict(raw["packet"])
                    if isinstance(raw.get("packet"), Mapping)
                    else {}
                ),
                "authority": (
                    dict(raw["authority"])
                    if isinstance(raw.get("authority"), Mapping)
                    else {}
                ),
            }
        )
    return _sha256_json(sources)


def _validate_persisted_planner_context_report(
    planned: Mapping[str, Any],
    refreshed: Mapping[str, Any],
) -> str:
    common_error = _validate_refreshed_context_common(planned, refreshed)
    if common_error:
        return common_error
    selected = [str(value) for value in refreshed.get("selected_sources", [])]
    planner = (refreshed.get("downstream_acknowledgements") or {}).get(
        "planner"
    )
    coder = (refreshed.get("downstream_acknowledgements") or {}).get("coder")
    if not (
        list(refreshed.get("applicable_consumers") or []) == ["planner"]
        and isinstance(planner, Mapping)
        and planner.get("applicable") is True
        and planner.get("acknowledged") is True
        and list(planner.get("sources") or []) == selected
        and isinstance(coder, Mapping)
        and coder.get("applicable") is False
        and coder.get("acknowledged") is False
    ):
        return "generic_workspace_refreshed_context_planner_acknowledgement_invalid"
    return ""


def _validate_coder_context_report(
    planned: Mapping[str, Any],
    refreshed: Mapping[str, Any],
) -> str:
    common_error = _validate_refreshed_context_common(planned, refreshed)
    if common_error:
        return common_error
    selected = [str(value) for value in refreshed.get("selected_sources", [])]
    planner = (refreshed.get("downstream_acknowledgements") or {}).get(
        "planner"
    )
    coder = (refreshed.get("downstream_acknowledgements") or {}).get("coder")
    if not (
        list(refreshed.get("applicable_consumers") or []) == [
            "planner",
            "coder",
        ]
        and isinstance(planner, Mapping)
        and planner.get("applicable") is True
        and planner.get("acknowledged") is True
        and list(planner.get("sources") or []) == selected
        and isinstance(coder, Mapping)
        and coder.get("applicable") is True
        and coder.get("acknowledged") is True
        and list(coder.get("sources") or []) == selected
        and list(refreshed.get("consumed_sources") or []) == selected
    ):
        return "generic_workspace_refreshed_context_coder_acknowledgement_missing"
    return ""


def _validate_refreshed_context_common(
    planned: Mapping[str, Any],
    refreshed: Mapping[str, Any],
) -> str:
    if (
        refreshed.get("canonical") is not True
        or refreshed.get("go_eligible") is not True
        or re.fullmatch(
            r"[0-9a-f]{64}",
            str(refreshed.get("canonical_report_hash") or "").removeprefix(
                "sha256:"
            ),
        )
        is None
        or not _canonical_context_report_self_consistent(refreshed)
    ):
        return "generic_workspace_refreshed_context_invalid"
    if [str(value) for value in refreshed.get("selected_sources", [])] != [
        str(value) for value in planned.get("selected_sources", [])
    ]:
        return "generic_workspace_refreshed_context_selection_mismatch"
    if _context_source_material_sha256(planned) != _context_source_material_sha256(
        refreshed
    ):
        return "generic_workspace_refreshed_context_material_mismatch"
    return ""


def _canonical_context_report_self_consistent(report: Mapping[str, Any]) -> bool:
    sources: list[dict[str, Any]] = []
    for raw in report.get("sources_considered", []):
        if not isinstance(raw, Mapping):
            return False
        source = dict(raw)
        source["consumed"] = raw.get("consumed_claimed") is True
        sources.append(source)
    rebuilt = build_context_broker_report(
        sources,
        downstream_consumers=(
            report.get("downstream_acknowledgements")
            if isinstance(report.get("downstream_acknowledgements"), Mapping)
            else {}
        ),
        applicable_consumers=list(report.get("applicable_consumers") or []),
    )
    decision_fields = (
        "schema_version",
        "canonical",
        "sources_considered",
        "source_status",
        "selected_sources",
        "included_sources",
        "consumed_sources",
        "applicable_consumers",
        "downstream_acknowledgements",
        "required_context_blockers",
        "go_eligible",
        "verdict",
        "canonical_report_hash",
    )
    return all(rebuilt.get(field) == report.get(field) for field in decision_fields)


def _context_callback_block_response(reason_code: str) -> str:
    return json.dumps(
        {
            "action": "blocked",
            "reason_code": reason_code,
            "reason": "Canonical context binding failed before provider dispatch.",
            "needed_context": [
                "Persist and acknowledge the exact canonical context report."
            ],
        },
        sort_keys=True,
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


def _is_timeout_exception(error: BaseException) -> bool:
    name = type(error).__name__.lower()
    message = str(error).lower()
    return "timeout" in name or "timed out" in message or "timeout" in message


def _preview_feedback(preview: Mapping[str, Any]) -> list[str]:
    feedback: list[str] = []
    coverage = preview.get("requirement_coverage")
    if isinstance(coverage, Mapping):
        missing = coverage.get("missing")
        if isinstance(missing, list):
            for item in missing[:8]:
                detail = " ".join(str(item or "").split())[:500]
                if detail:
                    feedback.append(
                        f"requirement_coverage_missing: {detail}"
                    )
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


def _canonical_review_artifact_snapshots_sha256(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
        default=str,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"
