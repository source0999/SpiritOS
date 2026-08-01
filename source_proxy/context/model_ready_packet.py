"""Canonical, qualification-only model-ready task packet helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


SCHEMA_VERSION = "source-proxy.model-ready-packet/v1"
CANONICAL_SECTION_ORDER = (
    "identity",
    "task",
    "desired_observable_behavior",
    "acceptance_criteria",
    "writable_files",
    "read_only_supporting_files",
    "mounted_tool_paths",
    "focused_validation_command",
    "minimal_constraints",
    "relevant_source_and_test_context",
    "minimal_required_tools",
    "hashes_and_budgets",
    "explicit_stop_condition",
)


def canonical_packet_bytes(packet: Mapping[str, Any]) -> bytes:
    """Render stable bytes without depending on caller dictionary insertion order."""

    return json.dumps(
        packet,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=False,
    ).encode("utf-8")


def packet_sha256(packet: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_packet_bytes(packet)).hexdigest()


def build_model_ready_packet(
    *,
    identity: Mapping[str, str],
    objective: str,
    desired_observable_behavior: str,
    acceptance_criteria: Sequence[str],
    writable_files: Sequence[str],
    read_only_files: Sequence[str],
    mounted_tool_paths: Sequence[str],
    focused_validation_command: str,
    stop_condition: str,
    file_manifest: Sequence[Mapping[str, Any]],
    tools: Sequence[Mapping[str, Any]],
    prohibited_paths: Sequence[str],
    context_limit_tokens: int,
    requested_output_tokens: int = 1024,
    safety_tokens: int = 256,
    truncation_receipt: str = "none",
    excluded_path_manifest: Sequence[str] = (),
) -> dict[str, Any]:
    """Build the task-first packet used only by Gate 2-J.9T qualification."""

    manifest = [dict(entry) for entry in file_manifest]
    context_bytes = sum(
        len(str(entry.get("content_or_excerpt", "")).encode("utf-8"))
        for entry in manifest
    )
    relevant_bytes = sum(
        len(str(entry.get("content_or_excerpt", "")).encode("utf-8"))
        for entry in manifest
        if entry.get("relevant", True)
    )
    relevant_ratio = relevant_bytes / context_bytes if context_bytes else 1.0
    packet: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "identity": dict(identity),
        "task": {
            "objective": objective,
            "desired_observable_behavior": desired_observable_behavior,
            "acceptance_criteria": list(acceptance_criteria),
            "writable_files": list(writable_files),
            "read_only_files": list(read_only_files),
            "mounted_tool_paths": list(mounted_tool_paths),
            "focused_validation_command": focused_validation_command,
            "stop_condition": stop_condition,
        },
        "context": {
            "file_manifest": manifest,
            "excluded_path_manifest": list(excluded_path_manifest),
            "truncation_receipt": truncation_receipt,
            "no_hidden_expectations": True,
            "no_unrelated_campaign_history": True,
        },
        "tools": [dict(tool) for tool in tools],
        "constraints": {
            "network_policy": "none",
            "write_policy": "declared writable files only",
            "prohibited_paths": list(prohibited_paths),
            "no_git_writes": True,
            "no_commit_push_deploy": True,
            "bounded_tool_turns": 3,
            "bounded_retries": "parser/recovery only",
            "no_cross_run_memory": True,
        },
        "ordering": list(CANONICAL_SECTION_ORDER),
        "quality_metrics": {
            "task_content_byte_position": 0,
            "relevant_context_ratio": relevant_ratio,
            "governance_noise_count": 0,
            "critical_file_presence": 1.0,
            "path_consistency": True,
            "duplicate_content_ratio": 0.0,
            "truncation_status": truncation_receipt,
            "total_model_visible_tokens": 0,
            "tool_schema_tokens": 0,
            "available_output_budget_tokens": 0,
            "context_limit_tokens": context_limit_tokens,
            "requested_output_tokens": requested_output_tokens,
            "safety_tokens": safety_tokens,
        },
    }
    _refresh_measurements(packet)
    return packet


def _refresh_measurements(packet: dict[str, Any]) -> None:
    quality = packet["quality_metrics"]
    initial_bytes = canonical_packet_bytes(packet)
    task = packet["task"]
    objective = str(task.get("objective", "")).encode("utf-8")
    quality["task_content_byte_position"] = initial_bytes.find(objective)
    quality["total_model_visible_tokens"] = (len(initial_bytes) + 3) // 4
    tool_bytes = len(json.dumps(packet.get("tools", []), separators=(",", ":")).encode("utf-8"))
    quality["tool_schema_tokens"] = (tool_bytes + 3) // 4
    quality["available_output_budget_tokens"] = int(quality["context_limit_tokens"]) - int(
        quality["total_model_visible_tokens"]
    )


def validate_model_ready_packet_schema(packet: Mapping[str, Any]) -> list[str]:
    """Small deterministic schema guard for the committed JSON-schema contract."""

    failures: list[str] = []
    if packet.get("schema_version") != SCHEMA_VERSION:
        failures.append("schema_version")
    identity = packet.get("identity")
    required_identity = (
        "task_id", "run_id", "campaign_id", "prompt_hash", "acceptance_hash",
        "context_hash", "base_commit", "executor_id", "model_profile_id",
        "tool_profile_id", "evaluator_profile_id",
    )
    if not isinstance(identity, Mapping):
        failures.append("identity")
    else:
        failures.extend(f"identity:{field}" for field in required_identity if not identity.get(field))
    task = packet.get("task")
    required_task = (
        "objective", "desired_observable_behavior", "acceptance_criteria", "writable_files",
        "read_only_files", "mounted_tool_paths", "focused_validation_command", "stop_condition",
    )
    if not isinstance(task, Mapping):
        failures.append("task")
    else:
        failures.extend(f"task:{field}" for field in required_task if not task.get(field))
    for section in ("context", "tools", "constraints", "ordering", "quality_metrics"):
        if section not in packet:
            failures.append(section)
    return failures


__all__ = [
    "CANONICAL_SECTION_ORDER",
    "SCHEMA_VERSION",
    "build_model_ready_packet",
    "canonical_packet_bytes",
    "packet_sha256",
    "validate_model_ready_packet_schema",
]
