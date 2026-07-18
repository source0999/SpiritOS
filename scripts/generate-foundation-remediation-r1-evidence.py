#!/usr/bin/env python3
"""Build deterministic, source-bound Foundation Remediation R1 evidence.

This tool does not change the remediation state, create a terminal tag, or create a
recovery bundle.  It builds the content-addressed inputs for those later closeout
steps and fails closed when a source, path, participant, authority, or protected-ref
binding is inconsistent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


REMEDIATION_ID = "spiritos-foundation-remediation-r1"
TERMINAL_VERDICT = "SPIRITOS_FOUNDATION_REMEDIATION_COMPLETE"
PROFILE_RECEIPT_SCHEMA = "spiritos-foundation-remediation-r1-profile-execution-receipt/v1"
PROFILE_ARTIFACT_SCHEMA = "spiritos-foundation-remediation-r1-profile-execution-artifact/v1"
TERMINAL_RECEIPT_SCHEMA = "spiritos-foundation-remediation-r1-terminal-receipt/v1"
MANIFEST_SCHEMA = "spiritos-foundation-remediation-r1-immutable-evidence-manifest/v1"
PROTECTED_REPORT_SCHEMA = "spiritos-foundation-remediation-r1-protected-head-report/v1"
PRODUCTION_PROVING_RECEIPT_SCHEMA = (
    "spiritos-foundation-remediation-r1-production-proving-receipt/v1"
)
LIFECYCLE_RECEIPT_SCHEMA = "spiritos-foundation-remediation-r1-lifecycle-receipt/v1"
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
EXPECTED_PROTECTED_HEADS = {
    "source_proxy": "594d66ef8280953af767a273d7c91be765d1a6eb",
    "spiritflix": "5fde4ae064d471e1133e00d6bf25fb5aecb5d196",
    "architecture_audit": "05612d2ae358bc01b6ef997243137649f8d65f14",
    "campaign_1_terminal": "8a20473c2260bc132e595c64230d3fdfc9fef97f",
    "campaign_2_engineering_terminal": "2b8ead66578d7f7053c01cb987e011b763c1c03d",
    "campaign_3_design_terminal": "4aec510409e8bb82386190af9fa8f666efcbc63e",
}
PROTECTED_REFS = {
    "source_proxy": "refs/heads/codex/source-proxy-structural-milestone-20260711",
    "spiritflix": "refs/heads/codex/spiritflix-smart-scan-identity-fix",
    "architecture_audit": "refs/heads/codex/spiritos-architecture-audit-20260712",
    "campaign_1_terminal": "refs/heads/codex/spiritos-campaign-1-foundation-20260712",
    "campaign_2_engineering_terminal": "refs/heads/codex/spiritos-campaign-2-core-coding-os-20260716",
    "campaign_3_design_terminal": "refs/heads/codex/spiritos-campaign-3-core-design-lane-20260717",
}
EXPECTED_PROTECTED_REF_TIPS = {
    **EXPECTED_PROTECTED_HEADS,
    "campaign_2_engineering_terminal": "39de31bb73cb4a910281705259b35a6d42a0726c",
}
TERMINAL_SPEC_FIELDS = {
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
    "redaction_verdict",
    "claim_ceiling",
}
REPOSITORY_IDENTITY_FIELDS = {"repository_id", "worktree_id", "worktree_realpath"}
BUILD_IDENTITY_REQUIRED_FIELDS = {"build_id", "source_commit"}
BUILD_IDENTITY_OPTIONAL_FIELDS = {"artifact_path", "artifact_sha256"}
TARGET_PLUGIN_IDENTITY_REQUIRED_FIELDS = {"plugin_id", "source_head"}
TARGET_PLUGIN_IDENTITY_OPTIONAL_FIELDS: set[str] = set()
CONTENT_IDENTITY_FIELDS = {"id", "sha256"}
PARTICIPANT_FIELDS = {
    "status",
    "invocation_id",
    "output_id",
    "output_sha256",
    "consumer_acknowledgement_id",
    "artifact_sha256",
}
APPROVAL_FIELDS = {
    "approval_id",
    "generation",
    "state",
    "artifact_sha256",
    "orchestrator_run_id",
}
PRODUCTION_PROOF_FIELDS = {
    "proof_sha256",
    "terminal_proof_eligible",
    "claim_ceiling",
    "recovery_id",
}
RECEIPT_BINDING_FIELDS = {"path", "sha256"}
PARTICIPANT_RESULT_FIELDS = {"status", "invocation_id"}
AUTHORITY_VALIDATION_FIELDS = {
    "source_commit",
    "tag_name",
    "validator_path",
    "validator_sha256",
    "artifact_path",
    "artifact_sha256",
    "result",
    "passed",
}
REDACTION_VERDICT_REQUIRED_FIELDS = {"verdict", "scanner"}
REDACTION_VERDICT_OPTIONAL_FIELDS = {"artifact_sha256"}
PROFILE_ARTIFACT_FIELDS = {
    "schema",
    "remediation_id",
    "profile_id",
    "command",
    "source_commit",
    "started_at",
    "completed_at",
    "returncode",
    "result",
    "passed",
    "stdout",
    "stderr",
    "claim_ceiling",
}
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


class EvidenceBuildError(RuntimeError):
    """An evidence input cannot truthfully satisfy the closeout contract."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_timestamp(value: object | None) -> str:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        raise EvidenceBuildError("generated_timestamp_invalid")
    candidate = value or utc_now()
    try:
        parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError as error:
        raise EvidenceBuildError("generated_timestamp_invalid") from error
    if parsed.tzinfo is None:
        raise EvidenceBuildError("generated_timestamp_timezone_missing")
    return parsed.astimezone(timezone.utc).isoformat()


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise EvidenceBuildError(f"json_unreadable_or_malformed:{path}") from error
    if not isinstance(value, dict):
        raise EvidenceBuildError(f"json_not_object:{path}")
    return value


def write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical_json_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def git_blob_sha256(root: Path, commit: str, path: str) -> str:
    _, relative = repo_path(root, path)
    if relative != path:
        raise EvidenceBuildError(f"source_blob_path_not_canonical:{path}")
    completed = subprocess.run(
        ["git", "-C", str(root), "cat-file", "blob", f"{commit}:{relative}"],
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise EvidenceBuildError(f"source_blob_unreadable:{relative}")
    return sha256_bytes(completed.stdout)


def git_commit(root: Path, value: str) -> str:
    if not HEX40.fullmatch(value):
        raise EvidenceBuildError("source_commit_invalid")
    result = run_git(root, "rev-parse", "--verify", f"{value}^{{commit}}")
    if result.returncode != 0 or result.stdout.strip() != value:
        raise EvidenceBuildError("source_commit_unreadable")
    return value


def require_source_head(root: Path, source_commit: str) -> None:
    head = run_git(root, "rev-parse", "HEAD")
    if head.returncode != 0 or head.stdout.strip() != source_commit:
        raise EvidenceBuildError("source_commit_not_current_head")


def repo_path(root: Path, value: str | Path, *, must_exist: bool = True) -> tuple[Path, str]:
    raw = Path(value)
    resolved = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError as error:
        raise EvidenceBuildError(f"path_outside_repository:{value}") from error
    if not relative or relative == ".":
        raise EvidenceBuildError(f"path_not_file:{value}")
    if must_exist and not resolved.is_file():
        raise EvidenceBuildError(f"file_missing:{relative}")
    return resolved, relative


def artifact_entry(
    root: Path,
    value: str | Path,
    *,
    kind: str | None = None,
    claim_ceiling: str | None = None,
) -> dict[str, Any]:
    path, relative = repo_path(root, value)
    entry: dict[str, Any] = {
        "path": relative,
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }
    if kind:
        entry["kind"] = kind
    if claim_ceiling:
        entry["claim_ceiling"] = claim_ceiling
    return entry


def evidence_set_hash(entries: Iterable[dict[str, Any] | tuple[str, str]]) -> str:
    normalized: list[tuple[str, str]] = []
    for entry in entries:
        if isinstance(entry, tuple):
            digest, path = entry
        else:
            digest, path = entry.get("sha256"), entry.get("path")
        if not isinstance(digest, str) or not HEX64.fullmatch(digest):
            raise EvidenceBuildError("artifact_sha256_invalid")
        if not isinstance(path, str) or not path:
            raise EvidenceBuildError("artifact_path_invalid")
        normalized.append((digest, path))
    if len({path for _, path in normalized}) != len(normalized):
        raise EvidenceBuildError("artifact_path_duplicate")
    canonical = "".join(f"{digest}  {path}\n" for digest, path in sorted(normalized))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_claim_ceiling(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or value.strip().lower() in {"go", "unbounded"}:
        raise EvidenceBuildError("claim_ceiling_invalid")
    return value


def exact_object(
    value: object,
    *,
    name: str,
    required: set[str],
    optional: set[str] | frozenset[str] = frozenset(),
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceBuildError(f"{name}_not_object")
    fields = set(value)
    missing = required - fields
    unknown = fields - required - set(optional)
    if missing:
        raise EvidenceBuildError(f"{name}_fields_missing:" + ",".join(sorted(missing)))
    if unknown:
        raise EvidenceBuildError(f"{name}_fields_unknown:" + ",".join(sorted(unknown)))
    return value


def nonempty_string(value: object, error: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceBuildError(error)
    return value


def compact_sha256(value: object) -> str:
    """Return the self-hash format used by the proving and lifecycle harnesses."""

    try:
        encoded = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise EvidenceBuildError("receipt_noncanonical_json") from error
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def raw_sha256(value: object, error: str) -> str:
    if not isinstance(value, str):
        raise EvidenceBuildError(error)
    candidate = value.removeprefix("sha256:")
    if not HEX64.fullmatch(candidate):
        raise EvidenceBuildError(error)
    return candidate


def require_mapping(value: object, error: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceBuildError(error)
    return value


def require_list(value: object, error: str) -> list[Any]:
    if not isinstance(value, list):
        raise EvidenceBuildError(error)
    return value


def validate_self_hash(receipt: dict[str, Any], *, label: str) -> str:
    unsigned = dict(receipt)
    recorded = unsigned.pop("receipt_sha256", None)
    expected = compact_sha256(unsigned)
    if recorded != expected:
        raise EvidenceBuildError(f"{label}_self_hash_mismatch")
    return expected


def load_receipt_binding(
    root: Path,
    value: object,
    *,
    label: str,
) -> tuple[dict[str, Any], Path, str]:
    binding = exact_object(
        value,
        name=f"terminal_spec_{label}",
        required=RECEIPT_BINDING_FIELDS,
    )
    path_value = nonempty_string(
        binding.get("path"),
        f"terminal_spec_{label}_path_invalid",
    )
    path, relative = repo_path(root, path_value)
    if path_value != relative:
        raise EvidenceBuildError(f"terminal_spec_{label}_path_not_canonical")
    recorded_hash = raw_sha256(
        binding.get("sha256"),
        f"terminal_spec_{label}_sha256_invalid",
    )
    if sha256_file(path) != recorded_hash:
        raise EvidenceBuildError(f"terminal_spec_{label}_sha256_mismatch")
    return load_json(path), path, relative


def validate_proving_run(
    run: object,
    *,
    source_commit: str,
    ordinal: int,
) -> dict[str, Any]:
    value = exact_object(
        run,
        name=f"production_proving_run_{ordinal}",
        required=PROVING_RUN_REQUIRED_FIELDS,
    )
    if value.get("ordinal") != ordinal or value.get("clean_rerun") is not (ordinal == 2):
        raise EvidenceBuildError(f"production_proving_run_{ordinal}_ordinal_invalid")
    if value.get("source_commit") != source_commit:
        raise EvidenceBuildError(f"production_proving_run_{ordinal}_source_mismatch")
    for field in ("task_id", "orchestrator_run_id", "orchestrator_attempt_id"):
        nonempty_string(
            value.get(field),
            f"production_proving_run_{ordinal}_{field}_missing",
        )
    raw_sha256(
        value.get("task_prompt_sha256"),
        f"production_proving_run_{ordinal}_prompt_hash_invalid",
    )
    if (
        value.get("task_status") != "completed"
        or value.get("verification_status") != "verified"
        or value.get("real_browser_used") is not True
        or value.get("approval_final_state") != "consumed"
        or value.get("verification_preceded_final_result") is not True
    ):
        raise EvidenceBuildError(f"production_proving_run_{ordinal}_terminal_state_invalid")
    artifact = require_mapping(
        value.get("artifact"),
        f"production_proving_run_{ordinal}_artifact_missing",
    )
    for field in ("artifact_sha256", "result_sha256", "approved_diff_sha256"):
        raw_sha256(
            artifact.get(field),
            f"production_proving_run_{ordinal}_artifact_hash_invalid:{field}",
        )
    approval = require_mapping(
        value.get("approval"),
        f"production_proving_run_{ordinal}_approval_missing",
    )
    if (
        approval.get("approval_id") != artifact.get("approval_id")
        or approval.get("approval_generation") != artifact.get("generation")
    ):
        raise EvidenceBuildError(f"production_proving_run_{ordinal}_approval_artifact_mismatch")
    proof = require_mapping(
        value.get("production_proof"),
        f"production_proving_run_{ordinal}_production_proof_missing",
    )
    if proof.get("terminal_proof_eligible") is not True or proof.get("failures") != []:
        raise EvidenceBuildError(f"production_proving_run_{ordinal}_production_proof_invalid")
    raw_sha256(
        proof.get("proof_sha256"),
        f"production_proving_run_{ordinal}_production_proof_hash_invalid",
    )
    participants = require_list(
        value.get("participants"),
        f"production_proving_run_{ordinal}_participants_missing",
    )
    if {item.get("role") for item in participants if isinstance(item, dict)} != set(
        PROVING_PARTICIPANT_ROLES.values()
    ):
        raise EvidenceBuildError(f"production_proving_run_{ordinal}_participant_roles_invalid")
    return value


def validate_production_proving_receipt(
    receipt: dict[str, Any],
    *,
    source_commit: str,
) -> dict[str, Any]:
    exact_object(
        receipt,
        name="production_proving_receipt",
        required=PRODUCTION_PROVING_FIELDS,
    )
    validate_self_hash(receipt, label="production_proving_receipt")
    if (
        receipt.get("schema_version") != PRODUCTION_PROVING_RECEIPT_SCHEMA
        or receipt.get("receipt_type") != "foundation_r1_black_box_production_proving"
        or receipt.get("remediation_id") != REMEDIATION_ID
        or receipt.get("run_mode") != "production_http"
        or receipt.get("terminal_proof_eligible") is not True
        or receipt.get("source_commit") != source_commit
        or receipt.get("failures") != []
    ):
        raise EvidenceBuildError("production_proving_receipt_identity_invalid")
    claim_ceiling = validate_claim_ceiling(receipt.get("claim_ceiling"))
    if claim_ceiling != "recovered_via_declared_fallback_only":
        raise EvidenceBuildError("production_proving_claim_ceiling_invalid")
    started_at = parse_timestamp(receipt.get("started_at"))
    completed_at = parse_timestamp(receipt.get("completed_at"))
    if datetime.fromisoformat(completed_at) < datetime.fromisoformat(started_at):
        raise EvidenceBuildError("production_proving_receipt_timestamp_order_invalid")

    expected_runtime = require_mapping(
        receipt.get("expected_runtime_identity"),
        "production_proving_expected_runtime_identity_missing",
    )
    repository = require_mapping(
        receipt.get("repository_identity"),
        "production_proving_repository_identity_missing",
    )
    target_identity = require_mapping(
        receipt.get("target_plugin_identity"),
        "production_proving_target_plugin_identity_missing",
    )
    if (
        expected_runtime.get("source_head") != source_commit
        or target_identity.get("source_head") != source_commit
        or repository.get("repository") != expected_runtime.get("repository_id")
        or target_identity.get("repository_id") != expected_runtime.get("repository_id")
        or target_identity.get("worktree_id") != expected_runtime.get("worktree_id")
        or repository.get("worktree") != repository.get("root")
    ):
        raise EvidenceBuildError("production_proving_runtime_identity_mismatch")
    for field in ("repository_id", "worktree_id"):
        nonempty_string(
            expected_runtime.get(field),
            f"production_proving_runtime_identity_missing:{field}",
        )
    nonempty_string(repository.get("root"), "production_proving_worktree_root_missing")
    nonempty_string(target_identity.get("plugin_id"), "production_proving_plugin_id_missing")
    nonempty_string(
        target_identity.get("selected_prompt_id"),
        "production_proving_prompt_id_missing",
    )
    nonempty_string(
        target_identity.get("selected_context_id"),
        "production_proving_context_id_missing",
    )
    task_prompt = require_mapping(
        receipt.get("task_prompt"),
        "production_proving_task_prompt_missing",
    )
    prompt_sha256 = raw_sha256(
        task_prompt.get("sha256"),
        "production_proving_task_prompt_hash_invalid",
    )
    transport = require_mapping(receipt.get("transport"), "production_proving_transport_missing")
    if (
        transport.get("kind") != "production_http"
        or transport.get("origins_distinct") is not True
        or transport.get("redirects_allowed") is not False
        or transport.get("services_started_by_harness") is not False
        or transport.get("application_modules_imported") is not False
        or transport.get("test_modules_imported") is not False
        or transport.get("callback_transport_allowed") is not False
    ):
        raise EvidenceBuildError("production_proving_transport_invalid")
    redaction = require_mapping(
        receipt.get("redaction"),
        "production_proving_redaction_missing",
    )
    if redaction.get("status") != "passed":
        raise EvidenceBuildError("production_proving_redaction_invalid")

    runs = require_list(receipt.get("runs"), "production_proving_runs_missing")
    if len(runs) != 2:
        raise EvidenceBuildError("production_proving_run_count_invalid")
    first = validate_proving_run(runs[0], source_commit=source_commit, ordinal=1)
    second = validate_proving_run(runs[1], source_commit=source_commit, ordinal=2)
    recovery_expectation = exact_object(
        receipt.get("expected_controlled_recovery"),
        name="production_proving_expected_controlled_recovery",
        required=EXPECTED_RECOVERY_FIELDS,
    )
    recovery_ids: set[str] = set()
    for ordinal, run in enumerate((first, second), start=1):
        recovery = require_mapping(
            run.get("controlled_recovery"),
            f"production_proving_run_{ordinal}_recovery_missing",
        )
        failure = require_mapping(
            recovery.get("failure"),
            f"production_proving_run_{ordinal}_recovery_failure_missing",
        )
        replacement = require_mapping(
            recovery.get("replacement"),
            f"production_proving_run_{ordinal}_recovery_replacement_missing",
        )
        adapter = require_mapping(
            run.get("target_adapter"),
            f"production_proving_run_{ordinal}_target_adapter_missing",
        )
        run_proof = require_mapping(
            run.get("production_proof"),
            f"production_proving_run_{ordinal}_production_proof_missing",
        )
        recovery_id = nonempty_string(
            recovery.get("recovery_id"),
            f"production_proving_run_{ordinal}_recovery_id_missing",
        )
        recovery_ids.add(recovery_id)
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
            raise EvidenceBuildError(f"production_proving_run_{ordinal}_recovery_mismatch")
        for label, item, fields in (
            ("failure", failure, ("invocation_id",)),
            ("replacement", replacement, ("invocation_id", "output_id")),
        ):
            for field in fields:
                nonempty_string(
                    item.get(field),
                    f"production_proving_run_{ordinal}_recovery_{label}_{field}_missing",
                )
    if len(recovery_ids) != 2:
        raise EvidenceBuildError("production_proving_clean_rerun_recovery_identity_reused")
    if any(
        first.get(field) == second.get(field)
        for field in ("task_id", "orchestrator_run_id", "orchestrator_attempt_id")
    ):
        raise EvidenceBuildError("production_proving_clean_rerun_identity_reused")
    if (
        first.get("approval", {}).get("approval_id")
        == second.get("approval", {}).get("approval_id")
        or first.get("artifact", {}).get("artifact_sha256")
        == second.get("artifact", {}).get("artifact_sha256")
    ):
        raise EvidenceBuildError("production_proving_clean_rerun_authority_reused")
    if (
        raw_sha256(second.get("task_prompt_sha256"), "production_proving_second_prompt_invalid")
        != prompt_sha256
        or second.get("production_proof", {}).get("claim_ceiling") != claim_ceiling
    ):
        raise EvidenceBuildError("production_proving_second_run_claim_mismatch")

    undo = require_mapping(receipt.get("undo"), "production_proving_undo_missing")
    reset = require_mapping(receipt.get("reset"), "production_proving_reset_missing")
    rerun = require_mapping(receipt.get("clean_rerun"), "production_proving_clean_rerun_missing")
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
        raise EvidenceBuildError("production_proving_undo_reset_invalid")
    rerun_fields = {
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
    }
    if any(rerun.get(field) is not True for field in rerun_fields):
        raise EvidenceBuildError("production_proving_clean_rerun_invalid")

    operator = require_mapping(
        receipt.get("operator_session"),
        "production_proving_operator_session_missing",
    )
    attestation = require_mapping(
        receipt.get("run_attestation"),
        "production_proving_run_attestation_missing",
    )
    exchanges = require_list(
        receipt.get("http_exchanges"),
        "production_proving_http_exchanges_missing",
    )
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
        raise EvidenceBuildError("production_proving_run_attestation_invalid")
    return second


def validate_lifecycle_receipt(
    receipt: dict[str, Any],
    *,
    inner_receipt: dict[str, Any],
    source_commit: str,
) -> None:
    exact_object(receipt, name="lifecycle_receipt", required=LIFECYCLE_FIELDS)
    validate_self_hash(receipt, label="lifecycle_receipt")
    if (
        receipt.get("schema_version") != LIFECYCLE_RECEIPT_SCHEMA
        or receipt.get("receipt_type") != "foundation_r1_clean_production_service_lifecycle"
        or receipt.get("remediation_id") != REMEDIATION_ID
        or receipt.get("status") != "passed"
        or receipt.get("terminal_proof_eligible") is not False
        or receipt.get("claim_ceiling")
        != "subordinate_clean_checkout_build_service_and_revocation_proof_only"
        or receipt.get("failures") != []
    ):
        raise EvidenceBuildError("lifecycle_receipt_identity_invalid")
    started_at = parse_timestamp(receipt.get("started_at"))
    completed_at = parse_timestamp(receipt.get("completed_at"))
    if datetime.fromisoformat(completed_at) < datetime.fromisoformat(started_at):
        raise EvidenceBuildError("lifecycle_receipt_timestamp_order_invalid")
    redaction = require_mapping(receipt.get("redaction"), "lifecycle_redaction_missing")
    if redaction.get("status") != "passed":
        raise EvidenceBuildError("lifecycle_redaction_invalid")
    embedded = require_mapping(receipt.get("inner_proving"), "lifecycle_inner_proving_missing")
    embedded_receipt = dict(embedded)
    execution = require_mapping(
        embedded_receipt.pop("execution", None),
        "lifecycle_inner_execution_missing",
    )
    published_after_teardown = embedded_receipt.pop(
        "published_only_after_lifecycle_teardown",
        None,
    )
    if published_after_teardown is not True:
        raise EvidenceBuildError("lifecycle_inner_receipt_publication_order_invalid")
    if embedded_receipt != inner_receipt:
        raise EvidenceBuildError("lifecycle_inner_proving_receipt_mismatch")
    if execution.get("receipt_sha256") != inner_receipt.get("receipt_sha256"):
        raise EvidenceBuildError("lifecycle_inner_execution_receipt_hash_mismatch")

    expected_runtime = require_mapping(
        inner_receipt.get("expected_runtime_identity"),
        "lifecycle_inner_runtime_identity_missing",
    )
    inner_repository = require_mapping(
        inner_receipt.get("repository_identity"),
        "lifecycle_inner_repository_identity_missing",
    )
    source = require_mapping(receipt.get("source"), "lifecycle_source_identity_missing")
    if (
        source.get("source_head") != source_commit
        or source.get("repository_id") != expected_runtime.get("repository_id")
        or source.get("worktree_id") != expected_runtime.get("worktree_id")
        or source.get("worktree_root") != inner_repository.get("root")
        or source.get("registered_linked_worktree") is not True
        or source.get("clean_before_build") is not True
    ):
        raise EvidenceBuildError("lifecycle_source_identity_mismatch")

    services = require_list(receipt.get("services"), "lifecycle_services_missing")
    if len(services) != 3 or {item.get("name") for item in services if isinstance(item, dict)} != {
        "source_proxy",
        "next",
        "next_tls",
    }:
        raise EvidenceBuildError("lifecycle_service_set_invalid")
    for service in services:
        service = require_mapping(service, "lifecycle_service_invalid")
        if any(
            service.get(field) is not True
            for field in (
                "cwd_bound_to_proof_worktree",
                "loopback_bound",
                "stopped",
                "process_absent",
                "process_group_absent",
                "process_session_absent",
                "descendant_processes_absent",
                "port_closed",
            )
        ) or any(
            service.get(field) is not False
            for field in ("raw_pid_recorded", "raw_port_recorded")
        ):
            raise EvidenceBuildError("lifecycle_service_teardown_invalid")
    teardown = require_mapping(receipt.get("teardown"), "lifecycle_teardown_missing")
    if teardown.get("failures") != [] or any(
        teardown.get(field) is not True
        for field in (
            "dependency_link_removed",
            "next_build_removed",
            "backup_state_removed",
            "runtime_receipts_removed",
            "proving_fixture_removed",
            "proving_fixture_tracked_paths_absent",
            "proving_fixture_symlinks_not_followed",
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
        )
    ):
        raise EvidenceBuildError("lifecycle_teardown_invalid")
    for service in services:
        raw_sha256(
            service.get("listener_identity_sha256"),
            "lifecycle_service_listener_identity_invalid",
        )
    temporary = require_mapping(
        receipt.get("temporary_authority"),
        "lifecycle_temporary_authority_missing",
    )
    if (
        temporary.get("state_root_removed") is not True
        or temporary.get("shared_signing_key_preexisted") is not True
        or temporary.get("shared_signing_key_unchanged") is not True
    ):
        raise EvidenceBuildError("lifecycle_temporary_authority_teardown_invalid")


def validate_terminal_production_cross_binding(
    root: Path,
    spec: dict[str, Any],
    *,
    source_commit: str,
) -> tuple[dict[str, Any], Path, str, Path, str]:
    proving, proving_path, proving_relative = load_receipt_binding(
        root,
        spec.get("production_proving_receipt"),
        label="production_proving_receipt",
    )
    lifecycle, lifecycle_path, lifecycle_relative = load_receipt_binding(
        root,
        spec.get("lifecycle_receipt"),
        label="lifecycle_receipt",
    )
    if proving_relative == lifecycle_relative:
        raise EvidenceBuildError("terminal_spec_proving_lifecycle_path_reused")
    second = validate_production_proving_receipt(proving, source_commit=source_commit)
    validate_lifecycle_receipt(
        lifecycle,
        inner_receipt=proving,
        source_commit=source_commit,
    )

    artifact = require_mapping(second.get("artifact"), "terminal_proving_artifact_missing")
    approval = require_mapping(second.get("approval"), "terminal_proving_approval_missing")
    proof = require_mapping(
        second.get("production_proof"),
        "terminal_proving_production_proof_missing",
    )
    recovery = require_mapping(
        second.get("controlled_recovery"),
        "terminal_proving_recovery_missing",
    )
    context = require_mapping(second.get("context"), "terminal_proving_context_missing")
    prompt = require_mapping(second.get("prompt_packet"), "terminal_proving_prompt_missing")
    cartographer = require_mapping(
        second.get("cartographer_proposal"),
        "terminal_proving_cartographer_proposal_missing",
    )
    proving_target = require_mapping(
        proving.get("target_plugin_identity"),
        "terminal_proving_target_plugin_identity_missing",
    )
    production_proof = exact_object(
        spec.get("production_proof"),
        name="terminal_spec_production_proof",
        required=PRODUCTION_PROOF_FIELDS,
    )
    expected_target_files = cartographer.get("proposed_files")
    expected = {
        "task_id": second.get("task_id"),
        "orchestrator_run_id": second.get("orchestrator_run_id"),
        "orchestrator_attempt_id": second.get("orchestrator_attempt_id"),
        "artifact_sha256": raw_sha256(
            artifact.get("artifact_sha256"),
            "terminal_proving_artifact_hash_invalid",
        ),
        "applied_diff_sha256": raw_sha256(
            artifact.get("approved_diff_sha256"),
            "terminal_proving_diff_hash_invalid",
        ),
        "result_sha256": raw_sha256(
            artifact.get("result_sha256"),
            "terminal_proving_result_hash_invalid",
        ),
    }
    for field, expected_value in expected.items():
        if spec.get(field) != expected_value:
            raise EvidenceBuildError(f"terminal_spec_proving_run_mismatch:{field}")
    if expected_target_files != [spec.get("target")]:
        raise EvidenceBuildError("terminal_spec_proving_target_mismatch")

    target = require_mapping(spec.get("target_plugin_identity"), "terminal_spec_target_missing")
    if (
        target.get("plugin_id") != proving_target.get("plugin_id")
        or target.get("source_head") != source_commit
    ):
        raise EvidenceBuildError("terminal_spec_proving_plugin_identity_mismatch")
    prompt_identity = require_mapping(spec.get("prompt_identity"), "terminal_spec_prompt_missing")
    if (
        prompt_identity.get("id") != prompt.get("selected_prompt_id")
        or prompt_identity.get("id") != proving_target.get("selected_prompt_id")
        or prompt_identity.get("sha256")
        != raw_sha256(second.get("task_prompt_sha256"), "terminal_proving_prompt_hash_invalid")
    ):
        raise EvidenceBuildError("terminal_spec_proving_prompt_identity_mismatch")
    context_identity = require_mapping(spec.get("context_identity"), "terminal_spec_context_missing")
    if (
        context_identity.get("id") != proving_target.get("selected_context_id")
        or context_identity.get("sha256")
        != raw_sha256(context.get("context_hash"), "terminal_proving_context_hash_invalid")
    ):
        raise EvidenceBuildError("terminal_spec_proving_context_identity_mismatch")

    terminal_approval = require_mapping(spec.get("approval"), "terminal_spec_approval_missing")
    if (
        terminal_approval.get("approval_id") != approval.get("approval_id")
        or terminal_approval.get("generation") != approval.get("approval_generation")
        or terminal_approval.get("state") != second.get("approval_final_state")
        or terminal_approval.get("artifact_sha256") != expected["artifact_sha256"]
        or terminal_approval.get("orchestrator_run_id") != second.get("orchestrator_run_id")
    ):
        raise EvidenceBuildError("terminal_spec_proving_approval_mismatch")

    expected_proof = {
        "proof_sha256": raw_sha256(
            proof.get("proof_sha256"),
            "terminal_proving_production_proof_hash_invalid",
        ),
        "terminal_proof_eligible": True,
        "claim_ceiling": proof.get("claim_ceiling"),
        "recovery_id": recovery.get("recovery_id"),
    }
    if production_proof != expected_proof:
        raise EvidenceBuildError("terminal_spec_production_proof_mismatch")
    if (
        spec.get("claim_ceiling") != expected_proof["claim_ceiling"]
        or proving.get("claim_ceiling") != expected_proof["claim_ceiling"]
        or recovery.get("claim_ceiling_impact") != expected_proof["claim_ceiling"]
        or recovery.get("proof_eligible") is not True
    ):
        raise EvidenceBuildError("terminal_spec_production_claim_ceiling_mismatch")

    proving_participants = {
        item.get("role"): item
        for item in require_list(second.get("participants"), "terminal_proving_participants_missing")
        if isinstance(item, dict)
    }
    terminal_participants = require_mapping(
        spec.get("participants"),
        "terminal_spec_participants_missing",
    )
    for role, proving_role in PROVING_PARTICIPANT_ROLES.items():
        record = require_mapping(
            terminal_participants.get(role),
            f"terminal_spec_participant_{role}_missing",
        )
        observed = require_mapping(
            proving_participants.get(proving_role),
            f"terminal_proving_participant_{role}_missing",
        )
        expected_record = {
            "status": "succeeded" if role == "executor" else "passed",
            "invocation_id": observed.get("invocation_id"),
            "output_id": observed.get("output_id"),
            "output_sha256": raw_sha256(
                observed.get("output_sha256"),
                f"terminal_proving_participant_output_hash_invalid:{role}",
            ),
            "consumer_acknowledgement_id": observed.get("consumer_acknowledgement_id"),
            "artifact_sha256": expected["artifact_sha256"],
        }
        if record != expected_record:
            raise EvidenceBuildError(f"terminal_spec_proving_participant_mismatch:{role}")

    repository = require_mapping(spec.get("repository_identity"), "terminal_spec_repository_missing")
    expected_runtime = require_mapping(
        proving.get("expected_runtime_identity"),
        "terminal_proving_runtime_identity_missing",
    )
    lifecycle_build = require_mapping(lifecycle.get("build"), "lifecycle_build_missing")
    next_build = require_mapping(lifecycle_build.get("next"), "lifecycle_next_build_missing")
    backend_build = require_mapping(
        lifecycle_build.get("source_proxy"),
        "lifecycle_backend_build_missing",
    )
    if repository.get("repository_id") != expected_runtime.get("repository_id"):
        raise EvidenceBuildError("terminal_spec_proving_repository_mismatch")
    if spec.get("shell_build_identity", {}).get("build_id") != next_build.get("build_id_sha256"):
        raise EvidenceBuildError("terminal_spec_proving_shell_build_mismatch")
    if spec.get("backend_build_identity", {}).get("build_id") != backend_build.get("source_tree"):
        raise EvidenceBuildError("terminal_spec_proving_backend_build_mismatch")
    return second, proving_path, proving_relative, lifecycle_path, lifecycle_relative


def build_profile_receipt(
    root: Path,
    *,
    profile_id: str,
    command: str,
    source_commit: str,
    artifact_path: str | Path,
    claim_ceiling: str,
    completed_at: str | None = None,
) -> dict[str, Any]:
    source_commit = git_commit(root, source_commit)
    require_source_head(root, source_commit)
    if not profile_id.strip() or not command.strip():
        raise EvidenceBuildError("profile_identity_invalid")
    artifact, relative = repo_path(root, artifact_path)
    execution = exact_object(
        load_json(artifact),
        name="profile_execution_artifact",
        required=PROFILE_ARTIFACT_FIELDS,
    )
    if execution.get("schema") != PROFILE_ARTIFACT_SCHEMA:
        raise EvidenceBuildError("profile_execution_artifact_schema_mismatch")
    if execution.get("remediation_id") != REMEDIATION_ID:
        raise EvidenceBuildError("profile_execution_artifact_remediation_mismatch")
    if execution.get("profile_id") != profile_id or execution.get("command") != command:
        raise EvidenceBuildError("profile_execution_artifact_identity_mismatch")
    if execution.get("source_commit") != source_commit:
        raise EvidenceBuildError("profile_execution_artifact_source_mismatch")
    if (
        not isinstance(execution.get("returncode"), int)
        or isinstance(execution.get("returncode"), bool)
        or execution["returncode"] != 0
        or execution.get("result") != "pass"
        or execution.get("passed") is not True
    ):
        raise EvidenceBuildError("profile_execution_artifact_not_passed")
    if not isinstance(execution.get("stdout"), str) or not isinstance(execution.get("stderr"), str):
        raise EvidenceBuildError("profile_execution_artifact_output_invalid")
    artifact_started_at = parse_timestamp(execution.get("started_at"))
    artifact_completed_at = parse_timestamp(execution.get("completed_at"))
    if datetime.fromisoformat(artifact_completed_at) < datetime.fromisoformat(artifact_started_at):
        raise EvidenceBuildError("profile_execution_artifact_timestamp_order_invalid")
    requested_claim_ceiling = validate_claim_ceiling(claim_ceiling)
    if validate_claim_ceiling(execution.get("claim_ceiling")) != requested_claim_ceiling:
        raise EvidenceBuildError("profile_execution_artifact_claim_ceiling_mismatch")
    if completed_at is not None and parse_timestamp(completed_at) != artifact_completed_at:
        raise EvidenceBuildError("profile_execution_artifact_completed_at_mismatch")
    return {
        "schema": PROFILE_RECEIPT_SCHEMA,
        "remediation_id": REMEDIATION_ID,
        "profile_id": profile_id,
        "command": command,
        "source_commit": source_commit,
        "artifact_path": relative,
        "artifact_sha256": sha256_file(artifact),
        "result": "pass",
        "passed": True,
        "claim_ceiling": requested_claim_ceiling,
        "completed_at": artifact_completed_at,
    }


def run_profile(
    root: Path,
    *,
    profile_id: str,
    command: str,
    source_commit: str,
    artifact_path: str | Path,
    receipt_path: str | Path,
    claim_ceiling: str,
) -> tuple[dict[str, Any], dict[str, Any] | None, int]:
    source_commit = git_commit(root, source_commit)
    require_source_head(root, source_commit)
    started_at = utc_now()
    completed = subprocess.run(
        ["bash", "-lc", command],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    completed_at = utc_now()
    artifact = {
        "schema": PROFILE_ARTIFACT_SCHEMA,
        "remediation_id": REMEDIATION_ID,
        "profile_id": profile_id,
        "command": command,
        "source_commit": source_commit,
        "started_at": started_at,
        "completed_at": completed_at,
        "returncode": completed.returncode,
        "result": "pass" if completed.returncode == 0 else "fail",
        "passed": completed.returncode == 0,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "claim_ceiling": validate_claim_ceiling(claim_ceiling),
    }
    artifact_output, _ = repo_path(root, artifact_path, must_exist=False)
    write_json_atomic(artifact_output, artifact)
    if completed.returncode != 0:
        return artifact, None, completed.returncode
    receipt = build_profile_receipt(
        root,
        profile_id=profile_id,
        command=command,
        source_commit=source_commit,
        artifact_path=artifact_output,
        claim_ceiling=claim_ceiling,
        completed_at=completed_at,
    )
    receipt_output, _ = repo_path(root, receipt_path, must_exist=False)
    write_json_atomic(receipt_output, receipt)
    return artifact, receipt, 0


def build_protected_head_report(
    root: Path,
    *,
    source_commit: str,
    state_path: str | Path = "docs/architecture/foundation-remediation-r1-state.json",
    generated_at: str | None = None,
) -> dict[str, Any]:
    source_commit = git_commit(root, source_commit)
    require_source_head(root, source_commit)
    state_file, _ = repo_path(root, state_path)
    state = load_json(state_file)
    inventory_matches = state.get("protected_heads") == EXPECTED_PROTECTED_HEADS
    entries: list[dict[str, Any]] = []
    for name in sorted(EXPECTED_PROTECTED_HEADS):
        protected_commit = EXPECTED_PROTECTED_HEADS[name]
        ref = PROTECTED_REFS[name]
        expected_tip = EXPECTED_PROTECTED_REF_TIPS[name]
        commit_result = run_git(root, "cat-file", "-e", f"{protected_commit}^{{commit}}")
        tip_result = run_git(root, "rev-parse", "--verify", ref)
        actual_tip = tip_result.stdout.strip() if tip_result.returncode == 0 else None
        ancestry = bool(
            actual_tip
            and run_git(root, "merge-base", "--is-ancestor", protected_commit, actual_tip).returncode == 0
        )
        entry = {
            "name": name,
            "protected_commit": protected_commit,
            "ref": ref,
            "expected_tip": expected_tip,
            "actual_tip": actual_tip,
            "commit_readable": commit_result.returncode == 0,
            "ref_matches": actual_tip == expected_tip,
            "protected_commit_in_ref_history": ancestry,
            "passed": commit_result.returncode == 0 and actual_tip == expected_tip and ancestry,
        }
        entries.append(entry)
    return {
        "schema": PROTECTED_REPORT_SCHEMA,
        "remediation_id": REMEDIATION_ID,
        "source_commit": source_commit,
        "generated_at": parse_timestamp(generated_at),
        "inventory_matches_state": inventory_matches,
        "entries": entries,
        "passed": inventory_matches and all(entry["passed"] for entry in entries),
    }


def validate_terminal_spec(
    root: Path,
    spec: dict[str, Any],
    source_commit: str,
    tag_name: str,
) -> None:
    exact_object(spec, name="terminal_spec", required=TERMINAL_SPEC_FIELDS)
    if spec.get("source_commit") != source_commit:
        raise EvidenceBuildError("terminal_spec_source_mismatch")

    repository = exact_object(
        spec.get("repository_identity"),
        name="terminal_spec_repository_identity",
        required=REPOSITORY_IDENTITY_FIELDS,
    )
    for field in ("repository_id", "worktree_id", "worktree_realpath"):
        nonempty_string(repository[field], f"terminal_spec_repository_identity_invalid:{field}")
    declared_worktree = Path(repository["worktree_realpath"])
    if not declared_worktree.is_absolute() or declared_worktree.resolve() != root.resolve():
        raise EvidenceBuildError("terminal_spec_repository_worktree_mismatch")

    if spec.get("protected_heads") != EXPECTED_PROTECTED_HEADS:
        raise EvidenceBuildError("terminal_spec_protected_heads_mismatch")
    for field in ("artifact_sha256", "applied_diff_sha256", "result_sha256"):
        if not isinstance(spec.get(field), str) or not HEX64.fullmatch(spec[field]):
            raise EvidenceBuildError(f"terminal_spec_hash_invalid:{field}")

    for field in ("shell_build_identity", "backend_build_identity"):
        value = exact_object(
            spec.get(field),
            name=f"terminal_spec_{field}",
            required=BUILD_IDENTITY_REQUIRED_FIELDS,
            optional=BUILD_IDENTITY_OPTIONAL_FIELDS,
        )
        nonempty_string(value["build_id"], f"terminal_spec_build_identity_invalid:{field}:build_id")
        if value.get("source_commit") != source_commit:
            raise EvidenceBuildError(f"terminal_spec_build_identity_invalid:{field}")
        has_artifact_path = "artifact_path" in value
        has_artifact_hash = "artifact_sha256" in value
        if has_artifact_path != has_artifact_hash:
            raise EvidenceBuildError(f"terminal_spec_build_artifact_incomplete:{field}")
        if has_artifact_path:
            artifact_value = nonempty_string(
                value["artifact_path"],
                f"terminal_spec_build_artifact_path_invalid:{field}",
            )
            artifact, relative = repo_path(root, artifact_value)
            if relative != artifact_value:
                raise EvidenceBuildError(f"terminal_spec_build_artifact_path_not_canonical:{field}")
            if not isinstance(value["artifact_sha256"], str) or not HEX64.fullmatch(value["artifact_sha256"]):
                raise EvidenceBuildError(f"terminal_spec_build_artifact_hash_invalid:{field}")
            if sha256_file(artifact) != value["artifact_sha256"]:
                raise EvidenceBuildError(f"terminal_spec_build_artifact_hash_mismatch:{field}")

    target = exact_object(
        spec.get("target_plugin_identity"),
        name="terminal_spec_target_plugin_identity",
        required=TARGET_PLUGIN_IDENTITY_REQUIRED_FIELDS,
        optional=TARGET_PLUGIN_IDENTITY_OPTIONAL_FIELDS,
    )
    nonempty_string(target["plugin_id"], "terminal_spec_target_plugin_id_invalid")
    if target.get("source_head") != source_commit:
        raise EvidenceBuildError("terminal_spec_target_identity_invalid")

    for field in ("prompt_identity", "context_identity"):
        identity = exact_object(
            spec.get(field),
            name=f"terminal_spec_{field}",
            required=CONTENT_IDENTITY_FIELDS,
        )
        nonempty_string(identity["id"], f"terminal_spec_content_identity_invalid:{field}:id")
        if not isinstance(identity["sha256"], str) or not HEX64.fullmatch(identity["sha256"]):
            raise EvidenceBuildError(f"terminal_spec_content_identity_invalid:{field}:sha256")

    run_id = nonempty_string(
        spec.get("orchestrator_run_id"),
        "terminal_spec_orchestrator_run_id_invalid",
    )
    nonempty_string(spec.get("task_id"), "terminal_spec_task_id_invalid")
    nonempty_string(
        spec.get("orchestrator_attempt_id"),
        "terminal_spec_orchestrator_attempt_id_invalid",
    )
    nonempty_string(spec.get("target"), "terminal_spec_target_invalid")
    participants = exact_object(
        spec.get("participants"),
        name="terminal_spec_participants",
        required=PARTICIPANT_ROLES,
    )
    invocation_ids: set[str] = set()
    output_ids: set[str] = set()
    acknowledgement_ids: set[str] = set()
    all_participant_ids: set[str] = set()
    artifact_hashes: set[str] = set()
    for role, record in participants.items():
        record = exact_object(
            record,
            name=f"terminal_spec_participant_{role}",
            required=PARTICIPANT_FIELDS,
        )
        if record.get("status") not in {"passed", "succeeded"}:
            raise EvidenceBuildError(f"terminal_spec_participant_invalid:{role}")
        for field, values in (
            ("invocation_id", invocation_ids),
            ("output_id", output_ids),
            ("consumer_acknowledgement_id", acknowledgement_ids),
        ):
            value = nonempty_string(
                record.get(field),
                f"terminal_spec_participant_field_invalid:{role}:{field}",
            )
            values.add(value)
            all_participant_ids.add(value)
        raw_sha256(
            record.get("output_sha256"),
            f"terminal_spec_participant_output_hash_invalid:{role}",
        )
        artifact = record.get("artifact_sha256")
        if not isinstance(artifact, str) or not HEX64.fullmatch(artifact):
            raise EvidenceBuildError(f"terminal_spec_participant_artifact_invalid:{role}")
        artifact_hashes.add(artifact)
    if min(len(invocation_ids), len(output_ids), len(acknowledgement_ids)) != len(PARTICIPANT_ROLES):
        raise EvidenceBuildError("terminal_spec_participant_id_reuse")
    if len(all_participant_ids) != 3 * len(PARTICIPANT_ROLES):
        raise EvidenceBuildError("terminal_spec_participant_cross_field_id_reuse")
    if artifact_hashes != {spec["artifact_sha256"]}:
        raise EvidenceBuildError("terminal_spec_participant_artifact_mismatch")

    approval = exact_object(
        spec.get("approval"),
        name="terminal_spec_approval",
        required=APPROVAL_FIELDS,
    )
    if (
        not isinstance(approval.get("approval_id"), str)
        or re.fullmatch(r"apr_[A-Za-z0-9_-]+", approval["approval_id"]) is None
        or not isinstance(approval.get("generation"), int)
        or isinstance(approval.get("generation"), bool)
        or approval["generation"] < 1
        or approval.get("state") != "consumed"
        or approval.get("artifact_sha256") != spec["artifact_sha256"]
        or approval.get("orchestrator_run_id") != run_id
    ):
        raise EvidenceBuildError("terminal_spec_approval_invalid")

    production_proof = exact_object(
        spec.get("production_proof"),
        name="terminal_spec_production_proof",
        required=PRODUCTION_PROOF_FIELDS,
    )
    raw_sha256(
        production_proof.get("proof_sha256"),
        "terminal_spec_production_proof_hash_invalid",
    )
    if production_proof.get("terminal_proof_eligible") is not True:
        raise EvidenceBuildError("terminal_spec_production_proof_not_terminal")
    nonempty_string(
        production_proof.get("recovery_id"),
        "terminal_spec_production_proof_recovery_id_invalid",
    )
    if validate_claim_ceiling(production_proof.get("claim_ceiling")) != spec.get("claim_ceiling"):
        raise EvidenceBuildError("terminal_spec_production_proof_claim_mismatch")

    for role, field in (
        ("reviewer", "reviewer_result"),
        ("verifier", "verifier_result"),
        ("anti_cheat", "anti_cheat_result"),
    ):
        result = exact_object(
            spec.get(field),
            name=f"terminal_spec_{field}",
            required=PARTICIPANT_RESULT_FIELDS,
        )
        if (
            result.get("status") not in {"passed", "succeeded"}
            or result.get("invocation_id") != participants[role]["invocation_id"]
        ):
            raise EvidenceBuildError(f"terminal_spec_participant_result_invalid:{role}")

    authority = exact_object(
        spec.get("authority_validation"),
        name="terminal_spec_authority_validation",
        required=AUTHORITY_VALIDATION_FIELDS,
    )
    if (
        authority.get("source_commit") != source_commit
        or authority.get("tag_name") != tag_name
        or authority.get("validator_path") != AUTHORITY_VALIDATOR_PATH
        or not isinstance(authority.get("validator_sha256"), str)
        or not HEX64.fullmatch(authority["validator_sha256"])
        or not isinstance(authority.get("artifact_sha256"), str)
        or not HEX64.fullmatch(authority["artifact_sha256"])
        or authority.get("result") != "pass"
        or authority.get("passed") is not True
    ):
        raise EvidenceBuildError("terminal_spec_authority_validation_invalid")
    if git_blob_sha256(root, source_commit, AUTHORITY_VALIDATOR_PATH) != authority["validator_sha256"]:
        raise EvidenceBuildError("terminal_spec_authority_validator_source_hash_mismatch")
    authority_artifact_value = nonempty_string(
        authority["artifact_path"],
        "terminal_spec_authority_artifact_path_invalid",
    )
    authority_artifact, authority_relative = repo_path(root, authority_artifact_value)
    if authority_relative != authority_artifact_value:
        raise EvidenceBuildError("terminal_spec_authority_artifact_path_not_canonical")
    if sha256_file(authority_artifact) != authority["artifact_sha256"]:
        raise EvidenceBuildError("terminal_spec_authority_artifact_hash_mismatch")

    redaction = exact_object(
        spec.get("redaction_verdict"),
        name="terminal_spec_redaction_verdict",
        required=REDACTION_VERDICT_REQUIRED_FIELDS,
        optional=REDACTION_VERDICT_OPTIONAL_FIELDS,
    )
    if redaction.get("verdict") != "passed":
        raise EvidenceBuildError("terminal_spec_redaction_verdict_invalid")
    nonempty_string(redaction.get("scanner"), "terminal_spec_redaction_scanner_invalid")
    if "artifact_sha256" in redaction and (
        not isinstance(redaction["artifact_sha256"], str)
        or not HEX64.fullmatch(redaction["artifact_sha256"])
    ):
        raise EvidenceBuildError("terminal_spec_redaction_artifact_hash_invalid")
    validate_claim_ceiling(spec.get("claim_ceiling"))
    validate_terminal_production_cross_binding(
        root,
        spec,
        source_commit=source_commit,
    )


def build_terminal_receipt(
    spec: dict[str, Any],
    *,
    evidence_hash: str,
    generated_at: str,
) -> dict[str, Any]:
    if not HEX64.fullmatch(evidence_hash):
        raise EvidenceBuildError("evidence_hash_invalid")
    return {
        "schema": TERMINAL_RECEIPT_SCHEMA,
        "remediation_id": REMEDIATION_ID,
        "verdict": TERMINAL_VERDICT,
        **spec,
        "evidence_hash": evidence_hash,
        "generated_at": generated_at,
    }


def protected_report_heads(report: dict[str, Any]) -> dict[str, str]:
    if report.get("schema") != PROTECTED_REPORT_SCHEMA or report.get("passed") is not True:
        raise EvidenceBuildError("protected_head_report_not_passed")
    entries = report.get("entries")
    if not isinstance(entries, list):
        raise EvidenceBuildError("protected_head_report_entries_invalid")
    heads: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("passed") is not True:
            raise EvidenceBuildError("protected_head_report_entry_invalid")
        name = entry.get("name")
        commit = entry.get("protected_commit")
        if not isinstance(name, str) or not isinstance(commit, str):
            raise EvidenceBuildError("protected_head_report_identity_invalid")
        heads[name] = commit
    return heads


def build_terminal_evidence(
    root: Path,
    *,
    spec_path: str | Path,
    artifact_paths: Sequence[str | Path],
    receipt_path: str | Path,
    manifest_path: str | Path,
    restoration_path: str | Path,
    protected_report_path: str | Path,
    tag_name: str,
    bundle_path: str | Path,
    generated_at: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    spec_file, _ = repo_path(root, spec_path)
    spec = load_json(spec_file)
    source_commit = git_commit(root, str(spec.get("source_commit") or ""))
    require_source_head(root, source_commit)
    if not tag_name.strip():
        raise EvidenceBuildError("tag_name_invalid")
    validate_terminal_spec(root, spec, source_commit, tag_name)
    receipt_output, receipt_relative = repo_path(root, receipt_path, must_exist=False)
    manifest_output, manifest_relative = repo_path(root, manifest_path, must_exist=False)
    if receipt_relative == manifest_relative:
        raise EvidenceBuildError("terminal_receipt_manifest_path_reused")

    restoration, restoration_relative = repo_path(root, restoration_path)
    protected_report_file, protected_report_relative = repo_path(root, protected_report_path)
    report = load_json(protected_report_file)
    if report.get("source_commit") != source_commit:
        raise EvidenceBuildError("protected_head_report_source_mismatch")
    if protected_report_heads(report) != spec["protected_heads"]:
        raise EvidenceBuildError("protected_head_report_inventory_mismatch")

    proving_binding = require_mapping(
        spec.get("production_proving_receipt"),
        "terminal_spec_production_proving_receipt_missing",
    )
    lifecycle_binding = require_mapping(
        spec.get("lifecycle_receipt"),
        "terminal_spec_lifecycle_receipt_missing",
    )
    proving_file, proving_relative = repo_path(root, str(proving_binding.get("path") or ""))
    lifecycle_file, lifecycle_relative = repo_path(root, str(lifecycle_binding.get("path") or ""))
    requested_paths: list[str | Path] = [
        *artifact_paths,
        restoration,
        protected_report_file,
        proving_file,
        lifecycle_file,
    ]
    entries_by_path: dict[str, dict[str, Any]] = {}
    for value in requested_paths:
        entry = artifact_entry(root, value)
        relative = entry["path"]
        if relative in {receipt_relative, manifest_relative}:
            raise EvidenceBuildError(f"recursive_terminal_artifact_forbidden:{relative}")
        entries_by_path.setdefault(relative, entry)
    artifacts = [entries_by_path[path] for path in sorted(entries_by_path)]
    if not artifacts:
        raise EvidenceBuildError("terminal_artifacts_missing")

    authority = spec["authority_validation"]
    authority_path = authority.get("artifact_path")
    authority_hash = authority.get("artifact_sha256")
    if (
        not isinstance(authority_path, str)
        or authority_path not in entries_by_path
        or entries_by_path[authority_path]["sha256"] != authority_hash
    ):
        raise EvidenceBuildError("authority_validation_artifact_not_in_evidence_set")

    evidence_hash = evidence_set_hash(artifacts)
    generated = parse_timestamp(generated_at)
    receipt = build_terminal_receipt(spec, evidence_hash=evidence_hash, generated_at=generated)
    write_json_atomic(receipt_output, receipt)
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "remediation_id": REMEDIATION_ID,
        "source_commit": source_commit,
        "tag_name": tag_name,
        "bundle_name": Path(bundle_path).name,
        "restoration_instructions": {
            "path": restoration_relative,
            "sha256": sha256_file(restoration),
        },
        "protected_heads_report": {
            "path": protected_report_relative,
            "sha256": sha256_file(protected_report_file),
        },
        "receipt": {
            "path": receipt_relative,
            "sha256": sha256_file(receipt_output),
        },
        "production_proving_receipt": {
            "path": proving_relative,
            "sha256": sha256_file(proving_file),
        },
        "lifecycle_receipt": {
            "path": lifecycle_relative,
            "sha256": sha256_file(lifecycle_file),
        },
        "artifacts": artifacts,
        "evidence_hash": evidence_hash,
        "generated_at": generated,
    }
    write_json_atomic(manifest_output, manifest)
    return receipt, manifest


def _root(value: str | None) -> Path:
    return Path(value or Path(__file__).resolve().parents[1]).resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="registered SpiritOS remediation worktree")
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    evidence = subparsers.add_parser("evidence-hash", help="hash a set of repository artifacts")
    evidence.add_argument("--artifact", action="append", required=True)

    profile = subparsers.add_parser("profile-receipt", help="hash an existing profile artifact")
    profile.add_argument("--profile-id", required=True)
    profile.add_argument("--command", required=True)
    profile.add_argument("--source-commit", required=True)
    profile.add_argument("--artifact-path", required=True)
    profile.add_argument("--receipt-path", required=True)
    profile.add_argument("--claim-ceiling", required=True)
    profile.add_argument("--completed-at")

    execute = subparsers.add_parser("run-profile", help="execute and receipt one exact profile command")
    execute.add_argument("--profile-id", required=True)
    execute.add_argument("--command", required=True)
    execute.add_argument("--source-commit", required=True)
    execute.add_argument("--artifact-path", required=True)
    execute.add_argument("--receipt-path", required=True)
    execute.add_argument("--claim-ceiling", required=True)

    protected = subparsers.add_parser("protected-head-report", help="verify protected commits and refs")
    protected.add_argument("--source-commit", required=True)
    protected.add_argument("--state", default="docs/architecture/foundation-remediation-r1-state.json")
    protected.add_argument("--output", required=True)
    protected.add_argument("--generated-at")

    terminal = subparsers.add_parser("terminal", help="build terminal receipt and immutable manifest")
    terminal.add_argument("--spec", required=True)
    terminal.add_argument("--artifact", action="append", required=True)
    terminal.add_argument("--receipt-path", required=True)
    terminal.add_argument("--manifest-path", required=True)
    terminal.add_argument("--restoration-path", required=True)
    terminal.add_argument("--protected-head-report", required=True)
    terminal.add_argument("--tag-name", required=True)
    terminal.add_argument("--bundle-path", required=True)
    terminal.add_argument("--generated-at")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = _root(args.root)
    try:
        if args.command_name == "evidence-hash":
            entries = [artifact_entry(root, path) for path in args.artifact]
            print(json.dumps({"artifacts": entries, "evidence_hash": evidence_set_hash(entries)}, sort_keys=True))
            return 0
        if args.command_name == "profile-receipt":
            receipt = build_profile_receipt(
                root,
                profile_id=args.profile_id,
                command=args.command,
                source_commit=args.source_commit,
                artifact_path=args.artifact_path,
                claim_ceiling=args.claim_ceiling,
                completed_at=args.completed_at,
            )
            output, _ = repo_path(root, args.receipt_path, must_exist=False)
            write_json_atomic(output, receipt)
            print(json.dumps({"receipt_path": args.receipt_path, "receipt_sha256": sha256_file(output)}))
            return 0
        if args.command_name == "run-profile":
            _, receipt, returncode = run_profile(
                root,
                profile_id=args.profile_id,
                command=args.command,
                source_commit=args.source_commit,
                artifact_path=args.artifact_path,
                receipt_path=args.receipt_path,
                claim_ceiling=args.claim_ceiling,
            )
            if receipt is not None:
                print(json.dumps({"profile_id": args.profile_id, "result": "pass"}))
            return returncode
        if args.command_name == "protected-head-report":
            report = build_protected_head_report(
                root,
                source_commit=args.source_commit,
                state_path=args.state,
                generated_at=args.generated_at,
            )
            output, _ = repo_path(root, args.output, must_exist=False)
            write_json_atomic(output, report)
            print(json.dumps({"output": args.output, "passed": report["passed"]}))
            return 0 if report["passed"] else 1
        if args.command_name == "terminal":
            receipt, manifest = build_terminal_evidence(
                root,
                spec_path=args.spec,
                artifact_paths=args.artifact,
                receipt_path=args.receipt_path,
                manifest_path=args.manifest_path,
                restoration_path=args.restoration_path,
                protected_report_path=args.protected_head_report,
                tag_name=args.tag_name,
                bundle_path=args.bundle_path,
                generated_at=args.generated_at,
            )
            print(json.dumps({
                "evidence_hash": receipt["evidence_hash"],
                "manifest_sha256": sha256_file(repo_path(root, args.manifest_path)[0]),
                "receipt_sha256": manifest["receipt"]["sha256"],
            }, sort_keys=True))
            return 0
        parser.error("unknown command")
    except EvidenceBuildError as error:
        print(f"FOUNDATION_REMEDIATION_R1_EVIDENCE_BUILD_FAILED {error}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
