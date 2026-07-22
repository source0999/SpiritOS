from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

import source_proxy.tasks.long_running as long_running


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
