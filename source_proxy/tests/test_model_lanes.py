from __future__ import annotations

import asyncio

from source_proxy.decision import model_lanes
from source_proxy.decision.model_lanes import (
    _call_json_lane,
    active_primary_coder_lane,
    build_model_lanes_preview,
    get_model_lane,
    lane_activation_status,
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
        "qwen14b_coder_challenger",
        "ornith_coder_challenger",
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


def test_ornith_challenger_is_not_primary_or_silent_replacement() -> None:
    registry = model_lane_registry()
    ornith = get_model_lane("ornith_coder_challenger")

    assert registry["primary_coder_lane"] == "qwen_local_coder"
    assert ornith["status"] == "installed_challenger_benchmark_prep_only"
    assert ornith["privacy_class"] == "local"
    assert ornith["cost_class"] == "local_compute"
    assert ornith["promotion_status"] == "not_promoted_challenger_only"
    assert "silent replacement for qwen_local_coder" in ornith["disallowed_uses"]


def test_qwen14b_challenger_is_not_primary_or_silent_replacement() -> None:
    registry = model_lane_registry()
    qwen14b = get_model_lane("qwen14b_coder_challenger")

    assert registry["primary_coder_lane"] == "qwen_local_coder"
    assert qwen14b["status"] == "installed_challenger_benchmark_prep_only"
    assert qwen14b["privacy_class"] == "local"
    assert qwen14b["cost_class"] == "local_compute_heavier_runtime"
    assert qwen14b["promotion_status"] == "not_promoted_challenger_only"
    assert "silent replacement for qwen_local_coder" in qwen14b["disallowed_uses"]


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
    assert "qwen14b_coder_challenger" in {lane["lane_id"] for lane in preview["available_lanes"]}
    assert "ornith_coder_challenger" in {lane["lane_id"] for lane in preview["available_lanes"]}
    assert "hermes_sidecar_verifier_preview" in preview["future_sidecar_lanes"]
    assert preview["verifier_requirement"] is True
    assert preview["lane_activation_status"]["fip4_qwen_coder"]["classification"] in {
        "ACTIVE_DECISION_BEARING",
        "DORMANT_BY_DESIGN",
    }


def test_lane_activation_status_reports_default_dormant_and_advisory_lanes(monkeypatch) -> None:
    for key in (
        "SOURCE_PROXY_FIP4_QWEN_CODER_ENABLED",
        "SOURCE_PROXY_FIP5_VERIFIER_ENABLED",
        "SOURCE_PROXY_FIP4_ALLOW_FIP5_CHAIN",
        "SOURCE_PROXY_FIP3_MODEL_LANES_ENABLED",
    ):
        monkeypatch.delenv(key, raising=False)

    status = lane_activation_status()

    assert status["fip4_qwen_coder"]["classification"] == "DORMANT_BY_DESIGN"
    assert status["fip5_verifier_repair"]["classification"] == "DORMANT_BY_DESIGN"
    assert status["hermes_critic"]["classification"] == "ACTIVE_ADVISORY_ONLY"
    assert status["gemma_context"]["classification"] == "ACTIVE_ADVISORY_ONLY"


def test_json_lane_accepts_ollama_thinking_when_response_is_empty(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "response": "",
                "thinking": '{"ambiguities":[],"risks":[],"requirement_conflicts":[],"pre_coder_notes":["ready"]}',
            }

    class FakeAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            return None

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def post(self, *args: object, **kwargs: object) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setattr(model_lanes.httpx, "AsyncClient", FakeAsyncClient)

    result = asyncio.run(
        _call_json_lane(
            base_url="http://127.0.0.1:11434",
            model="hermes4:latest",
            prompt="Return JSON.",
            schema_validator=model_lanes._normalize_hermes_output,
        )
    )

    assert result["status"] == "used"
    assert result["reason"] == "local_ollama_model_json_schema_valid"
    assert result["pre_coder_notes"] == ["ready"]
