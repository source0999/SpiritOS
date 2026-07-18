"""Read-only canonical shell observability for a persisted coding run."""
from __future__ import annotations

from typing import Any, Mapping

from source_proxy.approval.campaign_authority import coding_executor_consumer
from source_proxy.cartographer.lane_registry import CORE_CODING_LANE_IDS
from source_proxy.tasks.long_running import get_long_running_task_snapshot


def build_coding_shell_observability(task_id: str) -> dict[str, Any]:
    """Expose recorded run facts; absence is reported, never filled in."""

    envelope = get_long_running_task_snapshot(task_id)
    task = envelope.get("task") if isinstance(envelope, Mapping) else None
    if not isinstance(task, Mapping):
        raise ValueError("coding_observability_task_payload_invalid")
    snapshot = task.get("ast_snapshot")
    snapshot = snapshot if isinstance(snapshot, Mapping) else {}
    orchestrator = snapshot.get("coding_orchestrator")
    orchestrator = orchestrator if isinstance(orchestrator, Mapping) else {}
    authority = snapshot.get("campaign_2_approval")
    authority = authority if isinstance(authority, Mapping) else {}
    lane_states = orchestrator.get("lane_states")
    lane_states = lane_states if isinstance(lane_states, Mapping) else {}
    lane_reasons = orchestrator.get("lane_reasons")
    lane_reasons = lane_reasons if isinstance(lane_reasons, Mapping) else {}
    integrations = snapshot.get("plan_2_subsystem_integrations")
    integrations = integrations if isinstance(integrations, Mapping) else {}
    expected_consumer = coding_executor_consumer("coder")
    actual_consumer = str(authority.get("consumer") or "")
    identity = authority.get("target_plugin_identity")
    identity = dict(identity) if isinstance(identity, Mapping) else None
    authority_bound = bool(authority) and actual_consumer == expected_consumer
    orchestrator_recorded = orchestrator.get("schema_version") == "coding-orchestrator/v2"

    return {
        "schema_version": "coding-shell-observability/v1",
        "access_scope": "read_only_persisted_coding_run_observability",
        "task_id": task_id,
        "task_status": str(task.get("status") or "unknown"),
        "lane_participation": [
            {
                "lane_id": lane_id,
                "state": str(lane_states.get(lane_id) or "not_recorded"),
                "reason": str(lane_reasons.get(lane_id) or ""),
            }
            for lane_id in CORE_CODING_LANE_IDS
        ],
        "orchestrator": {
            "recorded": orchestrator_recorded,
            "run_id": str(orchestrator.get("run_id") or ""),
            "summary": str(orchestrator.get("summary") or "not_recorded"),
        },
        "authority": {
            "recorded": bool(authority),
            "consumer": actual_consumer or None,
            "expected_consumer": expected_consumer,
            "lane_binding_valid": authority_bound,
            "generation": authority.get("generation"),
        },
        "evidence_identity": identity,
        "extended_lane_lifecycle": [_extended_lifecycle(lane_id, record) for lane_id, record in sorted(integrations.items()) if isinstance(record, Mapping)],
        "diagnosis": {
            "schema_version": "campaign-3/diagnosis-envelope/v1",
            "read_only": True,
            "conflict_claim_ceiling": _conflict_claim_ceiling(snapshot),
            "redaction_verdict": "not_rendered_read_only_metadata_only",
            "recovery_available": any(str(record.get("status") or "").startswith("BLOCKED") for record in integrations.values() if isinstance(record, Mapping)),
        },
        "verdict": _observability_verdict(
            orchestrator_recorded=orchestrator_recorded,
            authority_recorded=bool(authority),
            authority_bound=authority_bound,
            identity=identity,
        ),
    }


def _observability_verdict(
    *,
    orchestrator_recorded: bool,
    authority_recorded: bool,
    authority_bound: bool,
    identity: dict[str, Any] | None,
) -> str:
    if not orchestrator_recorded:
        return "PENDING: coding_orchestrator_state_not_recorded"
    if not authority_recorded:
        return "PENDING: coding_authority_not_recorded"
    if not authority_bound:
        return "DEGRADED: coding_authority_lane_binding_invalid"
    if identity is None:
        return "PENDING: target_plugin_identity_not_recorded"
    return "RECORDED: canonical_coding_run_facts_available"


def _extended_lifecycle(lane_id: Any, record: Mapping[str, Any]) -> dict[str, Any]:
    status = str(record.get("status") or "not_recorded")
    failed = status in {"BLOCKED_ENV", "BLOCKED", "NEEDS_FIX", "FAILED", "DEGRADED"}
    return {
        "lane_id": str(lane_id), "applicable": True, "requested": True,
        "selected": True, "invoked": bool(record.get("invocation_event_id")),
        "active": False, "completed": not failed, "failed": failed,
        "timed_out": "timeout" in str(record.get("failure_reason") or "").lower(),
        "retried": False, "fallback": False, "status": status,
        "output_identity": str(record.get("output_hash") or "") or None,
        "consumed": bool(record.get("consumer_event_id")),
        "acknowledged": bool(record.get("consumer_subsystem")),
        "evidence_identity": str(record.get("output_hash") or "") or None,
        "failure_reason": str(record.get("failure_reason") or "") or None,
    }


def _conflict_claim_ceiling(snapshot: Mapping[str, Any]) -> str:
    last = snapshot.get("plan_2_last_subsystem_output")
    output = last.get("output") if isinstance(last, Mapping) and isinstance(last.get("output"), Mapping) else {}
    receipt = output.get("conflict_receipt") if isinstance(output.get("conflict_receipt"), Mapping) else {}
    return str(receipt.get("claim_ceiling") or "not_recorded")
