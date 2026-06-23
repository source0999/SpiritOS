from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


RUNNER_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "source-proxy-human-brain-full-live-integration-pivot-20260619"
    / "plan-03"
    / "continuation-3x10-dryrun"
    / "set-a-rerun"
    / "_stage4r_runner.py"
)


def _load_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("plan3_stage4r_runner", RUNNER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_packet_model_lanes_prefer_qwen_for_structured_authoring(monkeypatch) -> None:
    runner = _load_runner()
    monkeypatch.setattr(
        runner,
        "list_ollama_models",
        lambda: ["hermes4:latest", "gemma3n:e4b", "qwen2.5-coder:7b"],
    )

    lanes, unavailable = runner.packet_model_lanes()

    assert not any(lane["model"] == "qwen2.5-coder:7b" for lane in unavailable)
    assert lanes[0]["model"] == "qwen2.5-coder:7b"
    assert lanes[0]["reason"] == "structured_packet_author_primary_local_coder"
    assert [lane["model"] for lane in lanes[1:3]] == ["hermes4:latest", "gemma3n:e4b"]


def test_packet_model_lanes_do_not_hide_missing_qwen(monkeypatch) -> None:
    runner = _load_runner()
    monkeypatch.setattr(runner, "list_ollama_models", lambda: ["hermes4:latest", "gemma3n:e4b"])

    lanes, unavailable = runner.packet_model_lanes()

    assert lanes[0]["model"] == "hermes4:latest"
    assert any(
        lane["model"] == "qwen2.5-coder:7b"
        and lane["reason"] == "model_not_available:structured_packet_author_primary_local_coder"
        for lane in unavailable
    )


def test_invalid_packet_still_fails_validation() -> None:
    runner = _load_runner()
    digest = {
        "source_facts": [],
        "evidence_items": [],
        "repo_context": [],
        "mac_capability_evidence": {},
    }

    validation = runner.validate_decision_packet("A2", {"prompt_id": "A2"}, digest)

    assert validation["valid"] is False
    assert "missing_field:user_goal" in validation["errors"]
    assert "missing_field:evidence_items" in validation["errors"]
    assert "empty_decisions_changed_by_evidence" in validation["errors"]


def test_decision_packet_prompt_locks_packet_ready_evidence_items() -> None:
    runner = _load_runner()
    digest = {
        "prompt_id": "A2",
        "source_facts": [
            {
                "title": "Chrome MV3 native messaging",
                "host": "developer.chrome.com",
                "url": "https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging",
                "finding": "Chrome native messaging requires a registered native host and explicit extension permission.",
            }
        ],
        "repo_evidence": [
            {
                "file": "source_proxy/api/long_running_tasks.py",
                "exists": True,
                "snippet": "long-running task endpoint creates durable task receipts",
            }
        ],
        "mac_capability_evidence": {},
        "mac_evidence_summary": [],
        "evidence_items": [],
    }
    digest["evidence_items"] = runner.build_packet_evidence_items(digest)

    prompt = runner.decision_packet_prompt(
        "A2",
        {
            "user_prompt": "send selected browser text to Source Proxy",
            "expected_work_product": "plan",
        },
        digest,
    )

    assert "Packet-ready evidence_items" in prompt
    assert "Copy this exact JSON array into the output `evidence_items` field" in prompt
    assert '"finding": "Chrome native messaging requires a registered native host' in prompt
