from __future__ import annotations

from typing import Any


REQUIRED_PLAN5_FIELDS: tuple[str, ...] = (
    "task_id",
    "trace_id",
    "invocation_event_id",
    "consumer_event_id",
    "consumer_subsystem",
    "state_fields_changed",
    "focused_checks",
    "git_status",
    "evidence_budget_status",
)

FORBIDDEN_PLAN5_STATES: tuple[str, ...] = (
    "preview_only_completion",
    "advisory_only_completion",
    "read_only_completion_for_action_capable_system",
    "skipped_required_lane",
    "unconsumed_output",
    "fake_productive_go",
)


def build_plan5_acceptance_gate(
    task_payload: dict[str, Any],
    *,
    subsystem: str,
    focused_checks: list[str],
    git_status: str,
    evidence_budget_status: str,
) -> dict[str, Any]:
    """Validate one consumed subsystem trace for Plan 5 acceptance.

    The harness reads the existing long-running-task payload. It does not invoke
    a model, execute a route, apply a patch, or mint a consumer event. That keeps
    Plan 5 acceptance separate from the subsystem that must prove itself.
    """
    task = task_payload.get("task") if isinstance(task_payload.get("task"), dict) else {}
    snapshot = task.get("ast_snapshot") if isinstance(task.get("ast_snapshot"), dict) else {}
    integrations = (
        snapshot.get("plan_2_subsystem_integrations")
        if isinstance(snapshot.get("plan_2_subsystem_integrations"), dict)
        else {}
    )
    record = integrations.get(subsystem) if isinstance(integrations.get(subsystem), dict) else {}
    causal_events = task.get("causal_events") if isinstance(task.get("causal_events"), list) else []
    trace = task.get("causal_trace") if isinstance(task.get("causal_trace"), dict) else {}

    evidence = {
        "task_id": str(task.get("id") or ""),
        "trace_id": str(record.get("trace_id") or trace.get("trace_id") or ""),
        "invocation_event_id": str(record.get("invocation_event_id") or trace.get("invocation_event_id") or ""),
        "consumer_event_id": str(record.get("consumer_event_id") or trace.get("consumer_event_id") or ""),
        "consumer_subsystem": str(record.get("consumer_subsystem") or trace.get("consumer_subsystem") or ""),
        "state_fields_changed": _state_fields_changed_for(causal_events, str(record.get("consumer_event_id") or "")),
        "focused_checks": [item for item in focused_checks if item],
        "git_status": git_status.strip(),
        "evidence_budget_status": evidence_budget_status.strip(),
        "output_hash": str(record.get("output_hash") or ""),
        "subsystem": subsystem,
        "subsystem_status": str(record.get("status") or ""),
    }

    missing_fields = [
        field
        for field in REQUIRED_PLAN5_FIELDS
        if not _field_present(evidence.get(field))
    ]
    invocation_event = _event_by_id(causal_events, evidence["invocation_event_id"])
    consumer_event = _event_by_id(causal_events, evidence["consumer_event_id"])
    failures: list[str] = []
    record_invocation_event_id = str(record.get("invocation_event_id") or "")
    record_consumer_event_id = str(record.get("consumer_event_id") or "")

    if not record:
        failures.append("subsystem_record_missing")
    if not record_invocation_event_id:
        if "invocation_event_id" not in missing_fields:
            missing_fields.append("invocation_event_id")
        failures.append("invocation_event_missing")
    if not record_consumer_event_id:
        if "consumer_event_id" not in missing_fields:
            missing_fields.append("consumer_event_id")
        failures.append("consumer_event_missing")
    if invocation_event is None:
        failures.append("invocation_event_missing")
    if consumer_event is None:
        failures.append("consumer_event_missing")
    if invocation_event and invocation_event.get("trace_id") != evidence["trace_id"]:
        failures.append("invocation_trace_mismatch")
    if consumer_event and consumer_event.get("trace_id") != evidence["trace_id"]:
        failures.append("consumer_trace_mismatch")
    if consumer_event and consumer_event.get("consumer_subsystem") != evidence["consumer_subsystem"]:
        failures.append("consumer_subsystem_mismatch")
    if not evidence["output_hash"]:
        failures.append("output_hash_missing")
    if evidence["subsystem_status"] in {"", "PREVIEW_ONLY", "ADVISORY_ONLY", "READ_ONLY"}:
        failures.append("subsystem_not_decision_bearing")
    if missing_fields:
        failures.append("required_fields_missing")

    forbidden_states = _forbidden_states_present(task_payload)
    status = "GO" if not failures and not forbidden_states else "NEEDS_FIX"
    return {
        "plan": 5,
        "status": status,
        "required_verdict": "GO",
        "subsystem": subsystem,
        "required_fields": list(REQUIRED_PLAN5_FIELDS),
        "missing_fields": missing_fields,
        "forbidden_states": forbidden_states,
        "forbidden_state_catalog": list(FORBIDDEN_PLAN5_STATES),
        "failures": failures,
        "evidence": evidence,
        "output_consumed_downstream": consumer_event is not None and bool(record_consumer_event_id),
        "same_trace": (
            invocation_event is not None
            and consumer_event is not None
            and invocation_event.get("trace_id") == consumer_event.get("trace_id") == evidence["trace_id"]
        ),
        "state_fields_changed_present": bool(evidence["state_fields_changed"]),
        "failure_changes_final_verdict": _failure_changes_final_verdict(evidence),
    }


def _field_present(value: Any) -> bool:
    if isinstance(value, list):
        return bool(value)
    return bool(str(value or "").strip())


def _event_by_id(events: list[Any], event_id: str) -> dict[str, Any] | None:
    if not event_id:
        return None
    for event in events:
        if isinstance(event, dict) and event.get("event_id") == event_id:
            return event
    return None


def _state_fields_changed_for(events: list[Any], consumer_event_id: str) -> list[str]:
    event = _event_by_id(events, consumer_event_id)
    if not event:
        return []
    fields = event.get("changed_state_fields")
    if not isinstance(fields, list):
        return []
    return [str(field) for field in fields if str(field or "").strip()]


def _forbidden_states_present(value: Any) -> list[str]:
    found: set[str] = set()

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            for key, nested in item.items():
                text = str(key)
                if text in FORBIDDEN_PLAN5_STATES and nested:
                    found.add(text)
                if isinstance(nested, str) and nested in FORBIDDEN_PLAN5_STATES:
                    found.add(nested)
                visit(nested)
        elif isinstance(item, list):
            for nested in item:
                visit(nested)

    visit(value)
    return sorted(found)


def _failure_changes_final_verdict(evidence: dict[str, Any]) -> bool:
    fields = {str(field) for field in evidence.get("state_fields_changed", [])}
    status = str(evidence.get("subsystem_status") or "")
    return bool(
        fields.intersection({"status", "architect_status", "architect_reason"})
        or status.startswith("BLOCKED")
        or status in {"FAILED", "NEEDS_FIX"}
    )
