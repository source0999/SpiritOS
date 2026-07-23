from __future__ import annotations

import json
import shutil
import subprocess
import sys
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


def _optional_integer_callable_task() -> SimpleNamespace:
    prompt = (
        "Add pagination to `list_records` with optional `offset` and `limit` "
        "arguments. Defaults should still return all records, both values "
        "must be non-negative integers (with `limit` at least 1 when "
        "provided), and the function must never mutate the module's stored "
        "records. Raise `ValueError` for invalid pagination values."
    )
    return SimpleNamespace(
        description=prompt,
        ast_snapshot={
            "coding_orchestrator": {
                "target_plugin_proposal": {
                    "original_task": prompt,
                    "semantic_review_binding": {
                        "server_task_spec": {
                            "target": "src/records.py",
                        }
                    },
                }
            }
        },
    )


def _configure_backend_verifier(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    numeric_probe_result: dict[str, object] | None = None,
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
        if "-c" in command:
            result = numeric_probe_result or {
                "passed": True,
                "reason": "",
                "violation_count": 0,
                "violations": [],
            }
            return subprocess.CompletedProcess(
                command,
                0 if result.get("passed") is True else 1,
                stdout=(
                    long_running._GENERIC_BACKEND_PUBLIC_CONTRACT_SENTINEL
                    + json.dumps(result, separators=(",", ":"), sort_keys=True)
                    + "\n"
                ),
                stderr="",
            )
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


def test_generic_backend_verifier_runs_numeric_contract_in_same_sandbox(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace, calls = _configure_backend_verifier(monkeypatch, tmp_path)
    target = workspace / "src" / "records.py"
    target.parent.mkdir()
    target.write_text(
        "\n".join(
            [
                "RECORDS = []",
                "",
                "def _validate(name, value, minimum):",
                "    if type(value) is not int or value < minimum:",
                "        raise ValueError(name)",
                "",
                "def list_records(offset=0, limit=None):",
                "    _validate('offset', offset, 0)",
                "    if limit is not None:",
                "        _validate('limit', limit, 1)",
                "    end = None if limit is None else offset + limit",
                "    return RECORDS[offset:end]",
                "",
            ]
        ),
        encoding="utf-8",
    )

    checks, evidence = long_running._run_generic_backend_post_apply_verification(
        _optional_integer_callable_task(),
        changed_files=[{"path": "src/records.py"}],
    )

    assert [check["status"] for check in checks] == ["passed", "passed"]
    assert len(calls) == 2
    probe_command, probe_kwargs = calls[1]
    assert probe_command[probe_command.index("--network") + 1] == "none"
    assert "--read-only" in probe_command
    assert probe_command[probe_command.index("--cap-drop") + 1] == "ALL"
    assert probe_command[probe_command.index("--security-opt") + 1] == (
        "no-new-privileges=true"
    )
    assert probe_kwargs["env"] == {
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
    }
    contract_evidence = evidence["public_callable_contract"]
    assert contract_evidence["callable"] == "list_records"
    assert contract_evidence["optional_integer_parameters"] == [
        {"name": "offset", "minimum": 0},
        {"name": "limit", "minimum": 1},
    ]
    assert contract_evidence["runtime_probe"]["host_import"] is False
    assert contract_evidence["runtime_probe"]["result"]["passed"] is True


@pytest.mark.parametrize(
    ("probe_result", "expected_detail"),
    [
        (
            {
                "passed": False,
                "reason": "contract_violations",
                "violation_count": 1,
                "violations": [
                    {
                        "reason": "invalid_value_accepted",
                        "parameter": "offset",
                        "case": "bool_true",
                    }
                ],
            },
            "offset/bool_true/invalid_value_accepted",
        ),
        (
            {
                "passed": False,
                "reason": "contract_violations",
                "violation_count": 1,
                "violations": [
                    {
                        "reason": "wrong_invalid_exception",
                        "parameter": "offset",
                        "case": "numeric_string",
                        "exception_type": "TypeError",
                    }
                ],
            },
            "offset/numeric_string/wrong_invalid_exception/TypeError",
        ),
        (
            {
                "passed": False,
                "reason": "contract_violations",
                "violation_count": 1,
                "violations": [
                    {
                        "reason": "invalid_value_accepted",
                        "parameter": "limit",
                        "case": "below_minimum",
                    }
                ],
            },
            "limit/below_minimum/invalid_value_accepted",
        ),
        (
            {
                "passed": False,
                "reason": "contract_violations",
                "violation_count": 1,
                "violations": [
                    {
                        "reason": "wrong_invalid_exception",
                        "parameter": "limit",
                        "case": "fractional_float",
                        "exception_type": "TypeError",
                    }
                ],
            },
            "limit/fractional_float/wrong_invalid_exception/TypeError",
        ),
    ],
)
def test_generic_backend_verifier_rejects_numeric_contract_runtime_failures(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    probe_result: dict[str, object],
    expected_detail: str,
) -> None:
    workspace, _calls = _configure_backend_verifier(
        monkeypatch,
        tmp_path,
        numeric_probe_result=probe_result,
    )
    target = workspace / "src" / "records.py"
    target.parent.mkdir()
    target.write_text(
        "\n".join(
            [
                "RECORDS = []",
                "",
                "def list_records(offset=0, limit=None):",
                "    if offset < 0:",
                "        raise ValueError('offset')",
                "    if limit is not None and limit < 1:",
                "        raise ValueError('limit')",
                "    return RECORDS[offset:]",
                "",
            ]
        ),
        encoding="utf-8",
    )

    checks, evidence = long_running._run_generic_backend_post_apply_verification(
        _optional_integer_callable_task(),
        changed_files=[{"path": "src/records.py"}],
    )

    callable_check = checks[1]
    assert callable_check["required"] is True
    assert callable_check["status"] == "failed"
    assert expected_detail in callable_check["output_tail"]
    assert evidence["public_callable_contract"]["passed"] is False
    assert (
        evidence["public_callable_contract"]["runtime_probe"]["result"]
        == probe_result
    )


def test_generic_backend_verifier_rejects_required_numeric_parameter_before_probe(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace, calls = _configure_backend_verifier(monkeypatch, tmp_path)
    target = workspace / "src" / "records.py"
    target.parent.mkdir()
    target.write_text(
        "def list_records(offset, limit=None):\n    return []\n",
        encoding="utf-8",
    )

    checks, evidence = long_running._run_generic_backend_post_apply_verification(
        _optional_integer_callable_task(),
        changed_files=[{"path": "src/records.py"}],
    )

    assert checks[1]["status"] == "failed"
    assert "offset:parameter_is_not_optional" in checks[1]["output_tail"]
    assert len(calls) == 1
    assert evidence["public_callable_contract"]["runtime_probe"] is None


def test_generic_backend_verifier_fails_ambiguous_numeric_contract_without_probe(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace, calls = _configure_backend_verifier(monkeypatch, tmp_path)
    target = workspace / "src" / "records.py"
    target.parent.mkdir()
    target.write_text(
        "def list_records(offset=0, limit=None):\n    return []\n",
        encoding="utf-8",
    )
    prompt = (
        "Add pagination to `list_records` with optional `offset`, `offset`, "
        "and `limit` arguments. All values must be non-negative integers. "
        "Raise `ValueError` for invalid pagination values."
    )
    task = _optional_integer_callable_task()
    task.description = "A stale non-authoritative description."
    task.ast_snapshot["coding_orchestrator"]["target_plugin_proposal"][
        "original_task"
    ] = prompt

    checks, evidence = long_running._run_generic_backend_post_apply_verification(
        task,
        changed_files=[{"path": "src/records.py"}],
    )

    assert checks[1]["required"] is True
    assert checks[1]["status"] == "failed"
    assert "optional_integer_contract_ambiguous" in checks[1]["output_tail"]
    assert len(calls) == 1
    assert evidence["public_callable_contract"]["runtime_probe"] is None


def test_generic_backend_verifier_preserves_both_contract_subreceipts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace, calls = _configure_backend_verifier(monkeypatch, tmp_path)
    target = workspace / "src" / "records.py"
    target.parent.mkdir()
    target.write_text(
        "\n".join(
            [
                "ORDERS = []",
                "RECORDS = []",
                "",
                "def count_ready_orders(status):",
                "    return 0",
                "",
                "def list_records(offset=0, limit=None):",
                "    return RECORDS[offset:]",
                "",
            ]
        ),
        encoding="utf-8",
    )
    numeric_task = _optional_integer_callable_task()
    prompt = (
        "Add a `count_ready_orders` service function that returns the number "
        "of orders whose `status` exactly matches `ready_for_pickup`. "
        + numeric_task.description
    )
    numeric_task.description = prompt
    numeric_task.ast_snapshot["coding_orchestrator"]["target_plugin_proposal"][
        "original_task"
    ] = prompt

    checks, evidence = long_running._run_generic_backend_post_apply_verification(
        numeric_task,
        changed_files=[{"path": "src/records.py"}],
    )

    contract_evidence = evidence["public_callable_contract"]
    assert checks[1]["status"] == "failed"
    assert contract_evidence["callable"] == "list_records"
    assert contract_evidence["fixed_literal_contract"]["passed"] is False
    assert contract_evidence["fixed_literal_contract"][
        "required_zero_arg_callables"
    ] == ["count_ready_orders"]
    assert contract_evidence["runtime_probe"] is None
    assert len(calls) == 1


def test_restricted_numeric_probe_aggregates_exact_guard_defects(
    tmp_path: Path,
) -> None:
    docker = shutil.which("docker")
    if docker is None:
        pytest.skip("Docker is unavailable.")
    image = "scout-scout-api:latest"
    image_check = subprocess.run(
        [docker, "image", "inspect", image],
        capture_output=True,
        check=False,
        timeout=15,
        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
    )
    if image_check.returncode != 0:
        pytest.skip("The restricted backend image is unavailable.")
    site_packages = next(
        iter(sorted(Path(sys.prefix).resolve().glob("lib/python*/site-packages"))),
        None,
    )
    if site_packages is None:
        pytest.skip("The pinned verifier site-packages directory is unavailable.")

    target = tmp_path / "src" / "records.py"
    target.parent.mkdir()
    target.write_text(
        "\n".join(
            [
                "RECORDS = list(range(8))",
                "",
                "def list_records(offset=0, limit=None):",
                "    if offset < 0 or (",
                "        limit is not None",
                "        and (limit < 1 or not isinstance(limit, int))",
                "    ):",
                "        raise ValueError('invalid pagination')",
                "    if limit is None:",
                "        return RECORDS[offset:]",
                "    return RECORDS[offset:offset + limit]",
                "",
            ]
        ),
        encoding="utf-8",
    )
    contract = {
        "callable": "list_records",
        "parameters": [
            {"name": "offset", "minimum": 0},
            {"name": "limit", "minimum": 1},
        ],
    }

    passed, _summary, evidence = (
        long_running._run_generic_backend_public_numeric_contract_probe(
            root=tmp_path,
            target="src/records.py",
            contract=contract,
            docker=docker,
            site_packages=site_packages,
            image=image,
        )
    )

    assert passed is False
    violations = evidence["result"]["violations"]
    assert {item.get("parameter") for item in violations} == {
        "offset",
        "limit",
    }
    assert {
        (item.get("parameter"), item.get("case"), item.get("reason"))
        for item in violations
    }.issuperset(
        {
            ("offset", "integral_float", "wrong_invalid_exception"),
            ("offset", "fractional_float", "wrong_invalid_exception"),
            ("offset", "numeric_string", "wrong_invalid_exception"),
            ("offset", "bool_true", "invalid_value_accepted"),
            ("offset", "bool_false", "invalid_value_accepted"),
            ("limit", "numeric_string", "wrong_invalid_exception"),
            ("limit", "bool_true", "invalid_value_accepted"),
        }
    )

    target.write_text(
        "\n".join(
            [
                "import os",
                "",
                "def list_records(offset=0, limit=None):",
                "    os._exit(0)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    exited, _summary, exited_evidence = (
        long_running._run_generic_backend_public_numeric_contract_probe(
            root=tmp_path,
            target="src/records.py",
            contract=contract,
            docker=docker,
            site_packages=site_packages,
            image=image,
        )
    )

    assert exited is False
    assert exited_evidence["result"]["violations"] == [
        {"reason": "case_process_failed", "case": "default"}
    ]

    target.write_text(
        "\n".join(
            [
                "import json",
                "import os",
                "import sys",
                "",
                "_values = json.loads(sys.argv[3])",
                "_invalid = any(",
                "    type(value) is not int",
                "    or value < (1 if name == 'limit' else 0)",
                "    for name, value in _values.items()",
                ")",
                "os._exit(31 if _invalid else 30)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spoofed, _summary, spoofed_evidence = (
        long_running._run_generic_backend_public_numeric_contract_probe(
            root=tmp_path,
            target="src/records.py",
            contract=contract,
            docker=docker,
            site_packages=site_packages,
            image=image,
        )
    )

    assert spoofed is False
    assert spoofed_evidence["result"]["violations"] == [
        {"reason": "case_process_failed", "case": "default"}
    ]

    target.write_text(
        "\n".join(
            [
                "RECORDS = list(range(8))",
                "",
                "def _validate(value, minimum):",
                "    if type(value) is not int or value < minimum:",
                "        raise ValueError('invalid pagination')",
                "",
                "def list_records(offset=0, limit=None):",
                "    _validate(offset, 0)",
                "    if limit is not None:",
                "        _validate(limit, 1)",
                "    if offset > 0 and limit is not None:",
                "        raise ValueError('combined values rejected')",
                "    end = None if limit is None else offset + limit",
                "    return RECORDS[offset:end]",
                "",
            ]
        ),
        encoding="utf-8",
    )
    combined_failed, _summary, combined_evidence = (
        long_running._run_generic_backend_public_numeric_contract_probe(
            root=tmp_path,
            target="src/records.py",
            contract=contract,
            docker=docker,
            site_packages=site_packages,
            image=image,
        )
    )

    assert combined_failed is False
    assert {
        (item.get("case"), item.get("reason"))
        for item in combined_evidence["result"]["violations"]
    } == {
        ("all_minimums_plus_one", "valid_value_rejected"),
    }

    target.write_text(
        "\n".join(
            [
                "RECORDS = list(range(8))",
                "",
                "def _validate(value, minimum):",
                "    if type(value) is not int or value < minimum:",
                "        raise ValueError('invalid pagination')",
                "",
                "def list_records(offset=0, limit=None):",
                "    if limit is not None and offset != 0:",
                "        return RECORDS",
                "    _validate(offset, 0)",
                "    if limit is not None:",
                "        _validate(limit, 1)",
                "    end = None if limit is None else offset + limit",
                "    return RECORDS[offset:end]",
                "",
            ]
        ),
        encoding="utf-8",
    )
    combined_invalid, _summary, combined_invalid_evidence = (
        long_running._run_generic_backend_public_numeric_contract_probe(
            root=tmp_path,
            target="src/records.py",
            contract=contract,
            docker=docker,
            site_packages=site_packages,
            image=image,
        )
    )

    assert combined_invalid is False
    assert {
        (item.get("parameter"), item.get("case"), item.get("reason"))
        for item in combined_invalid_evidence["result"]["violations"]
    }.issuperset(
        {
            (
                "offset",
                "combined_below_minimum",
                "invalid_value_accepted",
            ),
            (
                "offset",
                "combined_fractional_float",
                "invalid_value_accepted",
            ),
        }
    )

    target.write_text(
        "\n".join(
            [
                "RECORDS = list(range(8))",
                "",
                "def _validate(value, minimum):",
                "    if type(value) is not int or value < minimum:",
                "        raise ValueError('invalid pagination')",
                "",
                "def list_records(offset=0, limit=None):",
                "    _validate(offset, 0)",
                "    if limit is not None:",
                "        _validate(limit, 1)",
                "    end = None if limit is None else offset + limit",
                "    return RECORDS[offset:end]",
                "",
            ]
        ),
        encoding="utf-8",
    )
    repaired, _summary, repaired_evidence = (
        long_running._run_generic_backend_public_numeric_contract_probe(
            root=tmp_path,
            target="src/records.py",
            contract=contract,
            docker=docker,
            site_packages=site_packages,
            image=image,
        )
    )

    assert repaired is True
    assert repaired_evidence["result"]["violations"] == []


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
