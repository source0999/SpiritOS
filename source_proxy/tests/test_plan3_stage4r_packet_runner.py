from __future__ import annotations

import importlib.util
import inspect
import json
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


def _valid_model_decision_body() -> dict:
    return {
        "decisions": [
            {
                "action_intent": "choose",
                "decision_summary": "Choose the bounded local bridge architecture because the supplied evidence constrains the safe implementation path.",
                "reasoning_summary": "The decision should follow the real source, repo, and machine evidence instead of model-authored provenance or fabricated host names.",
                "risk_notes": ["Do not trust model-owned source URLs or local API claims."],
                "ambiguity_notes": ["Human review still decides whether to implement after Set A."],
                "proposed_next_action": "Rerun the bounded Set A packet slice and inspect the receipt and trace before moving to any next set.",
                "confidence_reason": "The evidence IDs are supplied by code.",
            },
            {
                "action_intent": "use",
                "decision_summary": "Use the real evidence identifiers for every changed decision so validator checks remain tied to collected facts.",
                "reasoning_summary": "Evidence references are produced by code from the digest, which prevents source URL laundering through model text.",
                "risk_notes": [],
                "ambiguity_notes": [],
                "proposed_next_action": "Keep the generated packet bounded to the existing Plan 3 Set A validation contract.",
                "confidence_reason": "The assembler injects references.",
            },
            {
                "action_intent": "defer",
                "decision_summary": "Defer unsupported claims when the evidence digest lacks enough source, repo, or machine facts.",
                "reasoning_summary": "The model can summarize ambiguity but the shell must show insufficient evidence rather than inventing provenance.",
                "risk_notes": [],
                "ambiguity_notes": ["Insufficient source evidence should stay visible."],
                "proposed_next_action": "Return a diagnostic failure with the exact missing evidence class.",
                "confidence_reason": "The validator remains authoritative.",
            },
        ],
        "overall_recommendation": "Use the code-owned packet shell and keep the model limited to bounded decision text for this Set A packet.",
    }


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


def test_decision_packet_prompt_makes_packet_shell_code_owned() -> None:
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
    assert "Code owns the final packet shell" in prompt
    assert "Do not output source URLs" in prompt
    assert '"finding": "Chrome native messaging requires a registered native host' in prompt


def test_code_owned_assembler_drops_model_fabricated_urls() -> None:
    runner = _load_runner()
    digest = runner.synthetic_digest("A2")
    body = _valid_model_decision_body()
    body["decisions"][0]["decision_summary"] += " Ignore https://fake.example and ollama.ai from model prose."

    packet, shell_status = runner.assemble_code_owned_decision_packet(
        "A2",
        {"user_prompt": "send selected browser text to Source Proxy", "expected_work_product": "plan"},
        digest,
        body,
        {"lane_name": "ollama_qwen2.5-coder_7b", "provider_type": "ollama", "model": "qwen2.5-coder:7b"},
        "",
    )

    packet_text = json.dumps(packet, sort_keys=True)
    source_urls = {fact["url"] for fact in digest["source_facts"]}
    assembled_urls = {item["source_url"] for item in packet["evidence_items"] if item["evidence_type"] == "research"}
    assert "fake.example" not in packet_text
    assert "ollama.ai" not in packet_text
    assert assembled_urls <= source_urls
    assert shell_status["source_urls_from_code"] is True


def test_wrapped_json_body_is_nonfatal_when_unambiguous() -> None:
    runner = _load_runner()
    wrapped = "model note\n" + json.dumps(_valid_model_decision_body()) + "\ntrailing note"

    body, parse_error = runner.extract_json_object(wrapped)
    packet, shell_status = runner.assemble_code_owned_decision_packet(
        "A2",
        {"user_prompt": "send selected browser text to Source Proxy", "expected_work_product": "plan"},
        runner.synthetic_digest("A2"),
        body,
        {"lane_name": "ollama_qwen2.5-coder_7b", "provider_type": "ollama", "model": "qwen2.5-coder:7b"},
        parse_error,
    )
    validation = runner.validate_decision_packet("A2", packet, runner.synthetic_digest("A2"))

    assert parse_error == "non_json_wrapping_text"
    assert shell_status["model_decision_body_status"]["parse_status"] == "wrapped_json_extracted"
    assert "non_json_wrapping_text" not in validation["errors"]


def test_invalid_action_intent_remains_visible() -> None:
    runner = _load_runner()
    body = _valid_model_decision_body()
    body["decisions"][0]["action_intent"] = "teleport"

    _packet, shell_status = runner.assemble_code_owned_decision_packet(
        "A2",
        {"user_prompt": "send selected browser text to Source Proxy", "expected_work_product": "plan"},
        runner.synthetic_digest("A2"),
        body,
        {"lane_name": "ollama_qwen2.5-coder_7b", "provider_type": "ollama", "model": "qwen2.5-coder:7b"},
        "",
    )

    assert "invalid_action_intent:teleport" in shell_status["action_errors"]
    assert any(
        err == "model_decision_body_invalid_action_intent:teleport:0"
        for err in shell_status["model_decision_body_status"]["errors"]
    )


def test_test_later_action_intent_maps_to_defer_with_receipt_detail() -> None:
    runner = _load_runner()
    body = _valid_model_decision_body()
    body["decisions"][0]["action_intent"] = "test later"

    packet, shell_status = runner.assemble_code_owned_decision_packet(
        "A9",
        {"user_prompt": "compare current local llm tools", "expected_work_product": "research_pack"},
        runner.synthetic_digest("A9"),
        body,
        {"lane_name": "ollama_qwen2.5-coder_7b", "provider_type": "ollama", "model": "qwen2.5-coder:7b"},
        "",
    )

    assert shell_status["action_errors"] == []
    assert shell_status["action_intent_normalizations"][0] == {
        "index": 0,
        "action_intent_original": "test later",
        "action_intent_normalized": "defer",
        "action_intent_normalization_reason": "exact_semantic_alias:test_later_to_defer",
    }
    assert packet["decisions_changed_by_evidence"][0]["decision"].startswith("defer ")


def test_skip_action_intent_maps_to_reject_with_receipt_detail() -> None:
    runner = _load_runner()
    body = _valid_model_decision_body()
    body["decisions"][0]["action_intent"] = "skip"

    packet, shell_status = runner.assemble_code_owned_decision_packet(
        "A9",
        {"user_prompt": "compare current local llm tools", "expected_work_product": "research_pack"},
        runner.synthetic_digest("A9"),
        body,
        {"lane_name": "ollama_qwen2.5-coder_7b", "provider_type": "ollama", "model": "qwen2.5-coder:7b"},
        "",
    )

    assert shell_status["action_errors"] == []
    assert shell_status["action_intent_normalizations"][0] == {
        "index": 0,
        "action_intent_original": "skip",
        "action_intent_normalized": "reject",
        "action_intent_normalization_reason": "exact_semantic_alias:skip_to_reject",
    }
    assert packet["decisions_changed_by_evidence"][0]["decision"].startswith("reject ")


def test_missing_real_sources_do_not_fabricate_sources() -> None:
    runner = _load_runner()
    digest = runner.synthetic_digest("A2")
    digest["source_facts"] = []
    digest["evidence_items"] = runner.build_packet_evidence_items(digest)

    packet, _shell_status = runner.assemble_code_owned_decision_packet(
        "A2",
        {"user_prompt": "send selected browser text to Source Proxy", "expected_work_product": "plan"},
        digest,
        _valid_model_decision_body(),
        {"lane_name": "ollama_qwen2.5-coder_7b", "provider_type": "ollama", "model": "qwen2.5-coder:7b"},
        "",
    )
    validation = runner.validate_decision_packet("A2", packet, digest)

    assert validation["valid"] is False
    assert "insufficient_source_refs:0" in validation["errors"]
    assert not any(item["evidence_type"] == "research" for item in packet["evidence_items"])


def test_code_owned_shell_status_contains_runtime_truth() -> None:
    runner = _load_runner()

    _packet, shell_status = runner.assemble_code_owned_decision_packet(
        "A5",
        {"user_prompt": "assign Dell Mac Windows roles", "expected_work_product": "plan"},
        runner.synthetic_digest("A5"),
        _valid_model_decision_body(),
        {"lane_name": "ollama_qwen2.5-coder_7b", "provider_type": "ollama", "model": "qwen2.5-coder:7b"},
        "",
    )

    assert shell_status["local_api_truth_from_lane_metadata"] is True
    assert "evidence_items" in shell_status["code_owned_fields"]
    assert "decision_summary" in shell_status["model_owned_fields_used"]
    assert shell_status["model_decision_body_status"]["status"] == "valid"
    assert len(shell_status["raw_source_registry"]) >= 3


def test_garbled_token_guard_ignores_real_source_urls() -> None:
    runner = _load_runner()

    assert not runner.has_garbled_or_fabricated_tokens(
        "Source: https://www.reddit.com/r/LocalLLaMA/comments/1oclug7/getting_most_out_of_your_local_llm_setup/"
    )
    assert runner.has_garbled_or_fabricated_tokens("Use the fake local_l runtime name in prose")


def test_renderer_research_blocks_are_tied_to_source_facts() -> None:
    runner = _load_runner()
    digest = runner.synthetic_digest("A2")
    packet, _shell_status = runner.assemble_code_owned_decision_packet(
        "A2",
        {"user_prompt": "send selected browser text to Source Proxy", "expected_work_product": "plan"},
        digest,
        _valid_model_decision_body(),
        {"lane_name": "ollama_qwen2.5-coder_7b", "provider_type": "ollama", "model": "qwen2.5-coder:7b"},
        "",
    )

    work = runner.render_work_from_decision_packet("A2", packet, digest)
    blocks, errors = runner.research_change_blocks(
        work,
        [{"title": fact["title"], "url": fact["url"], "content": fact["finding"]} for fact in digest["source_facts"]],
    )

    assert len(blocks) >= 3
    assert "research_change_finding_not_tied_to_source_fact" not in errors
    assert "research_change_source_not_from_raw_sources" not in errors


def test_research_parser_ignores_repo_source_lines_after_research_section() -> None:
    runner = _load_runner()
    digest = runner.synthetic_digest("A2")
    packet, _shell_status = runner.assemble_code_owned_decision_packet(
        "A2",
        {"user_prompt": "send selected browser text to Source Proxy", "expected_work_product": "plan"},
        digest,
        _valid_model_decision_body(),
        {"lane_name": "ollama_qwen2.5-coder_7b", "provider_type": "ollama", "model": "qwen2.5-coder:7b"},
        "",
    )
    work = runner.render_work_from_decision_packet("A2", packet, digest)
    work += "\nRepo/Mac evidence that changed the plan\n"
    work += "- Evidence: 17 Source: source_proxy/api/long_running_tasks.py (repo); relevance: repo context only\n"

    blocks, errors = runner.research_change_blocks(
        work,
        [{"title": fact["title"], "url": fact["url"], "content": fact["finding"]} for fact in digest["source_facts"]],
    )

    assert len(blocks) >= 3
    assert "research_change_source_not_from_raw_sources" not in errors
    assert all("source_proxy/" not in block["source"] for block in blocks)


def test_research_source_line_can_match_raw_source_title() -> None:
    runner = _load_runner()
    sources = [
        {
            "title": "Send simple data to other apps | App data and files - Android Developers",
            "url": "https://developer.android.com/training/sharing/send",
            "content": "Android supports sending simple data to other apps through intents and chooser flows.",
        }
    ]
    work = """Recommendation
Use Android intents.

Research-to-decision changes
- Finding: Send simple data to other apps | App data and files - Android Developers: Android supports sending simple data to other apps through intents and chooser flows.
  Source: Send simple data to other apps | App data and files - Android Developers
  Decision changed: prioritize Android intents for passing task receipt data between app surfaces.
  Why this changes the recommendation: The raw source finding says Android supports sending simple data to other apps through intents and chooser flows, so the plan should prioritize an intent handoff.
"""

    blocks, errors = runner.research_change_blocks(work, sources)

    assert len(blocks) == 1
    assert errors == []


def test_research_source_line_can_match_raw_title_tokens_with_minor_model_typo() -> None:
    runner = _load_runner()
    sources = [
        {
            "title": "Send simple data to other apps | App data and files - Android Developers",
            "url": "https://developer.android.com/training/sharing/send",
            "content": "The Android intent resolver is best suited for passing data to the next stage of a well-defined task.",
        }
    ]
    work = """Recommendation
Use Android intents.

Research-to-decision changes
- Finding: Send simple data to other apps | App data and files - Android Developers: The Android intent resolver is best suited for passing data to the next stage of a well-defined task.
  Source: Send simple data to other apps | App data and files - Android Developeers
  Decision changed: evaluate Android intents for passing task receipt data between app surfaces.
  Why this changes the recommendation: The raw source finding says Android intent resolver is best suited for passing data to the next stage of a task, so the plan should evaluate an intent handoff.
"""

    blocks, errors = runner.research_change_blocks(work, sources)

    assert len(blocks) == 1
    assert errors == []


def test_research_source_line_rejects_fake_model_source() -> None:
    runner = _load_runner()
    sources = [
        {
            "title": "PKHeX - Save Editing - Project Pokemon Forums",
            "url": "https://projectpokemon.org/home/files/file/1-pkhex/",
            "content": "PKHeX supports Pokemon save files and related save editing workflows.",
        }
    ]
    work = """Recommendation
Use a save editor.

Research-to-decision changes
- Finding: PKHeX supports Pokemon save files and related save editing workflows.
  Source: Fake Tutorial Site (fake.example) https://fake.example/pkhex
  Decision changed: choose PKHeX as the starting point for save editing.
  Why this changes the recommendation: The raw source finding says PKHeX supports Pokemon save files, so the plan should choose a save-editor-specific route.
"""

    blocks, errors = runner.research_change_blocks(work, sources)

    assert blocks == []
    assert "research_change_source_not_from_raw_sources" in errors


def test_repo_only_prompt_does_not_require_research_source_materiality() -> None:
    runner = _load_runner()
    item = {
        "prompt_id": "A8",
        "internet_likely_required": False,
        "must_inspect_repo_context": False,
        "mac_likely_required": False,
    }
    work = """Recommendation
Build a small dashboard with clear limits and a next handoff.

Research-to-decision changes
- Finding: The repo has long-running task state fields.
  Source: source_proxy/tasks/long_running.py
  Decision changed: prioritize long-running task state in the dashboard.
  Why this changes the recommendation: The repo finding points to task state as the useful display target.

Evidence Used
- source_proxy/tasks/long_running.py

Plan
Use the existing task state and avoid new systems.

Limits
- Do not change runtime behavior.

Next Handoff
Build first dashboard slice.
"""

    result = runner.grade(item, work, None, None, None, runner.synthetic_task(), "")

    assert "research_change_source_not_from_raw_sources" not in result["failed_gates"]
    assert "research_materially_changed_output" not in result["failed_gates"]


def test_packet_assembler_has_no_prompt_specific_branches() -> None:
    runner = _load_runner()
    source = inspect.getsource(runner.assemble_code_owned_decision_packet)

    assert 'pid == "A2"' not in source
    assert 'pid == "A5"' not in source
    assert 'pid == "A9"' not in source
