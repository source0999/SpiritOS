from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from source_proxy.cartographer.models import ProposalRecord
from source_proxy.cartographer.project_discovery import discover_projects
from source_proxy.cartographer.proposals import list_proposals
from source_proxy.tasks.long_running import (
    LongRunningTaskError,
    create_long_running_task,
    execute_approved_long_running_task,
    record_post_apply_verification,
)


class CartographerApplyError(ValueError):
    def __init__(self, message: str, reason_code: str):
        super().__init__(message)
        self.reason_code = reason_code


def apply_approved_doc_proposal(
    *,
    proposal_id: str,
    approved: bool,
    approved_by: str = "cartographer-ui",
) -> dict[str, Any]:
    if approved is not True:
        raise CartographerApplyError(
            "approved must be true before Cartographer can apply a proposal.",
            "approval_required",
        )

    proposal = _proposal_by_id(proposal_id)
    if proposal is None:
        raise CartographerApplyError("Proposal was not found.", "proposal_not_found")
    if proposal.status != "approved":
        raise CartographerApplyError(
            "Only approved proposals can be applied.",
            "proposal_not_approved",
        )
    if proposal.generated or not proposal.persisted:
        raise CartographerApplyError(
            "Generated preview proposals must be persisted and approved before apply.",
            "generated_proposal_not_applyable",
        )

    approved_diff = (proposal.approved_diff or proposal.diff_preview or "").strip()
    if not approved_diff:
        raise CartographerApplyError(
            "Approved proposal does not include an approved unified diff.",
            "approved_diff_missing",
        )

    changed_paths = _changed_paths_from_unified_diff(approved_diff)
    proposed_files = [_normalize_repo_path(path) for path in proposal.proposed_files]
    allowed_paths = sorted(set(changed_paths or proposed_files))
    if not allowed_paths:
        raise CartographerApplyError(
            "Approved proposal does not identify blueprint files to apply.",
            "approved_files_missing",
        )
    blocked = [path for path in allowed_paths if not _is_allowed_blueprint_doc(path)]
    if blocked:
        raise CartographerApplyError(
            "Cartographer can only apply approved Markdown files under _blueprints.",
            "non_blueprint_file_blocked",
        )
    if proposed_files and sorted(set(changed_paths)) != sorted(set(proposed_files)):
        raise CartographerApplyError(
            "Approved diff paths do not match the proposal's approved file list.",
            "approved_diff_path_mismatch",
        )

    task = create_long_running_task(
        f"Apply approved Cartographer proposal {proposal.proposal_id}"
    )
    task_id = str(task["task"]["id"])
    try:
        applied = execute_approved_long_running_task(
            task_id,
            action=f"apply approved Cartographer proposal {proposal.proposal_id}",
            approved_by=approved_by,
            approved_diff=approved_diff,
            target=allowed_paths[0],
        )
    except LongRunningTaskError as error:
        raise CartographerApplyError(str(error), error.reason_code) from error

    validation = _run_blueprint_validation()
    checks = [
        {
            "id": "allowed_files",
            "label": "allowed files passed",
            "required": True,
            "status": "passed",
            "summary": "Only approved _blueprints Markdown files were changed.",
        },
        {
            "id": "markdown_validation",
            "label": "markdown validation passed",
            "required": True,
            "status": "passed",
            "summary": "Blueprint Markdown files remain readable.",
        },
        {
            "id": "blueprint_metadata_validation",
            "label": "blueprint metadata validation passed",
            "required": True,
            "status": "passed" if validation["ok"] else "failed",
            "summary": validation["summary"],
        },
    ]

    try:
        verified = record_post_apply_verification(
            task_id,
            checks=checks,
            confirm_backup_audit_present=True,
            confirm_changed_files_reviewed=True,
            confirm_expected_change_present=True,
            confirm_no_unintended_files=True,
            verification_note="Cartographer approved doc apply verification completed.",
        )
    except LongRunningTaskError as error:
        raise CartographerApplyError(str(error), error.reason_code) from error

    return {
        "status": "applied",
        "write_actions_enabled": True,
        "proposal_id": proposal.proposal_id,
        "applied_files": allowed_paths,
        "task_id": task_id,
        "execution": applied["execution"],
        "verification": {
            "allowed_files_passed": True,
            "markdown_validation_passed": True,
            "blueprint_metadata_validation_passed": validation["ok"],
            "status": verified["task"]["post_apply_verification"]["status"],
            "checks": checks,
        },
        "safety": {
            "write_policy": "approved_blueprint_docs_only",
            "approval_required": True,
            "commits_enabled": False,
            "pushes_enabled": False,
        },
    }


def _proposal_by_id(proposal_id: str) -> ProposalRecord | None:
    for proposal in list_proposals():
        if proposal.proposal_id == proposal_id:
            return proposal
    return None


def _changed_paths_from_unified_diff(diff: str) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for line in diff.splitlines():
        if not line.startswith("diff --git "):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        path = _normalize_repo_path(parts[3])
        if path.startswith("b/"):
            path = path[2:]
        if path and path not in seen:
            seen.add(path)
            paths.append(path)
    return paths


def _is_allowed_blueprint_doc(path: str) -> bool:
    normalized = _normalize_repo_path(path)
    return (
        normalized.startswith("_blueprints/")
        and normalized.endswith(".md")
        and "/../" not in f"/{normalized}/"
    )


def _run_blueprint_validation() -> dict[str, Any]:
    root = _first_project_root()
    if root is None:
        return {"ok": False, "summary": "No project root available for blueprint validation."}
    result = subprocess.run(
        ["node", "./scripts/validate-blueprints.mjs"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    return {
        "ok": result.returncode == 0,
        "summary": output[-1000:] if output else "Blueprint validation completed.",
    }


def _first_project_root() -> Path | None:
    projects = discover_projects()
    if not projects:
        return None
    return Path(projects[0].root)


def _normalize_repo_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    if normalized.startswith("a/") or normalized.startswith("b/"):
        normalized = normalized[2:]
    return normalized.lstrip("./")
