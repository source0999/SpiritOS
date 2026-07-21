"""Isolated, evidence-producing execution harness for Campaign 3.5.

This module is deliberately a harness, rather than an alternate coding path.
It materializes one disposable fixture, gives the production target adapter a
mode-0600 authority manifest, and applies only a canonical-router model diff
after the durable Campaign 3.5 apply check.  Private seeds and oracle profiles
are kept outside the fixture and are never written to the public receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Iterator
from uuid import uuid4

from source_proxy.approval.external_gate import central_gate_check
from source_proxy.benchmarks.campaign_3_5_assets.fixture_catalog import materialize_implemented_fixture
from source_proxy.benchmarks.campaign_3_5_assets.oracles import (
    PrivateOracleProfile,
    build_private_oracle_profiles,
    evaluate_profile,
)
from source_proxy.benchmarks.campaign_3_5_assets.seeding import (
    Campaign35RunSeed,
    derive_task_seed,
    generate_run_seed,
    task_seed_commitment,
)
from source_proxy.benchmarks.campaign_3_5_fixture_authority import ENV_MANIFEST
from source_proxy.benchmarks.campaign_3_5_private_store import create_private_store, write_private_task
from source_proxy.target_plugins.adapter import (
    GENERIC_WORKSPACE_CONTEXT_ID,
    GENERIC_WORKSPACE_PLUGIN_ID,
    GENERIC_WORKSPACE_PROFILE,
    GENERIC_WORKSPACE_PROMPT_ID,
    TARGET_PLUGIN_SCHEMA_VERSION,
    execute_target_plugin_command,
    resolve_target_plugin,
)


TASKS_PATH = Path(__file__).resolve().parents[2] / "benchmarks" / "coder-backend-100" / "v1.1" / "tasks.json"
RECEIPT_SCHEMA = "campaign-3.5-run-receipt/v1"


class Campaign35RunnerError(ValueError):
    """A harness precondition failed before a run could be scored."""


@dataclass(frozen=True)
class PreparedCampaign35Run:
    run_id: str
    task: dict[str, Any]
    fixture_root: Path
    private_store: Path
    manifest_path: Path
    seed_commitment: str
    fixture_content_sha256: str
    profile: PrivateOracleProfile


def load_campaign_tasks(path: Path = TASKS_PATH) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Campaign35RunnerError("campaign_3_5_tasks_unreadable") from error
    if not isinstance(payload, list) or not payload:
        raise Campaign35RunnerError("campaign_3_5_tasks_invalid")
    task_ids = [str(task.get("task_id") or "") for task in payload if isinstance(task, dict)]
    if len(task_ids) != len(payload) or len(set(task_ids)) != len(task_ids):
        raise Campaign35RunnerError("campaign_3_5_tasks_invalid")
    return payload


def prepare_campaign_3_5_run(
    task_id: str,
    *,
    run_root: Path | None = None,
    run_seed: Campaign35RunSeed | None = None,
) -> PreparedCampaign35Run:
    """Create a one-task fixture and its private authority/oracle boundary."""
    tasks = load_campaign_tasks()
    by_id = {str(task["task_id"]): task for task in tasks}
    task = by_id.get(task_id)
    if task is None:
        raise Campaign35RunnerError("campaign_3_5_task_unknown")
    seed = run_seed or generate_run_seed()
    base = Path(tempfile.mkdtemp(prefix="campaign-3-5-", dir=run_root)).resolve()
    os.chmod(base, 0o700)
    fixture_parent = base / "fixture"
    fixture_parent.mkdir(mode=0o700)
    private_store = create_private_store(base / "private")
    task_seed = derive_task_seed(seed, str(task["task_id"]), str(task["fixture"]))
    commitment = task_seed_commitment(task_seed)
    fixture = materialize_implemented_fixture(
        fixture_parent,
        task,
        task_seed=task_seed,
        task_seed_commitment=commitment,
    )
    profiles = build_private_oracle_profiles(tasks)
    profile = profiles[str(task["task_id"])]
    write_private_task(private_store, str(task["task_id"]), profile.private_payload())
    # The adapter accepts exactly this authority schema.  Do not pass builder
    # metadata (including seed commitment) through the production boundary.
    authority = {
        key: fixture.public_manifest[key]
        for key in (
            "schema_version",
            "fixture_id",
            "workspace_root",
            "baseline_tree_sha256",
            "allowed_paths",
            "execution_profile",
        )
    }
    manifest_path = base / "fixture-authority.json"
    manifest_path.write_text(json.dumps(authority, sort_keys=True), encoding="utf-8")
    os.chmod(manifest_path, 0o600)
    return PreparedCampaign35Run(
        run_id=f"campaign-3.5-{uuid4().hex}",
        task=task,
        fixture_root=fixture.fixture_root,
        private_store=private_store,
        manifest_path=manifest_path,
        seed_commitment=commitment,
        fixture_content_sha256=fixture.content_sha256,
        profile=profile,
    )


@contextmanager
def _fixture_authority(manifest_path: Path) -> Iterator[None]:
    old_value = os.environ.get(ENV_MANIFEST)
    os.environ[ENV_MANIFEST] = str(manifest_path)
    try:
        yield
    finally:
        if old_value is None:
            os.environ.pop(ENV_MANIFEST, None)
        else:
            os.environ[ENV_MANIFEST] = old_value


@contextmanager
def _temporary_environment(key: str, value: str) -> Iterator[None]:
    """Bind a process-local production setting without changing host state."""
    old_value = os.environ.get(key)
    os.environ[key] = value
    try:
        yield
    finally:
        if old_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = old_value


def _semantic_probe(task_id: str) -> Callable[[Path], tuple[bool, str]] | None:
    """Return a private runtime probe without exposing its implementation."""
    from source_proxy.benchmarks.campaign_3_5_assets.core_references import CORE_COMPLETED_TASKS, probe_core_reference
    from source_proxy.benchmarks.campaign_3_5_assets.go_runtime_validation import GO_RUNTIME_TASKS, probe_go_runtime
    from source_proxy.benchmarks.campaign_3_5_assets.java_runtime_validation import JAVA_RUNTIME_TASKS, probe_java_runtime
    from source_proxy.benchmarks.campaign_3_5_assets.python_runtime_references import PYTHON_RUNTIME_TASKS, probe_python_runtime
    from source_proxy.benchmarks.campaign_3_5_assets.rust_runtime_validation import RUST_RUNTIME_TASKS, probe_rust_runtime
    from source_proxy.benchmarks.campaign_3_5_assets.sql_runtime_validation import SQL_RUNTIME_TASKS, probe_sql_runtime
    from source_proxy.benchmarks.campaign_3_5_assets.typescript_runtime_validation import TYPESCRIPT_RUNTIME_TASKS, probe_typescript_runtime

    if task_id in PYTHON_RUNTIME_TASKS:
        return lambda root: probe_python_runtime(task_id, root)
    if task_id in TYPESCRIPT_RUNTIME_TASKS:
        return lambda root: probe_typescript_runtime(task_id, root)
    if task_id in GO_RUNTIME_TASKS:
        return lambda root: probe_go_runtime(task_id, root)
    if task_id in JAVA_RUNTIME_TASKS:
        return lambda root: probe_java_runtime(task_id, root)
    if task_id in RUST_RUNTIME_TASKS:
        return lambda root: probe_rust_runtime(task_id, root)
    if task_id in SQL_RUNTIME_TASKS:
        return lambda root: probe_sql_runtime(task_id, root)
    if task_id in CORE_COMPLETED_TASKS:
        return lambda root: probe_core_reference(task_id, root)
    return None


def _packet() -> dict[str, Any]:
    return {
        "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID,
        "target_plugin": {
            "schema_version": TARGET_PLUGIN_SCHEMA_VERSION,
            "id": GENERIC_WORKSPACE_PLUGIN_ID,
            "fixture_root": ".",
            "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID,
            "selected_context_id": GENERIC_WORKSPACE_CONTEXT_ID,
            "execution_profile": GENERIC_WORKSPACE_PROFILE,
        },
    }


def _receipt_path(evidence_dir: Path, run_id: str) -> Path:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    path = evidence_dir / f"{run_id}.json"
    if path.exists():
        raise Campaign35RunnerError("campaign_3_5_receipt_exists")
    return path


def _run_visible_tests(task: dict[str, Any], fixture_root: Path) -> dict[str, Any]:
    """Execute declared visible tests against the exact post-apply tree."""
    if "pytest passes" not in task.get("expected_tests", []):
        return {"status": "not_declared", "passed": True}
    started = datetime.now(UTC)
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=fixture_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": os.pathsep.join(filter(None, [str(fixture_root), os.environ.get("PYTHONPATH", "")])),
        },
    )
    return {
        "status": "completed",
        "passed": completed.returncode == 0,
        "command": "python -m pytest -q",
        "exit_code": completed.returncode,
        "started_at": started.isoformat(),
        "stdout_sha256": hashlib.sha256(completed.stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode("utf-8")).hexdigest(),
    }


def _stage_event(events: list[dict[str, Any]], name: str, **details: Any) -> None:
    events.append({"event": name, "at": datetime.now(UTC).isoformat(), **details})


class _PrivateModelOutputCapture:
    """Persist raw responses outside the fixture and public receipt boundary."""

    def __init__(self, evidence_dir: Path, run_id: str) -> None:
        self._root = evidence_dir / ".campaign-3-5-private-model-output"
        self._root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self._root, 0o700)
        self._run_id = run_id
        self.entries: list[dict[str, Any]] = []

    def __call__(self, call_record: dict[str, Any], raw_response: str) -> None:
        index = int(call_record["call_index"])
        path = self._root / f"{self._run_id}-call-{index}.txt"
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                output.write(raw_response)
        except BaseException:
            try:
                path.unlink(missing_ok=True)
            finally:
                raise
        os.chmod(path, 0o600)
        self.entries.append(
            {
                "call_index": index,
                "sha256": hashlib.sha256(raw_response.encode("utf-8")).hexdigest(),
            }
        )


def run_campaign_3_5_task(
    task_id: str,
    *,
    evidence_dir: Path,
    model_alias: str = "coder",
    run_root: Path | None = None,
    llm_call: Callable[[str, str], str] | None = None,
) -> dict[str, Any]:
    """Run one task through the production adapter and write a safe receipt.

    ``llm_call`` exists solely for hermetic adapter tests.  Its output is
    always noncanonical and can never be applied or recorded as a pass.
    """
    prepared = prepare_campaign_3_5_run(task_id, run_root=run_root)
    receipt_path = _receipt_path(evidence_dir, prepared.run_id)
    raw_output_capture = _PrivateModelOutputCapture(evidence_dir, prepared.run_id)
    adapter_result: dict[str, Any] = {}
    apply_receipt: dict[str, Any] | None = None
    runner_reason: str | None = None
    trace_events: list[dict[str, Any]] = []
    _stage_event(trace_events, "durable_task_created", task_id=task_id)
    try:
        # The production model client deliberately reads this established gate
        # setting.  Bind it locally so its own central check receives the
        # Campaign 3.5 authority, rather than the unrelated default increment.
        with _fixture_authority(prepared.manifest_path), _temporary_environment(
            "SOURCE_PROXY_GATE_INCREMENT", "campaign-3.5"
        ), _temporary_environment(
            "SOURCE_PROXY_DUMMY_PRODUCT_SITE_DIRECT_OLLAMA", "0"
        ):
            plugin = resolve_target_plugin(_packet(), prepared.fixture_root)
            _stage_event(trace_events, "planner_or_router_decision", plugin_id=plugin.plugin_id)
            adapter_result = execute_target_plugin_command(
                plugin,
                task=str(prepared.task["prompt"]),
                workspace_root=prepared.fixture_root,
                canonical_context={},
                canonical_context_text="",
                llm_call=llm_call,
                model_alias=model_alias,
                model_output_observer=raw_output_capture,
            )
            provenance = adapter_result.get("target_adapter_provenance", {})
            _stage_event(trace_events, "provider_model_called", call_count=provenance.get("call_count", 0))
            diff = str(adapter_result.get("proposed_diff") or "")
            adapter_reason = str(adapter_result.get("reason_code") or "").strip()
            if adapter_result.get("coder_blocked"):
                runner_reason = f"campaign_3_5_adapter_blocked:{adapter_reason or 'unspecified'}"
            elif diff and provenance.get("terminal_proof_eligible") is True:
                apply_receipt = central_gate_check(
                    "apply",
                    increment_id="campaign-3.5",
                    run_id=f"coding-run-{prepared.run_id}",
                ).as_payload()
                completed = subprocess.run(
                    ["git", "apply", "--recount", "-"],
                    input=diff,
                    text=True,
                    cwd=prepared.fixture_root,
                    capture_output=True,
                    check=False,
                    timeout=15,
                )
                if completed.returncode:
                    runner_reason = "PATCH_APPLICATION_ERROR"
                else:
                    _stage_event(trace_events, "patch_applied")
            elif diff:
                runner_reason = "campaign_3_5_noncanonical_diff_not_applied"
    except Exception as error:  # Preserve no model/provider/private content in receipts.
        runner_reason = f"campaign_3_5_execution_error:{type(error).__name__}"

    changed = subprocess.run(
        ["git", "-C", str(prepared.fixture_root), "diff", "--quiet", "HEAD"],
        check=False,
    ).returncode != 0
    tests = _run_visible_tests(prepared.task, prepared.fixture_root) if runner_reason is None and changed else {"status": "not_run", "passed": False}
    _stage_event(trace_events, "tests_completed", passed=tests["passed"])
    # One bounded repair pass lets the production coder inspect the exact
    # applied public tree after a visible-test failure.  It never receives a
    # private oracle result, expected answer, or hidden test name.
    if runner_reason is None and changed and not tests["passed"]:
        _stage_event(trace_events, "visible_test_repair_requested")
        try:
            with _fixture_authority(prepared.manifest_path), _temporary_environment(
                "SOURCE_PROXY_GATE_INCREMENT", "campaign-3.5"
            ), _temporary_environment(
                "SOURCE_PROXY_DUMMY_PRODUCT_SITE_DIRECT_OLLAMA", "0"
            ):
                plugin = resolve_target_plugin(_packet(), prepared.fixture_root)
                repair_task = (
                    str(prepared.task["prompt"])
                    + "\n\nA prior patch is already applied, but the declared visible tests still fail. "
                    + "Inspect the current repository context and return one scoped patch that makes the public task and visible tests pass. "
                    + "Do not rely on any hidden verification."
                )
                repair_result = execute_target_plugin_command(
                    plugin,
                    task=repair_task,
                    workspace_root=prepared.fixture_root,
                    canonical_context={},
                    canonical_context_text="",
                    llm_call=llm_call,
                    model_alias=model_alias,
                    model_output_observer=raw_output_capture,
                )
                repair_provenance = repair_result.get("target_adapter_provenance", {})
                repair_diff = str(repair_result.get("proposed_diff") or "")
                if repair_diff and repair_provenance.get("terminal_proof_eligible") is True:
                    completed = subprocess.run(
                        ["git", "apply", "--recount", "-"],
                        input=repair_diff,
                        text=True,
                        cwd=prepared.fixture_root,
                        capture_output=True,
                        check=False,
                        timeout=15,
                    )
                    if completed.returncode == 0:
                        adapter_result = repair_result
                        _stage_event(trace_events, "visible_test_repair_applied")
                        tests = _run_visible_tests(prepared.task, prepared.fixture_root)
                        _stage_event(trace_events, "tests_completed", passed=tests["passed"], retry=True)
                    else:
                        _stage_event(trace_events, "visible_test_repair_rejected", reason="PATCH_APPLICATION_ERROR")
                else:
                    _stage_event(trace_events, "visible_test_repair_rejected", reason=str(repair_result.get("reason_code") or "MODEL_OUTPUT_NOT_APPLICABLE"))
        except Exception as error:  # A failed repair transport preserves the original test failure.
            _stage_event(trace_events, "visible_test_repair_rejected", reason=f"repair_execution_error:{type(error).__name__}")
    candidate_disposition = "COMPLETED_VERIFIED" if runner_reason is None and changed and tests["passed"] else "BLOCKED_OR_DEGRADED_TRUTHFULLY"
    try:
        _stage_event(trace_events, "oracle_started")
        oracle = evaluate_profile(
            prepared.profile,
            fixture_root=prepared.fixture_root,
            allowed_paths=["src/", "tests/", "migrations/", "config/", "docs/", "pyproject.toml"],
            final_disposition=candidate_disposition,
            semantic_probe=_semantic_probe(str(prepared.task["task_id"])) if changed else None,
        )
        _stage_event(trace_events, "oracle_completed", passed=oracle["passed"])
    except Exception as error:  # An oracle crash is a failed benchmark result, never a lost receipt.
        runner_reason = runner_reason or "ORACLE_EXECUTION_ERROR"
        oracle = {
            "schema_version": "campaign-3.5-oracle-result/v1",
            "task_id": prepared.task["task_id"],
            "passed": False,
            "checks": {"oracle_execution": False},
            "changed_path_count": -1,
            "semantic_category": f"oracle_execution_error:{type(error).__name__}",
            "result_commitment": hashlib.sha256(type(error).__name__.encode("utf-8")).hexdigest(),
        }
        _stage_event(trace_events, "oracle_completed", passed=False, failure="ORACLE_EXECUTION_ERROR")
    reviewer = {"identity": "deterministic-scope-reviewer/v1", "passed": bool(changed and oracle["checks"].get("scope") is True)}
    _stage_event(trace_events, "reviewer_completed", passed=reviewer["passed"])
    verifier = {"identity": "deterministic-evidence-verifier/v1", "passed": bool(tests["passed"] and oracle["passed"] and reviewer["passed"])}
    _stage_event(trace_events, "verifier_completed", passed=verifier["passed"])
    if runner_reason is None and not tests["passed"]:
        runner_reason = "VISIBLE_TESTS_FAILED"
    if runner_reason is None and not oracle["passed"]:
        runner_reason = "SEMANTIC_VERIFICATION_FAILED"
    if runner_reason is None and not reviewer["passed"]:
        runner_reason = "REVIEWER_REJECTED"
    if runner_reason is None and not verifier["passed"]:
        runner_reason = "VERIFIER_REJECTED"
    disposition = "COMPLETED_VERIFIED" if runner_reason is None else "BLOCKED_OR_DEGRADED_TRUTHFULLY"
    provenance = adapter_result.get("target_adapter_provenance", {})
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "run_id": prepared.run_id,
        "recorded_at": datetime.now(UTC).isoformat(),
        "task_id": prepared.task["task_id"],
        "fixture_id": prepared.task["fixture"],
        "seed_commitment": prepared.seed_commitment,
        "fixture_content_sha256": prepared.fixture_content_sha256,
        "fixture_authority_sha256": hashlib.sha256(prepared.manifest_path.read_bytes()).hexdigest(),
        "model_alias": model_alias,
        "adapter": {
            key: provenance.get(key)
            for key in ("transport_kind", "provider_call_made", "provider_call_authorized", "trust_status", "terminal_proof_eligible", "call_count", "provider", "model")
        } | {"model_response_format": adapter_result.get("coder_diagnostics", {}).get("model_response_format")},
        "raw_model_output": {
            "captured_privately": bool(raw_output_capture.entries),
            "call_hashes": raw_output_capture.entries,
            "public_receipt_contains_raw_text": False,
        },
        "apply_authority": apply_receipt,
        "runner_reason": runner_reason,
        "final_disposition": disposition,
        "visible_tests": tests,
        "oracle": oracle,
        "reviewer": reviewer,
        "verifier": verifier,
        "trace_events": trace_events,
        "benchmark_passed": bool(disposition == "COMPLETED_VERIFIED" and provenance.get("terminal_proof_eligible") is True),
        "private_data_exposed": False,
    }
    try:
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.chmod(receipt_path, 0o600)
    finally:
        shutil.rmtree(prepared.fixture_root.parent.parent)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one isolated Campaign 3.5 benchmark task.")
    parser.add_argument("task_id")
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--model-alias", choices=("coder", "local"), default="coder")
    args = parser.parse_args()
    receipt = run_campaign_3_5_task(args.task_id, evidence_dir=args.evidence_dir, model_alias=args.model_alias)
    print(json.dumps({"run_id": receipt["run_id"], "benchmark_passed": receipt["benchmark_passed"], "runner_reason": receipt["runner_reason"]}, sort_keys=True))
    return 0 if receipt["benchmark_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
