from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


MODEL_LANE_REGISTRY_VERSION = "source-proxy-model-lane-registry-v0.1"


@dataclass(frozen=True)
class ModelLane:
    lane_id: str
    display_name: str
    role: str
    status: str
    allowed_uses: list[str]
    disallowed_uses: list[str]
    cost_class: str
    privacy_class: str
    approval_required: str
    evidence_required_for_promotion: list[str]
    known_failure_modes: list[str]
    promotion_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def model_lane_registry() -> dict[str, Any]:
    lanes = [_qwen(), _hermes(), _gemma(), _manual_handoff(), _cloud_future()]
    return {
        "registry_version": MODEL_LANE_REGISTRY_VERSION,
        "mode": "metadata_only_no_model_calls",
        "primary_coder_lane": "qwen_local_coder",
        "sidecar_lanes_live": False,
        "promotion_policy": "evidence_driven_operator_review",
        "global_rules": [
            "qwen_local_coder remains the primary coding/action lane",
            "preview/future sidecars cannot edit files",
            "preview/future sidecars cannot declare product success without behavior evidence",
            "cloud/API routes require Britton approval before use",
            "privacy and cost classes must be visible before lane selection",
        ],
        "lanes": [lane.to_dict() for lane in lanes],
    }


def get_model_lane(lane_id: str) -> dict[str, Any]:
    for lane in model_lane_registry()["lanes"]:
        if lane["lane_id"] == lane_id:
            return lane
    raise KeyError(f"Unknown model lane: {lane_id}")


def active_primary_coder_lane() -> dict[str, Any]:
    return get_model_lane("qwen_local_coder")


def lane_selection_observability(
    *,
    task_type: str = "disposable_artifact",
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    qwen = active_primary_coder_lane()
    sidecars = [
        get_model_lane("hermes_sidecar_verifier_preview"),
        get_model_lane("gemma_sidecar_context_preview"),
    ]
    return {
        "selected_coder_lane": qwen["lane_id"],
        "selected_coder_lane_display_name": qwen["display_name"],
        "sidecar_lanes_considered": [lane["lane_id"] for lane in sidecars],
        "sidecar_lanes_live": False,
        "verifier_lane_required": task_type in {"disposable_artifact", "repo_patch_preview", "behavior_check"},
        "lane_privacy_class": qwen["privacy_class"],
        "lane_cost_class": qwen["cost_class"],
        "lane_approval_required": qwen["approval_required"],
        "lane_selection_reason_codes": [
            "qwen_primary_local_coder_preserved",
            "sidecar_lanes_preview_only",
            "no_model_swap",
            "no_live_sidecar_call",
        ],
        "lane_evidence_refs": list(evidence_refs or []),
    }


def build_model_lanes_preview(*, task_type: str = "disposable_artifact") -> dict[str, Any]:
    registry = model_lane_registry()
    return {
        "preview_version": "source-proxy-model-lanes-preview-v0.1",
        "preview_only": True,
        "would_call_models": False,
        "would_start_workers": False,
        "would_mutate_state": False,
        "available_lanes": registry["lanes"],
        "active_primary_lane": registry["primary_coder_lane"],
        "future_sidecar_lanes": [
            lane["lane_id"]
            for lane in registry["lanes"]
            if "preview" in lane["status"] or "future" in lane["status"]
        ],
        "recommended_lane": lane_selection_observability(task_type=task_type),
        "approval_requirements": {
            lane["lane_id"]: lane["approval_required"]
            for lane in registry["lanes"]
        },
        "privacy_classes": {
            lane["lane_id"]: lane["privacy_class"]
            for lane in registry["lanes"]
        },
        "cost_classes": {
            lane["lane_id"]: lane["cost_class"]
            for lane in registry["lanes"]
        },
        "verifier_requirement": task_type in {"disposable_artifact", "repo_patch_preview", "behavior_check"},
        "reason_codes": [
            "preview_only",
            "qwen_primary_local_coder_preserved",
            "future_sidecars_not_executed",
            "operator_approval_required_for_external_routes",
        ],
    }


def _qwen() -> ModelLane:
    return ModelLane(
        lane_id="qwen_local_coder",
        display_name="Qwen local coder",
        role="coding/action",
        status="active_primary_local_lane",
        allowed_uses=["disposable artifact generation", "bounded local coding/action lane"],
        disallowed_uses=["unreviewed autonomy", "provider/cloud escalation", "declaring product PASS without verifier evidence"],
        cost_class="local_compute",
        privacy_class="local",
        approval_required="normal_source_proxy_gate",
        evidence_required_for_promotion=["behavior retest results", "receipt evidence", "false-positive audit"],
        known_failure_modes=["malformed action JSON", "weak UI state changes", "missing behavior evidence"],
        promotion_status="primary_preserved_not_promoted_by_this_task",
    )


def _hermes() -> ModelLane:
    return ModelLane(
        lane_id="hermes_sidecar_verifier_preview",
        display_name="Hermes sidecar verifier preview",
        role="verifier/critic",
        status="preview_future_only",
        allowed_uses=["future advisory verifier", "risk and unknown extraction preview"],
        disallowed_uses=["file editing", "coding/action lane", "product PASS override", "hidden benchmark hints"],
        cost_class="local_compute_if_available",
        privacy_class="local_if_available_runtime_explicit_required",
        approval_required="future_operator_approval_before_live_call",
        evidence_required_for_promotion=["advisory accuracy samples", "false-positive audit", "no-PASS-inflation proof"],
        known_failure_modes=["overtrusting model claims", "critic hallucination", "missing browser evidence"],
        promotion_status="not_promoted_preview_only",
    )


def _gemma() -> ModelLane:
    return ModelLane(
        lane_id="gemma_sidecar_context_preview",
        display_name="Gemma sidecar context preview",
        role="intent/context/spec/verifier",
        status="preview_future_only",
        allowed_uses=["future intent interpretation", "context/spec packet preview", "acceptance criteria preview"],
        disallowed_uses=["file editing", "coding/action lane", "success declaration without evidence", "implicit cloud use"],
        cost_class="runtime_dependent_must_be_explicit",
        privacy_class="local_or_cloud_runtime_must_be_explicit",
        approval_required="future_operator_approval_before_live_call",
        evidence_required_for_promotion=["context quality samples", "privacy route proof", "behavior-verifier comparison"],
        known_failure_modes=["scope drift", "privacy ambiguity", "over-specific acceptance criteria"],
        promotion_status="not_promoted_preview_only",
    )


def _manual_handoff() -> ModelLane:
    return ModelLane(
        lane_id="manual_handoff",
        display_name="Manual handoff",
        role="handoff",
        status="active_fallback",
        allowed_uses=["operator review", "approval request", "handoff packet routing"],
        disallowed_uses=["automatic escalation", "silent provider use"],
        cost_class="human_review",
        privacy_class="operator_visible",
        approval_required="operator_review",
        evidence_required_for_promotion=["not applicable"],
        known_failure_modes=["insufficient evidence packet", "ambiguous next route"],
        promotion_status="fallback_active",
    )


def _cloud_future() -> ModelLane:
    return ModelLane(
        lane_id="cloud_or_api_route_future",
        display_name="Cloud/API route future",
        role="stronger external route",
        status="future_approval_only",
        allowed_uses=["future approved stronger-route comparison"],
        disallowed_uses=["default coding lane", "silent execution", "secret or private context without approval"],
        cost_class="paid_or_metered",
        privacy_class="external_cloud",
        approval_required="explicit_britton_approval_before_send",
        evidence_required_for_promotion=["spend approval", "privacy review", "comparative proof", "false-positive audit"],
        known_failure_modes=["cost overrun", "privacy leakage", "overreliance on self-report"],
        promotion_status="not_promoted_future_only",
    )
