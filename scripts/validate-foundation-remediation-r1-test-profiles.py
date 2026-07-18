#!/usr/bin/env python3
"""Validate the R1 test-profile registry without trusting pass labels."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


EXPECTED_SCHEMA = "spiritos-foundation-remediation-r1-test-profiles/v1"
EXPECTED_ID = "spiritos-foundation-remediation-r1"
PROFILE_RECEIPT_SCHEMA = "spiritos-foundation-remediation-r1-profile-execution-receipt/v1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_STATUSES = {"pending", "passed", "failed", "blocked"}
REQUIRED_IDS = {
    "continuity",
    "authority-callgraph",
    "evidence-provenance",
    "test-profiles",
    "completion-regression",
    "portable-authority",
    "cartographer-authority",
    "spiritflix-authority",
    "design-security",
    "coding-lifecycle",
    "target-adapters-1-10",
    "production-orchestrator",
    "runtime-contracts",
    "backend-state",
    "recovery-fallback",
    "production-api-authority",
    "proving-harness-regression",
    "source-proxy-regression",
    "typecheck",
    "production-build",
    "secret-scan",
    "git-integrity",
}
PLACEHOLDER_COMMANDS = (
    "focused ",
    "complete authority",
    "isolated real ",
    " plus prompt",
    "tracked diff and ",
    "protected-head verification",
)
CONCRETE_COMMAND_PREFIXES = (
    "/home/source/spiritos/.venv/bin/python ",
    "bash ",
    "git ",
    "npm ",
    "python3 ",
)
RECURSIVE_PROFILE_COMMANDS = {
    "evidence-provenance": "validate-foundation-remediation-r1-evidence.py",
    "test-profiles": "validate-foundation-remediation-r1-test-profiles.py",
}
# The real HTTP proving run belongs to terminal authority/evidence validation. A
# test-profile receipt must never stand in for that production execution proof.
FORBIDDEN_PROFILE_IDS = {"clean-proving-task"}


def load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, f"json_unreadable_or_malformed:{path}:{error}"
    if not isinstance(value, dict):
        return None, f"json_not_object:{path}"
    return value, None


def is_terminal(state: dict[str, Any]) -> bool:
    closeout = state.get("closeout")
    return bool(
        state.get("go_eligible") is True
        or state.get("next_gate_id") in {"r1_complete", "none", None}
        or "r1_complete" in (state.get("completed_gate_ids") or [])
        or (isinstance(closeout, dict) and closeout.get("status") == "complete")
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tracked(root: Path, relative: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", relative],
        text=True,
        capture_output=True,
        check=False,
    ).returncode == 0


def git_blob_sha256(root: Path, ref: str, relative: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(root), "show", f"{ref}:{relative}"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return hashlib.sha256(result.stdout).hexdigest()


def safe_repo_path(root: Path, value: str) -> Path | None:
    path = (root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    return path


def command_definition_failure(profile_id: str, command: object) -> str | None:
    if not isinstance(command, str) or not command.strip():
        return f"profile_command_invalid:{profile_id}"
    normalized = " ".join(command.strip().split())
    lowered = normalized.lower()
    if profile_id in FORBIDDEN_PROFILE_IDS:
        return f"terminal_proof_must_not_be_test_profile:{profile_id}"
    if any(marker in lowered for marker in PLACEHOLDER_COMMANDS):
        return f"profile_command_placeholder:{profile_id}"
    recursive = RECURSIVE_PROFILE_COMMANDS.get(profile_id)
    if recursive and recursive in lowered:
        return f"profile_command_recursive:{profile_id}"
    if not lowered.startswith(CONCRETE_COMMAND_PREFIXES):
        return f"profile_command_not_executable:{profile_id}"
    return None


def validate_receipt(
    root: Path,
    profile: dict[str, Any],
    receipt: object,
    expected_source: str | None,
    terminal_tag: str | None,
    seen_receipt_paths: set[str],
    seen_bound_profile_ids: set[str],
    failures: list[str],
) -> None:
    profile_id = str(profile.get("id") or "")
    if not isinstance(receipt, dict):
        failures.append(f"latest_accepted_missing:{profile_id}")
        return
    required = {"status", "source_commit", "receipt_path", "receipt_sha256", "completed_at"}
    missing = sorted(required - set(receipt))
    if missing:
        failures.append(f"latest_accepted_fields_missing:{profile_id}:{','.join(missing)}")
        return
    if receipt.get("status") != "passed":
        failures.append(f"latest_accepted_not_passed:{profile_id}")
    source = receipt.get("source_commit")
    if not isinstance(source, str) or not HEX40.fullmatch(source):
        failures.append(f"latest_accepted_source_invalid:{profile_id}")
    elif expected_source and source != expected_source:
        failures.append(f"latest_accepted_source_mismatch:{profile_id}")
    receipt_hash = receipt.get("receipt_sha256")
    if not isinstance(receipt_hash, str) or not HEX64.fullmatch(receipt_hash):
        failures.append(f"latest_accepted_hash_invalid:{profile_id}")
    receipt_path = receipt.get("receipt_path")
    if not isinstance(receipt_path, str) or not receipt_path.strip():
        failures.append(f"latest_accepted_path_invalid:{profile_id}")
        return
    path = safe_repo_path(root, receipt_path)
    if path is None or not path.is_file():
        failures.append(f"latest_accepted_receipt_missing:{profile_id}")
        return
    relative = path.relative_to(root).as_posix()
    if relative in seen_receipt_paths:
        failures.append(f"latest_accepted_receipt_reused:{profile_id}:{relative}")
    seen_receipt_paths.add(relative)
    if not tracked(root, relative):
        failures.append(f"latest_accepted_receipt_untracked:{profile_id}")
    if isinstance(receipt_hash, str) and HEX64.fullmatch(receipt_hash) and sha256(path) != receipt_hash:
        failures.append(f"latest_accepted_receipt_hash_mismatch:{profile_id}")
    if not isinstance(receipt.get("completed_at"), str) or not receipt["completed_at"].strip():
        failures.append(f"latest_accepted_completed_at_invalid:{profile_id}")

    payload, payload_error = load_json(path)
    if payload_error:
        failures.append(f"profile_execution_receipt_invalid:{profile_id}:{payload_error}")
        return
    assert payload is not None
    payload_required = {
        "schema",
        "remediation_id",
        "profile_id",
        "command",
        "source_commit",
        "artifact_path",
        "artifact_sha256",
        "result",
        "passed",
        "claim_ceiling",
        "completed_at",
    }
    payload_missing = sorted(payload_required - set(payload))
    if payload_missing:
        failures.append(
            f"profile_execution_receipt_fields_missing:{profile_id}:{','.join(payload_missing)}"
        )
    if payload.get("schema") != PROFILE_RECEIPT_SCHEMA:
        failures.append(f"profile_execution_receipt_schema_mismatch:{profile_id}")
    if payload.get("remediation_id") != EXPECTED_ID:
        failures.append(f"profile_execution_receipt_remediation_mismatch:{profile_id}")
    bound_profile_id = payload.get("profile_id")
    if bound_profile_id != profile_id:
        failures.append(f"profile_execution_receipt_profile_mismatch:{profile_id}")
    elif bound_profile_id in seen_bound_profile_ids:
        failures.append(f"profile_execution_receipt_profile_reused:{profile_id}")
    else:
        seen_bound_profile_ids.add(profile_id)
    if payload.get("command") != profile.get("command"):
        failures.append(f"profile_execution_receipt_command_mismatch:{profile_id}")
    if payload.get("claim_ceiling") != profile.get("claim_ceiling"):
        failures.append(f"profile_execution_receipt_claim_ceiling_mismatch:{profile_id}")
    if payload.get("source_commit") != source or (expected_source and payload.get("source_commit") != expected_source):
        failures.append(f"profile_execution_receipt_source_mismatch:{profile_id}")
    if payload.get("result") != "pass" or payload.get("passed") is not True:
        failures.append(f"profile_execution_receipt_result_not_pass:{profile_id}")
    if payload.get("completed_at") != receipt.get("completed_at"):
        failures.append(f"profile_execution_receipt_completed_at_mismatch:{profile_id}")

    artifact_value = payload.get("artifact_path")
    artifact_hash = payload.get("artifact_sha256")
    if not isinstance(artifact_value, str) or not artifact_value.strip():
        failures.append(f"profile_execution_artifact_path_invalid:{profile_id}")
        return
    artifact_path = safe_repo_path(root, artifact_value)
    if artifact_path is None or not artifact_path.is_file():
        failures.append(f"profile_execution_artifact_missing:{profile_id}")
        return
    artifact_relative = artifact_path.relative_to(root).as_posix()
    if not tracked(root, artifact_relative):
        failures.append(f"profile_execution_artifact_untracked:{profile_id}")
    if not isinstance(artifact_hash, str) or not HEX64.fullmatch(artifact_hash):
        failures.append(f"profile_execution_artifact_hash_invalid:{profile_id}")
    elif sha256(artifact_path) != artifact_hash:
        failures.append(f"profile_execution_artifact_hash_mismatch:{profile_id}")

    if terminal_tag:
        if git_blob_sha256(root, terminal_tag, relative) != sha256(path):
            failures.append(f"profile_execution_receipt_not_bound_to_terminal_tag:{profile_id}")
        if git_blob_sha256(root, terminal_tag, artifact_relative) != sha256(artifact_path):
            failures.append(f"profile_execution_artifact_not_bound_to_terminal_tag:{profile_id}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(os.environ.get("SPIRITOS_FOUNDATION_R1_ROOT", Path(__file__).resolve().parents[1])),
    )
    args = parser.parse_args()
    root = args.root.resolve()
    registry_path = root / "docs/architecture/foundation-remediation-r1-test-profiles.json"
    state_path = root / "docs/architecture/foundation-remediation-r1-state.json"
    registry, registry_error = load_json(registry_path)
    state, state_error = load_json(state_path)
    failures: list[str] = []
    if registry_error:
        failures.append(registry_error)
    if state_error:
        failures.append(state_error)
    if failures:
        print("FOUNDATION_REMEDIATION_R1_TEST_PROFILES_INVALID")
        print("\n".join(failures))
        return 1
    assert registry is not None and state is not None

    terminal = is_terminal(state)
    if registry.get("schema") != EXPECTED_SCHEMA:
        failures.append("registry_schema_mismatch")
    if registry.get("remediation_id") != EXPECTED_ID:
        failures.append("registry_remediation_id_mismatch")
    profiles = registry.get("profiles")
    if not isinstance(profiles, list):
        failures.append("profiles_not_array")
        profiles = []

    seen: set[str] = set()
    terminal_evidence = state.get("terminal_evidence")
    expected_source = (
        terminal_evidence.get("source_commit")
        if isinstance(terminal_evidence, dict) and isinstance(terminal_evidence.get("source_commit"), str)
        else None
    )
    terminal_tag = (
        terminal_evidence.get("tag_name")
        if isinstance(terminal_evidence, dict) and isinstance(terminal_evidence.get("tag_name"), str)
        else None
    )
    seen_receipt_paths: set[str] = set()
    seen_bound_profile_ids: set[str] = set()
    for index, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            failures.append(f"profile_not_object:{index}")
            continue
        profile_id = profile.get("id")
        if not isinstance(profile_id, str) or not profile_id.strip():
            failures.append(f"profile_id_invalid:{index}")
            continue
        if profile_id in seen:
            failures.append(f"profile_id_duplicate:{profile_id}")
        seen.add(profile_id)
        for field in ("product", "command", "claim_ceiling"):
            if not isinstance(profile.get(field), str) or not profile[field].strip():
                failures.append(f"profile_field_invalid:{profile_id}:{field}")
        command_failure = command_definition_failure(profile_id, profile.get("command"))
        if command_failure:
            failures.append(command_failure)
        if profile.get("mandatory") is not True:
            failures.append(f"mandatory_profile_not_mandatory:{profile_id}")
        status = profile.get("status")
        if status not in ALLOWED_STATUSES:
            failures.append(f"profile_status_invalid:{profile_id}")
        receipt = profile.get("latest_accepted")
        if status == "passed":
            validate_receipt(
                root,
                profile,
                receipt,
                expected_source if terminal else None,
                terminal_tag if terminal else None,
                seen_receipt_paths,
                seen_bound_profile_ids,
                failures,
            )
        elif receipt is not None:
            failures.append(f"nonpassed_profile_has_accepted_receipt:{profile_id}")
        if terminal:
            if status != "passed":
                failures.append(f"terminal_profile_not_passed:{profile_id}")

    missing = sorted(REQUIRED_IDS - seen)
    unexpected = sorted(seen - REQUIRED_IDS)
    if missing:
        failures.append("required_profiles_missing:" + ",".join(missing))
    if unexpected:
        failures.append("unexpected_profiles:" + ",".join(unexpected))
    if terminal and not expected_source:
        failures.append("terminal_profile_source_commit_missing")
    if terminal and not terminal_tag:
        failures.append("terminal_profile_tag_name_missing")
    if terminal and len(seen_bound_profile_ids) != len(REQUIRED_IDS):
        failures.append("terminal_profile_execution_evidence_incomplete")

    if failures:
        print("FOUNDATION_REMEDIATION_R1_TEST_PROFILES_INVALID")
        print("\n".join(sorted(set(failures))))
        return 1
    print("FOUNDATION_REMEDIATION_R1_TEST_PROFILES_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
