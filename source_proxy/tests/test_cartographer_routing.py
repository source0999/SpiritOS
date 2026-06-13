from __future__ import annotations

from source_proxy.decision.cartographer_routing import (
    build_cartographer_routing_preview,
    cartographer_routing_ownership_contract,
)


def test_cartographer_ownership_contract_is_preview_only() -> None:
    contract = cartographer_routing_ownership_contract()

    assert contract["preview_only"] is True
    assert contract["live_routing_enabled"] is False
    assert contract["worker_start_enabled"] is False
    assert contract["model_calls_enabled"] is False
    assert "model lane inventory" in contract["eventual_owned_surfaces"]


def test_cartographer_preview_preserves_qwen_and_marks_sidecar_future_only() -> None:
    preview = build_cartographer_routing_preview(
        task_type="disposable_artifact",
        evidence_refs=["retest-result.json"],
    )

    assert preview["preview_only"] is True
    assert preview["would_start_worker"] is False
    assert preview["would_call_model"] is False
    assert preview["recommended_coder_lane"] == "qwen_local_coder"
    assert preview["recommended_sidecar_lane"] == "hermes_sidecar_verifier_preview"
    assert "future" in preview["recommended_sidecar_status"]
    assert preview["verifier_required"] is True
    assert preview["privacy_class"] == "local"


def test_cartographer_preview_surfaces_dirty_tree_awareness() -> None:
    preview = build_cartographer_routing_preview(
        task_type="repo_patch_preview",
        dirty_tree=True,
    )

    assert preview["dirty_tree_awareness"]["dirty_tree"] is True
    assert preview["dirty_tree_awareness"]["can_proceed_without_operator_review"] is False
    assert "dirty_tree_requires_operator_awareness" in preview["reason_codes"]
