"""Declared recovery behavior for every retained Campaign 3 lane."""
from __future__ import annotations

from typing import Any


RECOVERY_SCHEMA_VERSION = "campaign-3/extended-lane-recovery/v1"
_LANES = {
    "extended.scout-research": ("conditional", "retry", "block_when_required"),
    "extended.obsidian-knowledge": ("conditional", "exclude_stale", "degrade_context_claim"),
    "extended.mac-worker": ("conditional", "retry", "block_when_platform_required"),
    "extended.context-model": ("conditional", "declared_fallback", "degrade_model_claim"),
    "extended.retained-sub-agent": ("conditional", "declared_fallback", "block_or_degrade_by_task_policy"),
    "extended.platform-verifier": ("conditional", "retry", "block_when_platform_required"),
    "extended.conflict-resolver": ("mandatory", "no_replacement", "block_on_unresolved_conflict"),
    "extended.diagnosis-envelope": ("mandatory", "retry", "retain_failed_run_diagnosis"),
}


def assess_extended_lane_failure(*, lane_id: str, failure: str, applicable: bool, replacement_used: bool = False) -> dict[str, Any]:
    if lane_id not in _LANES:
        raise ValueError("campaign_3_recovery_unknown_lane")
    if not str(failure).strip():
        raise ValueError("campaign_3_recovery_failure_required")
    mandatory, recovery, consequence = _LANES[lane_id]
    required = mandatory == "mandatory" or applicable
    if not required:
        outcome, ceiling = "SKIPPED", "not_applicable_no_claim"
    elif replacement_used and recovery in {"declared_fallback", "retry"}:
        outcome, ceiling = "RECOVERING", "recovery_claim_only_not_full_success"
    else:
        outcome, ceiling = "BLOCKED_ENV", "required_lane_failure_blocks_full_success"
    return {
        "schema_version": RECOVERY_SCHEMA_VERSION, "lane_id": lane_id,
        "applicable": applicable, "requirement": mandatory, "required": required,
        "failure": failure, "recovery": recovery, "consequence": consequence,
        "replacement_used": replacement_used, "outcome": outcome,
        "claim_ceiling": ceiling, "full_success_allowed": False,
        "external_host_failure": failure in {"host_unreachable", "timeout", "provider_unreachable"},
    }


def record_extended_lane_recovery_for_task(task_id: str, *, assessment: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    from source_proxy.tasks.long_running import record_subsystem_integration_result
    lane = str(assessment["lane_id"]).replace(".", "_")
    blocked = assessment["outcome"] == "BLOCKED_ENV"
    result = record_subsystem_integration_result(
        task_id, subsystem=f"campaign_3_recovery_{lane}", consumer_subsystem="coding_recovery_claim_ceiling_consumer",
        upstream_state={"task_id": task_id, "lane_id": assessment["lane_id"], "failure": assessment["failure"]},
        output={"summary": assessment["claim_ceiling"], "assessment": assessment, "evidence": evidence},
        status="BLOCKED_ENV" if blocked else "INTEGRATED_LIVE",
        changed_state_fields=["ast_snapshot.campaign_3_recovery"],
        failure_reason=assessment["failure"] if blocked else None,
        authoritative_state_mutation=False,
    )
    return {"status": "BLOCKED_ENV" if blocked else "INTEGRATED_LIVE", "assessment": assessment, "task": result["task"]}
