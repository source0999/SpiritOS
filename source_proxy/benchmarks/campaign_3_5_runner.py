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
import re
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
from source_proxy.diagnostics.status_codes import classify_repair_failure
from source_proxy.safety.paths import normalize_repo_path_candidate, unsafe_target_finding
from source_proxy.target_plugins.adapter import (
    GENERIC_WORKSPACE_CONTEXT_ID,
    GENERIC_WORKSPACE_PLUGIN_ID,
    GENERIC_WORKSPACE_PROFILE,
    GENERIC_WORKSPACE_PROMPT_ID,
    GENERIC_RICH_EXECUTION_PATH,
    TARGET_PLUGIN_SCHEMA_VERSION,
    execute_target_plugin_command,
    resolve_target_plugin,
)
from source_proxy.verification.diff import DiffVerificationError, git_diff_changed_paths


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
        return {
            "status": "unsupported_declared_test_profile",
            "passed": False,
            "reason_code": "server_owned_test_command_unresolved",
            "failure_classification": _repair_failure_payload(
                "server_owned_test_command_unresolved",
                stage="tests",
            ),
        }
    docker = shutil.which("docker")
    virtualenv_root = Path(sys.prefix).resolve()
    site_packages = next(
        iter(sorted(virtualenv_root.glob("lib/python*/site-packages"))),
        None,
    )
    if docker is None or site_packages is None or not site_packages.is_dir():
        return {
            "status": "environment_blocked",
            "passed": False,
            "reason_code": "sandbox_runtime_unavailable",
            "failure_classification": _repair_failure_payload(
                "sandbox_runtime_unavailable",
                stage="tests",
            ),
        }
    container_name = f"campaign35-tests-{uuid4().hex}"
    sandbox_image = os.getenv(
        "SOURCE_PROXY_CAMPAIGN_3_5_SANDBOX_IMAGE",
        "scout-scout-api:latest",
    ).strip()
    command = [
        docker,
        "run",
        "--rm",
        "--name",
        container_name,
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges=true",
        "--pids-limit",
        "128",
        "--memory",
        "1g",
        "--cpus",
        "2",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,noexec,size=128m",
        "--mount",
        f"type=bind,src={fixture_root},dst=/workspace,readonly",
        "--mount",
        f"type=bind,src={site_packages},dst=/host-site,readonly",
        "--workdir",
        "/workspace",
        "--env",
        "HOME=/tmp",
        "--env",
        "PYTHONDONTWRITEBYTECODE=1",
        "--env",
        "PYTHONPATH=/workspace:/host-site",
        "--env",
        "PYTEST_ADDOPTS=-p no:cacheprovider",
        "--env",
        "LANG=C.UTF-8",
        "--entrypoint",
        "python",
        sandbox_image,
        "-m",
        "pytest",
        "-q",
    ]
    started = datetime.now(UTC)
    try:
        completed = subprocess.run(
            command,
            cwd=fixture_root,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
        )
    except subprocess.TimeoutExpired as error:
        subprocess.run(
            [docker, "rm", "-f", container_name],
            capture_output=True,
            check=False,
            timeout=15,
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
        )
        return {
            "status": "timed_out",
            "passed": False,
            "command": "sandboxed python -m pytest -q",
            "started_at": started.isoformat(),
            "reason_code": "visible_tests_timeout",
            "stdout_sha256": hashlib.sha256(str(error.stdout or "").encode("utf-8")).hexdigest(),
            "stderr_sha256": hashlib.sha256(str(error.stderr or "").encode("utf-8")).hexdigest(),
            "failure_classification": _repair_failure_payload(
                "visible_tests_timeout",
                stage="tests",
            ),
            "sandbox": {
                "runtime": "restricted_container",
                "image": sandbox_image,
                "filesystem": "fixture_and_python_dependencies_read_only_only",
                "network": "disabled",
                "environment": "strict_allowlist",
            },
        }
    except OSError as error:
        return {
            "status": "environment_blocked",
            "passed": False,
            "reason_code": f"sandbox_execution_error:{type(error).__name__}",
            "failure_classification": _repair_failure_payload(
                "sandbox_execution_error",
                stage="tests",
            ),
        }
    return {
        "status": "completed",
        "passed": completed.returncode == 0,
        "command": "sandboxed python -m pytest -q",
        "exit_code": completed.returncode,
        "started_at": started.isoformat(),
        "stdout_sha256": hashlib.sha256(completed.stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode("utf-8")).hexdigest(),
        # Keep the evidence alongside the 9k-character source context within
        # the smallest supported local coder context window.
        "stdout_excerpt": completed.stdout[-2500:],
        "stderr_excerpt": completed.stderr[-1000:],
        "stdout_truncated": len(completed.stdout) > 2500,
        "stderr_truncated": len(completed.stderr) > 1000,
        "sandbox": {
            "runtime": "restricted_container",
            "image": sandbox_image,
            "filesystem": "fixture_and_python_dependencies_read_only_only",
            "network": "disabled",
            "environment": "strict_allowlist",
            "private_store_mounted": False,
            "evidence_store_mounted": False,
        },
    }


def _workspace_changed_paths(fixture_root: Path) -> list[str]:
    completed = subprocess.run(
        [
            "git",
            "ls-files",
            "--modified",
            "--deleted",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        cwd=fixture_root,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise Campaign35RunnerError("campaign_3_5_workspace_status_unavailable")
    return sorted(
        {
            raw.decode("utf-8")
            for raw in completed.stdout.split(b"\0")
            if raw
        }
    )


def _stage_event(events: list[dict[str, Any]], name: str, **details: Any) -> None:
    events.append({"event": name, "at": datetime.now(UTC).isoformat(), **details})


def _repair_failure_payload(reason_code: str, *, stage: str, reason: str = "") -> dict[str, Any]:
    return classify_repair_failure(
        diagnostic_code=reason_code,
        stage=stage,
        reason=reason or reason_code,
        details={"diagnostic_code": reason_code, "stage": stage},
    ).to_dict()


def _rich_provenance_problem(provenance: dict[str, Any]) -> str | None:
    """Return the first fail-closed scored-path provenance defect."""

    if provenance.get("terminal_proof_eligible") is not True:
        return "campaign_3_5_terminal_proof_ineligible"
    if provenance.get("plugin_id") != GENERIC_WORKSPACE_PLUGIN_ID:
        return "campaign_3_5_target_plugin_provenance_mismatch"
    if provenance.get("selected_prompt_id") != GENERIC_WORKSPACE_PROMPT_ID:
        return "campaign_3_5_prompt_provenance_mismatch"
    if provenance.get("transport_kind") != "canonical_litellm_router":
        return "campaign_3_5_transport_provenance_mismatch"
    if provenance.get("provider_call_authorized") is not True:
        return "campaign_3_5_model_call_authority_missing"
    if provenance.get("execution_path") != GENERIC_RICH_EXECUTION_PATH:
        return "campaign_3_5_rich_execution_path_missing"
    if provenance.get("rich_path_proven") is not True:
        return "campaign_3_5_rich_path_proof_missing"
    calls = provenance.get("calls")
    if not isinstance(calls, list):
        return "campaign_3_5_model_call_trace_missing"
    coder_calls = [
        call
        for call in calls
        if isinstance(call, dict)
        and call.get("stage") == "coder"
        and call.get("completed") is True
        and call.get("raw_response_observed") is True
        and re.fullmatch(r"[0-9a-f]{64}", str(call.get("rendered_prompt_sha256") or ""))
        and re.fullmatch(r"[0-9a-f]{64}", str(call.get("raw_response_sha256") or ""))
    ]
    if not coder_calls:
        return "campaign_3_5_coder_stage_trace_missing"
    return None


def _scored_diff_paths(diff: str, *, workspace_root: Path, allowed_paths: tuple[str, ...]) -> list[str]:
    """Extract same-path git diff targets and enforce server-owned scope."""

    try:
        diff_paths = git_diff_changed_paths(diff, workspace_root=workspace_root)
    except DiffVerificationError as error:
        raise Campaign35RunnerError("campaign_3_5_diff_paths_invalid") from error
    normalized_allowed = tuple(
        normalize_repo_path_candidate(value).rstrip("/") for value in allowed_paths
    )
    normalized_allowed = tuple(value for value in normalized_allowed if value)
    if not normalized_allowed:
        raise Campaign35RunnerError("campaign_3_5_allowed_scope_missing")
    changed_paths: list[str] = []
    for path in diff_paths:
        normalized = normalize_repo_path_candidate(path)
        if normalized != path or unsafe_target_finding(normalized, workspace_root=workspace_root):
            raise Campaign35RunnerError("campaign_3_5_diff_path_unsafe")
        if not any(
            normalized == allowed or normalized.startswith(allowed + "/")
            for allowed in normalized_allowed
        ):
            raise Campaign35RunnerError("campaign_3_5_diff_scope_violation")
        candidate = workspace_root.resolve()
        for part in Path(normalized).parts:
            candidate = candidate / part
            if candidate.is_symlink():
                raise Campaign35RunnerError("campaign_3_5_diff_path_unsafe")
        try:
            resolved_relative = candidate.resolve().relative_to(
                workspace_root.resolve()
            ).as_posix()
        except ValueError as error:
            raise Campaign35RunnerError("campaign_3_5_diff_path_unsafe") from error
        if not any(
            resolved_relative == allowed
            or resolved_relative.startswith(allowed + "/")
            for allowed in normalized_allowed
        ):
            raise Campaign35RunnerError("campaign_3_5_diff_scope_violation")
        changed_paths.append(normalized)
    return sorted(set(changed_paths))


def _apply_scored_diff(
    *,
    diff: str,
    provenance: dict[str, Any],
    allowed_paths: tuple[str, ...],
    fixture_root: Path,
    run_id: str,
    phase: str,
    attempt_index: int,
    trace_events: list[dict[str, Any]],
) -> tuple[dict[str, Any], bool]:
    """Validate, authorize, and apply one rich-path diff with durable evidence."""

    safe_model_calls = [
        {
            key: call.get(key)
            for key in (
                "call_index",
                "stage",
                "model_alias",
                "provider",
                "model",
                "rendered_prompt_sha256",
                "raw_response_sha256",
                "completed",
                "raw_response_observed",
                "rendered_prompt_captured",
                "raw_response_captured",
                "model_call_authority",
            )
        }
        for call in provenance.get("calls", [])
        if isinstance(call, dict)
    ]
    attempt: dict[str, Any] = {
        "attempt_index": attempt_index,
        "phase": phase,
        "execution_path": provenance.get("execution_path"),
        "rich_path_proven": provenance.get("rich_path_proven") is True,
        "terminal_proof_eligible": provenance.get("terminal_proof_eligible") is True,
        "diff_sha256": hashlib.sha256(diff.encode("utf-8", errors="replace")).hexdigest(),
        "changed_paths": [],
        "model_calls": safe_model_calls,
        "model_provenance_sha256": hashlib.sha256(
            json.dumps(safe_model_calls, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "apply_check": {"passed": False},
        "apply_authority": None,
        "status": "rejected",
        "reason_code": None,
        "failure_classification": None,
    }

    def reject(reason_code: str, *, reason: str = "") -> tuple[dict[str, Any], bool]:
        attempt["reason_code"] = reason_code
        attempt["failure_classification"] = _repair_failure_payload(
            reason_code,
            stage="apply",
            reason=reason,
        )
        _stage_event(
            trace_events,
            "scored_apply_attempt",
            phase=phase,
            attempt_index=attempt_index,
            status="rejected",
            reason_code=reason_code,
            failure_kind=attempt["failure_classification"]["failure_kind"],
        )
        return attempt, False

    if not diff.strip():
        return reject("campaign_3_5_diff_missing")
    provenance_problem = _rich_provenance_problem(provenance)
    if provenance_problem:
        return reject(provenance_problem)
    try:
        attempt["changed_paths"] = _scored_diff_paths(
            diff,
            workspace_root=fixture_root,
            allowed_paths=allowed_paths,
        )
    except Campaign35RunnerError as error:
        return reject(str(error))

    checked = subprocess.run(
        ["git", "apply", "--check", "--recount", "-"],
        input=diff,
        text=True,
        cwd=fixture_root,
        capture_output=True,
        check=False,
        timeout=15,
    )
    attempt["apply_check"] = {
        "passed": checked.returncode == 0,
        "exit_code": checked.returncode,
        "stdout_sha256": hashlib.sha256(checked.stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(checked.stderr.encode("utf-8")).hexdigest(),
    }
    if checked.returncode:
        return reject("campaign_3_5_diff_apply_check_failed")

    try:
        authority = central_gate_check(
            "apply",
            increment_id="campaign-3.5",
            run_id=f"coding-run-{run_id}:{phase}:{attempt_index}",
        ).as_payload()
    except Exception as error:  # Preserve only structured authority/type evidence.
        reason_code = str(getattr(error, "reason_code", "campaign_3_5_apply_authority_denied"))
        return reject(reason_code, reason=type(error).__name__)
    attempt["apply_authority"] = authority

    completed = subprocess.run(
        ["git", "apply", "--recount", "-"],
        input=diff,
        text=True,
        cwd=fixture_root,
        capture_output=True,
        check=False,
        timeout=15,
    )
    if completed.returncode:
        return reject("campaign_3_5_patch_application_error")
    attempt.update({"status": "applied", "reason_code": None, "failure_classification": None})
    _stage_event(
        trace_events,
        "scored_apply_attempt",
        phase=phase,
        attempt_index=attempt_index,
        status="applied",
        changed_paths=attempt["changed_paths"],
        apply_authority_checked=True,
    )
    return attempt, True


def _public_repair_artifacts(task: dict[str, Any], fixture_root: Path, tests: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Create durable, public-evidence lane outputs for one repair pass.

    The oracle remains private. These artifacts contain only the public task,
    current changed paths, and visible-test output from this exact fixture.
    """
    changed = _workspace_changed_paths(fixture_root)
    current_state = _workspace_state_manifest(fixture_root)
    test_output = str(tests.get("stdout_excerpt") or "") + str(tests.get("stderr_excerpt") or "")
    diagnostics: list[str] = [
        "The declared visible test command exited nonzero on the exact current applied tree.",
        "Use the captured public output and current repository bytes to identify the cause.",
    ]
    debugger_findings = [
        "Reproduced the failure with the declared public test command on the current applied tree.",
        "No private oracle result, expected answer, or hidden test identifier is included.",
    ]
    reviewer_findings = [
        "Visible tests are failing; review the current diff against the public task and repository conventions.",
        "Keep any repair within the server-authorized path scope.",
    ]
    planner = {
        "identity": "campaign-3.5-public-planner/v1",
        "task": task["prompt"],
        "source_context": "current applied fixture workspace",
        "public_test_command": "python -m pytest -q",
    }
    architect = {
        "identity": "campaign-3.5-scope-architect/v1",
        "changed_paths": changed,
        "current_workspace_state": current_state,
        "allowed_paths": ["src/", "tests/", "migrations/", "config/", "docs/", "pyproject.toml"],
    }
    reviewer = {
        "identity": "campaign-3.5-visible-test-reviewer/v1",
        "finding": " ".join(reviewer_findings),
        "findings": reviewer_findings,
        "changed_paths": changed,
    }
    verifier = {"identity": "campaign-3.5-private-verifier-boundary/v1", "finding": "Independent verification has not approved the applied tree. Re-evaluate the public contract; no private oracle detail is disclosed."}
    diagnostics_payload = {"identity": "campaign-3.5-visible-test-diagnostics/v1", "findings": diagnostics, "test_output": test_output}
    debugger = {
        "identity": "campaign-3.5-visible-test-debugger/v1",
        "reproduction_command": tests.get("command"),
        "exit_code": tests.get("exit_code"),
        "findings": debugger_findings,
        "test_output": test_output,
    }
    artifacts = {"planner": planner, "architect": architect, "diagnostics": diagnostics_payload, "debugger": debugger, "reviewer": reviewer, "verifier": verifier}
    for payload in artifacts.values():
        payload["content_sha256"] = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return artifacts


class _PrivateModelInputCapture:
    """Persist exact rendered prompts outside receipts for a bounded audit."""

    def __init__(self, evidence_dir: Path, run_id: str, phase: str) -> None:
        self._root = evidence_dir / ".campaign-3-5-private-model-input"
        self._root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self._root, 0o700)
        self._run_id = run_id
        self._phase = phase
        self.entries: list[dict[str, Any]] = []

    def __call__(self, call_record: dict[str, Any], rendered_prompt: str) -> None:
        provider_call_index = int(call_record["call_index"])
        capture_index = len(self.entries) + 1
        path = self._root / f"{self._run_id}-{self._phase}-prompt-{capture_index}-provider-call-{provider_call_index}.txt"
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                output.write(rendered_prompt)
        except BaseException:
            try:
                path.unlink(missing_ok=True)
            finally:
                raise
        os.chmod(path, 0o600)
        self.entries.append(
            {
                "phase": self._phase,
                "capture_index": capture_index,
                "provider_call_index": provider_call_index,
                "sha256": hashlib.sha256(rendered_prompt.encode("utf-8")).hexdigest(),
            }
        )


class _PrivateModelOutputCapture:
    """Persist raw responses outside the fixture and public receipt boundary."""

    def __init__(self, evidence_dir: Path, run_id: str, phase: str) -> None:
        self._root = evidence_dir / ".campaign-3-5-private-model-output"
        self._root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self._root, 0o700)
        self._run_id = run_id
        self._phase = phase
        self.entries: list[dict[str, Any]] = []

    def __call__(self, call_record: dict[str, Any], raw_response: str) -> None:
        provider_call_index = int(call_record["call_index"])
        capture_index = len(self.entries) + 1
        path = self._root / f"{self._run_id}-{self._phase}-response-{capture_index}-provider-call-{provider_call_index}.txt"
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
                "phase": self._phase,
                "capture_index": capture_index,
                "provider_call_index": provider_call_index,
                "sha256": hashlib.sha256(raw_response.encode("utf-8")).hexdigest(),
            }
        )


def _workspace_state_manifest(fixture_root: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for relative_path in _workspace_changed_paths(fixture_root):
        candidate = fixture_root / relative_path
        if candidate.is_file() and not candidate.is_symlink():
            entries.append(
                {
                    "path": relative_path,
                    "state": "present",
                    "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
                }
            )
        else:
            entries.append({"path": relative_path, "state": "deleted_or_nonregular", "sha256": None})
    return {
        "changed_files": entries,
        "state_sha256": hashlib.sha256(
            json.dumps(entries, sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }


def _adapter_attempt_record(
    result: dict[str, Any],
    *,
    phase: str,
    attempt_index: int,
    fixture_root: Path,
) -> dict[str, Any]:
    provenance = result.get("target_adapter_provenance", {})
    diagnostics = result.get("coder_diagnostics", {})
    calls = [
        {
            key: call.get(key)
            for key in (
                "call_index",
                "stage",
                "model_alias",
                "provider",
                "model",
                "rendered_prompt_sha256",
                "raw_response_sha256",
                "completed",
                "raw_response_observed",
                "rendered_prompt_captured",
                "raw_response_captured",
                "error_type",
                "model_call_authority",
            )
        }
        for call in provenance.get("calls", [])
        if isinstance(call, dict)
    ]
    reason_code = str(result.get("reason_code") or "").strip() or None
    failure = diagnostics.get("failure_classification")
    if not isinstance(failure, dict) and (result.get("coder_blocked") or reason_code):
        failure = _repair_failure_payload(
            reason_code or "campaign_3_5_adapter_blocked",
            stage=str(diagnostics.get("failure_stage") or "coder"),
        )
    diff = str(result.get("proposed_diff") or "")
    return {
        "attempt_index": attempt_index,
        "phase": phase,
        "blocked": bool(result.get("coder_blocked")),
        "reason_code": reason_code,
        "failure_classification": failure if isinstance(failure, dict) else None,
        "execution_path": provenance.get("execution_path"),
        "rich_path_proven": provenance.get("rich_path_proven") is True,
        "terminal_proof_eligible": provenance.get("terminal_proof_eligible") is True,
        "transport_kind": provenance.get("transport_kind"),
        "provider_call_authorized": provenance.get("provider_call_authorized") is True,
        "proposed_diff_present": bool(diff.strip()),
        "proposed_diff_sha256": hashlib.sha256(diff.encode("utf-8")).hexdigest(),
        "model_calls": calls,
        "model_provenance_sha256": hashlib.sha256(
            json.dumps(calls, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "current_workspace_state": _workspace_state_manifest(fixture_root),
    }


def _model_evidence_complete(
    adapter_attempts: list[dict[str, Any]],
    *,
    input_entries: list[dict[str, Any]],
    output_entries: list[dict[str, Any]],
) -> bool:
    calls = [
        (str(attempt.get("phase") or ""), call)
        for attempt in adapter_attempts
        for call in attempt.get("model_calls", [])
        if isinstance(call, dict)
    ]
    expected_inputs = {
        (phase, int(call["call_index"]))
        for phase, call in calls
        if call.get("call_index") is not None
    }
    expected_outputs = {
        (phase, int(call["call_index"]))
        for phase, call in calls
        if call.get("call_index") is not None
        and call.get("raw_response_observed") is True
    }
    captured_inputs = {
        (str(entry.get("phase") or ""), int(entry["provider_call_index"]))
        for entry in input_entries
    }
    captured_outputs = {
        (str(entry.get("phase") or ""), int(entry["provider_call_index"]))
        for entry in output_entries
    }
    return bool(calls) and expected_inputs == captured_inputs and expected_outputs == captured_outputs


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
    initial_input_capture = _PrivateModelInputCapture(evidence_dir, prepared.run_id, "initial")
    repair_input_capture = _PrivateModelInputCapture(evidence_dir, prepared.run_id, "repair")
    initial_output_capture = _PrivateModelOutputCapture(evidence_dir, prepared.run_id, "initial")
    repair_output_capture = _PrivateModelOutputCapture(evidence_dir, prepared.run_id, "repair")
    adapter_result: dict[str, Any] = {}
    adapter_attempts: list[dict[str, Any]] = []
    apply_receipt: dict[str, Any] | None = None
    apply_attempts: list[dict[str, Any]] = []
    repair_artifacts: dict[str, dict[str, Any]] | None = None
    runner_reason: str | None = None
    trace_events: list[dict[str, Any]] = []
    _stage_event(trace_events, "authenticated_request_accepted", task_id=task_id)
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
                model_input_observer=initial_input_capture,
                model_output_observer=initial_output_capture,
                model_call_run_id=f"coding-run-{prepared.run_id}:initial",
            )
            adapter_attempts.append(
                _adapter_attempt_record(
                    adapter_result,
                    phase="initial",
                    attempt_index=1,
                    fixture_root=prepared.fixture_root,
                )
            )
            provenance = adapter_result.get("target_adapter_provenance", {})
            _stage_event(trace_events, "provider_model_called", call_count=provenance.get("call_count", 0))
            diff = str(adapter_result.get("proposed_diff") or "")
            adapter_reason = str(adapter_result.get("reason_code") or "").strip()
            if adapter_result.get("coder_blocked"):
                runner_reason = f"campaign_3_5_adapter_blocked:{adapter_reason or 'unspecified'}"
            elif diff:
                attempt, applied = _apply_scored_diff(
                    diff=diff,
                    provenance=provenance,
                    allowed_paths=tuple(plugin.allowed_actions),
                    fixture_root=prepared.fixture_root,
                    run_id=prepared.run_id,
                    phase="initial",
                    attempt_index=1,
                    trace_events=trace_events,
                )
                apply_attempts.append(attempt)
                if applied:
                    apply_receipt = attempt["apply_authority"]
                else:
                    runner_reason = str(attempt["reason_code"])
            else:
                runner_reason = "campaign_3_5_adapter_diff_missing"
            _stage_event(
                trace_events,
                "coder_or_terminal_disposition",
                blocked=bool(adapter_result.get("coder_blocked")),
                reason_code=runner_reason or adapter_reason or None,
                execution_path=provenance.get("execution_path"),
                rich_path_proven=provenance.get("rich_path_proven") is True,
            )
    except Exception as error:  # Preserve no model/provider/private content in receipts.
        runner_reason = f"campaign_3_5_execution_error:{type(error).__name__}"
        if not adapter_attempts:
            adapter_attempts.append(
                _adapter_attempt_record(
                    {
                        "coder_blocked": True,
                        "reason_code": runner_reason,
                        "coder_diagnostics": {
                            "failure_stage": "runner",
                            "failure_classification": _repair_failure_payload(
                                runner_reason,
                                stage="runner",
                            ),
                        },
                    },
                    phase="initial",
                    attempt_index=1,
                    fixture_root=prepared.fixture_root,
                )
            )
        _stage_event(
            trace_events,
            "coder_or_terminal_disposition",
            blocked=True,
            reason_code=runner_reason,
        )

    changed = bool(_workspace_changed_paths(prepared.fixture_root))
    tests = _run_visible_tests(prepared.task, prepared.fixture_root) if runner_reason is None and changed else {"status": "not_run", "passed": False}
    _stage_event(trace_events, "tests_completed", passed=tests["passed"])
    # One bounded repair pass lets the production coder inspect the exact
    # applied public tree after a visible-test failure.  It never receives a
    # private oracle result, expected answer, or hidden test name.
    if runner_reason is None and changed and not tests["passed"]:
        repair_artifacts = _public_repair_artifacts(prepared.task, prepared.fixture_root, tests)
        # These are deterministic repair-input packets, not dispatched agents.
        # Their names must not manufacture planner/debugger/reviewer trace proof.
        _stage_event(trace_events, "planner_failure_artifact_built", content_sha256=repair_artifacts["planner"]["content_sha256"])
        _stage_event(trace_events, "architect_failure_artifact_built", content_sha256=repair_artifacts["architect"]["content_sha256"])
        _stage_event(trace_events, "diagnostic_failure_packet_built", content_sha256=repair_artifacts["diagnostics"]["content_sha256"])
        _stage_event(trace_events, "debugger_failure_artifact_built", content_sha256=repair_artifacts["debugger"]["content_sha256"])
        _stage_event(trace_events, "reviewer_failure_artifact_built", phase="pre_repair", content_sha256=repair_artifacts["reviewer"]["content_sha256"])
        _stage_event(trace_events, "verifier_failure_artifact_built", phase="pre_repair", content_sha256=repair_artifacts["verifier"]["content_sha256"])
        _stage_event(trace_events, "visible_test_repair_requested", evidence_sha256=hashlib.sha256(json.dumps(repair_artifacts, sort_keys=True).encode("utf-8")).hexdigest())
        try:
            with _fixture_authority(prepared.manifest_path), _temporary_environment(
                "SOURCE_PROXY_GATE_INCREMENT", "campaign-3.5"
            ), _temporary_environment(
                "SOURCE_PROXY_DUMMY_PRODUCT_SITE_DIRECT_OLLAMA", "0"
            ):
                plugin = resolve_target_plugin(_packet(), prepared.fixture_root)
                repair_task = (
                    str(prepared.task["prompt"])
                    + "\n\nYou are performing one bounded evidence-guided public repair. A prior patch is already applied. "
                    + "Inspect the current repository context and return one scoped patch that makes the public task and visible tests pass. "
                    + "Use the following public repair evidence; it is from the current applied tree and includes no hidden oracle result. "
                    + json.dumps(repair_artifacts, sort_keys=True)
                )
                repair_result = execute_target_plugin_command(
                    plugin,
                    task=repair_task,
                    workspace_root=prepared.fixture_root,
                    canonical_context={},
                    canonical_context_text="",
                    llm_call=llm_call,
                    model_alias=model_alias,
                    model_input_observer=repair_input_capture,
                    model_output_observer=repair_output_capture,
                    model_call_run_id=f"coding-run-{prepared.run_id}:repair",
                )
                adapter_attempts.append(
                    _adapter_attempt_record(
                        repair_result,
                        phase="repair",
                        attempt_index=len(adapter_attempts) + 1,
                        fixture_root=prepared.fixture_root,
                    )
                )
                repair_provenance = repair_result.get("target_adapter_provenance", {})
                repair_diff = str(repair_result.get("proposed_diff") or "")
                repair_reason = str(repair_result.get("reason_code") or "").strip()
                _stage_event(
                    trace_events,
                    "coder_or_terminal_disposition",
                    phase="repair",
                    blocked=bool(repair_result.get("coder_blocked")),
                    reason_code=repair_reason or None,
                    execution_path=repair_provenance.get("execution_path"),
                    rich_path_proven=repair_provenance.get("rich_path_proven") is True,
                )
                if repair_diff:
                    attempt, applied = _apply_scored_diff(
                        diff=repair_diff,
                        provenance=repair_provenance,
                        allowed_paths=tuple(plugin.allowed_actions),
                        fixture_root=prepared.fixture_root,
                        run_id=prepared.run_id,
                        phase="repair",
                        attempt_index=len(apply_attempts) + 1,
                        trace_events=trace_events,
                    )
                    apply_attempts.append(attempt)
                    if applied:
                        adapter_result = repair_result
                        _stage_event(trace_events, "visible_test_repair_applied")
                        tests = _run_visible_tests(prepared.task, prepared.fixture_root)
                        _stage_event(trace_events, "tests_completed", passed=tests["passed"], retry=True)
                    else:
                        _stage_event(
                            trace_events,
                            "visible_test_repair_rejected",
                            reason=str(attempt["reason_code"]),
                        )
                else:
                    _stage_event(
                        trace_events,
                        "visible_test_repair_rejected",
                        reason=repair_reason or "MODEL_OUTPUT_NOT_APPLICABLE",
                    )
        except Exception as error:  # A failed repair transport preserves the original test failure.
            repair_error = f"repair_execution_error:{type(error).__name__}"
            if not any(attempt.get("phase") == "repair" for attempt in adapter_attempts):
                adapter_attempts.append(
                    _adapter_attempt_record(
                        {
                            "coder_blocked": True,
                            "reason_code": repair_error,
                            "coder_diagnostics": {
                                "failure_stage": "runner",
                                "failure_classification": _repair_failure_payload(
                                    repair_error,
                                    stage="runner",
                                ),
                            },
                        },
                        phase="repair",
                        attempt_index=len(adapter_attempts) + 1,
                        fixture_root=prepared.fixture_root,
                    )
                )
            _stage_event(trace_events, "visible_test_repair_rejected", reason=repair_error)
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
    _stage_event(trace_events, "reviewer_result", passed=reviewer["passed"], identity=reviewer["identity"])
    verifier = {"identity": "deterministic-evidence-verifier/v1", "passed": bool(tests["passed"] and oracle["passed"] and reviewer["passed"])}
    _stage_event(trace_events, "verifier_completed", passed=verifier["passed"])
    _stage_event(trace_events, "verifier_result", passed=verifier["passed"], identity=verifier["identity"])
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
    if runner_reason is None:
        runner_failure = None
    else:
        failure_stage = (
            "reviewer"
            if runner_reason == "REVIEWER_REJECTED"
            else "verifier"
            if runner_reason in {"VERIFIER_REJECTED", "SEMANTIC_VERIFICATION_FAILED"}
            else "tests"
            if runner_reason == "VISIBLE_TESTS_FAILED"
            else "runner"
        )
        runner_failure = _repair_failure_payload(
            runner_reason,
            stage=failure_stage,
        )
    task_required_trace_events = tuple(
        str(value) for value in prepared.task.get("required_trace_events", []) if str(value).strip()
    )
    _stage_event(
        trace_events,
        "evidence_envelope_written",
        task_id=task_id,
        disposition=disposition,
    )
    _stage_event(
        trace_events,
        "final_receipt_written",
        task_id=task_id,
        receipt_name=receipt_path.name,
    )
    observed_harness_events = sorted({str(event.get("event") or "") for event in trace_events})
    # These are explicitly harness telemetry. They must never be promoted to
    # authenticated production trace proof without a persisted orchestrator
    # event reconciliation carrying real event/run/attempt identities.
    trace_claim_reconciliation = {
        "schema_version": "campaign-3.5-trace-claim-reconciliation/v1",
        "telemetry_source": "adapter_harness",
        "required_task_events": list(task_required_trace_events),
        "observed_harness_events": observed_harness_events,
        "task_event_names_complete": all(
            required in observed_harness_events for required in task_required_trace_events
        ),
        "production_runtime_trace_observed": False,
        "production_event_ids": [],
        "eligible_for_scored_trace_proof": False,
        "reason_code": "authenticated_orchestrator_trace_not_observed",
    }
    coder_stage_proven = _rich_provenance_problem(provenance) is None
    applied_attempts = [
        attempt for attempt in apply_attempts if attempt.get("status") == "applied"
    ]
    all_applied_attempts_gated = bool(applied_attempts) and all(
        attempt.get("status") == "applied"
        and isinstance(attempt.get("apply_authority"), dict)
        and attempt["apply_authority"].get("central_gate_check_passed") is True
        for attempt in applied_attempts
    )
    input_capture_entries = initial_input_capture.entries + repair_input_capture.entries
    output_capture_entries = initial_output_capture.entries + repair_output_capture.entries
    model_evidence_complete = _model_evidence_complete(
        adapter_attempts,
        input_entries=input_capture_entries,
        output_entries=output_capture_entries,
    )
    hidden_answer_isolation = {
        "visible_tests_container_isolated": bool(
            tests.get("sandbox", {}).get("private_store_mounted") is False
            and tests.get("sandbox", {}).get("network") == "disabled"
            and tests.get("sandbox", {}).get("environment") == "strict_allowlist"
        ),
        "private_oracle_separate_uid_or_container": False,
        "isolation_fully_proven": False,
        "reason_code": "legacy_semantic_probe_runs_in_runner_process",
    }
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
            for key in (
                "transport_kind",
                "provider_call_made",
                "provider_call_authorized",
                "trust_status",
                "terminal_proof_eligible",
                "execution_path",
                "rich_path_proven",
                "selected_prompt_id",
                "call_count",
                "provider",
                "model",
            )
        }
        | {
            "call_stages": [
                str(call.get("stage") or "")
                for call in provenance.get("calls", [])
                if isinstance(call, dict)
            ],
            "model_response_format": adapter_result.get("coder_diagnostics", {}).get("model_response_format"),
        },
        "raw_model_output": {
            "captured_privately": bool(output_capture_entries),
            "call_hashes": output_capture_entries,
            "public_receipt_contains_raw_text": False,
        },
        "model_input": {
            "captured_privately": bool(input_capture_entries),
            "call_hashes": input_capture_entries,
            "public_receipt_contains_raw_text": False,
        },
        "model_evidence_complete": model_evidence_complete,
        "adapter_attempts": adapter_attempts,
        "apply_authority": apply_receipt,
        "apply_attempts": apply_attempts,
        "runner_reason": runner_reason,
        "runner_failure_classification": runner_failure,
        "final_disposition": disposition,
        "visible_tests": tests,
        "repair_artifacts": repair_artifacts,
        "oracle": oracle,
        "reviewer": reviewer,
        "verifier": verifier,
        "trace_events": trace_events,
        "trace_claim_reconciliation": trace_claim_reconciliation,
        "benchmark_passed": bool(
            disposition == "COMPLETED_VERIFIED"
            and provenance.get("terminal_proof_eligible") is True
            and provenance.get("execution_path") == GENERIC_RICH_EXECUTION_PATH
            and provenance.get("rich_path_proven") is True
            and coder_stage_proven
            and all_applied_attempts_gated
            and model_evidence_complete
            and hidden_answer_isolation["isolation_fully_proven"] is True
            and trace_claim_reconciliation["eligible_for_scored_trace_proof"] is True
        ),
        "hidden_answer_isolation": hidden_answer_isolation,
        "private_data_exposed": None,
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
