from __future__ import annotations

from typing import Any

from source_proxy.decision.model_lanes import (
    active_primary_coder_lane,
    get_model_lane,
    lane_selection_observability,
    model_lane_registry,
)


CARTOGRAPHER_ROUTING_PREVIEW_VERSION = "source-proxy-cartographer-routing-preview-v0.1"


def cartographer_routing_ownership_contract() -> dict[str, Any]:
    return {
        "contract_version": "source-proxy-cartographer-routing-ownership-v0.1",
        "preview_only": True,
        "live_routing_enabled": False,
        "worker_start_enabled": False,
        "model_calls_enabled": False,
        "memory_writes_enabled": False,
        "eventual_owner": "Cartographer",
        "eventual_owned_surfaces": [
            "model lane inventory",
            "context source selection",
            "worker eligibility",
            "verifier requirement",
            "dirty-tree awareness",
            "cost/usage class",
            "privacy/sovereignty class",
            "approval gates",
            "performance evidence",
            "promotion/demotion status",
            "known failure modes",
        ],
        "current_boundary": "Source Proxy emits preview metadata; Cartographer does not execute routing in this task.",
    }


def build_cartographer_routing_preview(
    *,
    task_type: str = "disposable_artifact",
    context_needed: list[str] | None = None,
    dirty_tree: bool = False,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    primary = active_primary_coder_lane()
    sidecar = get_model_lane("hermes_sidecar_verifier_preview")
    observability = lane_selection_observability(task_type=task_type, evidence_refs=evidence_refs)
    reason_codes = [
        "preview_only_no_worker_start",
        "qwen_primary_coder_preserved",
        "sidecar_lane_future_only",
        "cartographer_live_routing_not_enabled",
    ]
    if dirty_tree:
        reason_codes.append("dirty_tree_requires_operator_awareness")

    return {
        "preview_version": CARTOGRAPHER_ROUTING_PREVIEW_VERSION,
        "preview_only": True,
        "would_start_worker": False,
        "would_call_model": False,
        "would_write_memory": False,
        "task_type": task_type,
        "context_needed": list(context_needed or _default_context_for(task_type)),
        "recommended_coder_lane": primary["lane_id"],
        "recommended_sidecar_lane": sidecar["lane_id"],
        "recommended_sidecar_status": sidecar["status"],
        "verifier_required": observability["verifier_lane_required"],
        "approval_required": primary["approval_required"],
        "cost_class": primary["cost_class"],
        "privacy_class": primary["privacy_class"],
        "dirty_tree_awareness": {
            "dirty_tree": dirty_tree,
            "can_proceed_without_operator_review": not dirty_tree,
        },
        "promotion_status": primary["promotion_status"],
        "known_failure_modes": primary["known_failure_modes"],
        "reason_codes": reason_codes,
        "evidence_refs": list(evidence_refs or []),
        "lane_registry_version": model_lane_registry()["registry_version"],
        "future_only_explanation": "Hermes/Gemma sidecars are preview metadata only until separately approved and proven.",
    }


def _default_context_for(task_type: str) -> list[str]:
    if task_type in {"disposable_artifact", "behavior_check"}:
        return ["user_prompt", "behavior_contract", "generated_preview", "browser_observation", "retest_result"]
    if task_type == "repo_patch_preview":
        return ["user_prompt", "allowed_files", "diff_preview", "tests", "dirty_tree_status"]
    return ["user_prompt", "operator_scope"]
