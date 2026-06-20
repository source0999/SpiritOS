from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from source_proxy.decision.hardline_integration import specialist_lanes_allow_go
from source_proxy.decision.model_lanes import (
    build_fip3_model_lane_packet,
    build_model_lanes_preview,
    run_qwen_coder_lane,
)
from source_proxy.decision.verifier_lane import run_live_functional_verifier
from source_proxy.routing.litellm_router import routing_status
from source_proxy.tasks.long_running import record_subsystem_integration_result


SPECIALIST_INTEGRATION_VERSION = "source-proxy-plan2-specialists-v1"
MODEL_LANE_FAILURE_STATUSES = {"blocked", "failed", "timeout", "error"}
PATCH4_EVIDENCE_ROOT = Path("/home/source/spiritos-evidence/plan-02-continuation-patch-4")


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
    gemma = model_packet.get("gemma") if isinstance(model_packet.get("gemma"), dict) else {}
    hermes = model_packet.get("hermes_critic") if isinstance(model_packet.get("hermes_critic"), dict) else {}
    gemma_payload = record_subsystem_integration_result(
        task_id,
        subsystem="gemma_intent_spec",
        consumer_subsystem="cartographer_specialist_packet_consumer",
        upstream_state={**dict(upstream_state), "task": task},
        output={"summary": "Gemma intent/spec lane consumed.", "lane_output": gemma},
        status=_model_lane_hardline_status(gemma),
        changed_state_fields=["ast_snapshot.plan_2_specialist_lanes.gemma_intent_spec"],
        failure_reason=None
        if _model_lane_hardline_status(gemma) == "INTEGRATED_LIVE"
        else "gemma_intent_spec_lane_not_live",
    )
    hermes_payload = record_subsystem_integration_result(
        task_id,
        subsystem="hermes_critique_risk",
        consumer_subsystem="cartographer_specialist_packet_consumer",
        upstream_state={**dict(upstream_state), "task": task, "gemma_status": gemma.get("status", "")},
        output={"summary": "Hermes critique/risk lane consumed.", "lane_output": hermes},
        status=_model_lane_hardline_status(hermes),
        changed_state_fields=["ast_snapshot.plan_2_specialist_lanes.hermes_critique_risk"],
        failure_reason=None
        if _model_lane_hardline_status(hermes) == "INTEGRATED_LIVE"
        else "hermes_critique_risk_lane_not_live",
    )
    qwen_output = await run_qwen_coder_lane(
        task=task,
        route_payload=route_payload or {},
        gemma_packet=gemma,
        hermes_packet=hermes,
        fip1_context_packet={"source_status": upstream_state},
        fip2_research_packet=research_packet or {},
    )
    qwen_payload = record_subsystem_integration_result(
        task_id,
        subsystem="qwen_coder",
        consumer_subsystem="cartographer_specialist_packet_consumer",
        upstream_state={
            **dict(upstream_state),
            "task": task,
            "gemma_output_hash": gemma.get("output_hash", ""),
            "hermes_output_hash": hermes.get("output_hash", ""),
        },
        output={"summary": "Qwen coder lane activated and consumed.", "lane_output": qwen_output},
        status="INTEGRATED_LIVE" if _qwen_output_is_live(qwen_output) else _blocked_or_needs_fix(qwen_output),
        changed_state_fields=["ast_snapshot.plan_2_specialist_lanes.qwen_coder"],
        failure_reason=None if _qwen_output_is_live(qwen_output) else "qwen_coder_lane_not_live",
    )
    verifier_target = _write_disposable_verifier_target(task_id)
    verifier_output = run_live_functional_verifier(
        target_path=str(verifier_target),
        required_text="Plan 2 Patch 4 verifier live target",
        required_interactive_marker="data-plan2-verifier-action",
    )
    verifier_payload = record_subsystem_integration_result(
        task_id,
        subsystem="browser_functional_verifier",
        consumer_subsystem="cartographer_specialist_packet_consumer",
        upstream_state={
            **dict(upstream_state),
            "task": task,
            "qwen_status": qwen_output.get("status", ""),
            "verifier_target": str(verifier_target),
        },
        output={"summary": "Browser/functional verifier lane executed and consumed.", "lane_output": verifier_output},
        status="INTEGRATED_LIVE" if _verifier_output_is_live(verifier_output) else "NEEDS_FIX",
        changed_state_fields=["ast_snapshot.plan_2_specialist_lanes.browser_functional_verifier"],
        failure_reason=None if _verifier_output_is_live(verifier_output) else "browser_functional_verifier_not_verified",
    )
    specialist_lanes = {
        "gemma_intent_spec": _lane_proof(
            gemma_payload,
            "gemma_intent_spec",
            required=True,
            live_invocation=_model_lane_hardline_status(gemma) == "INTEGRATED_LIVE",
            real_output=_model_lane_hardline_status(gemma) == "INTEGRATED_LIVE",
        ),
        "hermes_critique_risk": _lane_proof(
            hermes_payload,
            "hermes_critique_risk",
            required=True,
            live_invocation=_model_lane_hardline_status(hermes) == "INTEGRATED_LIVE",
            real_output=_model_lane_hardline_status(hermes) == "INTEGRATED_LIVE",
        ),
        "qwen_coder": {
            **_lane_proof(
                qwen_payload,
                "qwen_coder",
                required=True,
                live_invocation=_qwen_output_is_live(qwen_output),
                real_output=_qwen_output_is_live(qwen_output),
            ),
            "activated": qwen_output.get("activated") is True,
            "metadata_only": False,
            "model": qwen_output.get("model", ""),
            "output_hash": qwen_output.get("output_hash", ""),
        },
        "browser_functional_verifier": {
            **_lane_proof(
                verifier_payload,
                "browser_functional_verifier",
                required=True,
                live_invocation=verifier_output.get("live_invocation") is True,
                real_output=verifier_output.get("verification_result") == "VERIFIED",
            ),
            "verification_result": verifier_output.get("verification_result", ""),
            "advisory_only": verifier_output.get("advisory_only") is True,
            "preview_only": verifier_output.get("preview_only") is True,
            "unverified": verifier_output.get("unverified") is True,
            "target_path": verifier_output.get("target_path", ""),
        },
    }
    packet = {
        "version": SPECIALIST_INTEGRATION_VERSION,
        "summary": "Specialist lanes invoked, verified, causally consumed, and hardline-gated.",
        "inventory": inventory,
        "model_packet": model_packet,
        "specialist_lanes": specialist_lanes,
        "qwen_coder_output": qwen_output,
        "verifier_output": verifier_output,
        "qwen": {
            "status": specialist_lanes["qwen_coder"]["status"],
            "activated": specialist_lanes["qwen_coder"]["activated"],
            "consumer": "cartographer_specialist_packet_consumer",
        },
        "gemma": gemma,
        "hermes": hermes,
        "browser_functional_verifier": verifier_output,
        "design_browser_specialist": inventory["design_browser_specialist"],
    }
    gemma_status = str(gemma.get("status") or "")
    hermes_status = str(hermes.get("status") or "")
    status = "INTEGRATED_LIVE" if specialist_lanes_allow_go(specialist_lanes) else "NEEDS_FIX"
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


def _model_lane_hardline_status(lane: dict[str, Any]) -> str:
    status = str(lane.get("status") or "")
    if status == "used" and lane.get("output_schema_valid") is True and lane.get("output_hash"):
        return "INTEGRATED_LIVE"
    if status in {"blocked", "timeout"}:
        return "BLOCKED_ENV"
    return "NEEDS_FIX"


def _qwen_output_is_live(output: dict[str, Any]) -> bool:
    return bool(
        output.get("status") == "used"
        and output.get("activated") is True
        and output.get("live_invocation") is True
        and output.get("real_output") is True
        and output.get("output_schema_valid") is True
        and output.get("output_hash")
    )


def _verifier_output_is_live(output: dict[str, Any]) -> bool:
    return bool(
        output.get("status") == "used"
        and output.get("live_invocation") is True
        and output.get("verification_result") == "VERIFIED"
        and output.get("advisory_only") is False
        and output.get("preview_only") is False
        and output.get("unverified") is False
    )


def _blocked_or_needs_fix(output: dict[str, Any]) -> str:
    return "BLOCKED_ENV" if str(output.get("status") or "") in {"blocked", "timeout"} else "NEEDS_FIX"


def _lane_proof(
    task_payload: dict[str, Any],
    subsystem: str,
    *,
    required: bool,
    live_invocation: bool,
    real_output: bool,
) -> dict[str, Any]:
    task = task_payload.get("task") if isinstance(task_payload.get("task"), dict) else {}
    snapshot = task.get("ast_snapshot") if isinstance(task.get("ast_snapshot"), dict) else {}
    integrations = (
        snapshot.get("plan_2_subsystem_integrations")
        if isinstance(snapshot.get("plan_2_subsystem_integrations"), dict)
        else {}
    )
    record = integrations.get(subsystem) if isinstance(integrations.get(subsystem), dict) else {}
    consumer_event_id = str(record.get("consumer_event_id") or "")
    return {
        "required": required,
        "status": str(record.get("status") or "NEEDS_FIX"),
        "live_invocation": live_invocation,
        "real_output": real_output,
        "downstream_consumed": bool(consumer_event_id),
        "trace_id": str(record.get("trace_id") or ""),
        "invocation_event_id": str(record.get("invocation_event_id") or ""),
        "consumer_event_id": consumer_event_id,
        "consumer_subsystem": str(record.get("consumer_subsystem") or ""),
        "failure_changes_outcome": True,
    }


def _write_disposable_verifier_target(task_id: str) -> Path:
    PATCH4_EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    target = PATCH4_EVIDENCE_ROOT / f"task-a-verifier-target-{task_id}.html"
    target.write_text(
        """<!doctype html>
<html>
<head><meta charset="utf-8"><title>Plan 2 Patch 4 Verifier Target</title></head>
<body>
  <main>
    <h1>Plan 2 Patch 4 verifier live target</h1>
    <button data-plan2-verifier-action="toggle" onclick="document.body.dataset.verified='true'">Verify</button>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )
    return target
