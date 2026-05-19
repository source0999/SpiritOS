from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from source_proxy.cartographer.models import (
    V1EvidenceArtifact,
    V1EvidenceProof,
    V1ProofGateRecord,
    to_jsonable,
)
from source_proxy.cartographer.project_discovery import configured_project_roots, discover_projects


CARTOGRAPHER_SOAK_PROFILE = "cartographer-soak-snapshot"
DIAGNOSTIC_PROFILES = {
    "proxy-closeout",
    "phase-4f-closeout",
    "scout-search-diagnostics",
}
PROOF_GATE_CHECK_IDS = {
    "typescript_pass": {
        "typecheck",
        "typescript",
        "typescript_pass",
        "tsc",
        "tsc_no_emit",
    },
    "lint_pass_or_warnings_only": {
        "eslint",
        "lint",
        "lint_pass",
        "lint_pass_or_warnings_only",
        "lint_warnings_only",
    },
    "blueprint_validation_pass": {
        "blueprint_metadata_validation",
        "blueprint_validation",
        "blueprint_validation_pass",
        "validate_blueprints",
    },
    "diff_check_pass": {
        "diff_check",
        "diff_check_pass",
        "git_diff_check",
        "task_spec_diff_check",
    },
    "targeted_vitest_pass": {
        "dashboard_smoke",
        "targeted_vitest",
        "targeted_vitest_pass",
        "vitest",
    },
}
PROOF_ARTIFACT_SEARCH_PATHS = [
    "data/cartographer-v1-proof-gates/*.json",
    "data/*.json",
    "source_proxy/cartographer/soak-logs/*.json",
]
FREEZE_MARKER_PATH = "data/cartographer-v1-freeze/freeze-marker.json"


def build_v1_freeze_marker_validation(project_root: Path | None = None) -> dict[str, Any]:
    validation_items = _validate_freeze_markers(project_root)
    present_items = [item for item in validation_items if item["present"]]
    invalid_items = [item for item in present_items if not item["valid"]]
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "validator_enabled": True,
        "validation_actions_enabled": False,
        "freeze_marker_enabled": False,
        "freeze_actions_enabled": False,
        "marker_path": FREEZE_MARKER_PATH,
        "marker_policy": "read_only_validate_existing_marker",
        "marker_count": len(present_items),
        "valid_marker_count": len(present_items) - len(invalid_items),
        "invalid_marker_count": len(invalid_items),
        "validation_status": (
            "valid"
            if present_items and not invalid_items
            else "issues_found"
            if invalid_items
            else "missing"
        ),
        "validation_items": validation_items,
        "issues": [
            issue
            for item in invalid_items
            for issue in item["issues"]
        ],
        "required_authority_boundary": {
            "write_actions_enabled": False,
            "authority_granted": False,
            "actions_taken": False,
            "passing_tests_grant_authority": False,
        },
    }


def build_v1_proof_artifact_contract() -> dict[str, Any]:
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "recorder_enabled": False,
        "recording_endpoint_enabled": False,
        "contract_version": "cartographer.v1.proof_artifact.v1",
        "artifact_policy": "external_recording_only_no_cartographer_writes",
        "accepted_paths": PROOF_ARTIFACT_SEARCH_PATHS,
        "required_top_level_fields": ["profile", "result", "checks"],
        "optional_top_level_fields": [
            "generated_at",
            "head_sha",
            "branch",
            "command",
            "summary",
            "actor",
            "source",
        ],
        "accepted_check_ids": {
            code: sorted(aliases)
            for code, aliases in PROOF_GATE_CHECK_IDS.items()
        },
        "accepted_statuses": ["passed", "pass", "ok", "success", "green", "warnings_only"],
        "failing_statuses": ["failed", "fail", "blocked", "error", "unknown"],
        "example_artifact": {
            "profile": "cartographer-v1-proof-gates",
            "result": "pass",
            "generated_at": "2026-05-18T00:00:00Z",
            "head_sha": "example-head-sha",
            "branch": "main",
            "checks": [
                {"id": "typecheck", "status": "passed", "summary": "tsc --noEmit passed"},
                {"id": "lint", "status": "warnings_only", "summary": "eslint completed with warnings only"},
                {"id": "blueprint_metadata_validation", "status": "passed"},
                {"id": "git_diff_check", "status": "passed"},
                {"id": "targeted_vitest", "status": "passed"},
            ],
        },
        "validation_notes": [
            "Cartographer reads matching JSON artifacts only.",
            "Cartographer does not run proof commands from this contract.",
            "Cartographer does not create, edit, delete, commit, or push proof artifacts.",
            "Passing proof artifacts do not grant write, apply, commit, push, or promotion authority.",
        ],
    }


def build_v1_proof_artifact_validation(project_root: Path | None = None) -> dict[str, Any]:
    validation_items = _validate_proof_artifacts(project_root)
    invalid_items = [item for item in validation_items if not item["valid"]]
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "validator_enabled": True,
        "validation_actions_enabled": False,
        "artifact_policy": "read_only_validate_existing_artifacts",
        "artifact_count": len(validation_items),
        "valid_artifact_count": len(validation_items) - len(invalid_items),
        "invalid_artifact_count": len(invalid_items),
        "validation_status": "valid" if validation_items and not invalid_items else "issues_found" if invalid_items else "no_artifacts",
        "validation_items": validation_items,
        "issues": [
            issue
            for item in invalid_items
            for issue in item["issues"]
        ],
        "accepted_check_ids": {
            code: sorted(aliases)
            for code, aliases in PROOF_GATE_CHECK_IDS.items()
        },
    }


def build_v1_proof_recording_proposal() -> dict[str, Any]:
    artifact_path = "data/cartographer-v1-proof-gates/manual-proof-gates.json"
    example = build_v1_proof_artifact_contract()["example_artifact"]
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "proposal_only": True,
        "recording_enabled": False,
        "recording_actions_enabled": False,
        "artifact_path": artifact_path,
        "proposal_policy": "human_or_external_tool_may_record_after_review",
        "proposal": {
            "proposal_id": "v1-proof-recording-proposal",
            "proposal_type": "manual_proof_artifact_recording",
            "status": "drafted",
            "requires_human_action": True,
            "requires_approval": True,
            "action_taken": False,
            "target_file": artifact_path,
            "reason": "Record proof-gate results so v1 readiness can consume them without rerunning commands.",
            "checks_to_record": list(PROOF_GATE_CHECK_IDS.keys()),
        },
        "suggested_commands": [
            "mkdir -p data/cartographer-v1-proof-gates",
            f"$EDITOR {artifact_path}",
            "curl -k -s https://localhost:3000/v1/cartographer/v1-proof-validation | jq .",
            "curl -k -s https://localhost:3000/v1/cartographer/v1-evidence | jq .",
        ],
        "example_artifact": example,
        "safety_notes": [
            "Cartographer is not writing this artifact.",
            "The proposal is informational and does not grant authority.",
            "Recording proof artifacts does not approve apply, commit, push, cleanup, or promotion.",
            "Validate the artifact after recording before relying on readiness output.",
        ],
    }


def build_v1_proof_import_dry_run(artifact: dict[str, Any] | None = None) -> dict[str, Any]:
    candidate = artifact or build_v1_proof_artifact_contract()["example_artifact"]
    current = build_v1_evidence_inventory()
    validation_item = _validation_item_from_payload(
        "dry-run/proposed-proof-artifact.json",
        candidate,
        dedicated_path=True,
    )
    records = _records_from_payload(
        Path("."),
        Path("dry-run/proposed-proof-artifact.json"),
        candidate,
    )
    passing_codes = sorted({record.code for record in records if record.passed})
    failing_codes = sorted({record.code for record in records if not record.passed})
    current_missing = [str(code) for code in current["missing_evidence"]]
    would_satisfy = [code for code in current_missing if code in passing_codes]
    remaining_missing = [code for code in current_missing if code not in would_satisfy]
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "dry_run": True,
        "import_enabled": False,
        "recording_enabled": False,
        "artifact_written": False,
        "candidate_valid": validation_item["valid"],
        "validation_issues": validation_item["issues"],
        "recognized_check_count": len(records),
        "passing_codes": passing_codes,
        "failing_codes": failing_codes,
        "current_missing_evidence": current_missing,
        "would_satisfy": would_satisfy,
        "would_satisfy_count": len(would_satisfy),
        "remaining_missing_evidence": remaining_missing,
        "remaining_missing_count": len(remaining_missing),
        "readiness_would_still_be_blocked": bool(remaining_missing),
        "candidate_artifact": candidate,
        "source_endpoint": "/v1/cartographer/v1-proof-contract",
    }


def build_v1_diagnostic_import_dry_run(
    artifacts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    candidates = artifacts or _default_diagnostic_artifacts()
    current = build_v1_evidence_inventory()
    candidate_artifacts = [
        artifact
        for index, candidate in enumerate(candidates)
        if (
            artifact := _artifact_from_payload(
                Path("."),
                Path(f"dry-run/diagnostic-artifact-{index}.json"),
                candidate,
            )
        )
        is not None
    ]
    clean_diagnostics = [
        artifact
        for artifact in candidate_artifacts
        if artifact.profile in DIAGNOSTIC_PROFILES and artifact.clean
    ]
    proxy_closeout = [
        artifact for artifact in clean_diagnostics if artifact.profile == "proxy-closeout"
    ]
    phase_4f_closeout = [
        artifact for artifact in clean_diagnostics if artifact.profile == "phase-4f-closeout"
    ]
    candidate_proofs = [
        _proof("three_clean_full_diagnostics", clean_diagnostics, 3),
        _proof("proxy_closeout_pass", proxy_closeout, 1),
        _proof("phase_4f_closeout_pass", phase_4f_closeout, 1),
    ]
    passing_codes = [proof.code for proof in candidate_proofs if proof.passed]
    current_missing = [str(code) for code in current["missing_evidence"]]
    would_satisfy = [code for code in current_missing if code in passing_codes]
    remaining_missing = [code for code in current_missing if code not in would_satisfy]
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "dry_run": True,
        "import_enabled": False,
        "recording_enabled": False,
        "artifact_written": False,
        "candidate_artifact_count": len(candidates),
        "recognized_diagnostic_count": len(candidate_artifacts),
        "clean_diagnostic_count": len(clean_diagnostics),
        "candidate_proofs": to_jsonable(candidate_proofs),
        "passing_codes": passing_codes,
        "current_missing_evidence": current_missing,
        "would_satisfy": would_satisfy,
        "would_satisfy_count": len(would_satisfy),
        "remaining_missing_evidence": remaining_missing,
        "remaining_missing_count": len(remaining_missing),
        "readiness_would_still_be_blocked": bool(remaining_missing),
        "candidate_artifacts": candidates,
        "source_endpoint": "/v1/cartographer/v1-evidence",
    }


def build_v1_combined_readiness_dry_run() -> dict[str, Any]:
    proof = build_v1_proof_import_dry_run()
    diagnostics = build_v1_diagnostic_import_dry_run()
    current_missing = [str(code) for code in proof["current_missing_evidence"]]
    would_satisfy = sorted(
        {
            *[str(code) for code in proof["would_satisfy"]],
            *[str(code) for code in diagnostics["would_satisfy"]],
            *(
                ["three_clean_soak_snapshots"]
                if "three_clean_soak_snapshots" in current_missing
                else []
            ),
        }
    )
    remaining_missing = [code for code in current_missing if code not in would_satisfy]
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "dry_run": True,
        "combined_preview": True,
        "import_enabled": False,
        "recording_enabled": False,
        "artifact_written": False,
        "proof_would_satisfy": proof["would_satisfy"],
        "diagnostic_would_satisfy": diagnostics["would_satisfy"],
        "soak_would_satisfy": (
            ["three_clean_soak_snapshots"]
            if "three_clean_soak_snapshots" in current_missing
            else []
        ),
        "would_satisfy": would_satisfy,
        "would_satisfy_count": len(would_satisfy),
        "current_missing_evidence": current_missing,
        "remaining_missing_evidence": remaining_missing,
        "remaining_missing_count": len(remaining_missing),
        "readiness_would_be_ready": not remaining_missing,
        "readiness_would_still_be_blocked": bool(remaining_missing),
        "authority_would_remain_locked": True,
        "passing_tests_grant_authority": False,
        "source_endpoints": [
            "/v1/cartographer/v1-proof-import-dry-run",
            "/v1/cartographer/v1-diagnostic-import-dry-run",
            "/v1/cartographer/v1-readiness",
        ],
    }


def build_v1_evidence_gap_report() -> dict[str, Any]:
    current = build_v1_evidence_inventory()
    combined = build_v1_combined_readiness_dry_run()
    missing = [str(code) for code in current["missing_evidence"]]
    gap_items = [
        {
            "code": code,
            "status": "missing_real_artifact",
            "dry_run_satisfied": code in combined["would_satisfy"],
            "satisfied_by_preview": _preview_source_for_code(code, combined),
            "recommended_endpoint": _recommended_endpoint_for_gap(code),
        }
        for code in missing
    ]
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "gap_report_mode": "read_only_current_vs_dry_run",
        "current_missing_count": len(missing),
        "current_missing_evidence": missing,
        "dry_run_would_satisfy_count": len(combined["would_satisfy"]),
        "dry_run_would_satisfy": combined["would_satisfy"],
        "remaining_after_dry_run": combined["remaining_missing_evidence"],
        "readiness_would_be_ready": combined["readiness_would_be_ready"],
        "authority_would_remain_locked": True,
        "passing_tests_grant_authority": False,
        "gap_items": gap_items,
        "source_endpoints": [
            "/v1/cartographer/v1-evidence",
            "/v1/cartographer/v1-combined-readiness-dry-run",
            "/v1/cartographer/v1-proof-recording-proposal",
        ],
    }


def build_v1_evidence_inventory(project_root: Path | None = None) -> dict[str, Any]:
    artifacts = _scan_artifacts(project_root)
    check_records = _scan_check_records(project_root)
    clean_soak = [
        artifact
        for artifact in artifacts
        if artifact.profile == CARTOGRAPHER_SOAK_PROFILE and artifact.clean
    ]
    clean_diagnostics = [
        artifact
        for artifact in artifacts
        if artifact.profile in DIAGNOSTIC_PROFILES and artifact.clean
    ]
    proxy_closeout = [
        artifact
        for artifact in clean_diagnostics
        if artifact.profile == "proxy-closeout"
    ]
    phase_4f_closeout = [
        artifact
        for artifact in clean_diagnostics
        if artifact.profile == "phase-4f-closeout"
    ]
    proof_items = [
        _proof("three_clean_full_diagnostics", clean_diagnostics, 3),
        _proof("three_clean_soak_snapshots", clean_soak, 3),
        _proof("proxy_closeout_pass", proxy_closeout, 1),
        _proof("phase_4f_closeout_pass", phase_4f_closeout, 1),
        *_check_proofs(check_records),
    ]
    check_records_by_gate = {
        code: [record for record in check_records if record.code == code]
        for code in PROOF_GATE_CHECK_IDS
    }

    return {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "evidence_collection_mode": "read_only_existing_artifacts",
        "clean_diagnostics_required": 3,
        "clean_diagnostics_count": len(clean_diagnostics),
        "clean_soak_required": 3,
        "clean_soak_count": len(clean_soak),
        "artifact_count": len(artifacts),
        "proof_gate_record_count": len(check_records),
        "latest_clean_diagnostics": to_jsonable(clean_diagnostics[:5]),
        "latest_clean_soak_snapshots": to_jsonable(clean_soak[:5]),
        "proof_gate_records": to_jsonable(check_records[:20]),
        "proof_gate_records_by_gate": to_jsonable(check_records_by_gate),
        "proof_items": to_jsonable(proof_items),
        "missing_evidence": [
            item.code for item in proof_items if not item.passed
        ],
        "inventory_policy": "read_only_no_commands_no_writes",
    }


def _scan_artifacts(project_root: Path | None) -> list[V1EvidenceArtifact]:
    roots = _project_roots(project_root)
    artifacts = [
        artifact
        for root in roots
        for artifact in _artifacts_for_root(root)
    ]
    cwd = Path.cwd()
    if (
        project_root is None
        and not artifacts
        and os.getenv("CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK", "").lower() != "true"
        and (cwd / ".git").exists()
        and str(cwd.resolve(strict=False)) not in {str(root.resolve(strict=False)) for root in roots}
    ):
        artifacts.extend(_artifacts_for_root(cwd))
    return sorted(
        artifacts,
        key=lambda artifact: (artifact.generated_at or "", artifact.path),
        reverse=True,
    )


def _scan_check_records(project_root: Path | None) -> list[V1ProofGateRecord]:
    roots = _project_roots(project_root)
    records = [
        record
        for root in roots
        for path in _candidate_paths(root)
        for record in _records_from_path(root, path)
    ]
    cwd = Path.cwd()
    if (
        project_root is None
        and not records
        and os.getenv("CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK", "").lower() != "true"
        and (cwd / ".git").exists()
        and str(cwd.resolve(strict=False)) not in {str(root.resolve(strict=False)) for root in roots}
    ):
        records.extend(
            record
            for path in _candidate_paths(cwd)
            for record in _records_from_path(cwd, path)
        )
    return sorted(records, key=lambda record: (record.path, record.check_id), reverse=True)


def _validate_proof_artifacts(project_root: Path | None) -> list[dict[str, Any]]:
    roots = _project_roots(project_root)
    items = [
        item
        for root in roots
        for path in _candidate_paths(root)
        if (item := _validation_item_from_path(root, path)) is not None
    ]
    cwd = Path.cwd()
    if (
        project_root is None
        and not items
        and os.getenv("CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK", "").lower() != "true"
        and (cwd / ".git").exists()
        and str(cwd.resolve(strict=False)) not in {str(root.resolve(strict=False)) for root in roots}
    ):
        items.extend(
            item
            for path in _candidate_paths(cwd)
            if (item := _validation_item_from_path(cwd, path)) is not None
        )
    return sorted(items, key=lambda item: str(item["path"]), reverse=True)


def _validate_freeze_markers(project_root: Path | None) -> list[dict[str, Any]]:
    roots = _project_roots(project_root)
    items = [_freeze_marker_item_from_root(root) for root in roots]
    cwd = Path.cwd()
    if (
        project_root is None
        and not any(item["present"] for item in items)
        and os.getenv("CARTOGRAPHER_DISABLE_CWD_EVIDENCE_FALLBACK", "").lower() != "true"
        and (cwd / ".git").exists()
        and str(cwd.resolve(strict=False)) not in {str(root.resolve(strict=False)) for root in roots}
    ):
        items.append(_freeze_marker_item_from_root(cwd))
    return sorted(items, key=lambda item: str(item["path"]), reverse=True)


def _freeze_marker_item_from_root(root: Path) -> dict[str, Any]:
    path = root / FREEZE_MARKER_PATH
    relative_path = _relative_path(root, path)
    if not path.exists():
        return {
            "path": relative_path,
            "present": False,
            "valid": False,
            "issues": ["freeze marker not found"],
            "marker_version": None,
            "readiness": None,
            "v1_ready": None,
            "authority_boundary_valid": False,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return _freeze_marker_validation_item(relative_path, {}, [f"invalid_json: {error}"])
    if not isinstance(payload, dict):
        return _freeze_marker_validation_item(relative_path, {}, ["marker must be a JSON object"])
    return _freeze_marker_validation_item(relative_path, payload, [])


def _freeze_marker_validation_item(
    relative_path: str,
    payload: dict[str, Any],
    existing_issues: list[str],
) -> dict[str, Any]:
    issues = list(existing_issues)
    required_fields = [
        "marker_version",
        "created_at",
        "head_sha",
        "branch",
        "readiness",
        "v1_ready",
        "evidence_summary",
        "authority_boundary",
    ]
    for field in required_fields:
        if field not in payload:
            issues.append(f"missing required field: {field}")
    if payload.get("marker_version") != "cartographer.v1.freeze_marker.v1":
        issues.append("marker_version must be cartographer.v1.freeze_marker.v1")
    evidence_summary = payload.get("evidence_summary")
    if not isinstance(evidence_summary, dict):
        issues.append("evidence_summary must be an object")
    authority = payload.get("authority_boundary")
    authority_boundary_valid = _freeze_marker_authority_valid(authority)
    if not authority_boundary_valid:
        issues.append("authority_boundary must keep write and promotion authority locked")
    return {
        "path": relative_path,
        "present": True,
        "valid": not issues,
        "issues": issues,
        "marker_version": payload.get("marker_version"),
        "created_at": payload.get("created_at"),
        "head_sha": payload.get("head_sha"),
        "branch": payload.get("branch"),
        "readiness": payload.get("readiness"),
        "v1_ready": payload.get("v1_ready"),
        "authority_boundary_valid": authority_boundary_valid,
    }


def _freeze_marker_authority_valid(authority: Any) -> bool:
    if not isinstance(authority, dict):
        return False
    return (
        authority.get("write_actions_enabled") is False
        and authority.get("authority_granted") is False
        and authority.get("actions_taken") is False
        and authority.get("passing_tests_grant_authority") is False
    )


def _project_roots(project_root: Path | None) -> list[Path]:
    if project_root is not None:
        return [project_root]

    roots = [Path(project.root) for project in discover_projects()]
    roots.extend(Path(root.path) for root in configured_project_roots())
    seen: set[str] = set()
    unique_roots: list[Path] = []
    for root in roots:
        normalized = str(root.resolve(strict=False))
        if normalized in seen:
            continue
        seen.add(normalized)
        unique_roots.append(root)
    return unique_roots


def _artifacts_for_root(root: Path) -> list[V1EvidenceArtifact]:
    return [
        artifact
        for path in _candidate_paths(root)
        if (artifact := _artifact_from_path(root, path)) is not None
    ]


def _candidate_paths(root: Path) -> list[Path]:
    search_roots = [
        root / "source_proxy" / "cartographer" / "soak-logs",
        root / "scout" / "soak-logs",
        root / "data",
    ]
    paths: list[Path] = []
    for search_root in search_roots:
        if search_root.exists() and search_root.is_dir():
            paths.extend(search_root.rglob("*.json"))
    return sorted(paths)


def _artifact_from_path(root: Path, path: Path) -> V1EvidenceArtifact | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None

    return _artifact_from_payload(root, path, payload)


def _artifact_from_payload(root: Path, path: Path, payload: dict[str, Any]) -> V1EvidenceArtifact | None:
    profile = _profile_for(payload)
    if not profile:
        return None
    result = str(payload.get("result") or payload.get("status") or "unknown")
    clean, evidence = _clean_state(payload, result=result)
    return V1EvidenceArtifact(
        path=_relative_path(root, path),
        profile=profile,
        result=result,
        generated_at=_generated_at(payload, path),
        clean=clean,
        evidence=evidence,
    )


def _default_diagnostic_artifacts() -> list[dict[str, Any]]:
    return [
        _diagnostic_artifact("proxy-closeout", "Proxy closeout passed."),
        _diagnostic_artifact("phase-4f-closeout", "Phase 4f closeout passed."),
        _diagnostic_artifact("scout-search-diagnostics", "Scout search diagnostics passed."),
    ]


def _diagnostic_artifact(profile: str, summary: str) -> dict[str, Any]:
    return {
        "profile": profile,
        "result": "pass",
        "generated_at": "2026-05-18T00:00:00Z",
        "summary": summary,
        "mutation_boundary": {
            "head_changed": False,
            "snapshot_log_only": True,
            "unexpected_status_delta": [],
        },
    }


def _preview_source_for_code(code: str, combined: dict[str, Any]) -> str | None:
    if code in combined["proof_would_satisfy"]:
        return "proof_artifact_preview"
    if code in combined["diagnostic_would_satisfy"]:
        return "diagnostic_artifact_preview"
    if code in combined["soak_would_satisfy"]:
        return "soak_snapshot_preview"
    return None


def _recommended_endpoint_for_gap(code: str) -> str:
    if code in PROOF_GATE_CHECK_IDS:
        return "/v1/cartographer/v1-proof-recording-proposal"
    if code in {"three_clean_full_diagnostics", "proxy_closeout_pass", "phase_4f_closeout_pass"}:
        return "/v1/cartographer/v1-diagnostic-import-dry-run"
    if code == "three_clean_soak_snapshots":
        return "/v1/cartographer/v1-evidence"
    return "/v1/cartographer/v1-readiness"


def _records_from_path(root: Path, path: Path) -> list[V1ProofGateRecord]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return []
    if not isinstance(payload, dict):
        return []

    return _records_from_payload(root, path, payload)


def _records_from_payload(root: Path, path: Path, payload: dict[str, Any]) -> list[V1ProofGateRecord]:
    records: list[V1ProofGateRecord] = []
    for check_id, status, evidence in _iter_check_statuses(payload):
        code = _proof_code_for_check_id(check_id)
        if not code:
            continue
        records.append(
            V1ProofGateRecord(
                code=code,
                path=_relative_path(root, path),
                check_id=check_id,
                status=status,
                passed=_status_passed(status),
                evidence=evidence,
            )
        )
    return records


def _validation_item_from_path(root: Path, path: Path) -> dict[str, Any] | None:
    relative_path = _relative_path(root, path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        if "data/cartographer-v1-proof-gates/" not in relative_path:
            return None
        return {
            "path": relative_path,
            "valid": False,
            "issues": [f"invalid_json: {error}"],
            "recognized_check_count": 0,
            "unknown_check_ids": [],
            "failing_check_ids": [],
        }
    if not isinstance(payload, dict):
        if "data/cartographer-v1-proof-gates/" not in relative_path:
            return None
        return _validation_item(relative_path, ["artifact must be a JSON object"], [], [])

    if not _is_proof_artifact_payload(payload, relative_path):
        return None

    return _validation_item_from_payload(relative_path, payload)


def _validation_item_from_payload(
    relative_path: str,
    payload: dict[str, Any],
    *,
    dedicated_path: bool = False,
) -> dict[str, Any]:
    issues: list[str] = []
    for field in ("profile", "result", "checks"):
        if field not in payload:
            issues.append(f"missing required field: {field}")
    if payload.get("profile") != "cartographer-v1-proof-gates":
        issues.append("profile must be cartographer-v1-proof-gates")

    checks = payload.get("checks")
    recognized: list[str] = []
    unknown: list[str] = []
    failing: list[str] = []
    if not isinstance(checks, (dict, list)):
        issues.append("checks must be an object or list")
    else:
        for check_id, status, _evidence in _iter_check_statuses({"checks": checks}):
            if _proof_code_for_check_id(check_id):
                recognized.append(check_id)
                if not _status_passed(status):
                    failing.append(check_id)
            else:
                unknown.append(check_id)
        if not recognized:
            issues.append("no recognized proof-gate check ids found")

    for check_id in unknown:
        issues.append(f"unknown check id: {check_id}")
    for check_id in failing:
        issues.append(f"failing check status: {check_id}")
    if dedicated_path and not relative_path:
        issues.append("artifact path is required")
    return _validation_item(relative_path, issues, recognized, unknown, failing)


def _is_proof_artifact_payload(payload: dict[str, Any], relative_path: str) -> bool:
    return (
        "data/cartographer-v1-proof-gates/" in relative_path
        or payload.get("profile") == "cartographer-v1-proof-gates"
    )


def _validation_item(
    path: str,
    issues: list[str],
    recognized_check_ids: list[str],
    unknown_check_ids: list[str],
    failing_check_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "path": path,
        "valid": not issues,
        "issues": issues,
        "recognized_check_count": len(recognized_check_ids),
        "recognized_check_ids": recognized_check_ids,
        "unknown_check_ids": unknown_check_ids,
        "failing_check_ids": failing_check_ids or [],
    }


def _iter_check_statuses(payload: dict[str, Any]) -> list[tuple[str, str, list[str]]]:
    found: list[tuple[str, str, list[str]]] = []
    checks = payload.get("checks")
    if isinstance(checks, dict):
        for key, value in checks.items():
            status = _status_from_value(value)
            found.append((str(key), status, [f"checks.{key}: {status}"]))
    elif isinstance(checks, list):
        for item in checks:
            if not isinstance(item, dict):
                continue
            check_id = str(item.get("id") or item.get("check_id") or item.get("name") or "").strip()
            if not check_id:
                continue
            status = _status_from_value(item.get("status", item.get("passed")))
            summary = str(item.get("summary") or item.get("evidence") or "")
            evidence = [f"check: {check_id}", f"status: {status}"]
            if summary:
                evidence.append(summary)
            found.append((check_id, status, evidence))

    proof_gates = payload.get("proof_gates") or payload.get("proof_items")
    if isinstance(proof_gates, list):
        for item in proof_gates:
            if not isinstance(item, dict):
                continue
            check_id = str(item.get("code") or item.get("id") or "").strip()
            if not check_id:
                continue
            status = _status_from_value(item.get("passed", item.get("status")))
            found.append((check_id, status, [f"proof gate: {check_id}", f"status: {status}"]))

    verification = payload.get("verification")
    if isinstance(verification, dict):
        for key, value in verification.items():
            if not key.endswith("_passed") and key not in PROOF_GATE_CHECK_IDS:
                continue
            status = _status_from_value(value)
            found.append((key.removesuffix("_passed"), status, [f"verification.{key}: {status}"]))

    return found


def _proof_code_for_check_id(check_id: str) -> str | None:
    normalized = _normalize_check_id(check_id)
    for code, aliases in PROOF_GATE_CHECK_IDS.items():
        if normalized == code or normalized in aliases:
            return code
    return None


def _normalize_check_id(check_id: str) -> str:
    return check_id.strip().lower().replace("-", "_").replace(" ", "_")


def _status_from_value(value: Any) -> str:
    if isinstance(value, bool):
        return "passed" if value else "failed"
    return str(value or "unknown").strip().lower()


def _status_passed(status: str) -> bool:
    return status in {"pass", "passed", "ok", "success", "green", "warnings_only"}


def _profile_for(payload: dict[str, Any]) -> str:
    profile = str(payload.get("profile") or "").strip()
    if profile:
        return profile
    if payload.get("closeout_status"):
        return "proxy-closeout"
    return ""


def _clean_state(payload: dict[str, Any], *, result: str) -> tuple[bool, list[str]]:
    evidence: list[str] = []
    normalized_result = result.lower()
    result_clean = normalized_result in {"pass", "passed", "ok", "success", "green"}
    evidence.append(f"result: {result}")

    mutation = payload.get("mutation_boundary")
    if isinstance(mutation, dict):
        head_changed = bool(mutation.get("head_changed"))
        unexpected_status_delta = mutation.get("unexpected_status_delta") or []
        snapshot_log_only = bool(mutation.get("snapshot_log_only"))
        evidence.append(f"head_changed: {head_changed}")
        evidence.append(f"unexpected_status_delta: {len(unexpected_status_delta)}")
        if snapshot_log_only:
            evidence.append("snapshot_log_only: true")
        mutation_clean = not head_changed and len(unexpected_status_delta) == 0
    else:
        mutation_clean = True

    return result_clean and mutation_clean, evidence


def _generated_at(payload: dict[str, Any], path: Path) -> str | None:
    for key in ("generated_at", "timestamp", "finished_at", "started_at"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return path.stat().st_mtime_ns.__str__()


def _relative_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _proof(code: str, artifacts: list[V1EvidenceArtifact], required_count: int) -> V1EvidenceProof:
    observed = len(artifacts)
    return V1EvidenceProof(
        code=code,
        required_count=required_count,
        observed_count=observed,
        passed=observed >= required_count,
        evidence=[artifact.path for artifact in artifacts[:required_count]],
    )


def _check_proofs(records: list[V1ProofGateRecord]) -> list[V1EvidenceProof]:
    proofs: list[V1EvidenceProof] = []
    for code in PROOF_GATE_CHECK_IDS:
        passed_records = [record for record in records if record.code == code and record.passed]
        proofs.append(
            V1EvidenceProof(
                code=code,
                required_count=1,
                observed_count=len(passed_records),
                passed=bool(passed_records),
                evidence=[record.path for record in passed_records[:1]],
            )
        )
    return proofs
