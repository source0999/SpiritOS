#!/usr/bin/env python3
"""Validate content-addressed R1 terminal evidence and its recovery anchor."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


STATE_SCHEMA = "spiritos-foundation-remediation-r1-state/v1"
RECEIPT_SCHEMA = "spiritos-foundation-remediation-r1-terminal-receipt/v1"
MANIFEST_SCHEMA = "spiritos-foundation-remediation-r1-immutable-evidence-manifest/v1"
PROFILE_RECEIPT_SCHEMA = "spiritos-foundation-remediation-r1-profile-execution-receipt/v1"
PROTECTED_REPORT_SCHEMA = "spiritos-foundation-remediation-r1-protected-head-report/v1"
PRODUCTION_PROVING_RECEIPT_SCHEMA = (
    "spiritos-foundation-remediation-r1-production-proving-receipt/v1"
)
LIFECYCLE_RECEIPT_SCHEMA = "spiritos-foundation-remediation-r1-lifecycle-receipt/v1"
REMEDIATION_ID = "spiritos-foundation-remediation-r1"
TERMINAL_VERDICT = "SPIRITOS_FOUNDATION_REMEDIATION_COMPLETE"
AUTHORITY_VALIDATOR_PATH = "scripts/validate-foundation-remediation-r1-authority.py"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
PARTICIPANT_ROLES = {
    "executor",
    "reviewer",
    "verifier",
    "anti_cheat",
    "evidence_recorder",
}
TERMINAL_EVIDENCE_FIELDS = {
    "source_commit",
    "receipt_path",
    "receipt_sha256",
    "manifest_path",
    "manifest_sha256",
    "tag_name",
    "bundle_path",
    "bundle_sha256_sidecar",
    "restoration_instructions_path",
}
CONTRACT_SCHEMAS = {
    "packages/contracts/schemas/foundation-remediation-r1-profile-execution-receipt.v1.schema.json": PROFILE_RECEIPT_SCHEMA,
    "packages/contracts/schemas/foundation-remediation-r1-terminal-receipt.v1.schema.json": RECEIPT_SCHEMA,
    "packages/contracts/schemas/foundation-remediation-r1-immutable-evidence-manifest.v1.schema.json": MANIFEST_SCHEMA,
}
PATH_HASH_FIELDS = {"path", "sha256"}
MANIFEST_ARTIFACT_REQUIRED_FIELDS = {"path", "sha256", "size_bytes"}
MANIFEST_ARTIFACT_OPTIONAL_FIELDS = {"kind", "claim_ceiling"}
RECEIPT_BINDING_FIELDS = {"path", "sha256"}
PRODUCTION_PROVING_FIELDS = {
    "schema_version",
    "receipt_type",
    "remediation_id",
    "run_mode",
    "terminal_proof_eligible",
    "claim_ceiling",
    "started_at",
    "completed_at",
    "source_commit",
    "expected_runtime_identity",
    "repository_identity",
    "transport",
    "task_prompt",
    "target_plugin_identity",
    "operator_session",
    "runs",
    "run_attestation",
    "undo",
    "reset",
    "clean_rerun",
    "expected_controlled_recovery",
    "http_exchanges",
    "redaction",
    "failures",
    "receipt_sha256",
}
LIFECYCLE_FIELDS = {
    "schema_version",
    "receipt_type",
    "remediation_id",
    "status",
    "terminal_proof_eligible",
    "claim_ceiling",
    "started_at",
    "completed_at",
    "source",
    "build",
    "services",
    "inner_proving",
    "temporary_authority",
    "teardown",
    "redaction",
    "failures",
    "receipt_sha256",
}
PROVING_RUN_REQUIRED_FIELDS = {
    "ordinal",
    "clean_rerun",
    "task_id",
    "orchestrator_run_id",
    "orchestrator_attempt_id",
    "source_commit",
    "task_prompt_sha256",
    "cartographer_proposal",
    "cartographer",
    "selection_preview_id",
    "selection_generation",
    "prompt_packet",
    "target_proposal",
    "context",
    "target_adapter",
    "controlled_recovery",
    "diff_preview",
    "approval",
    "execution_response_sha256",
    "verification_response_sha256",
    "final_readback_response_sha256",
    "task_status",
    "verification_status",
    "real_browser_used",
    "browser_engine",
    "artifact",
    "pre_apply_source_baseline",
    "participants",
    "runtime_boundary",
    "production_proof",
    "approval_final_state",
    "verification_preceded_final_result",
    "http_exchange_ordinals",
}
PROVING_PARTICIPANT_ROLES = {
    "executor": "coding-executor",
    "reviewer": "coding-reviewer",
    "verifier": "coding-verifier",
    "anti_cheat": "coding-anti-cheat",
    "evidence_recorder": "evidence-recorder",
}
EXPECTED_RECOVERY_FIELDS = {
    "failed_provider",
    "failed_model",
    "replacement_provider",
    "replacement_model",
}


class EvidenceValidationError(RuntimeError):
    pass


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def run_git_bytes(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        check=False,
    )


def load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, f"json_unreadable_or_malformed:{path}:{error}"
    if not isinstance(value, dict):
        return None, f"json_not_object:{path}"
    return value, None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def terminal_state(state: dict[str, Any]) -> bool:
    closeout = state.get("closeout")
    return bool(
        state.get("schema") == STATE_SCHEMA
        and state.get("remediation_id") == REMEDIATION_ID
        and state.get("go_eligible") is True
        and "r1_complete" in (state.get("completed_gate_ids") or [])
        and state.get("partial_gate_ids") == []
        and state.get("next_gate_id") in {"r1_complete", "none", None}
        and isinstance(closeout, dict)
        and closeout.get("status") == "complete"
        and closeout.get("verdict") == TERMINAL_VERDICT
    )


def resolve_repo_path(root: Path, value: str) -> Path | None:
    path = (root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    return path


def resolve_any_path(root: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def tracked(root: Path, path: Path) -> bool:
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        return False
    return run_git(root, "ls-files", "--error-unmatch", relative).returncode == 0


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def compact_sha256(value: object) -> str:
    try:
        encoded = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise EvidenceValidationError("receipt_noncanonical_json") from error
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def raw_sha256(value: object, reason: str) -> str:
    if not isinstance(value, str):
        raise EvidenceValidationError(reason)
    candidate = value.removeprefix("sha256:")
    if not HEX64.fullmatch(candidate):
        raise EvidenceValidationError(reason)
    return candidate


def required_mapping(value: object, reason: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceValidationError(reason)
    return value


def required_list(value: object, reason: str) -> list[Any]:
    if not isinstance(value, list):
        raise EvidenceValidationError(reason)
    return value


def required_text(value: object, reason: str) -> str:
    if not nonempty(value):
        raise EvidenceValidationError(reason)
    return str(value)


def exact_fields(value: dict[str, Any], fields: set[str], reason: str) -> None:
    if set(value) != fields:
        raise EvidenceValidationError(reason)


def validate_receipt_self_hash(receipt: dict[str, Any], reason: str) -> None:
    unsigned = dict(receipt)
    recorded = unsigned.pop("receipt_sha256", None)
    if recorded != compact_sha256(unsigned):
        raise EvidenceValidationError(reason)


def load_bound_receipt(
    root: Path,
    binding_value: object,
    *,
    label: str,
) -> tuple[dict[str, Any], Path, str]:
    binding = required_mapping(binding_value, f"{label}_binding_missing")
    exact_fields(binding, RECEIPT_BINDING_FIELDS, f"{label}_binding_fields_invalid")
    relative = required_text(binding.get("path"), f"{label}_path_missing")
    if Path(relative).is_absolute():
        raise EvidenceValidationError(f"{label}_path_not_repository_relative")
    path = resolve_repo_path(root, relative)
    if path is None or not path.is_file() or path.relative_to(root).as_posix() != relative:
        raise EvidenceValidationError(f"{label}_path_invalid")
    digest = raw_sha256(binding.get("sha256"), f"{label}_sha256_invalid")
    if sha256(path) != digest:
        raise EvidenceValidationError(f"{label}_sha256_mismatch")
    receipt, error = load_json(path)
    if error or receipt is None:
        raise EvidenceValidationError(f"{label}_json_invalid")
    return receipt, path, relative


def validate_proving_run_semantics(
    run: object,
    *,
    source_commit: str,
    ordinal: int,
) -> dict[str, Any]:
    value = required_mapping(run, f"production_proving_run_{ordinal}_missing")
    exact_fields(
        value,
        PROVING_RUN_REQUIRED_FIELDS,
        f"production_proving_run_{ordinal}_fields_invalid",
    )
    if (
        value.get("ordinal") != ordinal
        or value.get("clean_rerun") != (ordinal == 2)
        or value.get("source_commit") != source_commit
    ):
        raise EvidenceValidationError(f"production_proving_run_{ordinal}_identity_invalid")
    for field in ("task_id", "orchestrator_run_id", "orchestrator_attempt_id"):
        required_text(value.get(field), f"production_proving_run_{ordinal}_{field}_missing")
    raw_sha256(value.get("task_prompt_sha256"), f"production_proving_run_{ordinal}_prompt_invalid")
    if (
        value.get("task_status") != "completed"
        or value.get("verification_status") != "verified"
        or value.get("real_browser_used") is not True
        or value.get("approval_final_state") != "consumed"
        or value.get("verification_preceded_final_result") is not True
    ):
        raise EvidenceValidationError(f"production_proving_run_{ordinal}_terminal_state_invalid")
    artifact = required_mapping(
        value.get("artifact"),
        f"production_proving_run_{ordinal}_artifact_missing",
    )
    for field in ("artifact_sha256", "result_sha256", "approved_diff_sha256"):
        raw_sha256(
            artifact.get(field),
            f"production_proving_run_{ordinal}_artifact_hash_invalid:{field}",
        )
    approval = required_mapping(
        value.get("approval"),
        f"production_proving_run_{ordinal}_approval_missing",
    )
    if (
        approval.get("approval_id") != artifact.get("approval_id")
        or approval.get("approval_generation") != artifact.get("generation")
    ):
        raise EvidenceValidationError(f"production_proving_run_{ordinal}_approval_mismatch")
    proof = required_mapping(
        value.get("production_proof"),
        f"production_proving_run_{ordinal}_proof_missing",
    )
    if proof.get("terminal_proof_eligible") is not True or proof.get("failures") != []:
        raise EvidenceValidationError(f"production_proving_run_{ordinal}_proof_invalid")
    raw_sha256(proof.get("proof_sha256"), f"production_proving_run_{ordinal}_proof_hash_invalid")
    participants = required_list(
        value.get("participants"),
        f"production_proving_run_{ordinal}_participants_missing",
    )
    if {item.get("role") for item in participants if isinstance(item, dict)} != set(
        PROVING_PARTICIPANT_ROLES.values()
    ):
        raise EvidenceValidationError(f"production_proving_run_{ordinal}_participant_roles_invalid")
    return value


def validate_terminal_production_cross_binding(
    root: Path,
    receipt: dict[str, Any],
    *,
    source_commit: str,
) -> tuple[Path, str, Path, str]:
    proving, proving_path, proving_relative = load_bound_receipt(
        root,
        receipt.get("production_proving_receipt"),
        label="production_proving_receipt",
    )
    lifecycle, lifecycle_path, lifecycle_relative = load_bound_receipt(
        root,
        receipt.get("lifecycle_receipt"),
        label="lifecycle_receipt",
    )
    if proving_relative == lifecycle_relative:
        raise EvidenceValidationError("proving_lifecycle_receipt_path_reused")

    exact_fields(proving, PRODUCTION_PROVING_FIELDS, "production_proving_receipt_fields_invalid")
    validate_receipt_self_hash(proving, "production_proving_receipt_self_hash_mismatch")
    if (
        proving.get("schema_version") != PRODUCTION_PROVING_RECEIPT_SCHEMA
        or proving.get("receipt_type") != "foundation_r1_black_box_production_proving"
        or proving.get("remediation_id") != REMEDIATION_ID
        or proving.get("run_mode") != "production_http"
        or proving.get("terminal_proof_eligible") is not True
        or proving.get("source_commit") != source_commit
        or proving.get("failures") != []
        or not parse_timestamp(proving.get("started_at"))
        or not parse_timestamp(proving.get("completed_at"))
    ):
        raise EvidenceValidationError("production_proving_receipt_identity_invalid")
    if datetime.fromisoformat(str(proving["completed_at"]).replace("Z", "+00:00")) < datetime.fromisoformat(
        str(proving["started_at"]).replace("Z", "+00:00")
    ):
        raise EvidenceValidationError("production_proving_receipt_timestamp_order_invalid")
    claim_ceiling = required_text(proving.get("claim_ceiling"), "production_proving_claim_missing")
    if claim_ceiling != "recovered_via_declared_fallback_only":
        raise EvidenceValidationError("production_proving_claim_invalid")

    expected_runtime = required_mapping(
        proving.get("expected_runtime_identity"),
        "production_proving_runtime_identity_missing",
    )
    repository = required_mapping(
        proving.get("repository_identity"),
        "production_proving_repository_identity_missing",
    )
    target_identity = required_mapping(
        proving.get("target_plugin_identity"),
        "production_proving_target_identity_missing",
    )
    if (
        expected_runtime.get("source_head") != source_commit
        or target_identity.get("source_head") != source_commit
        or repository.get("repository") != expected_runtime.get("repository_id")
        or target_identity.get("repository_id") != expected_runtime.get("repository_id")
        or target_identity.get("worktree_id") != expected_runtime.get("worktree_id")
        or repository.get("worktree") != repository.get("root")
    ):
        raise EvidenceValidationError("production_proving_runtime_identity_mismatch")
    transport = required_mapping(proving.get("transport"), "production_proving_transport_missing")
    if (
        transport.get("kind") != "production_http"
        or transport.get("origins_distinct") is not True
        or transport.get("redirects_allowed") is not False
        or transport.get("services_started_by_harness") is not False
        or transport.get("application_modules_imported") is not False
        or transport.get("test_modules_imported") is not False
        or transport.get("callback_transport_allowed") is not False
    ):
        raise EvidenceValidationError("production_proving_transport_invalid")
    proving_redaction = required_mapping(
        proving.get("redaction"),
        "production_proving_redaction_missing",
    )
    if proving_redaction.get("status") != "passed":
        raise EvidenceValidationError("production_proving_redaction_invalid")

    runs = required_list(proving.get("runs"), "production_proving_runs_missing")
    if len(runs) != 2:
        raise EvidenceValidationError("production_proving_run_count_invalid")
    first = validate_proving_run_semantics(runs[0], source_commit=source_commit, ordinal=1)
    second = validate_proving_run_semantics(runs[1], source_commit=source_commit, ordinal=2)
    recovery_expectation = required_mapping(
        proving.get("expected_controlled_recovery"),
        "production_proving_recovery_expectation_missing",
    )
    exact_fields(
        recovery_expectation,
        EXPECTED_RECOVERY_FIELDS,
        "production_proving_recovery_expectation_fields_invalid",
    )
    recovery_ids: set[str] = set()
    for ordinal, run in enumerate((first, second), start=1):
        recovery = required_mapping(
            run.get("controlled_recovery"),
            f"production_proving_run_{ordinal}_recovery_missing",
        )
        failure = required_mapping(
            recovery.get("failure"),
            f"production_proving_run_{ordinal}_recovery_failure_missing",
        )
        replacement = required_mapping(
            recovery.get("replacement"),
            f"production_proving_run_{ordinal}_recovery_replacement_missing",
        )
        adapter = required_mapping(
            run.get("target_adapter"),
            f"production_proving_run_{ordinal}_adapter_missing",
        )
        run_proof = required_mapping(
            run.get("production_proof"),
            f"production_proving_run_{ordinal}_proof_missing",
        )
        recovery_ids.add(
            required_text(
                recovery.get("recovery_id"),
                f"production_proving_run_{ordinal}_recovery_id_missing",
            )
        )
        if (
            recovery.get("decision") != "fallback"
            or recovery.get("proof_eligible") is not True
            or recovery.get("claim_ceiling_impact") != claim_ceiling
            or run_proof.get("claim_ceiling") != claim_ceiling
            or failure.get("provider") != recovery_expectation.get("failed_provider")
            or failure.get("model") != recovery_expectation.get("failed_model")
            or replacement.get("provider") != recovery_expectation.get("replacement_provider")
            or replacement.get("model") != recovery_expectation.get("replacement_model")
            or adapter.get("provider") != replacement.get("provider")
            or adapter.get("model") != replacement.get("model")
        ):
            raise EvidenceValidationError(f"production_proving_run_{ordinal}_recovery_mismatch")
        required_text(
            failure.get("invocation_id"),
            f"production_proving_run_{ordinal}_recovery_failure_invocation_missing",
        )
        required_text(
            replacement.get("invocation_id"),
            f"production_proving_run_{ordinal}_recovery_replacement_invocation_missing",
        )
        required_text(
            replacement.get("output_id"),
            f"production_proving_run_{ordinal}_recovery_replacement_output_missing",
        )
    if len(recovery_ids) != 2:
        raise EvidenceValidationError("production_proving_clean_rerun_recovery_identity_reused")
    if any(
        first.get(field) == second.get(field)
        for field in ("task_id", "orchestrator_run_id", "orchestrator_attempt_id")
    ) or (
        first.get("approval", {}).get("approval_id")
        == second.get("approval", {}).get("approval_id")
    ) or (
        first.get("artifact", {}).get("artifact_sha256")
        == second.get("artifact", {}).get("artifact_sha256")
    ):
        raise EvidenceValidationError("production_proving_clean_rerun_identity_reused")
    task_prompt = required_mapping(proving.get("task_prompt"), "production_proving_task_prompt_missing")
    if raw_sha256(task_prompt.get("sha256"), "production_proving_task_prompt_invalid") != raw_sha256(
        second.get("task_prompt_sha256"),
        "production_proving_second_prompt_invalid",
    ):
        raise EvidenceValidationError("production_proving_second_prompt_mismatch")

    undo = required_mapping(proving.get("undo"), "production_proving_undo_missing")
    reset = required_mapping(proving.get("reset"), "production_proving_reset_missing")
    rerun = required_mapping(proving.get("clean_rerun"), "production_proving_clean_rerun_missing")
    if (
        undo.get("original_task_id") != first.get("task_id")
        or undo.get("source_baseline_restored") is not True
        or undo.get("fixture_absent") is not True
        or undo.get("filesystem_verified") is not True
        or undo.get("untouched_scope_assertion") is not True
        or undo.get("final_truth_status") != "UNDO_FILESYSTEM_VERIFIED"
        or reset.get("status") != "reset_verified"
        or reset.get("clean_verified") is not True
        or reset.get("source_baseline_verified") is not True
        or reset.get("source_head") != source_commit
        or reset.get("source_baseline_tracked_paths") != []
        or reset.get("removed_paths") != []
    ):
        raise EvidenceValidationError("production_proving_undo_reset_invalid")
    for field in (
        "completed",
        "source_commit_unchanged",
        "source_baseline_verified",
        "fixture_absent_before_each_run",
        "reset_was_idempotent_after_undo",
        "repository_identity_unchanged",
        "task_id_distinct",
        "run_id_distinct",
        "approval_id_distinct",
        "artifact_identity_distinct",
    ):
        if rerun.get(field) is not True:
            raise EvidenceValidationError("production_proving_clean_rerun_invalid")

    operator = required_mapping(proving.get("operator_session"), "production_proving_operator_missing")
    attestation = required_mapping(
        proving.get("run_attestation"),
        "production_proving_attestation_missing",
    )
    exchanges = required_list(proving.get("http_exchanges"), "production_proving_exchanges_missing")
    binding = {
        "schema_version": "spiritos-production-http-run-binding/v1",
        "operator_identity_sha256": operator.get("operator_identity_sha256"),
        "revocation_response_sha256": operator.get("revocation_response_sha256"),
        "retired_session_probe_response_sha256": operator.get(
            "retired_session_probe_response_sha256"
        ),
        "source_head": source_commit,
        "first_run_summary_sha256": compact_sha256(first),
        "second_run_summary_sha256": compact_sha256(second),
        "undo_summary_sha256": compact_sha256(undo),
        "reset_summary_sha256": compact_sha256(reset),
    }
    if (
        attestation.get("schema_version")
        != "spiritos-production-http-run-attestation/v1"
        or attestation.get("transcript_sha256") != compact_sha256(exchanges)
        or attestation.get("binding_sha256") != compact_sha256(binding)
        or attestation.get("exchange_count") != len(exchanges)
        or attestation.get("client_verified") is not True
        or operator.get("authenticated") is not True
        or operator.get("revoked") is not True
        or operator.get("retired_session_status") != "revoked"
        or operator.get("cookie_jar_cleared") is not True
    ):
        raise EvidenceValidationError("production_proving_attestation_invalid")

    exact_fields(lifecycle, LIFECYCLE_FIELDS, "lifecycle_receipt_fields_invalid")
    validate_receipt_self_hash(lifecycle, "lifecycle_receipt_self_hash_mismatch")
    if (
        lifecycle.get("schema_version") != LIFECYCLE_RECEIPT_SCHEMA
        or lifecycle.get("receipt_type") != "foundation_r1_clean_production_service_lifecycle"
        or lifecycle.get("remediation_id") != REMEDIATION_ID
        or lifecycle.get("status") != "passed"
        or lifecycle.get("terminal_proof_eligible") is not False
        or lifecycle.get("claim_ceiling")
        != "subordinate_clean_checkout_build_service_and_revocation_proof_only"
        or lifecycle.get("failures") != []
        or not parse_timestamp(lifecycle.get("started_at"))
        or not parse_timestamp(lifecycle.get("completed_at"))
    ):
        raise EvidenceValidationError("lifecycle_receipt_identity_invalid")
    if datetime.fromisoformat(str(lifecycle["completed_at"]).replace("Z", "+00:00")) < datetime.fromisoformat(
        str(lifecycle["started_at"]).replace("Z", "+00:00")
    ):
        raise EvidenceValidationError("lifecycle_receipt_timestamp_order_invalid")
    lifecycle_redaction = required_mapping(
        lifecycle.get("redaction"),
        "lifecycle_redaction_missing",
    )
    if lifecycle_redaction.get("status") != "passed":
        raise EvidenceValidationError("lifecycle_redaction_invalid")
    embedded = required_mapping(lifecycle.get("inner_proving"), "lifecycle_inner_proving_missing")
    embedded_receipt = dict(embedded)
    execution = required_mapping(
        embedded_receipt.pop("execution", None),
        "lifecycle_inner_execution_missing",
    )
    published_after_teardown = embedded_receipt.pop(
        "published_only_after_lifecycle_teardown",
        None,
    )
    if published_after_teardown is not True:
        raise EvidenceValidationError("lifecycle_inner_receipt_publication_order_invalid")
    if embedded_receipt != proving:
        raise EvidenceValidationError("lifecycle_inner_proving_receipt_mismatch")
    if execution.get("receipt_sha256") != proving.get("receipt_sha256"):
        raise EvidenceValidationError("lifecycle_inner_execution_hash_mismatch")
    lifecycle_source = required_mapping(lifecycle.get("source"), "lifecycle_source_missing")
    if (
        lifecycle_source.get("source_head") != source_commit
        or lifecycle_source.get("repository_id") != expected_runtime.get("repository_id")
        or lifecycle_source.get("worktree_id") != expected_runtime.get("worktree_id")
        or lifecycle_source.get("worktree_root") != repository.get("root")
        or lifecycle_source.get("registered_linked_worktree") is not True
        or lifecycle_source.get("clean_before_build") is not True
    ):
        raise EvidenceValidationError("lifecycle_source_identity_mismatch")
    services = required_list(lifecycle.get("services"), "lifecycle_services_missing")
    if len(services) != 3 or {item.get("name") for item in services if isinstance(item, dict)} != {
        "source_proxy",
        "next",
        "next_tls",
    }:
        raise EvidenceValidationError("lifecycle_service_set_invalid")
    for service_value in services:
        service = required_mapping(service_value, "lifecycle_service_invalid")
        for field in (
            "cwd_bound_to_proof_worktree",
            "loopback_bound",
            "stopped",
            "process_absent",
            "process_group_absent",
            "process_session_absent",
            "descendant_processes_absent",
            "port_closed",
        ):
            if service.get(field) is not True:
                raise EvidenceValidationError("lifecycle_service_teardown_invalid")
        if service.get("raw_pid_recorded") is not False or service.get("raw_port_recorded") is not False:
            raise EvidenceValidationError("lifecycle_service_redaction_invalid")
        raw_sha256(
            service.get("listener_identity_sha256"),
            "lifecycle_service_listener_identity_invalid",
        )
    teardown = required_mapping(lifecycle.get("teardown"), "lifecycle_teardown_missing")
    if teardown.get("failures") != []:
        raise EvidenceValidationError("lifecycle_teardown_failures_present")
    for field in (
        "dependency_link_removed",
        "next_build_removed",
        "backup_state_removed",
        "runtime_receipts_removed",
        "tracked_status_clean",
        "ignored_status_restored",
        "source_head_unchanged",
        "branch_unchanged",
        "repository_identity_unchanged",
        "linked_worktree_registration_unchanged",
        "index_visibility_unchanged",
        "all_services_stopped",
        "all_service_processes_absent",
        "all_service_ports_closed",
        "temporary_state_removed",
        "operator_session_revoked",
        "temporary_approval_authority_inactive",
    ):
        if teardown.get(field) is not True:
            raise EvidenceValidationError("lifecycle_teardown_invalid")
    temporary = required_mapping(
        lifecycle.get("temporary_authority"),
        "lifecycle_temporary_authority_missing",
    )
    if (
        temporary.get("state_root_removed") is not True
        or temporary.get("shared_signing_key_preexisted") is not True
        or temporary.get("shared_signing_key_unchanged") is not True
    ):
        raise EvidenceValidationError("lifecycle_temporary_authority_invalid")

    artifact = required_mapping(second.get("artifact"), "terminal_proving_artifact_missing")
    approval = required_mapping(second.get("approval"), "terminal_proving_approval_missing")
    proof = required_mapping(second.get("production_proof"), "terminal_proving_proof_missing")
    recovery = required_mapping(second.get("controlled_recovery"), "terminal_proving_recovery_missing")
    context = required_mapping(second.get("context"), "terminal_proving_context_missing")
    prompt = required_mapping(second.get("prompt_packet"), "terminal_proving_prompt_missing")
    cartographer = required_mapping(
        second.get("cartographer_proposal"),
        "terminal_proving_cartographer_missing",
    )
    expected = {
        "task_id": second.get("task_id"),
        "orchestrator_run_id": second.get("orchestrator_run_id"),
        "orchestrator_attempt_id": second.get("orchestrator_attempt_id"),
        "artifact_sha256": raw_sha256(artifact.get("artifact_sha256"), "terminal_artifact_hash_invalid"),
        "applied_diff_sha256": raw_sha256(
            artifact.get("approved_diff_sha256"),
            "terminal_diff_hash_invalid",
        ),
        "result_sha256": raw_sha256(artifact.get("result_sha256"), "terminal_result_hash_invalid"),
    }
    for field, expected_value in expected.items():
        if receipt.get(field) != expected_value:
            raise EvidenceValidationError(f"terminal_proving_run_mismatch:{field}")
    if cartographer.get("proposed_files") != [receipt.get("target")]:
        raise EvidenceValidationError("terminal_proving_target_mismatch")
    target = required_mapping(receipt.get("target_plugin_identity"), "terminal_target_identity_missing")
    if set(target) != {"plugin_id", "source_head"}:
        raise EvidenceValidationError("terminal_target_identity_fields_invalid")
    if target.get("plugin_id") != target_identity.get("plugin_id") or target.get("source_head") != source_commit:
        raise EvidenceValidationError("terminal_proving_plugin_identity_mismatch")
    prompt_identity = required_mapping(receipt.get("prompt_identity"), "terminal_prompt_identity_missing")
    if (
        prompt_identity.get("id") != prompt.get("selected_prompt_id")
        or prompt_identity.get("id") != target_identity.get("selected_prompt_id")
        or prompt_identity.get("sha256")
        != raw_sha256(second.get("task_prompt_sha256"), "terminal_prompt_hash_invalid")
    ):
        raise EvidenceValidationError("terminal_proving_prompt_identity_mismatch")
    context_identity = required_mapping(receipt.get("context_identity"), "terminal_context_identity_missing")
    if (
        context_identity.get("id") != target_identity.get("selected_context_id")
        or context_identity.get("sha256")
        != raw_sha256(context.get("context_hash"), "terminal_context_hash_invalid")
    ):
        raise EvidenceValidationError("terminal_proving_context_identity_mismatch")
    terminal_approval = required_mapping(receipt.get("approval"), "terminal_approval_missing")
    if (
        terminal_approval.get("approval_id") != approval.get("approval_id")
        or terminal_approval.get("generation") != approval.get("approval_generation")
        or terminal_approval.get("state") != second.get("approval_final_state")
        or terminal_approval.get("artifact_sha256") != expected["artifact_sha256"]
        or terminal_approval.get("orchestrator_run_id") != second.get("orchestrator_run_id")
    ):
        raise EvidenceValidationError("terminal_proving_approval_mismatch")
    terminal_proof = required_mapping(receipt.get("production_proof"), "terminal_production_proof_missing")
    expected_proof = {
        "proof_sha256": raw_sha256(proof.get("proof_sha256"), "terminal_proof_hash_invalid"),
        "terminal_proof_eligible": True,
        "claim_ceiling": proof.get("claim_ceiling"),
        "recovery_id": recovery.get("recovery_id"),
    }
    if terminal_proof != expected_proof:
        raise EvidenceValidationError("terminal_production_proof_mismatch")
    if (
        receipt.get("claim_ceiling") != expected_proof["claim_ceiling"]
        or proving.get("claim_ceiling") != expected_proof["claim_ceiling"]
        or recovery.get("claim_ceiling_impact") != expected_proof["claim_ceiling"]
        or recovery.get("proof_eligible") is not True
    ):
        raise EvidenceValidationError("terminal_production_claim_mismatch")
    participants = {
        item.get("role"): item
        for item in required_list(second.get("participants"), "terminal_proving_participants_missing")
        if isinstance(item, dict)
    }
    terminal_participants = required_mapping(receipt.get("participants"), "terminal_participants_missing")
    for role, proving_role in PROVING_PARTICIPANT_ROLES.items():
        record = required_mapping(terminal_participants.get(role), f"terminal_participant_{role}_missing")
        observed = required_mapping(participants.get(proving_role), f"terminal_proving_participant_{role}_missing")
        expected_record = {
            "status": "succeeded" if role == "executor" else "passed",
            "invocation_id": observed.get("invocation_id"),
            "output_id": observed.get("output_id"),
            "output_sha256": raw_sha256(
                observed.get("output_sha256"),
                f"terminal_participant_output_hash_invalid:{role}",
            ),
            "consumer_acknowledgement_id": observed.get("consumer_acknowledgement_id"),
            "artifact_sha256": expected["artifact_sha256"],
        }
        if record != expected_record:
            raise EvidenceValidationError(f"terminal_proving_participant_mismatch:{role}")
    terminal_repository = required_mapping(receipt.get("repository_identity"), "terminal_repository_missing")
    if terminal_repository.get("repository_id") != expected_runtime.get("repository_id"):
        raise EvidenceValidationError("terminal_proving_repository_mismatch")
    build = required_mapping(lifecycle.get("build"), "lifecycle_build_missing")
    next_build = required_mapping(build.get("next"), "lifecycle_next_build_missing")
    backend_build = required_mapping(build.get("source_proxy"), "lifecycle_backend_build_missing")
    if receipt.get("shell_build_identity", {}).get("build_id") != next_build.get("build_id_sha256"):
        raise EvidenceValidationError("terminal_shell_build_mismatch")
    if receipt.get("backend_build_identity", {}).get("build_id") != backend_build.get("source_tree"):
        raise EvidenceValidationError("terminal_backend_build_mismatch")
    return proving_path, proving_relative, lifecycle_path, lifecycle_relative


def validate_exact_fields(
    value: object,
    required: set[str],
    optional: set[str],
    label: str,
    failures: list[str],
) -> bool:
    if not isinstance(value, dict):
        failures.append(f"{label}_not_object")
        return False
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required - optional)
    if missing:
        failures.append(f"{label}_fields_missing:" + ",".join(missing))
    if unknown:
        failures.append(f"{label}_fields_unknown:" + ",".join(unknown))
    return not missing and not unknown


def parse_timestamp(value: object) -> bool:
    if not nonempty(value):
        return False
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def evidence_set_hash(entries: list[tuple[str, str]]) -> str:
    canonical = "".join(f"{digest}  {path}\n" for digest, path in sorted(entries))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def git_blob_sha256(root: Path, ref: str, relative: str) -> str | None:
    shown = run_git_bytes(root, "show", f"{ref}:{relative}")
    if shown.returncode != 0:
        return None
    return hashlib.sha256(shown.stdout).hexdigest()


def validate_tagged_file(
    root: Path,
    tag: object,
    path: Path,
    digest: str,
    label: str,
    failures: list[str],
) -> None:
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        failures.append(f"{label}_outside_repository")
        return
    if not tracked(root, path):
        failures.append(f"{label}_untracked:{relative}")
    if not isinstance(tag, str) or not tag:
        failures.append(f"{label}_terminal_tag_missing:{relative}")
    elif git_blob_sha256(root, tag, relative) != digest:
        failures.append(f"{label}_not_bound_to_terminal_tag:{relative}")


def validate_contract_schemas(
    root: Path,
    source_commit: object,
    tag: object,
    failures: list[str],
) -> None:
    for relative, expected_schema in CONTRACT_SCHEMAS.items():
        path = root / relative
        payload, error = load_json(path)
        if error:
            failures.append(f"evidence_contract_schema_invalid:{relative}")
            continue
        assert payload is not None
        schema_property = payload.get("properties")
        schema_value = schema_property.get("schema") if isinstance(schema_property, dict) else None
        if (
            payload.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
            or payload.get("additionalProperties") is not False
            or not isinstance(schema_value, dict)
            or schema_value.get("const") != expected_schema
        ):
            failures.append(f"evidence_contract_schema_identity_mismatch:{relative}")
        digest = sha256(path)
        validate_tagged_file(root, tag, path, digest, "evidence_contract_schema", failures)
        if not isinstance(source_commit, str) or git_blob_sha256(root, source_commit, relative) != digest:
            failures.append(f"evidence_contract_schema_not_bound_to_source:{relative}")


def validate_authority_binding(
    root: Path,
    binding: object,
    evidence: dict[str, Any],
    failures: list[str],
) -> None:
    if not isinstance(binding, dict):
        failures.append("receipt_authority_validation_missing")
        return
    required = {
        "source_commit",
        "tag_name",
        "validator_path",
        "validator_sha256",
        "artifact_path",
        "artifact_sha256",
        "result",
        "passed",
    }
    missing = sorted(required - set(binding))
    if missing:
        failures.append("receipt_authority_validation_fields_missing:" + ",".join(missing))
    source = evidence.get("source_commit")
    tag = evidence.get("tag_name")
    if binding.get("source_commit") != source:
        failures.append("receipt_authority_validation_source_mismatch")
    if binding.get("tag_name") != tag:
        failures.append("receipt_authority_validation_tag_mismatch")
    if binding.get("result") != "pass" or binding.get("passed") is not True:
        failures.append("receipt_authority_validation_not_passed")
    if binding.get("validator_path") != AUTHORITY_VALIDATOR_PATH:
        failures.append("receipt_authority_validator_path_mismatch")
    validator_hash = binding.get("validator_sha256")
    if not isinstance(validator_hash, str) or not HEX64.fullmatch(validator_hash):
        failures.append("receipt_authority_validator_hash_invalid")
    elif not isinstance(source, str) or git_blob_sha256(root, source, AUTHORITY_VALIDATOR_PATH) != validator_hash:
        failures.append("receipt_authority_validator_not_bound_to_source")
    elif not isinstance(tag, str) or git_blob_sha256(root, tag, AUTHORITY_VALIDATOR_PATH) != validator_hash:
        failures.append("receipt_authority_validator_not_bound_to_tag")

    artifact_value = binding.get("artifact_path")
    artifact_hash = binding.get("artifact_sha256")
    artifact = resolve_repo_path(root, artifact_value) if isinstance(artifact_value, str) else None
    if artifact is None or not artifact.is_file():
        failures.append("receipt_authority_validation_artifact_missing")
        return
    if not tracked(root, artifact):
        failures.append("receipt_authority_validation_artifact_untracked")
    if not isinstance(artifact_hash, str) or not HEX64.fullmatch(artifact_hash):
        failures.append("receipt_authority_validation_artifact_hash_invalid")
    elif sha256(artifact) != artifact_hash:
        failures.append("receipt_authority_validation_artifact_hash_mismatch")
    relative = artifact.relative_to(root).as_posix()
    if isinstance(tag, str) and git_blob_sha256(root, tag, relative) != sha256(artifact):
        failures.append("receipt_authority_validation_artifact_not_bound_to_tag")


def validate_receipt(
    root: Path,
    receipt: dict[str, Any],
    state: dict[str, Any],
    evidence: dict[str, Any],
    failures: list[str],
) -> None:
    source_commit = evidence.get("source_commit")
    required = {
        "schema",
        "remediation_id",
        "verdict",
        "source_commit",
        "repository_identity",
        "protected_heads",
        "shell_build_identity",
        "backend_build_identity",
        "target_plugin_identity",
        "prompt_identity",
        "context_identity",
        "task_id",
        "orchestrator_run_id",
        "orchestrator_attempt_id",
        "target",
        "participants",
        "approval",
        "artifact_sha256",
        "applied_diff_sha256",
        "result_sha256",
        "production_proof",
        "production_proving_receipt",
        "lifecycle_receipt",
        "reviewer_result",
        "verifier_result",
        "anti_cheat_result",
        "authority_validation",
        "evidence_hash",
        "generated_at",
        "redaction_verdict",
        "claim_ceiling",
    }
    missing = sorted(required - set(receipt))
    unknown = sorted(set(receipt) - required)
    if missing:
        failures.append("receipt_fields_missing:" + ",".join(missing))
    if unknown:
        failures.append("receipt_fields_unknown:" + ",".join(unknown))
    if receipt.get("schema") != RECEIPT_SCHEMA:
        failures.append("receipt_schema_mismatch")
    if receipt.get("remediation_id") != REMEDIATION_ID:
        failures.append("receipt_remediation_id_mismatch")
    if receipt.get("verdict") != TERMINAL_VERDICT:
        failures.append("receipt_verdict_mismatch")
    if receipt.get("source_commit") != source_commit or not isinstance(source_commit, str) or not HEX40.fullmatch(source_commit):
        failures.append("receipt_source_commit_mismatch")

    repository = receipt.get("repository_identity")
    if not isinstance(repository, dict):
        failures.append("receipt_repository_identity_missing")
    else:
        for field in ("repository_id", "worktree_id", "worktree_realpath"):
            if not nonempty(repository.get(field)):
                failures.append(f"receipt_repository_identity_missing:{field}")
        worktree = repository.get("worktree_realpath")
        if isinstance(worktree, str) and Path(worktree).resolve() != root:
            failures.append("receipt_worktree_identity_mismatch")

    if receipt.get("protected_heads") != state.get("protected_heads"):
        failures.append("receipt_protected_heads_mismatch")
    for field in ("shell_build_identity", "backend_build_identity"):
        identity = receipt.get(field)
        if not isinstance(identity, dict) or not nonempty(identity.get("build_id")):
            failures.append(f"receipt_build_identity_invalid:{field}")
        elif identity.get("source_commit") != source_commit:
            failures.append(f"receipt_build_source_mismatch:{field}")

    target = receipt.get("target_plugin_identity")
    if not isinstance(target, dict) or not nonempty(target.get("plugin_id")):
        failures.append("receipt_target_plugin_identity_invalid")
    elif target.get("source_head") != source_commit:
        failures.append("receipt_target_plugin_source_mismatch")
    for field in ("prompt_identity", "context_identity"):
        identity = receipt.get(field)
        if not isinstance(identity, dict) or not nonempty(identity.get("id")):
            failures.append(f"receipt_identity_invalid:{field}")
        elif not isinstance(identity.get("sha256"), str) or not HEX64.fullmatch(identity["sha256"]):
            failures.append(f"receipt_identity_hash_invalid:{field}")
    for field in ("task_id", "orchestrator_run_id", "orchestrator_attempt_id", "target"):
        if not nonempty(receipt.get(field)):
            failures.append(f"receipt_{field}_missing")

    participants = receipt.get("participants")
    if not isinstance(participants, dict) or set(participants) != PARTICIPANT_ROLES:
        failures.append("receipt_participant_roles_mismatch")
    else:
        invocation_ids: set[str] = set()
        output_ids: set[str] = set()
        acknowledgement_ids: set[str] = set()
        artifact_hashes: set[str] = set()
        for role, record in participants.items():
            if not isinstance(record, dict):
                failures.append(f"receipt_participant_record_invalid:{role}")
                continue
            if record.get("status") not in {"passed", "succeeded"}:
                failures.append(f"receipt_participant_not_passed:{role}")
            for field, target_set in (
                ("invocation_id", invocation_ids),
                ("output_id", output_ids),
                ("consumer_acknowledgement_id", acknowledgement_ids),
            ):
                value = record.get(field)
                if not nonempty(value):
                    failures.append(f"receipt_participant_field_missing:{role}:{field}")
                else:
                    target_set.add(str(value))
            try:
                raw_sha256(
                    record.get("output_sha256"),
                    f"receipt_participant_output_hash_invalid:{role}",
                )
            except EvidenceValidationError as error:
                failures.append(str(error))
            artifact = record.get("artifact_sha256")
            if not isinstance(artifact, str) or not HEX64.fullmatch(artifact):
                failures.append(f"receipt_participant_artifact_invalid:{role}")
            else:
                artifact_hashes.add(artifact)
        if len(invocation_ids) != len(PARTICIPANT_ROLES):
            failures.append("receipt_participant_invocation_ids_not_unique")
        if len(output_ids) != len(PARTICIPANT_ROLES):
            failures.append("receipt_participant_output_ids_not_unique")
        if len(acknowledgement_ids) != len(PARTICIPANT_ROLES):
            failures.append("receipt_participant_acknowledgement_ids_not_unique")
        if len(artifact_hashes) != 1:
            failures.append("receipt_participants_not_bound_to_one_artifact")
        elif receipt.get("artifact_sha256") not in artifact_hashes:
            failures.append("receipt_participant_artifact_result_mismatch")

    approval = receipt.get("approval")
    if not isinstance(approval, dict) or not str(approval.get("approval_id") or "").startswith("apr_"):
        failures.append("receipt_approval_invalid")
    elif not isinstance(approval.get("generation"), int) or approval["generation"] < 1:
        failures.append("receipt_approval_generation_invalid")
    elif approval.get("state") != "consumed":
        failures.append("receipt_approval_state_invalid")
    elif approval.get("artifact_sha256") != receipt.get("artifact_sha256"):
        failures.append("receipt_approval_artifact_mismatch")
    elif approval.get("orchestrator_run_id") != receipt.get("orchestrator_run_id"):
        failures.append("receipt_approval_orchestrator_mismatch")
    for field in ("artifact_sha256", "applied_diff_sha256", "result_sha256", "evidence_hash"):
        value = receipt.get(field)
        if not isinstance(value, str) or not HEX64.fullmatch(value):
            failures.append(f"receipt_hash_invalid:{field}")

    production_proof = receipt.get("production_proof")
    if not isinstance(production_proof, dict):
        failures.append("receipt_production_proof_missing")
    else:
        expected_fields = {
            "proof_sha256",
            "terminal_proof_eligible",
            "claim_ceiling",
            "recovery_id",
        }
        if set(production_proof) != expected_fields:
            failures.append("receipt_production_proof_fields_invalid")
        try:
            raw_sha256(
                production_proof.get("proof_sha256"),
                "receipt_production_proof_hash_invalid",
            )
        except EvidenceValidationError as error:
            failures.append(str(error))
        if production_proof.get("terminal_proof_eligible") is not True:
            failures.append("receipt_production_proof_not_terminal")
        if not nonempty(production_proof.get("recovery_id")):
            failures.append("receipt_production_proof_recovery_missing")

    result_to_role = {
        "reviewer_result": "reviewer",
        "verifier_result": "verifier",
        "anti_cheat_result": "anti_cheat",
    }
    for field, role in result_to_role.items():
        result = receipt.get(field)
        if not isinstance(result, dict) or result.get("status") not in {"passed", "succeeded"}:
            failures.append(f"receipt_result_invalid:{field}")
        elif isinstance(participants, dict) and isinstance(participants.get(role), dict):
            if result.get("invocation_id") != participants[role].get("invocation_id"):
                failures.append(f"receipt_result_invocation_mismatch:{field}")

    if not parse_timestamp(receipt.get("generated_at")):
        failures.append("receipt_generated_at_invalid")
    redaction = receipt.get("redaction_verdict")
    if not isinstance(redaction, dict) or redaction.get("verdict") != "passed" or not nonempty(redaction.get("scanner")):
        failures.append("receipt_redaction_verdict_invalid")
    claim_ceiling = receipt.get("claim_ceiling")
    if not nonempty(claim_ceiling) or str(claim_ceiling).lower() in {"unbounded", "go"}:
        failures.append("receipt_claim_ceiling_invalid")
    elif isinstance(production_proof, dict) and production_proof.get("claim_ceiling") != claim_ceiling:
        failures.append("receipt_production_proof_claim_mismatch")
    if isinstance(source_commit, str) and HEX40.fullmatch(source_commit):
        try:
            validate_terminal_production_cross_binding(
                root,
                receipt,
                source_commit=source_commit,
            )
        except EvidenceValidationError as error:
            failures.append(f"terminal_production_cross_binding_invalid:{error}")
    validate_authority_binding(root, receipt.get("authority_validation"), evidence, failures)


def validate_manifest(
    root: Path,
    manifest: dict[str, Any],
    evidence: dict[str, Any],
    receipt: dict[str, Any],
    receipt_path: Path,
    manifest_path: Path,
    failures: list[str],
) -> None:
    required = {
        "schema",
        "remediation_id",
        "source_commit",
        "tag_name",
        "bundle_name",
        "restoration_instructions",
        "protected_heads_report",
        "receipt",
        "production_proving_receipt",
        "lifecycle_receipt",
        "artifacts",
        "evidence_hash",
        "generated_at",
    }
    missing = sorted(required - set(manifest))
    unknown = sorted(set(manifest) - required)
    if missing:
        failures.append("manifest_fields_missing:" + ",".join(missing))
    if unknown:
        failures.append("manifest_fields_unknown:" + ",".join(unknown))
    if manifest.get("schema") != MANIFEST_SCHEMA:
        failures.append("manifest_schema_mismatch")
    if manifest.get("remediation_id") != REMEDIATION_ID:
        failures.append("manifest_remediation_id_mismatch")
    if manifest.get("source_commit") != evidence.get("source_commit"):
        failures.append("manifest_source_commit_mismatch")
    if manifest.get("tag_name") != evidence.get("tag_name"):
        failures.append("manifest_tag_name_mismatch")
    bundle_path = resolve_any_path(root, evidence.get("bundle_path"))
    if bundle_path is None or manifest.get("bundle_name") != bundle_path.name:
        failures.append("manifest_bundle_name_mismatch")
    if not parse_timestamp(manifest.get("generated_at")):
        failures.append("manifest_generated_at_invalid")

    tag = evidence.get("tag_name")
    restoration_entry = manifest.get("restoration_instructions")
    restoration_value = evidence.get("restoration_instructions_path")
    restoration_path = (
        resolve_repo_path(root, restoration_value)
        if isinstance(restoration_value, str) and not Path(restoration_value).is_absolute()
        else None
    )
    if not isinstance(restoration_entry, dict) or restoration_path is None:
        failures.append("manifest_restoration_instructions_missing")
    else:
        validate_exact_fields(
            restoration_entry,
            PATH_HASH_FIELDS,
            set(),
            "manifest_restoration_instructions",
            failures,
        )
        if restoration_entry.get("path") != restoration_value:
            failures.append("manifest_restoration_path_mismatch")
        elif restoration_path.relative_to(root).as_posix() != restoration_value:
            failures.append("manifest_restoration_path_not_canonical")
        restoration_hash = restoration_entry.get("sha256")
        if not isinstance(restoration_hash, str) or not HEX64.fullmatch(restoration_hash):
            failures.append("manifest_restoration_hash_invalid")
        elif not restoration_path.is_file() or sha256(restoration_path) != restoration_hash:
            failures.append("manifest_restoration_hash_mismatch")
        else:
            validate_tagged_file(
                root,
                tag,
                restoration_path,
                restoration_hash,
                "manifest_restoration",
                failures,
            )
    receipt_entry = manifest.get("receipt")
    if not isinstance(receipt_entry, dict):
        failures.append("manifest_receipt_entry_missing")
    else:
        validate_exact_fields(
            receipt_entry,
            PATH_HASH_FIELDS,
            set(),
            "manifest_receipt_entry",
            failures,
        )
        expected_relative = receipt_path.relative_to(root).as_posix()
        if receipt_entry.get("path") != expected_relative:
            failures.append("manifest_receipt_path_mismatch")
        if receipt_entry.get("sha256") != evidence.get("receipt_sha256"):
            failures.append("manifest_receipt_hash_mismatch")

    mandatory_receipts: dict[str, tuple[str, str]] = {}
    for field in ("production_proving_receipt", "lifecycle_receipt"):
        entry = manifest.get(field)
        binding = receipt.get(field)
        if not isinstance(entry, dict) or not isinstance(binding, dict):
            failures.append(f"manifest_{field}_missing")
            continue
        validate_exact_fields(entry, PATH_HASH_FIELDS, set(), f"manifest_{field}", failures)
        validate_exact_fields(binding, PATH_HASH_FIELDS, set(), f"receipt_{field}", failures)
        if entry != binding:
            failures.append(f"manifest_{field}_binding_mismatch")
            continue
        path_value = entry.get("path")
        digest = entry.get("sha256")
        path = (
            resolve_repo_path(root, path_value)
            if isinstance(path_value, str) and not Path(path_value).is_absolute()
            else None
        )
        if (
            path is None
            or not path.is_file()
            or path.relative_to(root).as_posix() != path_value
            or not isinstance(digest, str)
            or not HEX64.fullmatch(digest)
        ):
            failures.append(f"manifest_{field}_identity_invalid")
            continue
        if sha256(path) != digest:
            failures.append(f"manifest_{field}_hash_mismatch")
            continue
        validate_tagged_file(root, tag, path, digest, f"manifest_{field}", failures)
        mandatory_receipts[field] = (digest, path_value)

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        failures.append("manifest_artifacts_missing")
        return
    hash_entries: list[tuple[str, str]] = []
    seen_paths: set[str] = set()
    artifact_hash_by_path: dict[str, str] = {}
    receipt_relative = receipt_path.relative_to(root).as_posix()
    manifest_relative = manifest_path.relative_to(root).as_posix()
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            failures.append(f"manifest_artifact_invalid:{index}")
            continue
        validate_exact_fields(
            artifact,
            MANIFEST_ARTIFACT_REQUIRED_FIELDS,
            MANIFEST_ARTIFACT_OPTIONAL_FIELDS,
            f"manifest_artifact:{index}",
            failures,
        )
        path_value = artifact.get("path")
        digest = artifact.get("sha256")
        size = artifact.get("size_bytes")
        if not nonempty(path_value) or not isinstance(digest, str) or not HEX64.fullmatch(digest):
            failures.append(f"manifest_artifact_identity_invalid:{index}")
            continue
        if Path(str(path_value)).is_absolute():
            failures.append(f"manifest_artifact_path_not_repository_relative:{path_value}")
            continue
        if path_value in seen_paths:
            failures.append(f"manifest_artifact_duplicate:{path_value}")
            continue
        seen_paths.add(str(path_value))
        path = resolve_repo_path(root, str(path_value))
        if path is None or not path.is_file():
            failures.append(f"manifest_artifact_missing:{path_value}")
            continue
        canonical_relative = path.relative_to(root).as_posix()
        if canonical_relative != path_value:
            failures.append(f"manifest_artifact_path_not_canonical:{path_value}")
            continue
        if path_value in {receipt_relative, manifest_relative}:
            failures.append(f"manifest_recursive_artifact_forbidden:{path_value}")
        if sha256(path) != digest:
            failures.append(f"manifest_artifact_hash_mismatch:{path_value}")
        if not isinstance(size, int) or isinstance(size, bool) or size != path.stat().st_size:
            failures.append(f"manifest_artifact_size_mismatch:{path_value}")
        for optional_field in ("kind", "claim_ceiling"):
            if optional_field in artifact and not nonempty(artifact[optional_field]):
                failures.append(f"manifest_artifact_optional_field_invalid:{path_value}:{optional_field}")
        validate_tagged_file(root, tag, path, digest, "manifest_artifact", failures)
        hash_entries.append((digest, str(path_value)))
        artifact_hash_by_path[str(path_value)] = digest
    computed = evidence_set_hash(hash_entries)
    if manifest.get("evidence_hash") != computed:
        failures.append("manifest_evidence_hash_mismatch")
    if receipt.get("evidence_hash") != computed:
        failures.append("receipt_evidence_hash_mismatch")
    authority = receipt.get("authority_validation")
    if isinstance(authority, dict):
        authority_path = authority.get("artifact_path")
        authority_hash = authority.get("artifact_sha256")
        if not isinstance(authority_path, str) or (authority_hash, authority_path) not in hash_entries:
            failures.append("manifest_authority_validation_artifact_missing")

    for field, entry in mandatory_receipts.items():
        if entry not in hash_entries:
            failures.append(f"manifest_{field}_artifact_missing")

    if restoration_path is not None and restoration_path.is_file():
        restoration_relative = restoration_path.relative_to(root).as_posix()
        restoration_hash = sha256(restoration_path)
        if artifact_hash_by_path.get(restoration_relative) != restoration_hash:
            failures.append("manifest_restoration_artifact_missing")

    protected_entry = manifest.get("protected_heads_report")
    if not isinstance(protected_entry, dict):
        failures.append("manifest_protected_heads_report_missing")
        return
    validate_exact_fields(
        protected_entry,
        PATH_HASH_FIELDS,
        set(),
        "manifest_protected_heads_report",
        failures,
    )
    protected_value = protected_entry.get("path")
    protected_hash = protected_entry.get("sha256")
    protected_path = (
        resolve_repo_path(root, protected_value)
        if isinstance(protected_value, str) and not Path(protected_value).is_absolute()
        else None
    )
    if protected_path is None or not protected_path.is_file():
        failures.append("manifest_protected_heads_report_missing")
        return
    protected_relative = protected_path.relative_to(root).as_posix()
    if protected_relative != protected_value:
        failures.append("manifest_protected_heads_report_path_not_canonical")
    if not isinstance(protected_hash, str) or not HEX64.fullmatch(protected_hash):
        failures.append("manifest_protected_heads_report_hash_invalid")
        return
    if sha256(protected_path) != protected_hash:
        failures.append("manifest_protected_heads_report_hash_mismatch")
    validate_tagged_file(
        root,
        tag,
        protected_path,
        protected_hash,
        "manifest_protected_heads_report",
        failures,
    )
    if artifact_hash_by_path.get(protected_relative) != protected_hash:
        failures.append("manifest_protected_heads_report_artifact_missing")
    report, report_error = load_json(protected_path)
    if report_error:
        failures.append("manifest_protected_heads_report_invalid")
        return
    assert report is not None
    if report.get("schema") != PROTECTED_REPORT_SCHEMA:
        failures.append("manifest_protected_heads_report_schema_mismatch")
    if report.get("remediation_id") != REMEDIATION_ID:
        failures.append("manifest_protected_heads_report_remediation_mismatch")
    if report.get("source_commit") != evidence.get("source_commit"):
        failures.append("manifest_protected_heads_report_source_mismatch")
    if report.get("passed") is not True or report.get("inventory_matches_state") is not True:
        failures.append("manifest_protected_heads_report_not_passed")
    entries = report.get("entries")
    expected_heads = receipt.get("protected_heads")
    observed_heads: dict[str, str] = {}
    if not isinstance(entries, list):
        failures.append("manifest_protected_heads_report_entries_invalid")
    else:
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                failures.append(f"manifest_protected_heads_report_entry_invalid:{index}")
                continue
            name = entry.get("name")
            protected_commit = entry.get("protected_commit")
            actual_tip = entry.get("actual_tip")
            if (
                not isinstance(name, str)
                or not isinstance(protected_commit, str)
                or not HEX40.fullmatch(protected_commit)
                or not isinstance(actual_tip, str)
                or not HEX40.fullmatch(actual_tip)
                or entry.get("commit_readable") is not True
                or entry.get("ref_matches") is not True
                or entry.get("protected_commit_in_ref_history") is not True
                or entry.get("passed") is not True
            ):
                failures.append(f"manifest_protected_heads_report_entry_invalid:{index}")
                continue
            if name in observed_heads:
                failures.append(f"manifest_protected_heads_report_entry_duplicate:{name}")
            observed_heads[name] = protected_commit
    if not isinstance(expected_heads, dict) or observed_heads != expected_heads:
        failures.append("manifest_protected_heads_report_inventory_mismatch")


def validate_recovery_anchor(
    root: Path,
    evidence: dict[str, Any],
    receipt_path: Path,
    manifest_path: Path,
    failures: list[str],
) -> None:
    tag = evidence.get("tag_name")
    if not nonempty(tag):
        failures.append("terminal_tag_name_missing")
        return
    tag = str(tag)
    type_result = run_git(root, "cat-file", "-t", f"refs/tags/{tag}")
    if type_result.returncode != 0 or type_result.stdout.strip() != "tag":
        failures.append("terminal_tag_not_annotated")
        return
    target_result = run_git(root, "rev-parse", f"refs/tags/{tag}^{{}}")
    head_result = run_git(root, "rev-parse", "HEAD")
    if target_result.returncode != 0 or target_result.stdout.strip() != head_result.stdout.strip():
        failures.append("terminal_tag_target_mismatch")
        return
    tag_target = target_result.stdout.strip()
    source = str(evidence.get("source_commit") or "")
    if run_git(root, "merge-base", "--is-ancestor", source, tag_target).returncode != 0 or source == tag_target:
        failures.append("terminal_source_not_precloseout_ancestor")
    changed = run_git(root, "diff", "--name-only", source, tag_target)
    if changed.returncode != 0:
        failures.append("terminal_source_closeout_diff_unreadable")
    else:
        for relative in changed.stdout.splitlines():
            if not relative.startswith(("docs/architecture/", "docs/evidence-manifests/")):
                failures.append(f"post_proving_source_change:{relative}")

    for path in (receipt_path, manifest_path):
        relative = path.relative_to(root).as_posix()
        shown = run_git_bytes(root, "show", f"refs/tags/{tag}:{relative}")
        if shown.returncode != 0:
            failures.append(f"terminal_tag_missing_artifact:{relative}")
        elif hashlib.sha256(shown.stdout).hexdigest() != sha256(path):
            failures.append(f"terminal_tag_artifact_mismatch:{relative}")

    bundle = resolve_any_path(root, evidence.get("bundle_path"))
    sidecar = resolve_any_path(root, evidence.get("bundle_sha256_sidecar"))
    restoration = resolve_any_path(root, evidence.get("restoration_instructions_path"))
    if bundle is None or not bundle.is_file():
        failures.append("recovery_bundle_missing")
        return
    if sidecar is None or not sidecar.is_file():
        failures.append("recovery_bundle_sha256_sidecar_missing")
        return
    if restoration is None or not restoration.is_file() or not restoration.read_text(encoding="utf-8").strip():
        failures.append("restoration_instructions_missing")

    bundle_hash = sha256(bundle)
    matched_sidecar = False
    for line in sidecar.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) != 2 or not HEX64.fullmatch(parts[0]):
            continue
        recorded_path = parts[1].lstrip("* ")
        if recorded_path in {str(bundle), bundle.name} or Path(recorded_path).name == bundle.name:
            matched_sidecar = parts[0] == bundle_hash
            break
    if not matched_sidecar:
        failures.append("recovery_bundle_sha256_mismatch")
    verify = run_git(root, "bundle", "verify", str(bundle))
    if verify.returncode != 0:
        failures.append("recovery_bundle_verify_failed")
    heads = run_git(root, "bundle", "list-heads", str(bundle))
    if heads.returncode != 0 or f"refs/tags/{tag}" not in heads.stdout:
        failures.append("recovery_bundle_terminal_tag_missing")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(os.environ.get("SPIRITOS_FOUNDATION_R1_ROOT", Path(__file__).resolve().parents[1])),
    )
    args = parser.parse_args()
    root = args.root.resolve()
    state_path = root / "docs/architecture/foundation-remediation-r1-state.json"
    state, error = load_json(state_path)
    failures: list[str] = []
    if error:
        print("FOUNDATION_REMEDIATION_R1_EVIDENCE_INVALID")
        print(error)
        return 1
    assert state is not None
    terminal = terminal_state(state)
    if not terminal:
        failures.append("state_not_terminal")
    else:
        status = run_git(root, "status", "--porcelain=v1", "--untracked-files=all")
        if status.returncode != 0:
            failures.append("terminal_worktree_status_unreadable")
        elif status.stdout:
            failures.append("terminal_worktree_not_globally_clean")
    evidence = state.get("terminal_evidence")
    if not isinstance(evidence, dict):
        failures.append("terminal_evidence_missing")
        print("FOUNDATION_REMEDIATION_R1_EVIDENCE_INVALID")
        print("\n".join(failures))
        return 1
    missing_evidence = sorted(TERMINAL_EVIDENCE_FIELDS - set(evidence))
    if missing_evidence:
        failures.append("terminal_evidence_fields_missing:" + ",".join(missing_evidence))

    receipt_path = resolve_repo_path(root, str(evidence.get("receipt_path") or ""))
    manifest_path = resolve_repo_path(root, str(evidence.get("manifest_path") or ""))
    if receipt_path is None or not receipt_path.is_file():
        failures.append("terminal_receipt_missing_or_outside_repository")
    if manifest_path is None or not manifest_path.is_file():
        failures.append("terminal_manifest_missing_or_outside_repository")
    if receipt_path is None or not receipt_path.is_file() or manifest_path is None or not manifest_path.is_file():
        print("FOUNDATION_REMEDIATION_R1_EVIDENCE_INVALID")
        print("\n".join(sorted(set(failures))))
        return 1
    for label, path in (("receipt", receipt_path), ("manifest", manifest_path)):
        if not tracked(root, path):
            failures.append(f"terminal_{label}_untracked")
        expected_hash = evidence.get(f"{label}_sha256")
        if not isinstance(expected_hash, str) or not HEX64.fullmatch(expected_hash):
            failures.append(f"terminal_{label}_hash_invalid")
        elif sha256(path) != expected_hash:
            failures.append(f"terminal_{label}_hash_mismatch")

    receipt, receipt_error = load_json(receipt_path)
    manifest, manifest_error = load_json(manifest_path)
    if receipt_error:
        failures.append(receipt_error)
    if manifest_error:
        failures.append(manifest_error)
    validate_contract_schemas(
        root,
        evidence.get("source_commit"),
        evidence.get("tag_name"),
        failures,
    )
    if receipt is not None:
        validate_receipt(root, receipt, state, evidence, failures)
    if receipt is not None and manifest is not None:
        validate_manifest(root, manifest, evidence, receipt, receipt_path, manifest_path, failures)
    validate_recovery_anchor(root, evidence, receipt_path, manifest_path, failures)

    if failures:
        print("FOUNDATION_REMEDIATION_R1_EVIDENCE_INVALID")
        print("\n".join(sorted(set(failures))))
        return 1
    print("FOUNDATION_REMEDIATION_R1_EVIDENCE_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
