from __future__ import annotations

import hashlib
import json
from typing import Any

from source_proxy.decision.model_lanes import (
    build_fip3_model_lane_packet,
    build_model_lanes_preview,
)
from source_proxy.decision.verifier_lane import build_verifier_lane_packet, verifier_lane_preview
from source_proxy.routing.litellm_router import routing_status
from source_proxy.tasks.long_running import record_subsystem_integration_result


SPECIALIST_INTEGRATION_VERSION = "source-proxy-plan2-specialists-v1"
MODEL_LANE_FAILURE_STATUSES = {"blocked", "failed", "timeout", "error"}


def _json_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def confirmed_specialist_inventory() -> dict[str, Any]:
    preview = build_model_lanes_preview(task_type="repo_patch_preview")
    routes = routing_status()
    return {
        "version": SPECIALIST_INTEGRATION_VERSION,
        "qwen": _classification_for_lane(preview, "qwen_local_coder"),
        "gemma": _classification_for_lane(preview, "gemma_sidecar_context_preview"),
        "hermes": _classification_for_lane(preview, "hermes_sidecar_verifier_preview"),
        "browser_functional_verifier": "LIVE_INVOKABLE",
        "design_browser_specialist": "ADVISORY_ONLY",
        "route_status": routes,
    }


def _classification_for_lane(preview: dict[str, Any], lane_id: str) -> str:
    lanes = preview.get("available_lanes") if isinstance(preview.get("available_lanes"), list) else []
    lane = next((item for item in lanes if isinstance(item, dict) and item.get("lane_id") == lane_id), None)
    if not lane:
        return "MISSING"
    status = str(lane.get("status") or "")
    if lane_id == "qwen_local_coder" and status == "active_primary_local_lane":
        return "LIVE_INVOKABLE"
    if "preview" in status:
        return "PREVIEW_ONLY"
    return "STATUS_ONLY"


async def run_specialists_for_task(
    task_id: str,
    *,
    task: str,
    upstream_state: dict[str, Any],
    route_payload: dict[str, Any] | None = None,
    research_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inventory = confirmed_specialist_inventory()
    model_packet = await build_fip3_model_lane_packet(
        task=task,
        route_payload=route_payload or {},
        fip1_context_packet={"source_status": upstream_state},
        fip2_research_packet=research_packet or {},
    )
    verifier_packet = build_verifier_lane_packet(
        original_user_prompt=task,
        normalized_intent=str((model_packet.get("gemma") or {}).get("intent") or task),
        behavior_contract={"plan2_subsystem_acceptance": True},
        task_spec={"task_type": "plan2_subsystem_acceptance"},
        planner_criteria=[{"criterion_id": "plan2-causal-consumption"}],
        selected_coder_lane="qwen_local_coder",
        behavior_probe_evidence={"verdict": "UNVERIFIED", "reason": "Plan 2 contract proof, not a product PASS."},
    )
    verifier_output = verifier_lane_preview(verifier_packet)
    packet = {
        "version": SPECIALIST_INTEGRATION_VERSION,
        "summary": "Specialist lanes classified, invoked where current source exposes live callable paths, and verifier output consumed.",
        "inventory": inventory,
        "model_packet": model_packet,
        "verifier_output": verifier_output,
        "qwen": {
            "status": "INTEGRATED" if inventory["qwen"] == "LIVE_INVOKABLE" else inventory["qwen"],
            "consumer": "qwen_primary_coder_lane_selector",
        },
        "gemma": model_packet.get("gemma"),
        "hermes": model_packet.get("hermes_critic"),
        "browser_functional_verifier": verifier_output,
        "design_browser_specialist": inventory["design_browser_specialist"],
    }
    gemma_status = str((model_packet.get("gemma") or {}).get("status") or "")
    hermes_status = str((model_packet.get("hermes_critic") or {}).get("status") or "")
    status = "INTEGRATED_LIVE" if verifier_output.get("verdict") and inventory["qwen"] == "LIVE_INVOKABLE" else "NEEDS_FIX"
    if gemma_status in MODEL_LANE_FAILURE_STATUSES or hermes_status in MODEL_LANE_FAILURE_STATUSES:
        status = "BLOCKED_ENV"
    packet["status"] = status
    packet["specialist_packet_hash"] = _json_hash(packet)
    payload = record_subsystem_integration_result(
        task_id,
        subsystem="specialist_model_lanes",
        consumer_subsystem="cartographer_specialist_packet_consumer",
        upstream_state={
            **dict(upstream_state),
            "task": task,
            "research_packet_hash": (research_packet or {}).get("research_packet_hash", ""),
        },
        output=packet,
        status=status,
        changed_state_fields=["ast_snapshot.plan_2_specialists"],
        failure_reason=None if status == "INTEGRATED_LIVE" else "required_live_model_lane_unavailable_or_blocked",
    )
    return {
        "status": status,
        "specialist_packet": packet,
        "task": payload["task"],
    }
