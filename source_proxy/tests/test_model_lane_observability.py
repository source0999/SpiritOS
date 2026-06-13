from __future__ import annotations

from pathlib import Path

from source_proxy.decision.human_messy_homepage import run_human_messy_homepage


def test_human_messy_homepage_score_includes_model_lane_observability(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"

    def fake_model_call(_packet: dict) -> str:
        return (
            '{"action_type":"WriteFile","target":"index.html","arguments":'
            '{"content":"<!doctype html><html><body><button>Click</button><p>0</p></body></html>"},'
            '"reason":"create disposable artifact"}'
        )

    score = run_human_messy_homepage(
        prompt="make a counter app",
        workspace=run_dir / "workspace",
        receipt_path=run_dir / "receipt.json",
        score_path=run_dir / "score.json",
        transcript_path=run_dir / "transcript.txt",
        diff_path=run_dir / "workspace.diff",
        model_call=fake_model_call,
        mode="product",
    )

    assert score["selected_coder_lane"] == "qwen_local_coder"
    assert score["sidecar_lanes_considered"] == [
        "hermes_sidecar_verifier_preview",
        "gemma_sidecar_context_preview",
    ]
    assert score["verifier_lane_required"] is True
    assert score["lane_privacy_class"] == "local"
    assert score["lane_cost_class"] == "local_compute"
    assert "no_live_sidecar_call" in score["lane_selection_reason_codes"]
