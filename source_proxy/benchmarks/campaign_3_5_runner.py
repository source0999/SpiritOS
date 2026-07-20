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
    adapter_result: dict[str, Any] = {}
    apply_receipt: dict[str, Any] | None = None
    runner_reason: str | None = None
    try:
        # The production model client deliberately reads this established gate
        # setting.  Bind it locally so its own central check receives the
        # Campaign 3.5 authority, rather than the unrelated default increment.
        with _fixture_authority(prepared.manifest_path), _temporary_environment(
            "SOURCE_PROXY_GATE_INCREMENT", "campaign-3.5"
        ):
            plugin = resolve_target_plugin(_packet(), prepared.fixture_root)
            adapter_result = execute_target_plugin_command(
                plugin,
                task=str(prepared.task["prompt"]),
                workspace_root=prepared.fixture_root,
                canonical_context={},
                canonical_context_text="",
                llm_call=llm_call,
                model_alias=model_alias,
            )
            provenance = adapter_result.get("target_adapter_provenance", {})
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
                    runner_reason = "campaign_3_5_apply_failed"
            elif diff:
                runner_reason = "campaign_3_5_noncanonical_diff_not_applied"
    except Exception as error:  # Preserve no model/provider/private content in receipts.
        runner_reason = f"campaign_3_5_execution_error:{type(error).__name__}"

    changed = subprocess.run(
        ["git", "-C", str(prepared.fixture_root), "diff", "--quiet", "HEAD"],
        check=False,
    ).returncode != 0
    if runner_reason is None and changed:
        disposition = "COMPLETED_VERIFIED"
    elif runner_reason is None:
        disposition = "BLOCKED_OR_DEGRADED_TRUTHFULLY"
    else:
        disposition = "BLOCKED_OR_DEGRADED_TRUTHFULLY"
    oracle = evaluate_profile(
        prepared.profile,
        fixture_root=prepared.fixture_root,
        allowed_paths=["src/", "tests/", "migrations/", "config/", "docs/", "pyproject.toml"],
        final_disposition=disposition,
        semantic_probe=_semantic_probe(str(prepared.task["task_id"])) if changed else None,
    )
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
        },
        "apply_authority": apply_receipt,
        "runner_reason": runner_reason,
        "final_disposition": disposition,
        "oracle": oracle,
        "benchmark_passed": bool(oracle["passed"] and provenance.get("terminal_proof_eligible") is True),
        "private_data_exposed": False,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(receipt_path, 0o600)
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
