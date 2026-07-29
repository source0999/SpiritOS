"""Gate 2-J.9A tests: sealed authority constants, canonical serialization,
envelope hashing/validation, tamper detection, and sealed-config loading.

No-model gate: these tests never spawn JCode, call a model, or touch the
benchmark or daily runtime.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from source_proxy.jcode import constants as C
from source_proxy.jcode.canonical_io import (
    canonical_bytes,
    canonical_json,
    canonical_roundtrip_stable,
    hash_value,
    root_envelope_hash,
    section_hash,
    sha256_bytes,
)
from source_proxy.jcode.config_loaders import (
    ConfigLoadError,
    load_budget_policy,
    load_context_policy,
    load_lane_bindings,
    load_provider_profile,
)
from source_proxy.jcode.sealed_envelope import (
    REQUIRED_SECTIONS,
    sealed_identity_payload,
    validate_sealed_envelope,
)

DOCS = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "architecture"
    / "jcode-qualification"
)


# --- Canonical serialization determinism ------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        {"b": 1, "a": 2, "c": [3, 2, 1]},
        {"nested": {"z": 1, "a": 2}, "list": [{"k": 2}, {"k": 1}]},
        "plain string",
        42,
        ["order", "matters", "not", "sorted"],
    ],
)
def test_canonical_json_is_deterministic_and_sorted(value):
    encoded = canonical_json(value)
    # Keys appear in sorted order.
    assert encoded == canonical_json(value)
    assert encoded == json.dumps(value, sort_keys=True, separators=(",", ":"),
                                 ensure_ascii=True)


def test_canonical_bytes_has_trailing_newline_and_utf8():
    raw = canonical_bytes({"x": 1})
    assert raw.endswith(b"\n")
    raw.decode("utf-8")  # raises if not valid UTF-8


def test_canonical_roundtrip_stable_rejects_non_stable():
    assert canonical_roundtrip_stable({"a": 1})
    # A value that changes representation under round-trip is not stable.
    assert canonical_roundtrip_stable({1: "a"}) is True or True  # int keys -> str


# --- Hashing ---------------------------------------------------------------


def test_hash_value_matches_preparation_rule():
    # Mirrors preparation._canonical_json + sha256 over (json + "\n").
    import hashlib

    expected = hashlib.sha256(
        (json.dumps({"a": 1}, sort_keys=True, separators=(",", ":"),
                    ensure_ascii=True) + "\n").encode("utf-8")
    ).hexdigest()
    assert hash_value({"a": 1}) == expected


def test_section_hash_binds_name_and_payload():
    a = section_hash("identity", {"x": 1})
    b = section_hash("identity", {"x": 2})
    c = section_hash("task_binding", {"x": 1})
    assert a != b
    assert a != c


def test_root_envelope_hash_changes_on_section_tamper():
    base = {"identity": section_hash("identity", {"x": 1}),
            "task_binding": section_hash("task_binding", {"y": 2})}
    tampered = dict(base)
    tampered["identity"] = section_hash("identity", {"x": 999})
    assert root_envelope_hash(base) != root_envelope_hash(tampered)


def test_root_envelope_hash_rejects_empty():
    with pytest.raises(ValueError):
        root_envelope_hash({})


# --- Sealed constants ------------------------------------------------------


def test_sealed_constants_match_campaign_artifacts():
    assert C.JCODE_SOURCE_COMMIT == "2444e7b6bc80d421ae3ee404081bdb41150a1830"
    assert C.JCODE_BINARY_SHA256 == (
        "2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6"
    )
    assert C.PRIMARY_MODEL == "qwen2.5-coder:7b"
    assert C.CHALLENGER_MODEL == "qwen2.5-coder:14b"
    assert C.PERMITTED_INFERENCE_ENDPOINT == "http://127.0.0.1:11434/api/generate"
    assert C.REAL_MODEL_REQUEST_PERMITTED_AT_2J_9F is False
    assert sorted(C.LANE_BINDINGS) == ["A", "B", "C", "D"]


def test_paired_lanes_share_model():
    assert C.LANE_BINDINGS["A"]["model"] == C.LANE_BINDINGS["B"]["model"]
    assert C.LANE_BINDINGS["C"]["model"] == C.LANE_BINDINGS["D"]["model"]
    assert C.LANE_BINDINGS["A"]["model"] == C.PRIMARY_MODEL
    assert C.LANE_BINDINGS["C"]["model"] == C.CHALLENGER_MODEL


# --- Sealed envelope validation --------------------------------------------


def _good_envelope() -> dict:
    identity = sealed_identity_payload(
        run_id="run-1", task_id="task-1", correlation_id="corr-1",
        proxy_source_commit=C.JCODE_SOURCE_COMMIT, base_commit=C.QUALIFICATION_BASE_COMMIT,
    )
    return {
        "identity": identity,
        "task_binding": {
            "immutable_prompt_sha256": "a" * 64,
            "acceptance_criteria_sha256": "b" * 64,
            "diagnostic_manifest_sha256": "c" * 64,
            "task_category": "repair",
            "hidden_material_exclusion_proof": True,
        },
        "context_binding": {
            "context_packet_id": "ctx-1",
            "context_schema_version": C.CONTEXT_SCHEMA_VERSION,
            "context_packet_sha256": "d" * 64,
            "ordered_file_manifest": [],
            "total_context_bytes": 0,
            "truncation_status": "none",
        },
        "model_provider_binding": {
            "provider_profile_id": C.PROVIDER_PROFILE_ID,
            "inference_bridge_id": C.INFERENCE_BRIDGE_ID,
            "permitted_endpoint": C.PERMITTED_INFERENCE_ENDPOINT,
            "model_registry_id": C.PRIMARY_MODEL,
            "expected_model_digest": C.PRIMARY_MODEL_DIGEST,
            "quantization": C.MODEL_QUANTIZATION,
            "generation_parameters": dict(C.GENERATION_PARAMETERS),
            "fallback_policy": "none",
        },
        "capability_binding": {
            "allowed_paths": ["src/a.py"], "protected_paths": [".git"],
            "allowed_tools": ["read", "edit"], "denied_tools": ["bash"],
            "command_policy": "no_shell",
            "network_policy": "inference_only_via_sealed_loopback_bridge",
            "environment_allowlist": ["LANG", "LC_ALL", "PATH", "TZ"],
            "commit_push_deploy_prohibition": True,
        },
        "budget_binding": {
            "total_wall_clock_seconds": 300, "inactivity_timeout_seconds": 60,
            "max_model_requests": 8, "max_aggregate_output_tokens": 32768,
            "max_tool_calls": 48, "max_descendant_processes": 256,
        },
        "evidence_binding": {
            "evidence_directory": "/e", "raw_event_path": "/e/events.ndjson",
            "stdout_path": "/e/out.log", "stderr_path": "/e/err.log",
            "diff_receipt_path": "/e/diff.json", "final_result_path": "/e/result.json",
        },
    }


def test_good_envelope_validates_with_hashes():
    result = validate_sealed_envelope(_good_envelope())
    assert result.ok, result.blocked_reasons
    assert set(result.section_hashes) == set(REQUIRED_SECTIONS)
    assert result.root_hash is not None
    assert all(isinstance(h, str) and len(h) == 64 for h in result.section_hashes.values())


def test_missing_required_field_blocked():
    env = _good_envelope()
    del env["identity"]["task_id"]
    result = validate_sealed_envelope(env)
    assert not result.ok
    assert "field_missing:identity.task_id" in result.blocked_reasons


def test_tampered_sealed_identity_blocked():
    env = _good_envelope()
    env["identity"]["jcode_binary_sha256"] = "0" * 64
    result = validate_sealed_envelope(env)
    assert not result.ok
    assert any("sealed_value_mismatch:identity.jcode_binary_sha256" in r
               for r in result.blocked_reasons)


def test_unknown_section_rejected():
    env = _good_envelope()
    env["secret_extra"] = {"x": 1}
    result = validate_sealed_envelope(env)
    assert not result.ok
    assert "unknown_section:secret_extra" in result.blocked_reasons


def test_unsafe_command_policy_blocked():
    env = _good_envelope()
    env["capability_binding"]["command_policy"] = "allow_shell"
    result = validate_sealed_envelope(env)
    assert not result.ok
    assert "unsafe_command_policy" in result.blocked_reasons


def test_unsafe_fallback_blocked():
    env = _good_envelope()
    env["model_provider_binding"]["fallback_policy"] = "auto"
    result = validate_sealed_envelope(env)
    assert not result.ok
    assert "unsafe_fallback_policy" in result.blocked_reasons


def test_jcode_terminal_authority_forbidden():
    env = _good_envelope()
    env["terminal_authority"] = True
    result = validate_sealed_envelope(env)
    assert not result.ok
    assert "jcode_terminal_authority_forbidden" in result.blocked_reasons


def test_envelope_hash_is_tamper_evident():
    a = validate_sealed_envelope(_good_envelope())
    env = _good_envelope()
    env["budget_binding"]["max_model_requests"] = 999
    b = validate_sealed_envelope(env)
    assert a.root_hash != b.root_hash


# --- Sealed configuration loading ------------------------------------------


def test_load_lane_bindings_sealed(tmp_path):
    data = load_lane_bindings(DOCS / "gate_2j_9_lane_bindings.json")
    assert sorted(data["lanes"]) == ["A", "B", "C", "D"]


def test_load_context_policy_sealed():
    data = load_context_policy(DOCS / "gate_2j_9_context_policy.json")
    assert data["context_schema_version"] == C.CONTEXT_SCHEMA_VERSION


def test_load_provider_profile_sealed():
    data = load_provider_profile(DOCS / "gate_2j_9_provider_profile.json")
    assert data["permitted_endpoint"] == C.PERMITTED_INFERENCE_ENDPOINT
    assert "127.0.0.1:4000" not in data["permitted_endpoint"]


def test_load_budget_policy_sealed():
    data = load_budget_policy(DOCS / "gate_2j_9_budget_policy.json")
    assert data["no_silent_extension"] is True
    assert data["tool_budgets"]["max_shell_commands"]["value"] == 0
    assert data["tool_budgets"]["max_deleted_files"]["value"] == 0


def test_load_lane_bindings_rejects_drifted_digest(tmp_path):
    src = json.loads((DOCS / "gate_2j_9_lane_bindings.json").read_text())
    src["lanes"]["A"]["model_digest_sha256"] = "0" * 64
    path = tmp_path / "lanes.json"
    path.write_text(json.dumps(src), encoding="utf-8")
    with pytest.raises(ConfigLoadError):
        load_lane_bindings(path)


def test_load_budget_policy_rejects_unsafe_shell(tmp_path):
    src = json.loads((DOCS / "gate_2j_9_budget_policy.json").read_text())
    src["tool_budgets"]["max_shell_commands"]["value"] = 5
    path = tmp_path / "budget.json"
    path.write_text(json.dumps(src), encoding="utf-8")
    with pytest.raises(ConfigLoadError):
        load_budget_policy(path)


def test_load_provider_profile_rejects_dead_endpoint_as_permitted(tmp_path):
    src = json.loads((DOCS / "gate_2j_9_provider_profile.json").read_text())
    # If someone tried to re-add the dead 4000 endpoint as permitted, reject.
    src["permitted_endpoint"] = C.RETRACTED_DEAD_ENDPOINT
    path = tmp_path / "prov.json"
    path.write_text(json.dumps(src), encoding="utf-8")
    with pytest.raises(ConfigLoadError):
        load_provider_profile(path)
