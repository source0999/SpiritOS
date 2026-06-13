from __future__ import annotations

import json
from pathlib import Path

from source_proxy.decision.artifact_behavior_contract import build_artifact_behavior_contract
from source_proxy.decision.artifact_repair_contract import (
    build_artifact_failure_packet,
    build_behavior_failure_packet,
    build_repair_prompt_from_failure_packet,
)
from source_proxy.decision.artifact_repair_loop import run_limited_artifact_repair_loop
from source_proxy.decision.artifact_retest_result import build_artifact_retest_result


def _packet(workspace: Path, *, artifact_name: str = "index.html", attempt_count: int = 0) -> dict:
    artifact = workspace / artifact_name
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("<!doctype html><html><body><output>0</output></body></html>\n", encoding="utf-8")
    contract = build_artifact_behavior_contract(
        prompt="make a calculator app",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )
    return build_artifact_failure_packet(
        prompt="make a calculator app",
        behavior_contract=contract,
        verifier_result={
            "path": str(artifact),
            "test": "click 2 + 3 =",
            "observed": {"display": "0"},
            "verdict": "FAIL",
            "reason": "display did not equal 5",
        },
        evidence_packet={"source_proxy_score_status": "GO"},
        allowed_workspace=str(workspace),
        attempt_count=attempt_count,
    )


def _write_action(target: str, content: str) -> str:
    return json.dumps(
        {
            "action_type": "WriteFile",
            "target": target,
            "arguments": {"content": content},
            "reason": "Repair the generated disposable artifact.",
        }
    )


def test_repair_loop_records_changed_artifact_diff(tmp_path: Path) -> None:
    packet = _packet(tmp_path)
    result = run_limited_artifact_repair_loop(
        failure_packet=packet,
        repair_call=lambda _packet, _prompt, _attempt: _write_action(
            "index.html",
            "<!doctype html><html><body><output>5</output></body></html>\n",
        ),
    )

    assert result["status"] == "READY_FOR_RETEST"
    assert result["handoff_required"] is False
    assert result["changed_files"] == ["index.html"]
    assert result["repair_attempts"] == 1
    assert result["repaired_files"] == ["index.html"]
    assert result["repair_model_authored_targets"] == ["index.html"]
    assert result["file_equals_model_action_content"] is True
    assert result["bytes_written_match_model_authored_content"] is True
    assert result["valid_repaired_targets"] == ["index.html"]
    assert "-<!doctype html><html><body><output>0</output></body></html>" in result["diffs"][0]
    assert "+<!doctype html><html><body><output>5</output></body></html>" in result["diffs"][0]


def test_repair_loop_accepts_valid_path_bound_html_css_js_blocks(tmp_path: Path) -> None:
    packet = _packet(tmp_path)
    transcript = "\n".join(
        [
            '<file path="index.html">',
            '<!doctype html><html><head><link rel="stylesheet" href="styles.css"></head><body><button id="go">Add</button><output>5</output><script src="app.js"></script></body></html>',
            "</file>",
            '<file path="styles.css">',
            "body { font-family: system-ui; }",
            "</file>",
            '<file path="app.js">',
            "document.querySelector('#go').addEventListener('click',()=>document.querySelector('output').textContent='5');",
            "</file>",
        ]
    )

    result = run_limited_artifact_repair_loop(
        failure_packet=packet,
        repair_call=lambda _packet, _prompt, _attempt: transcript,
    )

    assert result["status"] == "READY_FOR_RETEST"
    assert result["repaired_files"] == ["app.js", "index.html", "styles.css"]
    assert sorted(result["repair_model_authored_targets"]) == ["app.js", "index.html", "styles.css"]
    assert result["file_equals_model_action_content"] is True
    assert result["bytes_written_match_model_authored_content"] is True
    assert (tmp_path / "app.js").read_text(encoding="utf-8").startswith("document.querySelector")


def test_behavior_fail_with_open_pass_creates_repair_packet(tmp_path: Path) -> None:
    artifact = tmp_path / "index.html"
    artifact.write_text("<!doctype html><html><body><button>Save</button></body></html>\n", encoding="utf-8")
    contract = build_artifact_behavior_contract(
        prompt="make a notes app",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )
    packet = build_behavior_failure_packet(
        prompt="make a scratch jot app",
        artifact_class="static_ui_artifact",
        behavior_contract=contract,
        behavior_probe={
            "test": "notes-create-edit-visible-note",
            "verdict": "FAIL",
            "actual": {"before": "Save", "after": "Note saved!", "appears": False},
        },
        selected_preview_path=str(artifact),
        generated_files=["index.html", "script.js", "styles.css"],
        model_authored_targets=["index.html", "script.js", "styles.css"],
        final_reason_codes=["behavior_required_but_unverified"],
        allowed_workspace=str(tmp_path),
    )

    assert packet["status"] == "READY_FOR_LOCAL_REPAIR"
    assert packet["failure_kind"] == "post_behavior_probe_failure"
    assert packet["observed_behavior"]["actual"]["appears"] is False
    assert "behavior_failed_verified" in packet["reason_codes"]
    assert "behavior_required_but_unverified" not in packet["reason_codes"]
    assert packet["repair_attempt_count"] == 0
    assert packet["expected_observable_behavior"] == "Entered note text remains visible in the app artifact; a saved-status message alone is not enough."
    assert packet["behavior_probe_evidence"]["actual_values"]["appears"] is False
    assert packet["file_list"] == ["index.html", "script.js", "styles.css"]


def test_failed_probe_evidence_builds_repair_packet_when_contract_is_partial(tmp_path: Path) -> None:
    artifact = tmp_path / "index.html"
    artifact.write_text("<!doctype html><html><body><button>Go</button><output>0</output></body></html>\n", encoding="utf-8")
    partial_contract = {
        "contract_version": "partial-contract",
        "behavior_required": True,
        "probe_targets": [],
    }

    packet = build_behavior_failure_packet(
        prompt="make a count button",
        artifact_class="static_ui_artifact",
        behavior_contract=partial_contract,
        behavior_probe={
            "probe_id": "counter-visible-increment",
            "test": "counter-visible-increment",
            "verdict": "FAIL",
            "acceptance_criterion": "Clicking the primary button visibly changes the counter.",
            "expected_observation": "Counter text increments after click.",
            "observable_actions": ["click primary counter button"],
            "actual": {"before": "0", "after": "0", "clicked": ["button"]},
            "reason_codes": ["counter_value_unchanged"],
        },
        selected_preview_path=str(artifact),
        generated_files=["index.html"],
        model_authored_targets=["index.html"],
        final_reason_codes=["behavior_required_but_unverified"],
        allowed_workspace=str(tmp_path),
        console_details={"errors": []},
    )
    prompt = build_repair_prompt_from_failure_packet(packet)

    assert packet["status"] == "READY_FOR_LOCAL_REPAIR"
    assert packet["handoff_required"] is False
    assert packet["probe_id"] == "counter-visible-increment"
    assert packet["expected_behavior"]["acceptance_criterion"] == "Clicking the primary button visibly changes the counter."
    assert packet["observed_behavior"]["before"] == "0"
    assert packet["observed_behavior"]["after"] == "0"
    assert packet["behavior_probe_evidence"]["clicked"] == ["button"]
    assert "counter_value_unchanged" in packet["reason_codes"]
    assert "behavior_failed_verified" in packet["reason_codes"]
    assert "behavior_required_but_unverified" not in packet["reason_codes"]
    assert "Counter text increments after click." in prompt


def test_failed_probe_string_expected_metadata_does_not_handoff(tmp_path: Path) -> None:
    artifact = tmp_path / "index.html"
    artifact.write_text("<!doctype html><html><body><button>Start</button><output>00:00</output></body></html>\n", encoding="utf-8")

    packet = build_behavior_failure_packet(
        prompt="make a countdown widget",
        artifact_class="static_ui_artifact",
        behavior_contract={"contract_version": "partial", "behavior_required": True, "probe_targets": []},
        behavior_probe={
            "test": "timer-change",
            "verdict": "FAIL",
            "expected": "timer text changes after start",
            "primary_behavior_failure_bucket": "timer_no_visible_change_after_start",
            "actual": {"before": "00:00", "afterStart": "00:00"},
        },
        selected_preview_path=str(artifact),
        generated_files=["index.html"],
        model_authored_targets=["index.html"],
        final_reason_codes=[],
        allowed_workspace=str(tmp_path),
    )
    prompt = build_repair_prompt_from_failure_packet(packet)

    assert packet["status"] == "READY_FOR_LOCAL_REPAIR"
    assert packet["handoff_required"] is False
    assert packet["expected_behavior"]["acceptance_criterion"] == "timer text changes after start"
    assert packet["primary_behavior_failure_bucket"] == "timer_no_visible_change_after_start"
    assert "Primary failure bucket: timer_no_visible_change_after_start" in prompt
    assert '{"action_type":"WriteFile"' in prompt
    assert '<file path="RELATIVE_ALLOWED_FILE">' in prompt


def test_failed_probe_without_contract_or_expected_probe_metadata_handoffs(tmp_path: Path) -> None:
    artifact = tmp_path / "index.html"
    artifact.write_text("<!doctype html><html><body><button>Go</button></body></html>\n", encoding="utf-8")

    packet = build_behavior_failure_packet(
        prompt="make a mystery interaction",
        artifact_class="static_ui_artifact",
        behavior_contract={"behavior_required": True, "probe_targets": []},
        behavior_probe={"test": "unknown-probe", "verdict": "FAIL", "actual": {"clicked": True}},
        selected_preview_path=str(artifact),
        generated_files=["index.html"],
        model_authored_targets=["index.html"],
        final_reason_codes=[],
        allowed_workspace=str(tmp_path),
    )

    assert packet["status"] == "HANDOFF"
    assert "missing_probe_metadata" in packet["handoff_reasons"]
    assert "repair_metadata_incomplete" in packet["reason_codes"]


def test_repair_prompt_includes_observed_failure_without_solution_code(tmp_path: Path) -> None:
    artifact = tmp_path / "index.html"
    artifact.write_text("<!doctype html><html><body><button>Save</button></body></html>\n", encoding="utf-8")
    contract = build_artifact_behavior_contract(
        prompt="make a notes app",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )
    packet = build_behavior_failure_packet(
        prompt="make a scratch jot app",
        artifact_class="static_ui_artifact",
        behavior_contract=contract,
        behavior_probe={
            "test": "notes-create-edit-visible-note",
            "verdict": "FAIL",
            "actual": {"before": "Save", "after": "Note saved!", "appears": False},
        },
        selected_preview_path=str(artifact),
        generated_files=["index.html"],
        model_authored_targets=["index.html"],
        final_reason_codes=[],
        allowed_workspace=str(tmp_path),
    )
    prompt = build_repair_prompt_from_failure_packet(packet)

    assert "make a scratch jot app" in prompt
    assert "Note saved!" in prompt
    assert "Entered note text remains visible" in prompt
    assert "function saveNote" not in prompt
    assert "<script>" not in prompt
    assert "Use only relative .html, .css, and .js paths" in prompt


def test_repair_loop_handoff_on_path_escape_or_unallowed_target(tmp_path: Path) -> None:
    packet = _packet(tmp_path)
    result = run_limited_artifact_repair_loop(
        failure_packet=packet,
        repair_call=lambda _packet, _prompt, _attempt: _write_action("../outside.html", "escape"),
    )

    assert result["status"] == "HANDOFF"
    assert result["handoff_reason"] == "unsafe_or_blocked_repair_output"
    assert "path_escape" in result["reason_codes"]
    assert not (tmp_path.parent / "outside.html").exists()


def test_repair_loop_rejects_secret_package_and_real_app_paths(tmp_path: Path) -> None:
    packet = _packet(tmp_path)
    cases = [
        ('<file path=".env">TOKEN=bad</file>', "protected_path"),
        ('<file path="package.json">{}</file>', "target_not_allowed"),
        ('<file path="src/app.html"><!doctype html></file>', "protected_path"),
        ('<file path="source_proxy/demo.html"><!doctype html></file>', "protected_path"),
    ]

    for transcript, reason in cases:
        result = run_limited_artifact_repair_loop(
            failure_packet=packet,
            repair_call=lambda _packet, _prompt, _attempt, transcript=transcript: transcript,
        )

        assert result["status"] == "HANDOFF", transcript
        assert reason in result["reason_codes"], transcript
        assert result["attempts_used"] == 1, transcript


def test_repair_loop_respects_attempt_limit(tmp_path: Path) -> None:
    packet = _packet(tmp_path, attempt_count=1)
    result = run_limited_artifact_repair_loop(
        failure_packet=packet,
        repair_call=lambda _packet, _prompt, _attempt: _write_action("index.html", "unused"),
        max_attempts=1,
    )

    assert result["status"] == "HANDOFF"
    assert result["handoff_reason"] == "attempt_limit_reached"
    assert result["attempts_used"] == 0


def test_repair_loop_does_not_retry_after_failed_repair(tmp_path: Path) -> None:
    packet = _packet(tmp_path)
    calls = 0

    def bad_repair(_packet: dict, _prompt: str, _attempt: int) -> str:
        nonlocal calls
        calls += 1
        return _write_action("index.html", "<!doctype html><html><body><output>still 0</output></body></html>\n")

    result = run_limited_artifact_repair_loop(failure_packet=packet, repair_call=bad_repair, max_attempts=1)
    retest = build_artifact_retest_result(
        repair_result=result,
        behavior_contract=packet["behavior_contract"],
        artifact_ready=True,
        behavior_result={"verdict": "FAIL", "test": "calculator-basic-arithmetic", "actual": {"display": "0"}},
    )

    assert calls == 1
    assert result["attempts_used"] == 1
    assert retest["canonical_final_verdict"] == "FAIL"
    assert "post_repair_behavior_fail" in retest["final_reason_codes"]
    assert "repair_attempts_1" in retest["final_reason_codes"]
    assert "behavior_required_but_unverified" not in retest["final_reason_codes"]


def test_repair_loop_handoff_on_failed_local_worker(tmp_path: Path) -> None:
    packet = _packet(tmp_path)

    def fail_worker(_packet: dict, _prompt: str, _attempt: int) -> str:
        raise RuntimeError("local worker unavailable")

    result = run_limited_artifact_repair_loop(failure_packet=packet, repair_call=fail_worker)

    assert result["status"] == "HANDOFF"
    assert result["handoff_reason"] == "repair_worker_failed"
    assert "repair_worker_failed" in result["reason_codes"]


def test_repair_loop_handoff_on_malformed_repair_output(tmp_path: Path) -> None:
    packet = _packet(tmp_path)
    result = run_limited_artifact_repair_loop(
        failure_packet=packet,
        repair_call=lambda _packet, _prompt, _attempt: "Here is some prose without a file action.",
    )

    assert result["status"] == "HANDOFF"
    assert result["handoff_reason"] == "repair_attempts_exhausted"
    assert "invalid_action_schema" in result["reason_codes"]


def test_repair_loop_rejects_free_floating_repair_code(tmp_path: Path) -> None:
    packet = _packet(tmp_path)
    result = run_limited_artifact_repair_loop(
        failure_packet=packet,
        repair_call=lambda _packet, _prompt, _attempt: "```html\n<html><body>no path</body></html>\n```",
    )

    assert result["status"] == "HANDOFF"
    assert "free_floating_code_no_path_action" in result["reason_codes"]


def test_repair_loop_blocks_protected_packet_before_repair(tmp_path: Path) -> None:
    contract = build_artifact_behavior_contract(
        prompt="make a password checker",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )
    packet = build_behavior_failure_packet(
        prompt="make a password checker",
        artifact_class="static_ui_artifact",
        behavior_contract=contract,
        behavior_probe={"test": "password-strength-feedback-change", "verdict": "FAIL", "actual": {}},
        selected_preview_path=str(tmp_path.parent / "outside.html"),
        generated_files=["index.html"],
        model_authored_targets=["index.html"],
        final_reason_codes=[],
        allowed_workspace=str(tmp_path),
    )

    result = run_limited_artifact_repair_loop(
        failure_packet=packet,
        repair_call=lambda _packet, _prompt, _attempt: _write_action("index.html", "unused"),
    )

    assert packet["handoff_required"] is True
    assert result["status"] == "HANDOFF"
    assert result["attempts_used"] == 0


def test_repaired_behavior_pass_updates_final_verdict() -> None:
    contract = build_artifact_behavior_contract(
        prompt="make a password checker",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )
    result = build_artifact_retest_result(
        repair_result={"status": "READY_FOR_RETEST", "attempts_used": 1, "changed_files": ["index.html"]},
        behavior_contract=contract,
        artifact_ready=True,
        behavior_result={"verdict": "PASS", "test": "password-strength-feedback-change", "actual": {"changed": True}},
    )

    assert result["canonical_final_verdict"] == "PASS"
    assert "post_repair_behavior_pass" in result["final_reason_codes"]
    assert "repair_attempts_1" in result["final_reason_codes"]
