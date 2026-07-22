from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

from source_proxy.benchmarks import campaign_3_5_runner as campaign_runner
from source_proxy.benchmarks.campaign_3_5_runner import (
    _apply_scored_diff,
    _public_repair_artifacts,
    _run_visible_tests,
    _workspace_changed_paths,
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
    assert receipt["private_data_exposed"] is None
    assert receipt["hidden_answer_isolation"]["isolation_fully_proven"] is False
    assert receipt["runner_reason"] == "campaign_3_5_adapter_blocked:architect_llm_invalid_json"
    assert receipt["trace_claim_reconciliation"]["eligible_for_scored_trace_proof"] is False
    assert receipt["trace_claim_reconciliation"]["production_runtime_trace_observed"] is False
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
    assert len(private_files) >= 1
    assert all(path.read_text(encoding="utf-8") == raw_output for path in private_files)
    assert private_dir.stat().st_mode & 0o777 == 0o700
    assert all(path.stat().st_mode & 0o777 == stat.S_IRUSR | stat.S_IWUSR for path in private_files)
    assert raw_output not in json.dumps(stored)
    assert len(stored["raw_model_output"]["call_hashes"]) == len(private_files)
    assert {entry["phase"] for entry in stored["raw_model_output"]["call_hashes"]} == {"initial"}
    private_inputs = list((tmp_path / ".campaign-3-5-private-model-input").glob("*.txt"))
    assert receipt["model_input"]["captured_privately"] is True
    assert len(private_inputs) == len(private_files)
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
    assert any("exact current applied tree" in finding for finding in artifacts["diagnostics"]["findings"])
    assert artifacts["debugger"]["reproduction_command"] == "python -m pytest -q"
    assert any("No private oracle result" in finding for finding in artifacts["debugger"]["findings"])
    assert any("server-authorized path scope" in finding for finding in artifacts["reviewer"]["findings"])
    assert all(len(payload["content_sha256"]) == 64 for payload in artifacts.values())
    assert "http_range_contract_failed" not in json.dumps(artifacts)
    assert "endpoint now returns" not in json.dumps(artifacts)
    assert "raising it, not returning it" not in json.dumps(artifacts)


def _canonical_rich_provenance() -> dict[str, object]:
    return {
        "plugin_id": campaign_runner.GENERIC_WORKSPACE_PLUGIN_ID,
        "selected_prompt_id": campaign_runner.GENERIC_WORKSPACE_PROMPT_ID,
        "transport_kind": "canonical_litellm_router",
        "provider_call_authorized": True,
        "terminal_proof_eligible": True,
        "execution_path": campaign_runner.GENERIC_RICH_EXECUTION_PATH,
        "rich_path_proven": True,
        "calls": [
            {
                "stage": "coder",
                "completed": True,
                "raw_response_observed": True,
                "rendered_prompt_sha256": "a" * 64,
                "raw_response_sha256": "b" * 64,
            }
        ],
    }


def _prepared_patch_repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "runner@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Runner Test"], cwd=root, check=True)
    source = root / "src" / "value.py"
    source.parent.mkdir()
    source.write_text("VALUE = 1\n", encoding="utf-8")
    (root / "outside.py").write_text("OUTSIDE = 0\n", encoding="utf-8")
    subprocess.run(["git", "add", "src/value.py", "outside.py"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=root, check=True)
    source.write_text("VALUE = 2\n", encoding="utf-8")
    diff = subprocess.run(
        ["git", "diff", "--", "src/value.py"],
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    source.write_text("VALUE = 1\n", encoding="utf-8")
    return root, diff


def test_scored_apply_checks_then_gates_and_records_rich_attempt(tmp_path: Path, monkeypatch) -> None:
    root, diff = _prepared_patch_repo(tmp_path)
    gate_calls: list[tuple[str, str, str]] = []

    class Receipt:
        def as_payload(self) -> dict[str, object]:
            return {"central_gate_check_passed": True, "approval_token_id": "test-authority"}

    def gate(action: str, *, increment_id: str, run_id: str):
        gate_calls.append((action, increment_id, run_id))
        assert (root / "src" / "value.py").read_text(encoding="utf-8") == "VALUE = 1\n"
        return Receipt()

    monkeypatch.setattr(campaign_runner, "central_gate_check", gate)
    events: list[dict[str, object]] = []
    attempt, applied = _apply_scored_diff(
        diff=diff,
        provenance=_canonical_rich_provenance(),
        allowed_paths=("src/",),
        fixture_root=root,
        run_id="test-run",
        phase="initial",
        attempt_index=1,
        trace_events=events,
    )

    assert applied is True
    assert attempt["status"] == "applied"
    assert attempt["apply_check"]["passed"] is True
    assert attempt["changed_paths"] == ["src/value.py"]
    assert attempt["apply_authority"]["central_gate_check_passed"] is True
    assert gate_calls == [("apply", "campaign-3.5", "coding-run-test-run:initial:1")]
    assert (root / "src" / "value.py").read_text(encoding="utf-8") == "VALUE = 2\n"


def test_scored_apply_rejects_missing_rich_proof_before_gate(tmp_path: Path, monkeypatch) -> None:
    root, diff = _prepared_patch_repo(tmp_path)
    provenance = _canonical_rich_provenance()
    provenance["rich_path_proven"] = False
    gate_called = False

    def gate(*_args, **_kwargs):
        nonlocal gate_called
        gate_called = True
        raise AssertionError("gate must not be reached")

    monkeypatch.setattr(campaign_runner, "central_gate_check", gate)
    attempt, applied = _apply_scored_diff(
        diff=diff,
        provenance=provenance,
        allowed_paths=("src/",),
        fixture_root=root,
        run_id="test-run",
        phase="initial",
        attempt_index=1,
        trace_events=[],
    )

    assert applied is False
    assert attempt["reason_code"] == "campaign_3_5_rich_path_proof_missing"
    assert gate_called is False
    assert (root / "src" / "value.py").read_text(encoding="utf-8") == "VALUE = 1\n"


def test_scored_apply_rejects_path_escape_before_gate(tmp_path: Path, monkeypatch) -> None:
    root, _diff = _prepared_patch_repo(tmp_path)
    escaped = """diff --git a/../outside.py b/../outside.py
--- a/../outside.py
+++ b/../outside.py
@@ -0,0 +1 @@
+outside = True
"""
    monkeypatch.setattr(
        campaign_runner,
        "central_gate_check",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("gate must not be reached")),
    )
    attempt, applied = _apply_scored_diff(
        diff=escaped,
        provenance=_canonical_rich_provenance(),
        allowed_paths=("src/",),
        fixture_root=root,
        run_id="test-run",
        phase="repair",
        attempt_index=2,
        trace_events=[],
    )

    assert applied is False
    assert attempt["reason_code"] == "campaign_3_5_diff_path_unsafe"
    assert not (tmp_path / "outside.py").exists()


def test_scored_apply_rejects_unheaded_extra_patch_before_gate(tmp_path: Path, monkeypatch) -> None:
    root, allowed_diff = _prepared_patch_repo(tmp_path)
    mixed_diff = """--- a/outside.py
+++ b/outside.py
@@ -1 +1 @@
-OUTSIDE = 0
+OUTSIDE = 1
""" + allowed_diff
    monkeypatch.setattr(
        campaign_runner,
        "central_gate_check",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("gate must not be reached")),
    )
    attempt, applied = _apply_scored_diff(
        diff=mixed_diff,
        provenance=_canonical_rich_provenance(),
        allowed_paths=("src/",),
        fixture_root=root,
        run_id="test-run",
        phase="initial",
        attempt_index=1,
        trace_events=[],
    )

    assert applied is False
    assert attempt["reason_code"] == "campaign_3_5_diff_paths_invalid"
    assert (root / "src" / "value.py").read_text(encoding="utf-8") == "VALUE = 1\n"
    assert (root / "outside.py").read_text(encoding="utf-8") == "OUTSIDE = 0\n"


def test_scored_apply_tracks_created_files_as_workspace_changes(tmp_path: Path, monkeypatch) -> None:
    root, _diff = _prepared_patch_repo(tmp_path)
    created_diff = """diff --git a/src/new_value.py b/src/new_value.py
new file mode 100644
--- /dev/null
+++ b/src/new_value.py
@@ -0,0 +1 @@
+VALUE = 3
"""

    class Receipt:
        def as_payload(self) -> dict[str, object]:
            return {"central_gate_check_passed": True, "approval_token_id": "test-authority"}

    monkeypatch.setattr(campaign_runner, "central_gate_check", lambda *_args, **_kwargs: Receipt())
    attempt, applied = _apply_scored_diff(
        diff=created_diff,
        provenance=_canonical_rich_provenance(),
        allowed_paths=("src/",),
        fixture_root=root,
        run_id="test-run",
        phase="initial",
        attempt_index=1,
        trace_events=[],
    )

    assert applied is True
    assert attempt["changed_paths"] == ["src/new_value.py"]
    assert "src/new_value.py" in _workspace_changed_paths(root)


def test_visible_tests_cannot_read_host_environment_or_sibling_store(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fixture = tmp_path / "fixture"
    tests = fixture / "tests"
    tests.mkdir(parents=True)
    os.chmod(fixture, 0o700)
    sibling_secret = tmp_path / "private" / "oracle.json"
    sibling_secret.parent.mkdir()
    sibling_secret.write_text('{"hidden":"canary"}', encoding="utf-8")
    tests.joinpath("test_isolation.py").write_text(
        """import os
from pathlib import Path

def test_container_boundary():
    assert os.getenv('CAMPAIGN_HOST_SECRET') is None
    assert not Path(r'HOST_SECRET_PATH').exists()
""".replace("HOST_SECRET_PATH", str(sibling_secret)),
        encoding="utf-8",
    )
    monkeypatch.setenv("CAMPAIGN_HOST_SECRET", "must-not-enter-container")

    result = _run_visible_tests({"expected_tests": ["pytest passes"]}, fixture)

    if shutil.which("docker") is None:
        assert result["status"] == "environment_blocked"
    else:
        assert result["passed"] is True
        assert result["sandbox"]["private_store_mounted"] is False
        assert result["sandbox"]["network"] == "disabled"
