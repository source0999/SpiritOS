from __future__ import annotations

from source_proxy.decision.model_lanes import (
    active_primary_coder_lane,
    build_model_lanes_preview,
    get_model_lane,
    lane_selection_observability,
    model_lane_registry,
)


def test_model_lane_registry_is_metadata_only_and_preserves_qwen_primary() -> None:
    registry = model_lane_registry()

    assert registry["mode"] == "metadata_only_no_model_calls"
    assert registry["primary_coder_lane"] == "qwen_local_coder"
    assert registry["sidecar_lanes_live"] is False
    lane_ids = {lane["lane_id"] for lane in registry["lanes"]}
    assert {
        "qwen_local_coder",
        "hermes_sidecar_verifier_preview",
        "gemma_sidecar_context_preview",
        "manual_handoff",
        "cloud_or_api_route_future",
    }.issubset(lane_ids)


def test_sidecar_lanes_cannot_edit_or_claim_success_without_evidence() -> None:
    hermes = get_model_lane("hermes_sidecar_verifier_preview")
    gemma = get_model_lane("gemma_sidecar_context_preview")

    for lane in (hermes, gemma):
        disallowed = " ".join(lane["disallowed_uses"])
        assert "file editing" in disallowed
        assert "success" in disallowed or "product PASS" in disallowed
        assert lane["promotion_status"] == "not_promoted_preview_only"


def test_lane_selection_observability_does_not_swap_primary_lane() -> None:
    observability = lane_selection_observability(task_type="disposable_artifact")

    assert observability["selected_coder_lane"] == active_primary_coder_lane()["lane_id"]
    assert observability["sidecar_lanes_live"] is False
    assert observability["verifier_lane_required"] is True
    assert "no_model_swap" in observability["lane_selection_reason_codes"]


def test_model_lanes_preview_is_inspectable_without_execution() -> None:
    preview = build_model_lanes_preview(task_type="disposable_artifact")

    assert preview["preview_only"] is True
    assert preview["would_call_models"] is False
    assert preview["would_start_workers"] is False
    assert preview["active_primary_lane"] == "qwen_local_coder"
    assert "hermes_sidecar_verifier_preview" in preview["future_sidecar_lanes"]
    assert preview["verifier_requirement"] is True
