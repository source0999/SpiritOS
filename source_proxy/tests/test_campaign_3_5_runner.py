from __future__ import annotations

import json
import shutil
import stat
from pathlib import Path

from source_proxy.benchmarks.campaign_3_5_runner import (
    _public_repair_artifacts,
    prepare_campaign_3_5_run,
    run_campaign_3_5_task,
)


def test_prepared_run_keeps_private_profile_outside_fixture() -> None:
    prepared = prepare_campaign_3_5_run("S01")
    try:
        assert prepared.fixture_root.is_dir()
        assert prepared.private_store.is_dir()
        assert prepared.private_store not in prepared.fixture_root.parents
        assert prepared.manifest_path.stat().st_mode & 0o777 == 0o600
        assert prepared.private_store.stat().st_mode & 0o777 == 0o700
        assert not list(prepared.fixture_root.rglob("*oracle*"))
        assert not list(prepared.fixture_root.rglob("*private*"))
    finally:
        shutil.rmtree(prepared.fixture_root.parent.parent)


def test_injected_or_malformed_output_can_never_pass(tmp_path: Path) -> None:
    receipt = run_campaign_3_5_task(
        "S01",
        evidence_dir=tmp_path,
        llm_call=lambda _prompt, _alias: "not a diff",
    )

    assert receipt["benchmark_passed"] is False
    assert receipt["private_data_exposed"] is False
    assert receipt["runner_reason"] == "campaign_3_5_adapter_blocked:generic_workspace_model_diff_invalid"
    stored = json.loads(next(tmp_path.glob("*.json")).read_text(encoding="utf-8"))
    assert stored["oracle"]["task_id"] == "S01"
    assert "expected_artifacts" not in json.dumps(stored)


def test_raw_model_output_is_private_but_its_hash_is_receipted(tmp_path: Path) -> None:
    raw_output = "not a diff; this must not be placed in the public receipt"
    receipt = run_campaign_3_5_task(
        "S01",
        evidence_dir=tmp_path,
        llm_call=lambda _prompt, _alias: raw_output,
    )

    stored = json.loads(next(tmp_path.glob("*.json")).read_text(encoding="utf-8"))
    private_dir = tmp_path / ".campaign-3-5-private-model-output"
    private_files = list(private_dir.glob("*.txt"))
    assert receipt["raw_model_output"]["captured_privately"] is True
    assert len(private_files) == 3
    assert all(path.read_text(encoding="utf-8") == raw_output for path in private_files)
    assert private_dir.stat().st_mode & 0o777 == 0o700
    assert all(path.stat().st_mode & 0o777 == stat.S_IRUSR | stat.S_IWUSR for path in private_files)
    assert raw_output not in json.dumps(stored)
    assert len(stored["raw_model_output"]["call_hashes"]) == 3
    private_inputs = list((tmp_path / ".campaign-3-5-private-model-input").glob("*.txt"))
    assert receipt["model_input"]["captured_privately"] is True
    assert len(private_inputs) == 3
    assert all(path.stat().st_mode & 0o777 == stat.S_IRUSR | stat.S_IWUSR for path in private_inputs)
    assert "Repository context" not in json.dumps(stored)


def test_public_repair_artifacts_bind_visible_failure_to_each_lane() -> None:
    prepared = prepare_campaign_3_5_run("S01")
    try:
        source_path = prepared.fixture_root / "src" / "api" / "items.py"
        source_path.write_text(
            source_path.read_text(encoding="utf-8") + "\nHTTPException(status_code=422)\n",
            encoding="utf-8",
        )
        artifacts = _public_repair_artifacts(
            prepared.task,
            prepared.fixture_root,
            {
                "command": "python -m pytest -q",
                "exit_code": 1,
                "stdout_excerpt": "FAILED tests/test_items.py::test_limit - NameError: HTTPException\nAssertionError: assert 20 >= 100",
                "stderr_excerpt": "",
            },
        )
    finally:
        shutil.rmtree(prepared.fixture_root.parent.parent)

    assert set(artifacts) == {"planner", "architect", "diagnostics", "debugger", "reviewer", "verifier"}
    assert "NameError" in artifacts["diagnostics"]["test_output"]
    assert any("undefined" in finding for finding in artifacts["diagnostics"]["findings"])
    assert any("raising" in finding for finding in artifacts["diagnostics"]["findings"])
    assert artifacts["debugger"]["reproduction_command"] == "python -m pytest -q"
    assert any("endpoint now returns" in finding for finding in artifacts["debugger"]["findings"])
    assert any("without importing it" in finding for finding in artifacts["reviewer"]["findings"])
    assert all(len(payload["content_sha256"]) == 64 for payload in artifacts.values())
    assert "http_range_contract_failed" not in json.dumps(artifacts)
