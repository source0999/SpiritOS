from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from source_proxy.tasks.long_running import (
    LongRunningTaskError,
    _append_causal_event,
    _ensure_ast_snapshot_dict,
    _ensure_causal_trace_id,
    _lookup_task,
    _now_iso,
    _save_task,
    create_long_running_task,
    get_long_running_task,
)


PLAN3_STATUSES: tuple[str, ...] = (
    "queued",
    "policy_checking",
    "policy_blocked",
    "executing",
    "worker_dispatched",
    "worker_returned",
    "applied_needs_verification",
    "verification_running",
    "verified",
    "repair_needed",
    "repair_running",
    "repair_applied_needs_verification",
    "failed_needs_human",
    "blocked_env",
    "blocked_human",
    "cancelled",
)

PLAN3_TERMINAL_STATUSES = {
    "policy_blocked",
    "verified",
    "failed_needs_human",
    "blocked_env",
    "blocked_human",
    "cancelled",
}

PLAN3_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "queued": ("policy_checking", "cancelled"),
    "policy_checking": ("policy_blocked", "executing", "blocked_env", "blocked_human"),
    "executing": (
        "worker_dispatched",
        "worker_returned",
        "repair_needed",
        "failed_needs_human",
        "blocked_env",
    ),
    "worker_dispatched": (
        "worker_returned",
        "repair_needed",
        "failed_needs_human",
        "blocked_env",
    ),
    "worker_returned": (
        "applied_needs_verification",
        "verification_running",
        "repair_needed",
        "failed_needs_human",
    ),
    "applied_needs_verification": (
        "verification_running",
        "repair_needed",
        "verified",
        "failed_needs_human",
    ),
    "verification_running": ("verified", "repair_needed", "failed_needs_human"),
    "repair_needed": ("repair_running", "failed_needs_human"),
    "repair_running": (
        "repair_applied_needs_verification",
        "repair_needed",
        "failed_needs_human",
    ),
    "repair_applied_needs_verification": (
        "verification_running",
        "verified",
        "failed_needs_human",
    ),
    "policy_blocked": (),
    "verified": (),
    "failed_needs_human": (),
    "blocked_env": (),
    "blocked_human": (),
    "cancelled": (),
}

PLAN3_FAILURE_CLASSES = {
    "policy_blocked",
    "blocked_human",
    "blocked_env",
    "worker_unavailable",
    "provider_unavailable",
    "model_timeout",
    "model_failed",
    "verifier_failed",
    "repair_failed",
    "unsafe_path_rejected",
    "unsupported_job_type",
    "validation_failed",
    "unknown_error",
}

FAIL_CLOSED_ACTIONS = {
    "cartographer_git_mutation",
    "push",
    "media_jellyfin_mutation",
    "docker_systemd_mutation",
}

HUMAN_REQUIRED_ACTIONS = {
    "mac_write",
    "obsidian_write",
    "source_patch",
    "external_web_research",
    "model_lane_execution",
    "browser_functional_verification",
    "repair_apply",
}

ENV_REQUIRED_ACTIONS = {"worker_dispatch"}


Verifier = Callable[[Path], bool]


def create_plan3_durable_task(
    description: str,
    *,
    run_id: str = "plan3-durable-execution",
    approval_id: str | None = None,
    max_attempts: int = 3,
) -> dict[str, Any]:
    envelope = create_long_running_task(description)
    task_id = envelope["task"]["id"]
    task = _lookup_task(task_id)
    trace_id = _ensure_causal_trace_id(task)
    created_at = _now_iso()
    state = {
        "task_id": task.id,
        "trace_id": trace_id,
        "run_id": run_id,
        "approval_id": approval_id,
        "current_status": task.status,
        "previous_status": "",
        "attempt_count": 0,
        "max_attempts": max(1, int(max_attempts)),
        "last_error": "",
        "blocked_reason": "",
        "policy_decision": "",
        "recovery_marker": "",
        "repair_attempt_count": 0,
        "verification_result": "",
        "repair_result": "",
        "latest_invocation_event_id": "",
        "latest_consumer_event_id": "",
        "created_at": created_at,
        "updated_at": created_at,
    }
    snapshot = _ensure_ast_snapshot_dict(task)
    snapshot["plan_3_durable_state"] = state
    task.ast_snapshot = snapshot
    invocation = _append_causal_event(
        task,
        event_type="invocation",
        subsystem="source_proxy_plan3_durable_execution",
        run_id=run_id,
        status_before="",
        status_after=task.status,
        changed_state_fields=["ast_snapshot"],
        notes=["Plan 3 durable task initialized in existing long-running task store"],
    )
    state["latest_invocation_event_id"] = invocation["event_id"]
    _store_plan3_state(task, state)
    return get_long_running_task(task.id)


def transition_plan3_status(
    task_id: str,
    next_status: str,
    *,
    reason: str = "",
    failure_class: str = "",
    last_error: str = "",
    policy_decision: str = "",
    recovery_marker: str = "",
    verification_result: str = "",
    repair_result: str = "",
) -> dict[str, Any]:
    task = _lookup_task(task_id)
    state = _require_plan3_state(task)
    return _transition_plan3_status(
        task,
        state,
        next_status,
        event_type="status_transition",
        reason=reason,
        failure_class=failure_class,
        last_error=last_error,
        policy_decision=policy_decision,
        recovery_marker=recovery_marker,
        verification_result=verification_result,
        repair_result=repair_result,
    )


def apply_plan3_policy(
    task_id: str,
    *,
    action: str,
    target_path: str = "",
    approved_actions: set[str] | None = None,
) -> dict[str, Any]:
    task = _lookup_task(task_id)
    state = _require_plan3_state(task)
    if state["current_status"] == "queued":
        _transition_plan3_status(
            task,
            state,
            "policy_checking",
            event_type="status_transition",
            reason="policy gate entered",
        )
        task = _lookup_task(task_id)
        state = _require_plan3_state(task)

    decision = evaluate_plan3_policy(
        action=action,
        target_path=target_path,
        approved_actions=approved_actions or set(),
    )
    status_after = decision["status_after"]
    event = _append_causal_event(
        task,
        event_type="policy",
        subsystem="source_proxy_plan3_policy_gate",
        run_id=state["run_id"],
        status_before=task.status,
        status_after=status_after,
        changed_state_fields=["ast_snapshot", "status"],
        notes=[
            f"action={decision['action']}",
            f"policy_decision={decision['policy_decision']}",
            f"reason={decision['reason']}",
        ],
    )
    state["policy_decision"] = decision["policy_decision"]
    state["blocked_reason"] = decision["reason"] if decision["blocked"] else ""
    state["latest_policy_event_id"] = event["event_id"]
    _store_plan3_state(task, state)
    return _transition_plan3_status(
        task,
        state,
        status_after,
        event_type="status_transition",
        reason=decision["reason"],
        failure_class=decision["failure_class"],
        policy_decision=decision["policy_decision"],
    )


def evaluate_plan3_policy(
    *,
    action: str,
    target_path: str = "",
    approved_actions: set[str] | None = None,
) -> dict[str, Any]:
    normalized_action = _normalize_action(action)
    approved = {_normalize_action(item) for item in (approved_actions or set())}
    normalized_target = target_path.replace("\\", "/").lower()
    if normalized_action == "mac_write" and (
        normalized_target.startswith("/system/")
        or "/../" in normalized_target
        or normalized_target.startswith("../")
    ):
        return _policy_decision(
            normalized_action,
            "policy_blocked",
            "unsafe_path_rejected",
            "unsafe_path_rejected",
        )
    if normalized_action in FAIL_CLOSED_ACTIONS:
        return _policy_decision(
            normalized_action,
            "policy_blocked",
            "policy_blocked",
            f"{normalized_action}_forbidden",
        )
    if normalized_action in ENV_REQUIRED_ACTIONS and normalized_action not in approved:
        return _policy_decision(
            normalized_action,
            "blocked_env",
            "blocked_env",
            f"{normalized_action}_environment_missing",
        )
    if normalized_action in HUMAN_REQUIRED_ACTIONS and normalized_action not in approved:
        return _policy_decision(
            normalized_action,
            "blocked_human",
            "blocked_human",
            f"{normalized_action}_requires_explicit_approval",
        )
    if normalized_action not in HUMAN_REQUIRED_ACTIONS | FAIL_CLOSED_ACTIONS | ENV_REQUIRED_ACTIONS:
        return _policy_decision(
            normalized_action,
            "policy_blocked",
            "unsupported_job_type",
            "unsupported_job_type",
        )
    return {
        "action": normalized_action,
        "blocked": False,
        "failure_class": "",
        "policy_decision": "allow",
        "reason": "allowed_by_explicit_plan3_policy",
        "status_after": "executing",
    }


def record_plan3_failure_attempt(
    task_id: str,
    *,
    failure_class: str,
    last_error: str,
    retryable: bool,
) -> dict[str, Any]:
    if failure_class not in PLAN3_FAILURE_CLASSES:
        failure_class = "unknown_error"
    task = _lookup_task(task_id)
    state = _require_plan3_state(task)
    state["attempt_count"] = int(state.get("attempt_count") or 0) + 1
    state["last_error"] = last_error[:1000]
    state["last_failure_class"] = failure_class
    state["retryable"] = bool(retryable)
    max_attempts = int(state.get("max_attempts") or 1)
    exhausted = state["attempt_count"] >= max_attempts
    event_type = "retry" if retryable and not exhausted else "failure"
    event = _append_causal_event(
        task,
        event_type=event_type,
        subsystem="source_proxy_plan3_retry_timeout_failure",
        run_id=state["run_id"],
        status_before=task.status,
        status_after=task.status,
        changed_state_fields=["ast_snapshot"],
        notes=[
            f"failure_class={failure_class}",
            f"attempt={state['attempt_count']}/{max_attempts}",
            f"retryable={retryable}",
        ],
    )
    state["latest_failure_event_id"] = event["event_id"]
    state["retry_delay_recorded"] = retryable and not exhausted
    _store_plan3_state(task, state)
    if failure_class in {"policy_blocked", "unsafe_path_rejected", "unsupported_job_type"}:
        return transition_plan3_status(
            task.id,
            "policy_blocked",
            reason=failure_class,
            failure_class=failure_class,
            last_error=last_error,
        )
    if failure_class == "blocked_env":
        return transition_plan3_status(
            task.id,
            "blocked_env",
            reason=failure_class,
            failure_class=failure_class,
            last_error=last_error,
        )
    if retryable and not exhausted:
        return get_long_running_task(task.id)
    return transition_plan3_status(
        task.id,
        "failed_needs_human",
        reason=f"{failure_class}_attempts_exhausted",
        failure_class=failure_class,
        last_error=last_error,
    )


def recover_plan3_task(task_id: str) -> dict[str, Any]:
    task = _lookup_task(task_id)
    state = _require_plan3_state(task)
    status = str(state.get("current_status") or task.status)
    terminal = status in PLAN3_TERMINAL_STATUSES
    marker = "terminal_readback_no_reexecution" if terminal else f"recovered_from_{status}"
    state["recovery_marker"] = marker
    state["duplicate_action_prevented"] = True
    event = _append_causal_event(
        task,
        event_type="recovery",
        subsystem="source_proxy_plan3_recovery",
        run_id=state["run_id"],
        status_before=task.status,
        status_after=task.status,
        changed_state_fields=["ast_snapshot"],
        notes=[marker],
    )
    state["latest_recovery_event_id"] = event["event_id"]
    _store_plan3_state(task, state)
    return get_long_running_task(task.id)


def run_plan3_verifier_driven_repair(
    task_id: str,
    *,
    workspace: Path,
    relative_file: str,
    repair_content: str,
    verifier: Verifier,
    max_repair_attempts: int = 2,
) -> dict[str, Any]:
    task = _lookup_task(task_id)
    state = _require_plan3_state(task)
    workspace = workspace.resolve()
    target = (workspace / relative_file).resolve()
    try:
        target.relative_to(workspace)
    except ValueError as error:
        raise LongRunningTaskError(
            "Repair target escapes disposable workspace.",
            "unsafe_path_rejected",
        ) from error
    if not target.is_file():
        raise LongRunningTaskError("Repair target is missing.", "validation_failed")

    if verifier(target):
        transition_plan3_status(
            task.id,
            "verified",
            reason="initial_verifier_passed",
            verification_result="VERIFIED",
        )
        return get_long_running_task(task.id)

    _transition_plan3_status(
        task,
        state,
        "repair_needed",
        event_type="verification",
        reason="verifier_failed_before_repair",
        failure_class="verifier_failed",
        verification_result="UNVERIFIED",
    )
    task = _lookup_task(task_id)
    state = _require_plan3_state(task)
    _transition_plan3_status(
        task,
        state,
        "repair_running",
        event_type="repair",
        reason="verifier_failure_triggered_repair",
    )
    task = _lookup_task(task_id)
    state = _require_plan3_state(task)
    state["repair_attempt_count"] = int(state.get("repair_attempt_count") or 0) + 1
    if state["repair_attempt_count"] > max_repair_attempts:
        _store_plan3_state(task, state)
        return transition_plan3_status(
            task.id,
            "failed_needs_human",
            reason="repair_attempts_exhausted",
            failure_class="repair_failed",
            repair_result="repair_attempts_exhausted",
        )

    target.write_text(repair_content, encoding="utf-8")
    state["repair_result"] = "actual_change_applied"
    state["repair_changed_files"] = [relative_file]
    _store_plan3_state(task, state)
    transition_plan3_status(
        task.id,
        "repair_applied_needs_verification",
        reason="repair_change_applied",
        repair_result="actual_change_applied",
    )
    task = _lookup_task(task_id)
    state = _require_plan3_state(task)
    _transition_plan3_status(
        task,
        state,
        "verification_running",
        event_type="verification",
        reason="repair_reverification_started",
    )
    final_verified = verifier(target)
    if final_verified:
        return transition_plan3_status(
            task.id,
            "verified",
            reason="repair_reverified",
            verification_result="VERIFIED",
            repair_result="repair_applied_and_reverified",
        )
    return transition_plan3_status(
        task.id,
        "failed_needs_human",
        reason="repair_reverification_failed",
        failure_class="repair_failed",
        verification_result="UNVERIFIED",
        repair_result="repair_applied_but_reverification_failed",
    )


def plan3_final_go_allowed(
    *,
    plan_2_carryforward: str,
    durable_state: str,
    policy_gates: str,
    retry_timeout_failure: str,
    recovery: str,
    repair_loop: str,
    task_a_policy: str,
    task_b_recovery: str,
    task_c_repair: str,
    operator_check: str,
    focused_tests: str,
    fake_go_detected: dict[str, bool],
    plan_4_started: bool,
) -> bool:
    return (
        plan_2_carryforward == "PASS"
        and durable_state == "INTEGRATED_LIVE"
        and policy_gates == "INTEGRATED_LIVE"
        and retry_timeout_failure == "INTEGRATED_LIVE"
        and recovery == "INTEGRATED_LIVE"
        and repair_loop == "INTEGRATED_LIVE"
        and task_a_policy == "PASS"
        and task_b_recovery == "PASS"
        and task_c_repair == "PASS"
        and operator_check == "PASS"
        and focused_tests == "PASS"
        and not any(fake_go_detected.values())
        and not plan_4_started
    )


def _transition_plan3_status(
    task: Any,
    state: dict[str, Any],
    next_status: str,
    *,
    event_type: str,
    reason: str,
    failure_class: str = "",
    last_error: str = "",
    policy_decision: str = "",
    recovery_marker: str = "",
    verification_result: str = "",
    repair_result: str = "",
) -> dict[str, Any]:
    if next_status not in PLAN3_STATUSES:
        raise LongRunningTaskError("Unsupported Plan 3 status.", "invalid_plan3_status")
    current_status = str(state.get("current_status") or task.status)
    if current_status in PLAN3_TERMINAL_STATUSES and next_status != current_status:
        raise LongRunningTaskError(
            "Terminal Plan 3 status cannot silently revert.",
            "terminal_status_revert_rejected",
        )
    if next_status != current_status and next_status not in PLAN3_TRANSITIONS.get(current_status, ()):
        raise LongRunningTaskError(
            f"Invalid Plan 3 transition: {current_status} -> {next_status}",
            "invalid_plan3_transition",
        )
    previous_status = current_status
    task.status = next_status
    state["previous_status"] = previous_status
    state["current_status"] = next_status
    state["updated_at"] = _now_iso()
    if failure_class:
        state["last_failure_class"] = failure_class
        state["blocked_reason"] = failure_class if next_status.startswith("blocked") else state.get("blocked_reason", "")
    if last_error:
        state["last_error"] = last_error[:1000]
    if policy_decision:
        state["policy_decision"] = policy_decision
    if recovery_marker:
        state["recovery_marker"] = recovery_marker
    if verification_result:
        state["verification_result"] = verification_result
    if repair_result:
        state["repair_result"] = repair_result
    event = _append_causal_event(
        task,
        event_type=event_type,  # type: ignore[arg-type]
        subsystem="source_proxy_plan3_durable_execution",
        run_id=state["run_id"],
        status_before=previous_status,
        status_after=next_status,
        changed_state_fields=["status", "ast_snapshot"],
        notes=[reason or f"{previous_status}->{next_status}"],
    )
    if event_type == "consumer":
        state["latest_consumer_event_id"] = event["event_id"]
    elif event_type == "invocation":
        state["latest_invocation_event_id"] = event["event_id"]
    _store_plan3_state(task, state)
    return get_long_running_task(task.id)


def _store_plan3_state(task: Any, state: dict[str, Any]) -> None:
    state["causal_events_json"] = list(task.causal_events[-50:])
    snapshot = _ensure_ast_snapshot_dict(task)
    snapshot["plan_3_durable_state"] = state
    task.ast_snapshot = snapshot
    task.updated_at = _now_iso()
    _save_task(task)


def _require_plan3_state(task: Any) -> dict[str, Any]:
    snapshot = task.ast_snapshot if isinstance(task.ast_snapshot, dict) else {}
    state = snapshot.get("plan_3_durable_state")
    if not isinstance(state, dict):
        raise LongRunningTaskError(
            "Task does not have Plan 3 durable state.",
            "plan3_state_missing",
        )
    return dict(state)


def _policy_decision(
    action: str,
    status_after: str,
    failure_class: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "action": action,
        "blocked": True,
        "failure_class": failure_class,
        "policy_decision": status_after,
        "reason": reason,
        "status_after": status_after,
    }


def _normalize_action(action: str) -> str:
    return "_".join(str(action or "").strip().lower().replace("/", " ").split())
