from __future__ import annotations

import json
import shutil
import stat
from pathlib import Path

from source_proxy.benchmarks.campaign_3_5_runner import (
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
