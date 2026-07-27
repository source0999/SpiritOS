"""Preparation-only sealing for the Campaign 2-J diagnostic comparison.

This module never starts an executor, opens a provider connection, or runs a
diagnostic task. It turns the immutable manifest, fixture checkout, and a
read-only local registry observation into an auditable run packet for a later
authorized gate.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from source_proxy.jcode.adapter import (
    DEFAULT_JCODE_MAX_OUTPUT_BYTES,
    DEFAULT_JCODE_TIMEOUT_SECONDS,
    JCODE_PINNED_COMMIT,
)


PREPARATION_SCHEMA_VERSION = "source-proxy.jcode-gate-2j-8-5-run-packet/v1"
PRIMARY_MODEL = "qwen2.5-coder:7b"
CHALLENGER_MODEL = "qwen2.5-coder:14b"
EXPECTED_MODEL_DETAILS = {
    PRIMARY_MODEL: {
        "digest": "dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364",
        "quantization_level": "Q4_K_M",
    },
    CHALLENGER_MODEL: {
        "digest": "9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849",
        "quantization_level": "Q4_K_M",
    },
}
JCODE_BINARY_SHA256 = "d7598ca48bb4fc8ff9c37d122fde5dd47314cd36fc2516ce6156795b71a545cc"
FIXTURE_ROOTS = ("qualification_fixture", "fixture_proxy")
MODEL_PARAMETERS = {"max_tokens": 4096, "seed": 7, "temperature": 0}
RUN_BUDGETS = {
    "turn_budget": 4,
    "token_budget": 32768,
    "timeout_seconds": DEFAULT_JCODE_TIMEOUT_SECONDS,
    "max_output_bytes": DEFAULT_JCODE_MAX_OUTPUT_BYTES,
}


class PreparationPacketError(ValueError):
    """The requested pre-execution packet is incomplete or has drifted."""


def load_registry_snapshot(path: Path) -> dict[str, Any]:
    value = _load_json(path)
    if not isinstance(value.get("models"), list):
        raise PreparationPacketError("registry_snapshot_models_missing")
    observed: dict[str, dict[str, Any]] = {}
    for raw in value["models"]:
        if isinstance(raw, dict) and isinstance(raw.get("name"), str):
            observed[raw["name"]] = raw
    results: dict[str, Any] = {}
    for model, expected in EXPECTED_MODEL_DETAILS.items():
        item = observed.get(model)
        details = item.get("details") if isinstance(item, dict) else None
        if not isinstance(item, dict) or not isinstance(details, dict):
            raise PreparationPacketError(f"registry_model_missing:{model}")
        if item.get("digest") != expected["digest"]:
            raise PreparationPacketError(f"registry_digest_mismatch:{model}")
        if details.get("quantization_level") != expected["quantization_level"]:
            raise PreparationPacketError(f"registry_quantization_mismatch:{model}")
        results[model] = {
            "model": model,
            "digest": item["digest"],
            "family": details.get("family"),
            "parameter_size": details.get("parameter_size"),
            "quantization_level": details["quantization_level"],
            "registry_modified_at": item.get("modified_at"),
        }
    return results


def fixture_tree_receipt(repository_root: Path) -> dict[str, Any]:
    repository_root = repository_root.resolve()
    files: list[dict[str, str]] = []
    for root_name in FIXTURE_ROOTS:
        root = repository_root / root_name
        if not root.is_dir() or root.is_symlink():
            raise PreparationPacketError(f"fixture_root_missing:{root_name}")
        for path in sorted(root.rglob("*")):
            if path.is_dir():
                continue
            if path.is_symlink() or not path.is_file():
                raise PreparationPacketError("fixture_non_regular_file")
            relative = path.relative_to(repository_root).as_posix()
            if "__pycache__" in path.parts:
                continue
            files.append({"path": relative, "sha256": _sha256(path.read_bytes())})
    if not files:
        raise PreparationPacketError("fixture_files_missing")
    canonical = _canonical_json(files).encode("utf-8")
    return {
        "roots": list(FIXTURE_ROOTS),
        "file_count": len(files),
        "files": files,
        "tree_sha256": _sha256(canonical),
    }


def build_run_packet(
    *,
    manifest_path: Path,
    repository_root: Path,
    fixture_commit: str,
    registry_snapshot_path: Path,
    created_at_utc: str,
) -> dict[str, Any]:
    manifest = _load_json(manifest_path)
    _require_manifest(manifest)
    if not _is_sha(fixture_commit, 40):
        raise PreparationPacketError("fixture_commit_invalid")
    registry_models = load_registry_snapshot(registry_snapshot_path)
    task_packets = [_task_packet(task) for task in manifest["tasks"]]
    return {
        "schema_version": PREPARATION_SCHEMA_VERSION,
        "campaign_id": "campaign-2-j",
        "gate_id": "2-J.8.5",
        "status": "SEALED_PRE_EXECUTION_NO_TASKS_RUN",
        "created_at_utc": created_at_utc,
        "manifest": {
            "path": str(manifest_path.as_posix()),
            "manifest_id": manifest["manifest_id"],
            "sha256": _sha256(manifest_path.read_bytes()),
            "task_count": len(task_packets),
            "frozen_benchmark_dependency": manifest["frozen_benchmark_dependency"],
        },
        "fixture": {"commit": fixture_commit, **fixture_tree_receipt(repository_root)},
        "binary_expectation": {
            "jcode_source_commit": JCODE_PINNED_COMMIT,
            "jcode_binary_sha256": JCODE_BINARY_SHA256,
            "build_profile": "CARGO_BUILD_JOBS=1 cargo build --offline --locked --no-default-features --features linux-compat-vendored-openssl --bin jcode",
            "before_first_task": "rebuild_or_locate_binary_and_verify_exact_sha256",
        },
        "providers": {
            "host_registry_endpoint": "http://127.0.0.1:11434",
            "jcode_provider_profile": "spiritos-qualification",
            "jcode_sandbox_endpoint": "http://127.0.0.1:4000/v1",
            "jcode_bridge_target": {"host": "127.0.0.1", "port": 11434},
            "credentials": "none",
            "routing": "fixed_local_loopback_only_no_fallback",
            "models": registry_models,
        },
        "generation": {"parameters": MODEL_PARAMETERS, "budgets": RUN_BUDGETS},
        "containment": {
            "fresh_disposable_worktree_per_run": True,
            "fresh_executor_home_per_run": True,
            "fresh_jcode_home_per_jcode_run": True,
            "allowed_tools": ["read", "glob", "grep", "ls", "write", "edit", "multiedit", "patch", "apply_patch"],
            "denied_tools": ["bash", "batch", "browser", "communicate", "launch", "memory", "open", "selfdev", "swarm", "webfetch", "websearch"],
            "network": "bubblewrap_no_network_plus_fixed_loopback_unix_bridge",
            "no_session_resume": True,
            "no_cross_task_memory": True,
            "proxy_terminal_authority": True,
        },
        "evidence": {
            "strict_ndjson_required": True,
            "raw_request_response_metadata_required": True,
            "independent_proxy_checks": ["git_diff", "protected_path_policy", "tests", "reviewer", "verifier", "anti_cheat", "terminal_truth"],
            "terminal_outcome_count": 1,
        },
        "task_packets": task_packets,
        "run_order": _run_order(task_packets),
        "execution_prohibited_by_preparation_stage": True,
    }


def _task_packet(task: Mapping[str, Any]) -> dict[str, Any]:
    prompt = task.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        raise PreparationPacketError("task_prompt_missing")
    task_id = task.get("id")
    if not isinstance(task_id, str) or not task_id:
        raise PreparationPacketError("task_id_missing")
    return {
        "task_id": task_id,
        "category": task.get("category"),
        "prompt_sha256": _sha256(prompt.encode("utf-8")),
        "allowed_paths": task.get("allowed_paths", []),
        "protected_paths": task.get("protected_paths", []),
        "test_command": task.get("test_command"),
        "expected_terminal": task.get("expected_terminal"),
    }


def _run_order(tasks: list[dict[str, Any]]) -> list[dict[str, str]]:
    ordered: list[dict[str, str]] = []
    for model_role, lanes in (("primary", ("A", "B")), ("challenger", ("C", "D"))):
        for task in tasks:
            for lane in lanes:
                ordered.append(
                    {
                        "run_id": f"c2j-9-{model_role}-{lane.lower()}-{task['task_id'].lower()}",
                        "lane": lane,
                        "model_role": model_role,
                        "task_id": task["task_id"],
                    }
                )
    return ordered


def write_sealed_packet(packet: Mapping[str, Any], output_path: Path) -> dict[str, str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (_canonical_json(packet) + "\n").encode("utf-8")
    output_path.write_bytes(encoded)
    digest = _sha256(encoded)
    digest_path = output_path.with_suffix(output_path.suffix + ".sha256")
    digest_path.write_text(f"{digest}  {output_path.name}\n", encoding="ascii")
    return {"packet_sha256": digest, "packet_path": str(output_path), "digest_path": str(digest_path)}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PreparationPacketError(f"json_load_failed:{path}") from error
    if not isinstance(value, dict):
        raise PreparationPacketError(f"json_object_required:{path}")
    return value


def _require_manifest(manifest: Mapping[str, Any]) -> None:
    if manifest.get("schema_version") != "source-proxy.jcode-diagnostic-manifest/v1":
        raise PreparationPacketError("manifest_schema_mismatch")
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 20:
        raise PreparationPacketError("manifest_task_count_invalid")
    if manifest.get("frozen_benchmark_dependency") is not False:
        raise PreparationPacketError("manifest_benchmark_dependency_invalid")


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _is_sha(value: str, length: int) -> bool:
    return len(value) == length and all(character in "0123456789abcdef" for character in value)
