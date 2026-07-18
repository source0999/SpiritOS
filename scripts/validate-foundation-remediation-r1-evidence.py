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


def parse_timestamp(value: object) -> bool:
    if not nonempty(value):
        return False
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def evidence_set_hash(entries: list[tuple[str, str]]) -> str:
    canonical = "".join(f"{digest}  {path}\n" for digest, path in sorted(entries))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def git_blob_sha256(root: Path, ref: str, relative: str) -> str | None:
    shown = run_git_bytes(root, "show", f"{ref}:{relative}")
    if shown.returncode != 0:
        return None
    return hashlib.sha256(shown.stdout).hexdigest()


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
        "orchestrator_run_id",
        "participants",
        "approval",
        "applied_diff_sha256",
        "result_sha256",
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
    if missing:
        failures.append("receipt_fields_missing:" + ",".join(missing))
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
    if not nonempty(receipt.get("orchestrator_run_id")):
        failures.append("receipt_orchestrator_run_id_missing")

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
        elif receipt.get("result_sha256") not in artifact_hashes:
            failures.append("receipt_participant_artifact_result_mismatch")

    approval = receipt.get("approval")
    if not isinstance(approval, dict) or not str(approval.get("approval_id") or "").startswith("apr_"):
        failures.append("receipt_approval_invalid")
    elif not isinstance(approval.get("generation"), int) or approval["generation"] < 1:
        failures.append("receipt_approval_generation_invalid")
    elif approval.get("artifact_sha256") != receipt.get("result_sha256"):
        failures.append("receipt_approval_artifact_mismatch")
    elif approval.get("orchestrator_run_id") != receipt.get("orchestrator_run_id"):
        failures.append("receipt_approval_orchestrator_mismatch")
    for field in ("applied_diff_sha256", "result_sha256", "evidence_hash"):
        value = receipt.get(field)
        if not isinstance(value, str) or not HEX64.fullmatch(value):
            failures.append(f"receipt_hash_invalid:{field}")

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
    validate_authority_binding(root, receipt.get("authority_validation"), evidence, failures)


def validate_manifest(
    root: Path,
    manifest: dict[str, Any],
    evidence: dict[str, Any],
    receipt: dict[str, Any],
    receipt_path: Path,
    failures: list[str],
) -> None:
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
    restoration_entry = manifest.get("restoration_instructions")
    restoration_path = resolve_any_path(root, evidence.get("restoration_instructions_path"))
    if not isinstance(restoration_entry, dict) or restoration_path is None:
        failures.append("manifest_restoration_instructions_missing")
    else:
        if restoration_entry.get("path") != evidence.get("restoration_instructions_path"):
            failures.append("manifest_restoration_path_mismatch")
        restoration_hash = restoration_entry.get("sha256")
        if not isinstance(restoration_hash, str) or not HEX64.fullmatch(restoration_hash):
            failures.append("manifest_restoration_hash_invalid")
        elif not restoration_path.is_file() or sha256(restoration_path) != restoration_hash:
            failures.append("manifest_restoration_hash_mismatch")
    receipt_entry = manifest.get("receipt")
    if not isinstance(receipt_entry, dict):
        failures.append("manifest_receipt_entry_missing")
    else:
        expected_relative = receipt_path.relative_to(root).as_posix()
        if receipt_entry.get("path") != expected_relative:
            failures.append("manifest_receipt_path_mismatch")
        if receipt_entry.get("sha256") != evidence.get("receipt_sha256"):
            failures.append("manifest_receipt_hash_mismatch")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        failures.append("manifest_artifacts_missing")
        return
    hash_entries: list[tuple[str, str]] = []
    seen_paths: set[str] = set()
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            failures.append(f"manifest_artifact_invalid:{index}")
            continue
        path_value = artifact.get("path")
        digest = artifact.get("sha256")
        size = artifact.get("size_bytes")
        if not nonempty(path_value) or not isinstance(digest, str) or not HEX64.fullmatch(digest):
            failures.append(f"manifest_artifact_identity_invalid:{index}")
            continue
        if path_value in seen_paths:
            failures.append(f"manifest_artifact_duplicate:{path_value}")
            continue
        seen_paths.add(str(path_value))
        path = resolve_any_path(root, path_value)
        if path is None or not path.is_file():
            failures.append(f"manifest_artifact_missing:{path_value}")
            continue
        if sha256(path) != digest:
            failures.append(f"manifest_artifact_hash_mismatch:{path_value}")
        if not isinstance(size, int) or size != path.stat().st_size:
            failures.append(f"manifest_artifact_size_mismatch:{path_value}")
        hash_entries.append((digest, str(path_value)))
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
    if receipt is not None:
        validate_receipt(root, receipt, state, evidence, failures)
    if receipt is not None and manifest is not None:
        validate_manifest(root, manifest, evidence, receipt, receipt_path, failures)
    validate_recovery_anchor(root, evidence, receipt_path, manifest_path, failures)

    if failures:
        print("FOUNDATION_REMEDIATION_R1_EVIDENCE_INVALID")
        print("\n".join(sorted(set(failures))))
        return 1
    print("FOUNDATION_REMEDIATION_R1_EVIDENCE_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
