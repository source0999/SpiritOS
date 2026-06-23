from __future__ import annotations

from types import SimpleNamespace

from source_proxy.api import decision
from source_proxy.decision.worker_tool_adapters import run_process_adapter


def test_process_adapter_serializes_typed_contract(monkeypatch) -> None:
    def fake_run(command, cwd, check, capture_output, text, timeout):
        assert command == ["git", "status"]
        assert check is False
        assert capture_output is True
        assert text is True
        assert timeout == 3
        return SimpleNamespace(returncode=0, stdout="ok\n", stderr="")

    monkeypatch.setattr("source_proxy.decision.worker_tool_adapters.subprocess.run", fake_run)

    result = run_process_adapter(
        adapter_id="unit_git_status",
        command=("git", "status"),
        cwd="/tmp/work",
        timeout_seconds=3,
        owner="unit-test",
        evidence_ref="ev-1",
    )
    payload = result.to_dict()

    assert payload["status"] == "used"
    assert payload["returncode"] == 0
    assert payload["request"]["adapter_id"] == "unit_git_status"
    assert payload["request"]["attempt"] == 1
    assert payload["request"]["owner"] == "unit-test"
    assert payload["request"]["evidence_ref"] == "ev-1"
    assert payload["request"]["failure_class"] == "TOOL_FAILURE"


def test_safe_dirty_tree_status_preserves_existing_payload_shape(monkeypatch) -> None:
    def fake_adapter(**kwargs):
        assert kwargs["adapter_id"] == "git_status_dirty_tree"
        assert kwargs["timeout_seconds"] == 5
        return SimpleNamespace(returncode=0, stdout=" M source_proxy/api/decision.py\n", stderr="")

    monkeypatch.setattr(decision, "run_process_adapter", fake_adapter)

    payload = decision._safe_dirty_tree_status()

    assert payload == {
        "status": "used",
        "is_dirty": True,
        "tracked_change_count": 1,
        "returncode": 0,
        "stderr": "",
    }


def test_safe_dirty_tree_status_exception_path_is_unchanged(monkeypatch) -> None:
    def fail_adapter(**kwargs):
        raise RuntimeError("adapter unavailable")

    monkeypatch.setattr(decision, "run_process_adapter", fail_adapter)

    payload = decision._safe_dirty_tree_status()

    assert payload["status"] == "blocked"
    assert payload["reason"] == "git_status_unavailable"
    assert "RuntimeError" in payload["error"]
