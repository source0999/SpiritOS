"""Deterministic quality gates for model-ready qualification packets."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from source_proxy.context.model_ready_packet import (
    CANONICAL_SECTION_ORDER,
    canonical_packet_bytes,
    packet_sha256,
    validate_model_ready_packet_schema,
)


GOVERNANCE_MARKERS = ("campaign ", "gate ", "batch ", "operator authorization", "glm review")
HIDDEN_ANSWER_MARKERS = ("__hidden_answer__", "hidden answer", "expected patch", "answer key")
MIN_RELEVANCE_RATIO = 0.40
MIN_OUTPUT_BUDGET_TOKENS = 1280


@dataclass(frozen=True)
class PacketQualityReport:
    verdict: str
    failures: tuple[str, ...]
    measurements: dict[str, Any]

    @property
    def ready(self) -> bool:
        return self.verdict == "PACKET_READY"

    def to_dict(self) -> dict[str, Any]:
        return {"verdict": self.verdict, "failures": list(self.failures), "measurements": self.measurements}


def validate_packet_quality(
    packet: Mapping[str, Any],
    *,
    required_source_paths: Sequence[str],
    required_test_paths: Sequence[str],
    sandbox_mounted_paths: Sequence[str],
    paired_lane_packet_bytes: bytes | None = None,
) -> PacketQualityReport:
    """Enforce every readiness condition; a relevance pass is never sufficient."""

    failures = list(validate_model_ready_packet_schema(packet))
    packet_bytes = canonical_packet_bytes(packet)
    repeated_bytes = canonical_packet_bytes(json.loads(packet_bytes.decode("utf-8")))
    task = packet.get("task") if isinstance(packet.get("task"), Mapping) else {}
    context = packet.get("context") if isinstance(packet.get("context"), Mapping) else {}
    quality = packet.get("quality_metrics") if isinstance(packet.get("quality_metrics"), Mapping) else {}
    manifest = context.get("file_manifest", []) if isinstance(context.get("file_manifest"), list) else []
    manifest_paths = {str(entry.get("path", "")) for entry in manifest if isinstance(entry, Mapping)}
    combined_text = json.dumps(packet, ensure_ascii=True).lower()
    objective = str(task.get("objective", "")).encode("utf-8")
    acceptance = task.get("acceptance_criteria", [])
    acceptance_text = str(acceptance[0]).encode("utf-8") if acceptance else b""
    first_critical = min(
        (position for position in (packet_bytes.find(objective), packet_bytes.find(acceptance_text)) if position >= 0),
        default=-1,
    )
    governance_noise = sum(combined_text.count(marker) for marker in GOVERNANCE_MARKERS)
    relevance_ratio = float(quality.get("relevant_context_ratio", 0.0) or 0.0)
    mounted_paths = tuple(task.get("mounted_tool_paths", []))
    expected_paths = tuple(sandbox_mounted_paths)
    truncation = str(context.get("truncation_receipt", "")).lower()
    output_budget = int(quality.get("available_output_budget_tokens", 0) or 0)

    if not task.get("objective"):
        failures.append("missing_task")
    if not acceptance:
        failures.append("missing_acceptance_criteria")
    if first_critical < 0 or first_critical > 1024:
        failures.append("critical_content_after_1024_bytes")
    if relevance_ratio < MIN_RELEVANCE_RATIO:
        failures.append("relevance_below_threshold")
    if governance_noise:
        failures.append("governance_contamination")
    failures.extend(f"missing_critical_source:{path}" for path in required_source_paths if path not in manifest_paths)
    failures.extend(f"missing_critical_test:{path}" for path in required_test_paths if path not in manifest_paths)
    if mounted_paths != expected_paths:
        failures.append("sandbox_path_mismatch")
    if "critical" in truncation and "none" not in truncation:
        failures.append("critical_truncation")
    if tuple(packet.get("ordering", [])) != CANONICAL_SECTION_ORDER:
        failures.append("nondeterministic_or_invalid_section_order")
    if len(set(packet.get("ordering", []))) != len(packet.get("ordering", [])):
        failures.append("duplicate_sections")
    if repeated_bytes != packet_bytes:
        failures.append("nondeterministic_packet_bytes")
    if any(marker in combined_text for marker in HIDDEN_ANSWER_MARKERS):
        failures.append("hidden_answer_leakage")
    constraints = packet.get("constraints") if isinstance(packet.get("constraints"), Mapping) else {}
    if constraints.get("network_policy") != "none" or "all files writable" in combined_text:
        failures.append("contradictory_instructions")
    if paired_lane_packet_bytes is not None and paired_lane_packet_bytes != packet_bytes:
        failures.append("paired_lane_packet_mismatch")
    if output_budget < MIN_OUTPUT_BUDGET_TOKENS:
        failures.append("insufficient_output_budget")

    unique_failures = tuple(dict.fromkeys(failures))
    measurements = {
        "packet_sha256": packet_sha256(packet),
        "packet_byte_count": len(packet_bytes),
        "relevance_ratio": relevance_ratio,
        "first_critical_content_byte": first_critical,
        "governance_marker_count": governance_noise,
        "critical_sources_present": all(path in manifest_paths for path in required_source_paths),
        "critical_tests_present": all(path in manifest_paths for path in required_test_paths),
        "mounted_paths_match": mounted_paths == expected_paths,
        "critical_truncation": "critical" in truncation and "none" not in truncation,
        "deterministic_packet_bytes": repeated_bytes == packet_bytes,
        "paired_lane_bytes_match": paired_lane_packet_bytes is None or paired_lane_packet_bytes == packet_bytes,
        "available_output_budget_tokens": output_budget,
    }
    return PacketQualityReport(
        verdict="PACKET_READY" if not unique_failures else "PACKET_NOT_READY",
        failures=unique_failures,
        measurements=measurements,
    )


__all__ = ["MIN_OUTPUT_BUDGET_TOKENS", "MIN_RELEVANCE_RATIO", "PacketQualityReport", "validate_packet_quality"]
