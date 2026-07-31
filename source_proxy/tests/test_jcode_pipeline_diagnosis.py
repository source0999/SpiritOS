from __future__ import annotations

import json
from pathlib import Path

import pytest

from source_proxy.jcode.pipeline_diagnosis import (
    PipelineDiagnosisError,
    build_context_manifest,
    build_task_manifest,
    diff_snapshots,
    evaluate_run,
    execute_diagnostic_tool,
    legacy_bridge_transform,
    openai_sse_response,
    parse_jcode_ndjson,
    safe_inline_candidate_passes,
    safe_relative_path,
    snapshot_overlay,
    task_definition,
    tool_preserving_bridge_transform,
    tool_schemas,
)


FIXTURES = Path(__file__).parent / "fixtures/jcode_pipeline_diagnosis"


def _copy_fixture(tmp_path: Path, task_key: str) -> Path:
    source = FIXTURES / task_definition(task_key)["fixture"]
    overlay = tmp_path / "overlay"
    overlay.mkdir()
    for path in source.iterdir():
        (overlay / path.name).write_bytes(path.read_bytes())
    return overlay


def test_task_and_context_manifests_are_deterministic_and_do_not_expose_evaluator(tmp_path: Path):
    overlay = _copy_fixture(tmp_path, "R")
    first_context = build_context_manifest("R", overlay)
    second_context = build_context_manifest("R", overlay)
    task = build_task_manifest("R", first_context)

    assert first_context == second_context
    assert [item["path"] for item in first_context["ordered_file_manifest"]] == [
        "focused_check.py",
        "ledger.py",
    ]
    assert all(item["content"] for item in first_context["ordered_file_manifest"])
    assert task["context_packet_sha256"] == first_context["context_packet_sha256"]
    assert "expected" not in task
    assert "task_manifest_sha256" in task


def test_minimal_tool_schemas_are_native_function_tools():
    read_tools = tool_schemas("R")
    write_tools = tool_schemas("W")

    assert [tool["function"]["name"] for tool in read_tools] == ["read_file"]
    assert [tool["function"]["name"] for tool in write_tools] == [
        "read_file",
        "write_file",
        "apply_patch",
        "run_test",
    ]
    assert all(tool["type"] == "function" for tool in write_tools)
    assert write_tools[2]["function"]["parameters"]["required"] == ["path", "old", "new"]


def test_legacy_bridge_proves_role_and_tool_loss():
    request = {
        "model": "qwen2.5-coder:7b",
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "task"},
        ],
        "tools": tool_schemas("R"),
        "tool_choice": "auto",
    }

    transformed = legacy_bridge_transform(request, request["model"])

    assert transformed["prompt"] == "system\ntask"
    assert "messages" not in transformed
    assert "tools" not in transformed
    assert "tool_choice" not in transformed


def test_corrected_bridge_preserves_roles_tools_and_tool_result_name():
    request = {
        "model": "qwen2.5-coder:14b",
        "messages": [
            {"role": "system", "content": "system"},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {"name": "read_file", "arguments": '{"path":"ledger.py"}'},
                    }
                ],
            },
            {"role": "tool", "tool_call_id": "call-1", "content": "contents"},
        ],
        "tools": tool_schemas("R"),
        "tool_choice": "auto",
    }

    transformed = tool_preserving_bridge_transform(request, request["model"])

    assert [message["role"] for message in transformed["messages"]] == ["system", "assistant", "tool"]
    assert transformed["messages"][-1]["tool_name"] == "read_file"
    assert transformed["messages"][1]["tool_calls"][0]["function"]["arguments"] == {
        "path": "ledger.py"
    }
    assert transformed["tools"] == request["tools"]
    assert transformed["model"] == request["model"]


def test_ollama_tool_call_is_reconstructed_as_openai_sse():
    raw = openai_sse_response(
        {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"function": {"name": "read_file", "arguments": {"path": "ledger.py"}}}
                ],
            }
        },
        "qwen2.5-coder:7b",
    ).decode("utf-8")
    events = [
        json.loads(line.removeprefix("data: "))
        for line in raw.splitlines()
        if line.startswith("data: {")
    ]

    call = events[0]["choices"][0]["delta"]["tool_calls"][0]
    assert call["function"]["name"] == "read_file"
    assert json.loads(call["function"]["arguments"]) == {"path": "ledger.py"}
    assert events[-1]["choices"][0]["finish_reason"] == "tool_calls"
    assert raw.endswith("data: [DONE]\n\n")


def test_jcode_ndjson_parser_preserves_events_and_errors():
    parsed = parse_jcode_ndjson(
        '{"type":"tool_start","name":"read"}\n'
        '{"type":"tool_done","name":"read","status":"completed"}\n'
        'not-json\n'
        '{"type":"done","text":"grounded"}\n'
    )

    assert parsed["event_types"] == ["tool_start", "tool_done", "done"]
    assert [event["type"] for event in parsed["tool_events"]] == ["tool_start", "tool_done"]
    assert parsed["done_events"][0]["text"] == "grounded"
    assert parsed["parse_errors"][0]["line"] == 3


def test_diagnostic_tools_enforce_paths_and_apply_one_file(tmp_path: Path):
    overlay = _copy_fixture(tmp_path, "W")
    read = execute_diagnostic_tool(
        call={"function": {"name": "read_file", "arguments": {"path": "label.py"}}},
        task_key="W",
        overlay=overlay,
        turn=1,
    )
    denied = execute_diagnostic_tool(
        call={"function": {"name": "read_file", "arguments": {"path": "../secret"}}},
        task_key="W",
        overlay=overlay,
        turn=1,
    )
    patched = execute_diagnostic_tool(
        call={
            "function": {
                "name": "apply_patch",
                "arguments": {
                    "path": "label.py",
                    "old": "return value.strip()",
                    "new": 'return "-".join(value.strip().lower().split())',
                },
            }
        },
        task_key="W",
        overlay=overlay,
        turn=2,
    )
    tested = execute_diagnostic_tool(
        call={"function": {"name": "run_test", "arguments": {}}},
        task_key="W",
        overlay=overlay,
        turn=2,
    )

    assert read.status == "completed"
    assert denied.status == "failed"
    assert patched.status == "completed"
    assert tested.status == "completed"
    assert json.loads(tested.result)["exit_code"] == 0


def test_snapshot_ignores_test_caches_and_evaluator_accepts_only_source_change(tmp_path: Path):
    overlay = _copy_fixture(tmp_path, "W")
    before = snapshot_overlay(overlay)
    (overlay / "label.py").write_text(
        'def normalize_label(value: str) -> str:\n    return "-".join(value.strip().lower().split())\n',
        encoding="utf-8",
    )
    cache = overlay / "__pycache__"
    cache.mkdir()
    (cache / "label.cpython-313.pyc").write_bytes(b"runtime")
    pytest_cache = overlay / ".pytest_cache"
    pytest_cache.mkdir()
    (pytest_cache / "README.md").write_text("runtime", encoding="utf-8")
    (overlay / "DIAGNOSTIC_CONTEXT.json").write_text("", encoding="utf-8")
    (overlay / "DIAGNOSTIC_TASK.txt").write_text("", encoding="utf-8")
    after = snapshot_overlay(overlay)
    diff = diff_snapshots(before, after)
    evaluation = evaluate_run(
        "W",
        "B",
        {
            "final_text": "done",
            "tool_ledger": [
                {"tool_name": "run_test", "status": "completed", "result": '{"exit_code":0}'}
            ],
        },
        diff,
        {"exit_code": 0},
    )

    assert diff["changed_files"] == ["label.py"]
    assert evaluation["passed"] is True


def test_inline_candidate_evaluation_is_bounded():
    assert safe_inline_candidate_passes(
        'def normalize_label(value: str) -> str:\n    return "-".join(value.strip().lower().split())\n'
    )
    assert not safe_inline_candidate_passes("import os\ndef normalize_label(value):\n    return value")


@pytest.mark.parametrize("value", ["", ".", "../x", "/tmp/x", "a/../b"])
def test_unsafe_relative_paths_fail_closed(value: str):
    with pytest.raises(PipelineDiagnosisError):
        safe_relative_path(value)
