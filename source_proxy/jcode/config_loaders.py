"""Loaders for the sealed Gate 2-J.9A configuration artifacts.

Each loader reads one canonical machine-readable JSON artifact and validates it
against the sealed policy. They fail closed on schema drift, sealed-value
mismatch, or forbidden content. No execution authority is granted.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from source_proxy.jcode import constants as C


class ConfigLoadError(ValueError):
    """A sealed configuration artifact is missing, malformed, or drifted."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigLoadError(f"json_load_failed:{path}") from error
    if not isinstance(value, dict):
        raise ConfigLoadError(f"json_object_required:{path}")
    return value


def _require(value: dict[str, Any], key: str, *, expected: Any | None = None) -> Any:
    if key not in value:
        raise ConfigLoadError(f"field_missing:{key}")
    if expected is not None and value[key] != expected:
        raise ConfigLoadError(f"field_mismatch:{key}:{value[key]}!={expected}")
    return value[key]


def load_lane_bindings(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    _require(data, "schema_version",
             expected="source-proxy.gate-2j-9-lane-bindings/v1")
    _require(data, "decision",
             expected="SEALED_DECISION_1_LANE_AND_EXECUTOR_BINDING")
    lanes = _require(data, "lanes")
    if not isinstance(lanes, dict) or sorted(lanes) != ["A", "B", "C", "D"]:
        raise ConfigLoadError("lanes_must_be_A_B_C_D")
    # Paired lanes share a model (A==B primary, C==D challenger).
    for baseline, jcode, model in (("A", "B", C.PRIMARY_MODEL),
                                   ("C", "D", C.CHALLENGER_MODEL)):
        if lanes[baseline]["model_registry_id"] != model:
            raise ConfigLoadError(f"lane_model_mismatch:{baseline}")
        if lanes[jcode]["model_registry_id"] != model:
            raise ConfigLoadError(f"lane_model_mismatch:{jcode}")
    # Digests must match sealed values.
    digest_for = {C.PRIMARY_MODEL: C.PRIMARY_MODEL_DIGEST,
                  C.CHALLENGER_MODEL: C.CHALLENGER_MODEL_DIGEST}
    for lane_id, lane in lanes.items():
        model = lane["model_registry_id"]
        if lane.get("model_digest_sha256") != digest_for[model]:
            raise ConfigLoadError(f"lane_digest_mismatch:{lane_id}")
    return data


def load_context_policy(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    schema = data.get("schema_version")
    if schema not in ("source-proxy.gate-2j-9-context-policy/v1",
                      "source-proxy.gate-2j-9-context-policy/v2"):
        raise ConfigLoadError(
            f"context_schema_unsupported:{schema}"
        )
    _require(data, "decision",
             expected="SEALED_DECISION_2_CONTEXT_PACKET_CONSTRUCTION")
    budget = _require(data, "context_budget")
    if not isinstance(budget, dict) or budget.get("max_total_context_bytes", 0) <= 0:
        raise ConfigLoadError("context_budget_invalid")
    # Exclusions must include the frozen benchmark and daily runtime.
    exclusions = _require(data, "exclusions_enforced")
    joined = " ".join(exclusions)
    if "benchmark" not in joined or "daily runtime" not in joined:
        raise ConfigLoadError("context_exclusions_incomplete")
    # v2 correction: one canonical context for all four lanes (no per-model split default).
    if schema.endswith("/v2"):
        if data.get("canonical_invariant") != "ONE_TASK_ONE_CANONICAL_CONTEXT_PACKET_ALL_LANES":
            raise ConfigLoadError("context_v2_requires_all_lanes_invariant")
        rule = " ".join(data.get("determinism_rules", []))
        if "A==B==C==D" not in rule:
            raise ConfigLoadError("context_v2_requires_all_lanes_equality_rule")
    return data


def load_provider_profile(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    _require(data, "schema_version",
             expected="source-proxy.gate-2j-9-provider-profile/v1")
    _require(data, "provider_profile_id", expected=C.PROVIDER_PROFILE_ID)
    _require(data, "permitted_endpoint", expected=C.PERMITTED_INFERENCE_ENDPOINT)
    _require(data, "fallback_policy", expected="none")
    _require(data, "credential_policy", expected="none")
    # The dead 4000 endpoint must not appear as a permitted endpoint.
    forbidden = data.get("forbidden_flows_rejected_by_bridge", [])
    if C.PERMITTED_INFERENCE_ENDPOINT in str(forbidden):
        raise ConfigLoadError("permitted_endpoint_listed_as_forbidden")
    return data


def _validate_budget_bucket(bucket: dict[str, Any], label: str) -> None:
    if not isinstance(bucket, dict) or not bucket:
        raise ConfigLoadError(f"budget_group_empty:{label}")
    for name, spec in bucket.items():
        if not isinstance(spec, dict) or "value" not in spec or "rationale" not in spec:
            raise ConfigLoadError(f"budget_spec_invalid:{label}.{name}")


def load_budget_policy(path: Path) -> dict[str, Any]:
    """Load a sealed budget policy (v1 flat or v2 shared_base + gate_profiles).

    v1 is the original single-profile conservative budget. v2 splits the universal
    budget into gate-specific profiles so later coding qualification is not
    artificially prevented from running legitimate tools and tests; the schema-only
    gate (9a) must still keep shell commands and deletions at zero.
    """
    data = _load_json(path)
    schema = data.get("schema_version")
    if schema not in ("source-proxy.gate-2j-9-budget-policy/v1",
                      "source-proxy.gate-2j-9-budget-policy/v2"):
        raise ConfigLoadError(f"budget_schema_unsupported:{schema}")
    if data.get("no_silent_extension") is not True:
        raise ConfigLoadError("no_silent_extension_required")

    if schema.endswith("/v1"):
        _require(data, "decision", expected="SEALED_DECISION_4_BUDGETS_AND_LIMITS")
        for group in ("process_budgets", "model_budgets", "tool_budgets", "evidence_budgets"):
            _validate_budget_bucket(_require(data, group), group)
        if data["tool_budgets"]["max_shell_commands"]["value"] != 0:
            raise ConfigLoadError("shell_commands_must_be_zero")
        if data["tool_budgets"]["max_deleted_files"]["value"] != 0:
            raise ConfigLoadError("deleted_files_must_be_zero")
        return data

    # v2: shared_base + gate_profiles.
    _require(data, "decision",
             expected="SEALED_DECISION_4_BUDGETS_AND_LIMITS_GATE_SPECIFIC_PROFILES")
    base = _require(data, "shared_base")
    if not isinstance(base, dict):
        raise ConfigLoadError("shared_base_required")
    for group in ("process_budgets", "model_budgets", "tool_budgets", "evidence_budgets"):
        _validate_budget_bucket(_require(base, group), f"shared_base.{group}")
    profiles = _require(data, "gate_profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise ConfigLoadError("gate_profiles_required")
    for pid, prof in profiles.items():
        if not isinstance(prof, dict) or prof.get("inherits") != "shared_base":
            raise ConfigLoadError(f"profile_must_inherit_shared_base:{pid}")
        for key in ("allowed_command_classes", "denied_command_classes", "failure_mapping"):
            if key not in prof:
                raise ConfigLoadError(f"profile_field_missing:{pid}.{key}")
        for dotted, spec in (prof.get("overrides") or {}).items():
            if not isinstance(spec, dict) or "value" not in spec or "rationale" not in spec:
                raise ConfigLoadError(f"profile_override_invalid:{pid}.{dotted}")
    # The schema-only gate must keep shell and deletes at zero (no execution yet).
    schema_only = profiles.get("gate_2j_9a_schema_only", {})
    so_overrides = schema_only.get("overrides", {})
    if so_overrides.get("tool_budgets.max_shell_commands", {}).get("value", 0) != 0:
        raise ConfigLoadError("schema_only_shell_must_be_zero")
    if so_overrides.get("tool_budgets.max_deleted_files", {}).get("value", 0) != 0:
        raise ConfigLoadError("schema_only_deletes_must_be_zero")
    # No raw unrestricted shell anywhere: command policy uses structured classes.
    for pid, prof in profiles.items():
        denied = set(prof.get("denied_command_classes", []))
        if "shell_unrestricted" not in denied and "shell" not in denied:
            if "dangerous_command" not in denied:
                raise ConfigLoadError(f"profile_must_deny_unrestricted_shell:{pid}")
    return data
