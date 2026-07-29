"""Sealed execution envelope schemas and fail-closed validation for Gate 2-J.9A.

This defines the canonical request-envelope section set and validates that an
envelope carries every sealed identity/binding field with correct types and
exact sealed values. It reuses the fail-closed discipline already present in
``source_proxy/jcode/adapter.validate_jcode_envelope`` but operates on the
sealed Gate 2-J.9A schema. It does not dispatch anything.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from source_proxy.jcode import constants as C
from source_proxy.jcode.canonical_io import (
    root_envelope_hash,
    section_hash,
)


# Ordered list of required envelope sections and the sealed fields each must carry.
REQUIRED_SECTIONS: dict[str, tuple[str, ...]] = {
    "identity": (
        "schema_version", "campaign_id", "gate_id", "run_id", "task_id",
        "correlation_id", "harness_id", "harness_version", "adapter_version",
        "jcode_source_commit", "jcode_binary_sha256", "proxy_source_commit",
        "base_commit",
    ),
    "task_binding": (
        "immutable_prompt_sha256", "acceptance_criteria_sha256",
        "diagnostic_manifest_sha256", "task_category",
        "hidden_material_exclusion_proof",
    ),
    "context_binding": (
        "context_packet_id", "context_schema_version", "context_packet_sha256",
        "ordered_file_manifest", "total_context_bytes", "truncation_status",
    ),
    "model_provider_binding": (
        "provider_profile_id", "inference_bridge_id", "permitted_endpoint",
        "model_registry_id", "expected_model_digest", "quantization",
        "generation_parameters", "fallback_policy",
    ),
    "capability_binding": (
        "allowed_paths", "protected_paths", "allowed_tools", "denied_tools",
        "command_policy", "network_policy", "environment_allowlist",
        "commit_push_deploy_prohibition",
    ),
    "budget_binding": (
        "total_wall_clock_seconds", "inactivity_timeout_seconds",
        "max_model_requests", "max_aggregate_output_tokens",
        "max_tool_calls", "max_descendant_processes",
    ),
    "evidence_binding": (
        "evidence_directory", "raw_event_path", "stdout_path", "stderr_path",
        "diff_receipt_path", "final_result_path",
    ),
}


# Sealed identity values an envelope MUST match exactly when present.
SEALED_IDENTITY_VALUES = {
    "identity.schema_version": C.QUALIFICATION_SCHEMA_VERSION,
    "identity.campaign_id": C.CAMPAIGN_ID,
    "identity.gate_id": C.GATE_ID,
    "identity.harness_id": C.HARNESS_ID,
    "identity.harness_version": C.HARNESS_VERSION,
    "identity.adapter_version": C.ADAPTER_VERSION,
    "identity.jcode_source_commit": C.JCODE_SOURCE_COMMIT,
    "identity.jcode_binary_sha256": C.JCODE_BINARY_SHA256,
}


@dataclass(frozen=True)
class SealedEnvelopeValidation:
    ok: bool
    blocked_reasons: list[str] = field(default_factory=list)
    section_hashes: dict[str, str] = field(default_factory=dict)
    root_hash: str | None = None


def validate_sealed_envelope(envelope: dict[str, Any]) -> SealedEnvelopeValidation:
    """Validate a sealed Gate 2-J.9A envelope and compute its section/root hashes."""
    if not isinstance(envelope, dict):
        return SealedEnvelopeValidation(False, ["envelope_not_object"])

    blocked: list[str] = []

    # 1. Required sections present.
    for section, fields in REQUIRED_SECTIONS.items():
        payload = envelope.get(section)
        if not isinstance(payload, dict):
            blocked.append(f"section_missing:{section}")
            continue
        for name in fields:
            if name not in payload:
                blocked.append(f"field_missing:{section}.{name}")

    # 2. Sealed identity values match exactly.
    for dotted, expected in SEALED_IDENTITY_VALUES.items():
        section, name = dotted.split(".", 1)
        payload = envelope.get(section)
        if isinstance(payload, dict) and name in payload and payload[name] != expected:
            blocked.append(
                f"sealed_value_mismatch:{dotted}:{payload[name]}!={expected}"
            )

    # 3. Unknown sections are rejected (no silent extension).
    for section in envelope:
        if section not in REQUIRED_SECTIONS and section != "root_hash":
            blocked.append(f"unknown_section:{section}")

    # 4. Network/command policy must be the sealed safe values.
    cap = envelope.get("capability_binding")
    if isinstance(cap, dict):
        if cap.get("command_policy") != "no_shell":
            blocked.append("unsafe_command_policy")
        if cap.get("network_policy") != "inference_only_via_sealed_loopback_bridge":
            blocked.append("unsafe_network_policy")
        if cap.get("commit_push_deploy_prohibition") is not True:
            blocked.append("commit_push_deploy_prohibition_not_enforced")

    # 5. Fallback must be none (no silent model substitution).
    mpb = envelope.get("model_provider_binding")
    if isinstance(mpb, dict) and mpb.get("fallback_policy") != "none":
        blocked.append("unsafe_fallback_policy")

    # 6. JCode never holds terminal authority.
    if envelope.get("terminal_authority") not in (None, False):
        blocked.append("jcode_terminal_authority_forbidden")

    # Section hashes (computed even on failure, for evidence).
    section_hashes: dict[str, str] = {}
    for section in REQUIRED_SECTIONS:
        payload = envelope.get(section)
        if isinstance(payload, dict):
            section_hashes[section] = section_hash(section, payload)
    root_hash = root_envelope_hash(section_hashes) if section_hashes else None

    return SealedEnvelopeValidation(
        ok=not blocked,
        blocked_reasons=blocked,
        section_hashes=section_hashes,
        root_hash=root_hash,
    )


def sealed_identity_payload(*, run_id: str, task_id: str, correlation_id: str,
                            proxy_source_commit: str, base_commit: str) -> dict[str, Any]:
    """Build the canonical identity section with sealed values filled in."""
    return {
        "schema_version": C.QUALIFICATION_SCHEMA_VERSION,
        "campaign_id": C.CAMPAIGN_ID,
        "gate_id": C.GATE_ID,
        "run_id": run_id,
        "task_id": task_id,
        "correlation_id": correlation_id,
        "harness_id": C.HARNESS_ID,
        "harness_version": C.HARNESS_VERSION,
        "adapter_version": C.ADAPTER_VERSION,
        "jcode_source_commit": C.JCODE_SOURCE_COMMIT,
        "jcode_binary_sha256": C.JCODE_BINARY_SHA256,
        "proxy_source_commit": proxy_source_commit,
        "base_commit": base_commit,
    }
