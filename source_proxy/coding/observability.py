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
    expected_consumer = coding_executor_consumer("coder")
    actual_consumer = str(authority.get("consumer") or "")
    identity = authority.get("target_plugin_identity")
    identity = dict(identity) if isinstance(identity, Mapping) else None
    authority_bound = bool(authority) and actual_consumer == expected_consumer
    orchestrator_recorded = orchestrator.get("schema_version") == "coding-orchestrator/v1"

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
