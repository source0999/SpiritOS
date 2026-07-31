from __future__ import annotations

import json
from pathlib import Path

import pytest

from source_proxy.jcode.pipeline_diagnosis import (
    ExactOllamaClient,
    FreshRunState,
    PipelineDiagnosisError,
    build_context_manifest,
    build_task_manifest,
    canonical_json,
    diff_snapshots,
    evaluate_run,
    execute_diagnostic_tool,
    legacy_bridge_transform,
    model_request_capture_receipt,
    openai_sse_response,
    parse_jcode_ndjson,
    run_diagnostic,
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


def test_exact_request_is_durably_journaled_before_failed_network_send(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    evidence_root = tmp_path / "evidence"
    monkeypatch.setattr(
        ExactOllamaClient,
        "verify_registry",
        lambda self: {"verified": True, "model": self.model},
    )
    network_observation: dict[str, object] = {}

    def fail_after_observing_journal(request, timeout):
        journals = list((evidence_root / "request-journal").glob("*.json"))
        network_observation["journal_count"] = len(journals)
        network_observation["ledger_exists"] = (evidence_root / "MODEL_REQUEST_LEDGER.ndjson").is_file()
        network_observation["request_bytes"] = request.data
        raise TimeoutError("bounded-test-timeout")

    monkeypatch.setattr(
        "source_proxy.jcode.pipeline_diagnosis.urllib.request.urlopen",
        fail_after_observing_journal,
    )
    client = ExactOllamaClient(
        "qwen2.5-coder:7b",
        run_id="failed-journal-test",
        evidence_root=evidence_root,
    )
    payload = {
        "model": "qwen2.5-coder:7b",
        "messages": [{"role": "user", "content": "hello"}],
        "stream": False,
    }

    with pytest.raises(TimeoutError, match="bounded-test-timeout"):
        client.post("/api/chat", payload)

    capture = model_request_capture_receipt(evidence_root, "failed-journal-test")
    entry = capture["journal_entries"][0]
    assert network_observation == {
        "journal_count": 1,
        "ledger_exists": True,
        "request_bytes": canonical_json(payload).encode("utf-8"),
    }
    assert capture["status"] == "COMPLETE"
    assert entry["request_body"] == payload
    assert entry["write_order"].startswith("durably_written_before")
    assert client.records[0].error == "TimeoutError:bounded-test-timeout"


def test_pre_repair_hash_only_request_is_explicitly_incomplete(tmp_path: Path):
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    events = [
        {
            "event": "request_started",
            "ledger_id": "model-request-01",
            "run_id": "old-timeout",
            "model": "qwen2.5-coder:7b",
            "request_sha256": "abc",
        },
        {
            "event": "request_finished",
            "ledger_id": "model-request-01",
            "error": "TimeoutError:timed out",
        },
    ]
    (evidence_root / "MODEL_REQUEST_LEDGER.ndjson").write_text(
        "".join(canonical_json(event) for event in events),
        encoding="utf-8",
    )

    capture = model_request_capture_receipt(evidence_root, "old-timeout")

    assert capture["status"] == "EVIDENCE_INCOMPLETE"
    assert capture["missing_request_body_ledger_ids"] == ["model-request-01"]
    assert capture["journal_entries"] == []


def test_run_timeout_seals_complete_failure_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    overlay = _copy_fixture(tmp_path, "R")
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()
    source_worktree = runtime_root / "source-worktree"
    source_worktree.mkdir()
    monkeypatch.setattr(
        "source_proxy.jcode.pipeline_diagnosis.create_fresh_run_state",
        lambda root, run_id, task_key: FreshRunState(
            source_worktree=source_worktree,
            overlay=overlay,
            runtime_root=runtime_root,
            base_head="test-head",
        ),
    )
    monkeypatch.setattr(
        "source_proxy.jcode.pipeline_diagnosis.cleanup_fresh_run_state",
        lambda root, state: {"runtime_root_removed": True},
    )
    monkeypatch.setattr(
        ExactOllamaClient,
        "verify_registry",
        lambda self: {"verified": True, "model": self.model},
    )
    monkeypatch.setattr(
        "source_proxy.jcode.pipeline_diagnosis.urllib.request.urlopen",
        lambda request, timeout: (_ for _ in ()).throw(TimeoutError("sealed-timeout")),
    )

    summary = run_diagnostic(
        run_id="sealed-timeout-run",
        task_key="R",
        lane="A",
        model="qwen2.5-coder:7b",
        root=tmp_path,
    )

    run_dir = tmp_path / "docs/architecture/jcode-qualification/pipeline-diagnosis/runs/sealed-timeout-run"
    evaluation = json.loads((run_dir / "evaluation_receipt.json").read_text(encoding="utf-8"))
    capture = json.loads((run_dir / "model_request_capture_receipt.json").read_text(encoding="utf-8"))
    packet = json.loads((run_dir / "exact_model_visible_packet.json").read_text(encoding="utf-8"))
    assert summary["classification"] == "diagnostic_run_error"
    assert summary["evidence_completeness"] == "COMPLETE"
    assert evaluation["failure"] == "TimeoutError:sealed-timeout"
    assert capture["status"] == "COMPLETE"
    assert packet["backend_requests"][0]["model"] == "qwen2.5-coder:7b"
    assert (run_dir / "hashes.json").is_file()


@pytest.mark.parametrize("value", ["", ".", "../x", "/tmp/x", "a/../b"])
def test_unsafe_relative_paths_fail_closed(value: str):
    with pytest.raises(PipelineDiagnosisError):
        safe_relative_path(value)
