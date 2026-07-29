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
    _require(data, "schema_version",
             expected="source-proxy.gate-2j-9-context-policy/v1")
    _require(data, "decision",
             expected="SEALED_DECISION_2_CONTEXT_PACKET_CONSTRUCTION")
    budget = _require(data, "context_budget")
    if not isinstance(budget, dict) or budget.get("max_total_context_bytes", 0) <= 0:
        raise ConfigLoadError("context_budget_invalid")
    # Exclusions must include the frozen benchmark and daily runtime.
    exclusions = _require(data, "exclusions_enforced")
    required = {"benchmark expectations", "daily runtime (/home/source/SpiritOS)"}
    joined = " ".join(exclusions)
    if "benchmark" not in joined or "daily runtime" not in joined:
        raise ConfigLoadError("context_exclusions_incomplete")
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


def load_budget_policy(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    _require(data, "schema_version",
             expected="source-proxy.gate-2j-9-budget-policy/v1")
    _require(data, "decision",
             expected="SEALED_DECISION_4_BUDGETS_AND_LIMITS")
    for group in ("process_budgets", "model_budgets", "tool_budgets", "evidence_budgets"):
        bucket = _require(data, group)
        if not isinstance(bucket, dict) or not bucket:
            raise ConfigLoadError(f"budget_group_empty:{group}")
        for name, spec in bucket.items():
            if not isinstance(spec, dict) or "value" not in spec or "rationale" not in spec:
                raise ConfigLoadError(f"budget_spec_invalid:{group}.{name}")
    # Safety invariants: shell commands and deletes are zero; no silent extension.
    if data["tool_budgets"]["max_shell_commands"]["value"] != 0:
        raise ConfigLoadError("shell_commands_must_be_zero")
    if data["tool_budgets"]["max_deleted_files"]["value"] != 0:
        raise ConfigLoadError("deleted_files_must_be_zero")
    if data.get("no_silent_extension") is not True:
        raise ConfigLoadError("no_silent_extension_required")
    return data
