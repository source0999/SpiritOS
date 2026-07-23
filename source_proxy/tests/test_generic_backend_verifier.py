from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

import source_proxy.tasks.long_running as long_running


def _fixed_literal_callable_task() -> SimpleNamespace:
    prompt = (
        "Please add a small `count_ready_orders` service function that returns "
        "the number of orders whose `status` exactly matches "
        "`ready_for_pickup`. Keep existing lookup behavior and add focused tests."
    )
    return SimpleNamespace(
        description=prompt,
        ast_snapshot={
            "coding_orchestrator": {
                "target_plugin_proposal": {
                    "original_task": prompt,
                    "semantic_review_binding": {
                        "server_task_spec": {
                            "target": "src/service.py",
                        }
                    },
                }
            }
        },
    )


def _configure_backend_verifier(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[Path, list[tuple[list[str], dict[str, object]]]]:
    workspace = (tmp_path / "fixture").resolve()
    workspace.mkdir()
    site_packages = tmp_path / "runtime" / "lib" / "python3.11" / "site-packages"
    site_packages.mkdir(parents=True)
    calls: list[tuple[list[str], dict[str, object]]] = []

    monkeypatch.setattr(
        long_running,
        "_task_target_plugin_identity",
        lambda _task: {"plugin_id": "generic-workspace"},
    )
    monkeypatch.setattr(
        long_running,
        "_approved_execution_workspace_root",
        lambda _task, reason_prefix: workspace,
    )
    monkeypatch.setattr(
        long_running,
        "_target_plugin_execution_workspace",
        lambda _identity, require_state_match: workspace,
    )
    monkeypatch.setattr(long_running.shutil, "which", lambda name: "/usr/bin/docker")
    monkeypatch.setattr(long_running.sys, "prefix", str(tmp_path / "runtime"))

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((list(command), dict(kwargs)))
        return subprocess.CompletedProcess(command, 0, stdout="2 passed\n", stderr="")

    monkeypatch.setattr(long_running.subprocess, "run", fake_run)
    return workspace, calls


def test_generic_backend_verifier_uses_restricted_read_only_container(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace, calls = _configure_backend_verifier(monkeypatch, tmp_path)

    checks, evidence = long_running._run_generic_backend_post_apply_verification(
        SimpleNamespace(),
        changed_files=[{"path": "src/example.py"}],
    )

    assert checks[0]["status"] == "passed"
    assert evidence["runtime"] == "restricted_container"
    assert evidence["network"] == "none"
    assert evidence["workspace_mount"] == "read_only"
    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command[:3] == ["/usr/bin/docker", "run", "--rm"]
    assert command[command.index("--network") + 1] == "none"
    assert "--read-only" in command
    assert command[command.index("--cap-drop") + 1] == "ALL"
    assert command[command.index("--security-opt") + 1] == "no-new-privileges=true"
    assert f"type=bind,src={workspace},dst=/workspace,readonly" in command
    assert any(
        item.startswith("type=bind,src=") and item.endswith(",dst=/host-site,readonly")
        for item in command
    )
    assert kwargs["cwd"] == workspace
    assert kwargs["env"] == {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
    assert "PYTEST_ADDOPTS=-p no:cacheprovider" in command


def test_generic_backend_verifier_records_test_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_backend_verifier(monkeypatch, tmp_path)
    monkeypatch.setattr(
        long_running.subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            command,
            1,
            stdout="1 failed\n",
            stderr="assertion failed\n",
        ),
    )

    checks, evidence = long_running._run_generic_backend_post_apply_verification(
        SimpleNamespace(),
        changed_files=[{"path": "tests/test_example.py"}],
    )

    assert checks[0]["status"] == "failed"
    assert checks[0]["exit_code"] == 1
    assert "1 failed" in checks[0]["output_tail"]
    assert evidence["exit_code"] == 1


def test_generic_backend_verifier_rejects_invented_required_callable_input(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace, _calls = _configure_backend_verifier(monkeypatch, tmp_path)
    target = workspace / "src" / "service.py"
    target.parent.mkdir()
    target.write_text(
        "\n".join(
            [
                "ORDERS = []",
                "",
                "def count_ready_orders(status: str) -> int:",
                "    return sum(",
                "        1 for order in ORDERS",
                '        if order["status"] == "ready_for_pickup"',
                "    )",
                "",
            ]
        ),
        encoding="utf-8",
    )

    checks, evidence = long_running._run_generic_backend_post_apply_verification(
        _fixed_literal_callable_task(),
        changed_files=[
            {"path": "src/service.py"},
            {"path": "tests/test_service.py"},
        ],
    )

    callable_check = checks[1]
    assert checks[0]["status"] == "passed"
    assert callable_check["id"] == "generic_backend_public_callable_contract"
    assert callable_check["required"] is True
    assert callable_check["status"] == "failed"
    assert "zero required parameters" in callable_check["output_tail"]
    assert evidence["public_callable_contract"] == {
        "applicable": True,
        "target": "src/service.py",
        "required_zero_arg_callables": ["count_ready_orders"],
        "missing_callables": [],
        "violations": [
            {
                "callable": "count_ready_orders",
                "required_positional_parameters": 1,
                "required_keyword_only_parameters": 0,
                "required_parameters": 1,
            }
        ],
        "passed": False,
    }


def test_generic_backend_verifier_accepts_repaired_zero_arg_callable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace, _calls = _configure_backend_verifier(monkeypatch, tmp_path)
    target = workspace / "src" / "service.py"
    target.parent.mkdir()
    target.write_text(
        "\n".join(
            [
                "ORDERS = []",
                "",
                "def count_ready_orders() -> int:",
                "    return sum(",
                "        1 for order in ORDERS",
                '        if order["status"] == "ready_for_pickup"',
                "    )",
                "",
            ]
        ),
        encoding="utf-8",
    )

    checks, evidence = long_running._run_generic_backend_post_apply_verification(
        _fixed_literal_callable_task(),
        changed_files=[
            {"path": "src/service.py"},
            {"path": "tests/test_service.py"},
        ],
    )

    assert [check["status"] for check in checks] == ["passed", "passed"]
    assert evidence["public_callable_contract"]["passed"] is True
    assert evidence["public_callable_contract"]["violations"] == []


def test_generic_backend_verifier_rejects_non_generic_task() -> None:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(long_running, "_task_target_plugin_identity", lambda _task: {})
        with pytest.raises(
            long_running.LongRunningTaskError,
            match="generic backend verifier requires",
        ) as raised:
            long_running._run_generic_backend_post_apply_verification(
                SimpleNamespace(),
                changed_files=[{"path": "src/example.py"}],
            )
    assert raised.value.reason_code == "generic_backend_target_plugin_identity_missing"
