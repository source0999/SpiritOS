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


def test_inline_research_change_labels_are_parsed_without_weakening_source_match() -> None:
    runner = _load_runner()
    sources = [
        {
            "title": "PKHeX - Save Editing - Project Pokemon Forums",
            "url": "https://projectpokemon.org/home/files/file/1-pkhex/",
            "content": "PKHeX supports Pokemon core series save files including main, sav, dsv, dat, and GameCube memory card files.",
        }
    ]
    work = """Recommendation
Use PKHeX as the first save-editor framework.

Research-to-decision changes
- Finding: PKHeX supports Pokemon core series save files including main, sav, dsv, dat, and GameCube memory card files.
  Source: PKHeX - Save Editing - Project Pokemon Forums | host=projectpokemon.org | url=https://projectpokemon.org/home/files/file/1-pkhex/ | Decision changed: Choose PKHeX as the initial framework because it already targets the required Pokemon save formats. Why this changes the recommendation: This source turns the route away from a generic tutorial and toward an existing save-editor codebase with format coverage.
"""

    blocks, errors = runner.research_change_blocks(work, sources)

    assert len(blocks) == 1
    assert errors == []
    assert blocks[0]["decision"].startswith("Choose PKHeX")


def test_research_change_field_repair_derives_missing_why_from_raw_source_and_decision() -> None:
    runner = _load_runner()
    sources = [
        {
            "title": "PKHeX for Web - A Cross-Platform Pokemon Save File Editor",
            "url": "https://pkhex-web.github.io/",
            "content": "PKHeX for Web runs on Windows, Linux, MacOS, Steam Deck, or anywhere a browser is supported.",
        }
    ]
    work = """Recommendation
Use PKHeX for the first save-editor route.

Research-to-decision changes
- Finding: PKHeX for Web runs on Windows, Linux, MacOS, Steam Deck, or anywhere a browser is supported.
  Source: PKHeX for Web - A Cross-Platform Pokemon Save File Editor | host=pkhex-web.github.io | url=https://pkhex-web.github.io/ | Decision changed: Consider the web-based PKHeX route for broader platform compatibility during development.

Evidence Used
- PKHeX for Web
"""

    repaired, status = runner.repair_research_change_fields(work, sources)
    blocks, errors = runner.research_change_blocks(repaired, sources)

    assert status["derived_why_fields"] == 1
    assert "derived_missing_why_from_raw_source_and_decision" in status["repairs"]
    assert len(blocks) == 1
    assert errors == []
    assert "Why this changes the recommendation:" in repaired


def test_research_change_field_repair_does_not_promote_fake_sources() -> None:
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
  Source: Fake Tutorial Site (fake.example) https://fake.example/pkhex | Decision changed: Choose PKHeX as the starting point for save editing.
"""

    repaired, status = runner.repair_research_change_fields(work, sources)
    blocks, errors = runner.research_change_blocks(repaired, sources)

    assert status["derived_why_fields"] == 0
    assert status["dropped_non_raw_source_blocks"] == 1
    assert "dropped_non_raw_research_source_block" in status["repairs"]
    assert blocks == []
    assert errors == []
    assert "fake.example" not in repaired


def test_a3_like_repair_canonicalizes_raw_sources_and_drops_repo_research_leak() -> None:
    runner = _load_runner()
    sources = [
        {
            "title": "Send simple data to other apps | App data and files - Android Developers",
            "url": "https://developer.android.com/training/sharing/send",
            "content": "When you construct an intent, you must specify the action you want the intent to trigger and ACTION_SEND indicates data sharing.",
        },
        {
            "title": "Handle user interaction | Jetpack Compose | Android Developers",
            "url": "https://developer.android.com/develop/ui/compose/glance/user-interaction",
            "content": "Underneath, the parameters are included in the intent used to launch the activity, allowing the target Activity to retrieve it.",
        },
    ]
    work = """Recommendation
Use Android intents for the phone handoff.

Research-to-decision changes
Finding: When you construct an intent, you must specify the action you want the intent to trigger and ACTION_SEND indicates data sharing.
Source: Send simple data to other apps | App data and files - Android Deveopers (davelopeer.android.com)
Decision changed: Choose Android Intents for inter-process communication to initiate proxy tasks and retrieve receipt information.
Why this changes the recommendation: This confirms the Android handoff mechanism needed to start tasks and pass receipt context.

Finding: Underneath, the parameters are included in the intent used to launch the activity, allowing the target Activity to retrieve it.
Source: Handle user interaction | Jeptack Compose | Android Developers (deveelopeer.android.com)
Decision changed: Use Intent parameters to pass receipt identifiers and task context to the Android app surface.
Why this changes the recommendation: This gives the app a source-backed way to carry task data into the receipt-check flow.

Finding: The project uses long-running tasks for receipt creation.
Source: source_proxy/api/long_running_tasks.py
Decision changed: Leverage existing repo task plumbing as research provenance.
Why this changes the recommendation: This repo evidence belongs in repo context, not research source provenance.

Evidence Used
- source_proxy/api/long_running_tasks.py
"""

    repaired, status = runner.repair_research_change_fields(work, sources)
    blocks, errors = runner.research_change_blocks(repaired, sources)

    assert status["canonicalized_source_refs"] == 2
    assert status["dropped_non_raw_source_blocks"] == 1
    assert "source_proxy/api/long_running_tasks.py" not in repaired.split("Evidence Used", 1)[0]
    assert "davelopeer" not in repaired
    assert "deveelopeer" not in repaired
    assert len(blocks) == 2
    assert errors == []
    assert all(block["source"].endswith("developer.android.com/develop/ui/compose/glance/user-interaction") or "training/sharing/send" in block["source"] for block in blocks)


def test_missing_raw_research_source_still_fails_honestly_after_repair() -> None:
    runner = _load_runner()
    item = {
        "prompt_id": "A3",
        "internet_likely_required": True,
        "must_inspect_repo_context": False,
        "mac_likely_required": False,
    }
    work = """Recommendation
Use Android intents.

Research-to-decision changes
Finding: The repo has long-running task state fields.
Source: source_proxy/api/long_running_tasks.py
Decision changed: Choose repo task plumbing as if it were research provenance.
Why this changes the recommendation: This should not count as a raw research source.

Plan
Use the existing task state and avoid new systems.

Limits
Do not touch protected paths.

Next Handoff
Inspect source provenance.
"""

    repaired, status = runner.repair_research_change_fields(work, [])
    result = runner.grade(item, repaired, {"research_packet": {"sources": []}}, None, None, runner.synthetic_task(), "")

    assert status["enabled"] is False
    assert "live_search_sources" in result["failed_gates"]
    assert "research_materially_changed_output" in result["failed_gates"]


def test_research_change_repair_has_no_prompt_specific_branches() -> None:
    runner = _load_runner()
    source = inspect.getsource(runner.repair_research_change_fields)

    assert 'pid == "A3"' not in source
    assert '"A3"' not in source


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


def test_decision_verb_vocabulary_accepts_common_planning_verbs() -> None:
    runner = _load_runner()
    accepted = [
        "Investigate the use of intents for proxy task initiation",
        "Adopt compose multiplatform for receipt data sharing",
        "Integrate a share button into the compose user interface",
        "Build the receipt polling screen against the task endpoint",
        "Recommend intents as the task initiation path forward",
        "Validate the polling loop against the long-running route",
        "Assess the privacy tradeoff between local and cloud routes",
        "Test the share path against the real receipt payload",
        "Leverage the existing long-running route handler",
        "Deploy the worker behind the local api boundary",
        "Determine the endpoint shape before writing the client",
        "Prototype a minimal intent receiver before full integration",
    ]
    for line in accepted:
        assert runner.specific_decision_verb_present(line), f"expected verb-accepted: {line}"
        assert not runner.decision_line_is_vague(line), f"unexpected vague: {line}"


def test_vague_non_decisions_still_fail() -> None:
    runner = _load_runner()
    rejected = [
        "Think about it",
        "Maybe consider stuff",
        "do things",
        "Look into it",
        "consider it",
        "I guess maybe",
        "Consider various things",
        "Look into stuff",
    ]
    for line in rejected:
        fails = (not runner.specific_decision_verb_present(line)) or runner.decision_line_is_vague(line)
        assert fails, f"expected vague/verbless rejection: {line}"


def test_research_change_no_specific_decision_uses_general_vocabulary_not_a3_tuning() -> None:
    runner = _load_runner()
    source = inspect.getsource(runner.specific_decision_verb_present)
    # Must not branch on prompt id and must not use the old narrow inline regex.
    assert 'pid == "A3"' not in source
    assert '"A3"' not in source
    assert "DECISION_VERB_VOCABULARY" in source
    # The vocabulary is a maintained general set, not tuned to a single prompt.
    vocab_source = inspect.getsource(runner)
    assert "investigate" in vocab_source
    assert "leverage" in vocab_source
    assert "recommend" in vocab_source


def test_decision_line_vague_guard_has_no_prompt_specific_branches() -> None:
    runner = _load_runner()
    source = inspect.getsource(runner.decision_line_is_vague)
    assert 'pid ==' not in source
    assert '"A3"' not in source


def test_work_product_lane_selection_is_by_task_shape_not_prompt_id() -> None:
    runner = _load_runner()
    # The generic stabilized lane must be selected by task SHAPE, not prompt id. Prove
    # generalization behaviorally: a research-required prompt of ANY id (including a
    # hypothetical Set B/C id) routes to the stabilized lane; a non-research prompt does not.
    research_item = {"prompt_id": "A3", "internet_likely_required": True, "must_inspect_repo_context": True}
    assert runner.select_work_product_lane(research_item) == "generic_stabilized_research"
    future_research_item = {"prompt_id": "B7", "internet_likely_required": True, "must_inspect_repo_context": True}
    assert runner.select_work_product_lane(future_research_item) == "generic_stabilized_research"
    # Same shape, different id => same lane (not prompt-id-tailored).
    assert runner.select_work_product_lane(research_item) == runner.select_work_product_lane(future_research_item)
    non_research_item = {"prompt_id": "A7", "internet_likely_required": False, "must_inspect_repo_context": True}
    assert runner.select_work_product_lane(non_research_item) != "generic_stabilized_research"
    # A2/A5/A9 still route to the structured packet lane.
    for pid in ("A2", "A5", "A9"):
        assert runner.select_work_product_lane({"prompt_id": pid, "internet_likely_required": True}) == "validated_decision_packet"
    # The selector source must not contain a literal A3 branch on the executable path.
    # (The docstring may mention the forbidden pattern in prose; assert on the AST body.)
    import ast
    tree = ast.parse(inspect.getsource(runner.select_work_product_lane))
    code_text = "\n".join(ast.unparse(node) for node in ast.walk(tree) if not isinstance(node, (ast.FunctionDef, ast.Expr, ast.Constant, ast.Module)))
    assert 'pid == "A3"' not in code_text
    assert '"A3"' not in code_text


def test_generic_lane_metadata_surfaces_sampling_contract() -> None:
    runner = _load_runner()
    meta = runner.generic_lane_metadata()
    assert meta["lane"] == "generic_stabilized_research"
    assert meta["provider"] == "ollama"
    assert meta["local_first"] is True
    assert meta["api_or_frontier_call_added"] is False
    assert "temperature" in meta and meta["temperature"] <= 0.1
    assert "num_predict" in meta and meta["num_predict"] >= 6000
    assert meta["selection_basis"] == "task_shape_internet_required_not_prompt_id"


def test_generic_research_prompt_requires_canonical_research_change_blocks() -> None:
    runner = _load_runner()
    item = {
        "prompt_id": "B7",
        "user_prompt": "research a mobile proxy task receipt flow",
        "expected_work_product": "plan",
        "internet_likely_required": True,
        "must_inspect_repo_context": False,
        "mac_likely_required": False,
    }
    research = {
        "research_packet": {
            "sources": [
                {
                    "title": "Send simple data to other apps",
                    "url": "https://developer.android.com/training/sharing/send",
                    "content": "Android intents pass data between app components and apps.",
                }
            ]
        }
    }
    prompt = runner.model_prompt("B7", item, research, None, None, False, {}, None)
    assert "use this exact four-line template" in prompt
    assert "Finding: <copy or closely paraphrase one concrete in-run finding>" in prompt
    assert 'Do not use "Evidence Used" bullets' in prompt
    assert "Source: <copy one exact source citation" in prompt
    assert "S1: title=Send simple data to other apps" in prompt
    assert "investigate, validate, test, adopt, integrate, build, recommend, assess" in prompt


def test_classification_for_stability_detects_nondeterminism() -> None:
    runner = _load_runner()
    stable = runner.classification_for_stability(["PASS", "PASS", "PASS"])
    assert stable["stable"] is True
    assert stable["classification"] == "STABLE"
    unstable = runner.classification_for_stability(["PASS", "NEEDS_FIX", "PASS"])
    assert unstable["stable"] is False
    assert unstable["classification"] == "MODEL_NONDETERMINISM"
    assert set(unstable["unique_verdicts"]) == {"NEEDS_FIX", "PASS"}


def test_research_provider_debug_summary_surfaces_retry_and_counts() -> None:
    runner = _load_runner()
    bundle = {
        "query_variants": ["Android Jetpack Compose share intent local task app receipt polling"],
        "attempts": [
            {
                "index": 1,
                "query": "Android Jetpack Compose share intent local task app receipt polling",
                "source_count": 0,
                "result": {
                    "research_packet": {
                        "research_provider_retry_count": 2,
                        "research_provider_max_retries": 2,
                        "research_provider_failure_classification": "PROVIDER_ZERO_RESULTS",
                        "research_provider_attempts": [
                            {"attempt": 1, "source_count": 0, "providers": {"searxng": "blocked"}},
                            {"attempt": 2, "source_count": 0, "providers": {"searxng": "blocked"}},
                            {"attempt": 3, "source_count": 0, "providers": {"searxng": "blocked"}},
                        ],
                    }
                },
            }
        ],
    }
    summary = runner.research_provider_debug_summary(bundle)
    assert summary["query_attempt_count"] == 1
    assert summary["query_variant_source_counts"] == [0]
    assert summary["provider_attempt_count"] == 3
    assert summary["retry_count"] == 2
    assert summary["failure_classification"] == "PROVIDER_ZERO_RESULTS"


def test_research_provider_debug_summary_has_no_a3_specific_branch() -> None:
    runner = _load_runner()
    source = inspect.getsource(runner.research_provider_debug_summary)
    assert 'pid ==' not in source
    assert '"A3"' not in source


def test_run_stability_check_has_no_prompt_specific_branches() -> None:
    runner = _load_runner()
    source = inspect.getsource(runner.run_stability_check)
    assert 'pid == "A3"' not in source
    assert '"A3"' not in source


def test_repair_vague_decision_lines_does_not_invent_sources_or_pass(monkeypatch) -> None:
    runner = _load_runner()
    repair_source = inspect.getsource(runner.repair_vague_decision_lines)
    assert 'pid ==' not in repair_source
    assert '"A3"' not in repair_source
    monkeypatch.setattr(runner, "_rewrite_vague_decision", lambda decision, finding_hint: "")
    # With an empty/vague decision and no model available, the original line is preserved
    # (not silently fixed) and the grader still fails it honestly.
    sources = [
        {"title": "Send simple data to other apps", "url": "https://developer.android.com/training/sharing/send", "content": "Intents pass data between app components."},
        {"title": "android - Share Button In Compose - Stack Overflow", "url": "https://stackoverflow.com/questions/68870406/share-button-in-compose", "content": "A share button in compose can share data like download links between screens."},
    ]
    work = """Recommendation
Use intents and a compose share button to start proxy tasks and show receipts on the phone.

Research-to-decision changes
Finding: Intents pass data between app components and other apps on the device.
Source: Send simple data to other apps | host=developer.android.com | url=https://developer.android.com/training/sharing/send
Decision changed: Use Android intents to initiate proxy tasks from the phone and pass receipt data.
Why this changes the recommendation: This directly supports starting proxy tasks on mobile and routing receipt payloads.
Finding: A share button in compose can share data like download links between screens.
Source: android - Share Button In Compose - Stack Overflow | host=stackoverflow.com | url=https://stackoverflow.com/questions/68870406/share-button-in-compose
Decision changed: Think about it and maybe look into the various options later on.
Why this changes the recommendation: This is vague and offers no concrete actionable commitment for the plan.

Plan
Use intents and a compose share button, then validate the receipt payload path.

Limits
- Do not mutate protected paths or runtime behavior.

Next Handoff
Inspect the decision line and build the first share slice.
"""
    repaired, status = runner.repair_vague_decision_lines(work, sources)
    assert status["enabled"] is True
    # The grader must still fail the vague decision (no silent PASS / no invention).
    item = {"prompt_id": "A3", "internet_likely_required": True, "must_inspect_repo_context": False, "mac_likely_required": False, "expected_work_product": "plan"}
    result = runner.grade(item, repaired, {"research_packet": {"sources": sources}}, None, None, runner.synthetic_task(), "")
    assert result["final_status"] != "PASS"
    assert "research_change_no_specific_decision" in result["failed_gates"]


def test_fake_go_still_detected_after_generic_contract_changes() -> None:
    runner = _load_runner()
    item = {"prompt_id": "A3", "internet_likely_required": True, "must_inspect_repo_context": False, "mac_likely_required": False, "expected_work_product": "plan"}
    sources = [
        {"title": "Send simple data to other apps", "url": "https://developer.android.com/training/sharing/send", "content": "Intents pass data between app components and other applications."},
    ]
    # A work product with a real source but a fabricated/garbled token must still fail,
    # and fake_go must not be triggered by the contract changes.
    work = """Recommendation
Use intents with dexevelopeer local_l.

Research-to-decision changes
Finding: Intents pass data between app components and other applications.
Source: Send simple data to other apps | host=developer.android.com | url=https://developer.android.com/training/sharing/send
Decision changed: Use intents to initiate proxy tasks from the phone.
Why this changes the recommendation: This directly supports starting proxy tasks on mobile.

Plan
Use intents.

Limits
- Avoid fabricating tool names.

Next Handoff
Build first slice.
"""
    result = runner.grade(item, work, {"research_packet": {"sources": sources}}, None, None, runner.synthetic_task(), "")
    assert result["final_status"] != "PASS"
    assert "garbled_or_fabricated_tokens_detected" in result["failed_gates"]
    assert result["fake_go_detected"] is False


def test_model_owned_source_url_still_fails_after_contract_changes() -> None:
    runner = _load_runner()
    item = {"prompt_id": "A3", "internet_likely_required": True, "must_inspect_repo_context": False, "mac_likely_required": False, "expected_work_product": "plan"}
    real_sources = [
        {"title": "Send simple data to other apps", "url": "https://developer.android.com/training/sharing/send", "content": "Intents pass data between app components."},
    ]
    # A model-invented host that is NOT in the raw source registry must still fail provenance.
    work = """Recommendation
Use intents.

Research-to-decision changes
Finding: Intents pass data between app components and other applications.
Source: Awesome Intent Guide | host=modelinvented.example | url=https://modelinvented.example/intents
Decision changed: Use intents to initiate proxy tasks from the phone.
Why this changes the recommendation: This directly supports starting proxy tasks on mobile.

Plan
Use intents.

Limits
- Do not invent sources.

Next Handoff
Build first slice.
"""
    result = runner.grade(item, work, {"research_packet": {"sources": real_sources}}, None, None, runner.synthetic_task(), "")
    assert result["final_status"] != "PASS"
    assert "research_change_source_not_from_raw_sources" in result["failed_gates"]
