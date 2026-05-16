from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from source_proxy.cartographer.branch_recommendations import recommend_branches
from source_proxy.cartographer.commit_proposals import build_commit_proposals
from source_proxy.cartographer.project_discovery import discover_projects
from source_proxy.cartographer.push_queue import build_push_queue


ApprovalKind = Literal["branch", "commit", "push"]
_GIT_TIMEOUT_SECONDS = 30
_SAFE_BRANCH_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,119}$")


class CartographerGitApprovalError(ValueError):
    def __init__(self, message: str, reason_code: str):
        super().__init__(message)
        self.reason_code = reason_code


def approve_git_queue_item(
    *,
    kind: ApprovalKind,
    item_id: str,
    approved: bool,
    approved_by: str,
) -> dict[str, Any]:
    if approved is not True:
        if kind == "branch":
            return _reject_branch_item(item_id=item_id, rejected_by=approved_by)
        raise CartographerGitApprovalError(
            "approved must be true before Cartographer can record Git approval.",
            "approval_required",
        )

    item = _find_item(kind, item_id)
    if item is None:
        raise CartographerGitApprovalError(
            "Requested Cartographer Git approval item was not found.",
            "approval_item_not_found",
        )

    if kind == "branch":
        return _create_approved_branch(item=item, item_id=item_id, approved_by=approved_by)
    if kind == "commit":
        return _create_approved_commit(item=item, item_id=item_id, approved_by=approved_by)
    if kind == "push":
        return _run_approved_push(item=item, item_id=item_id, approved_by=approved_by)

    timestamp = _now_timestamp()
    event = {
        "event": f"{kind}_approved",
        "approved_at": timestamp,
        "approved_by": approved_by or "cartographer-ui",
        "approval_kind": kind,
        "item_id": item_id,
        "project_id": item["project_id"],
        "result": "approval_recorded_no_execution",
        "changed_files": item.get("files") or item.get("related_files") or [],
        "branch": item.get("suggested_branch") or item.get("branch"),
        "remote": item.get("remote"),
        "action_taken": False,
        "branch_created": False,
        "commit_created": False,
        "push_ran": False,
    }
    _append_approval_record(event)

    return {
        "status": "approval_recorded",
        "write_actions_enabled": False,
        "approval_kind": kind,
        "item_id": item_id,
        "approved_by": event["approved_by"],
        "approved_at": timestamp,
        "item": item,
        "actions_taken": False,
        "branch_created": False,
        "commit_created": False,
        "push_ran": False,
        "next_step": _next_step_for_kind(kind),
        "safety": {
            "approval_recorded": True,
            "branch_creation_enabled": False,
            "commit_enabled": False,
            "push_enabled": False,
        },
    }


def read_git_approval_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for project in discover_projects():
        path = _approval_record_path(Path(project.root))
        if not path.exists() or not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()[-100:]
        except OSError:
            continue
        for line in lines:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                records.append(payload)
    return records


def _find_item(kind: ApprovalKind, item_id: str) -> dict[str, Any] | None:
    if kind == "branch":
        for item in recommend_branches():
            if item.recommendation_id == item_id:
                return {
                    "project_id": item.project_id,
                    "recommendation_id": item.recommendation_id,
                    "current_branch": item.current_branch,
                    "suggested_branch": item.suggested_branch,
                    "related_files": item.related_files,
                    "status": item.status,
                    "branch_creation_enabled": item.branch_creation_enabled,
                    "action_taken": item.action_taken,
                }
    if kind == "commit":
        for item in build_commit_proposals():
            if item.commit_proposal_id == item_id:
                return {
                    "project_id": item.project_id,
                    "commit_proposal_id": item.commit_proposal_id,
                    "source_proposal_id": item.source_proposal_id,
                    "suggested_message": item.suggested_message,
                    "files": item.files,
                    "status": item.status,
                    "commit_enabled": item.commit_enabled,
                    "action_taken": item.action_taken,
                }
    if kind == "push":
        for item in build_push_queue():
            if item.push_id == item_id:
                return {
                    "project_id": item.project_id,
                    "push_id": item.push_id,
                    "remote": item.remote,
                    "branch": item.branch,
                    "upstream": item.upstream,
                    "commits_ahead": item.commits_ahead,
                    "files": item.files,
                    "status": item.status,
                    "push_enabled": item.push_enabled,
                    "action_taken": item.action_taken,
                }
    return None


def _reject_branch_item(*, item_id: str, rejected_by: str) -> dict[str, Any]:
    item = _find_item("branch", item_id)
    if item is None:
        raise CartographerGitApprovalError(
            "Requested Cartographer branch recommendation was not found.",
            "approval_item_not_found",
        )

    timestamp = _now_timestamp()
    event = {
        "event": "branch_rejected",
        "rejected_at": timestamp,
        "approved_at": timestamp,
        "approved_by": rejected_by or "cartographer-ui",
        "approval_kind": "branch",
        "item_id": item_id,
        "project_id": item["project_id"],
        "result": "branch_rejected_no_execution",
        "changed_files": item.get("related_files") or [],
        "branch": item.get("suggested_branch"),
        "remote": None,
        "action_taken": False,
        "branch_created": False,
        "commit_created": False,
        "push_ran": False,
    }
    _append_approval_record(event)

    return {
        "status": "branch_rejected",
        "write_actions_enabled": False,
        "approval_kind": "branch",
        "item_id": item_id,
        "approved_by": event["approved_by"],
        "approved_at": timestamp,
        "item": item,
        "actions_taken": False,
        "branch_created": False,
        "commit_created": False,
        "push_ran": False,
        "next_step": "Branch recommendation rejected; Git was left untouched.",
        "safety": {
            "approval_recorded": True,
            "branch_creation_enabled": False,
            "commit_enabled": False,
            "push_enabled": False,
        },
    }


def _create_approved_branch(
    *,
    item: dict[str, Any],
    item_id: str,
    approved_by: str,
) -> dict[str, Any]:
    project_root = _project_root(str(item["project_id"]))
    if project_root is None:
        raise CartographerGitApprovalError(
            "Project root for branch recommendation was not found.",
            "project_not_found",
        )

    branch_name = str(item.get("suggested_branch") or "")
    _validate_safe_branch_name(branch_name)
    if _branch_exists(project_root, branch_name):
        raise CartographerGitApprovalError(
            "Recommended branch already exists; Cartographer will not overwrite it.",
            "branch_already_exists",
        )

    before_branch = _current_branch(project_root)
    result = _git(project_root, "switch", "-c", branch_name)
    if result.returncode != 0:
        raise CartographerGitApprovalError(
            (result.stderr or result.stdout or "Git branch creation failed.").strip(),
            "git_branch_create_failed",
        )

    timestamp = _now_timestamp()
    event = {
        "event": "branch_created",
        "approved_at": timestamp,
        "approved_by": approved_by or "cartographer-ui",
        "approval_kind": "branch",
        "item_id": item_id,
        "project_id": item["project_id"],
        "result": "branch_created",
        "changed_files": item.get("related_files") or [],
        "branch": branch_name,
        "previous_branch": before_branch,
        "remote": None,
        "action_taken": True,
        "branch_created": True,
        "commit_created": False,
        "push_ran": False,
    }
    _append_approval_record(event)

    return {
        "status": "branch_created",
        "write_actions_enabled": True,
        "approval_kind": "branch",
        "item_id": item_id,
        "approved_by": event["approved_by"],
        "approved_at": timestamp,
        "branch": branch_name,
        "previous_branch": before_branch,
        "item": item,
        "actions_taken": True,
        "branch_created": True,
        "commit_created": False,
        "push_ran": False,
        "committed": False,
        "pushed": False,
        "next_step": "Branch created; review the dirty tree before approving any commit.",
        "safety": {
            "approval_recorded": True,
            "branch_creation_enabled": True,
            "commit_enabled": False,
            "push_enabled": False,
        },
    }


def _create_approved_commit(
    *,
    item: dict[str, Any],
    item_id: str,
    approved_by: str,
) -> dict[str, Any]:
    project_root = _project_root(str(item["project_id"]))
    if project_root is None:
        raise CartographerGitApprovalError(
            "Project root for commit proposal was not found.",
            "project_not_found",
        )

    files = _approval_files(item)
    if not files:
        raise CartographerGitApprovalError(
            "Commit proposal has no files to commit.",
            "commit_proposal_empty",
        )
    message = str(item.get("suggested_message") or "").strip()
    if not message:
        raise CartographerGitApprovalError(
            "Commit proposal has no approved commit message.",
            "commit_message_required",
        )

    checks = _run_commit_checks(project_root, files)
    failing = [check for check in checks if check["status"] == "failed"]
    if failing:
        raise CartographerGitApprovalError(
            failing[0]["summary"],
            str(failing[0]["id"]),
        )

    add_result = _git(project_root, "add", "--", *files)
    if add_result.returncode != 0:
        raise CartographerGitApprovalError(
            (add_result.stderr or add_result.stdout or "Git add failed.").strip(),
            "git_add_failed",
        )

    commit_result = _git(project_root, "commit", "-m", message)
    if commit_result.returncode != 0:
        raise CartographerGitApprovalError(
            (commit_result.stderr or commit_result.stdout or "Git commit failed.").strip(),
            "git_commit_failed",
        )

    commit_sha = _git(project_root, "rev-parse", "HEAD").stdout.strip()
    branch = _current_branch(project_root)
    timestamp = _now_timestamp()
    event = {
        "event": "commit_created",
        "approved_at": timestamp,
        "approved_by": approved_by or "cartographer-ui",
        "approval_kind": "commit",
        "item_id": item_id,
        "project_id": item["project_id"],
        "result": "commit_created",
        "changed_files": files,
        "branch": branch,
        "commit_sha": commit_sha,
        "commit_message": message,
        "remote": None,
        "action_taken": True,
        "branch_created": False,
        "commit_created": True,
        "push_ran": False,
        "checks": checks,
    }
    _append_approval_record(event)

    return {
        "status": "commit_created",
        "write_actions_enabled": True,
        "approval_kind": "commit",
        "item_id": item_id,
        "approved_by": event["approved_by"],
        "approved_at": timestamp,
        "item": item,
        "branch": branch,
        "commit_sha": commit_sha,
        "commit_message": message,
        "checks": checks,
        "actions_taken": True,
        "branch_created": False,
        "commit_created": True,
        "push_ran": False,
        "committed": True,
        "pushed": False,
        "next_step": "Commit created after checks; review push queue before approving any push.",
        "safety": {
            "approval_recorded": True,
            "branch_creation_enabled": False,
            "commit_enabled": True,
            "push_enabled": False,
        },
    }


def _run_approved_push(
    *,
    item: dict[str, Any],
    item_id: str,
    approved_by: str,
) -> dict[str, Any]:
    project_root = _project_root(str(item["project_id"]))
    if project_root is None:
        raise CartographerGitApprovalError(
            "Project root for push item was not found.",
            "project_not_found",
        )

    remote = str(item.get("remote") or "").strip()
    branch = str(item.get("branch") or "").strip()
    if not remote or not branch:
        raise CartographerGitApprovalError(
            "Push item is missing a remote or branch.",
            "push_target_required",
        )
    _validate_safe_branch_name(branch)

    upstream = item.get("upstream")
    push_args = ["push", remote, branch]
    if not upstream:
        push_args = ["push", "-u", remote, branch]
    result = _git(project_root, *push_args)
    if result.returncode != 0:
        raise CartographerGitApprovalError(
            (result.stderr or result.stdout or "Git push failed.").strip(),
            "git_push_failed",
        )

    timestamp = _now_timestamp()
    event = {
        "event": "push_approved",
        "approved_at": timestamp,
        "approved_by": approved_by or "cartographer-ui",
        "approval_kind": "push",
        "item_id": item_id,
        "project_id": item["project_id"],
        "result": "pushed",
        "changed_files": item.get("files") or [],
        "branch": branch,
        "remote": remote,
        "upstream": item.get("upstream"),
        "commits_ahead": item.get("commits_ahead"),
        "action_taken": True,
        "branch_created": False,
        "commit_created": False,
        "push_ran": True,
    }
    _append_approval_record(event)

    return {
        "status": "pushed",
        "write_actions_enabled": True,
        "approval_kind": "push",
        "item_id": item_id,
        "approved_by": event["approved_by"],
        "approved_at": timestamp,
        "item": item,
        "remote": remote,
        "branch": branch,
        "actions_taken": True,
        "branch_created": False,
        "commit_created": False,
        "push_ran": True,
        "committed": False,
        "pushed": True,
        "next_step": "Push completed; review merge readiness before merging.",
        "safety": {
            "approval_recorded": True,
            "branch_creation_enabled": False,
            "commit_enabled": False,
            "push_enabled": True,
        },
    }


def _approval_files(item: dict[str, Any]) -> list[str]:
    values = item.get("files")
    if not isinstance(values, list):
        return []
    files = []
    for value in values:
        normalized = str(value).strip().replace("\\", "/")
        if normalized and not normalized.startswith("/") and ".." not in normalized.split("/"):
            files.append(normalized)
    return files


def _run_commit_checks(project_root: Path, files: list[str]) -> list[dict[str, Any]]:
    checks = [_run_git_diff_check(project_root, files)]
    blueprint_check = _run_blueprint_validation(project_root)
    if blueprint_check:
        checks.append(blueprint_check)
    pytest_check = _run_cartographer_pytest(project_root)
    if pytest_check:
        checks.append(pytest_check)
    return checks


def _run_git_diff_check(project_root: Path, files: list[str]) -> dict[str, Any]:
    result = _git(project_root, "diff", "--check", "--", *files)
    return _check_result(
        "git_diff_check",
        "git diff --check",
        result.returncode,
        result.stdout,
        result.stderr,
        "Whitespace check passed for approved commit files.",
    )


def _run_blueprint_validation(project_root: Path) -> dict[str, Any] | None:
    validator = project_root / "scripts" / "validate-blueprints.mjs"
    if not validator.exists():
        return None
    result = _run(project_root, ["node", str(validator.relative_to(project_root))])
    return _check_result(
        "blueprint_metadata_validation",
        "npm run validate:blueprints",
        result.returncode,
        result.stdout,
        result.stderr,
        "Blueprint validation passed.",
    )


def _run_cartographer_pytest(project_root: Path) -> dict[str, Any] | None:
    test_files = [
        project_root / "source_proxy" / "tests" / "test_cartographer_api.py",
        project_root / "source_proxy" / "tests" / "test_cartographer_safety_audit.py",
    ]
    if not all(path.exists() for path in test_files):
        return None
    result = _run(
        project_root,
        [
            sys.executable,
            "-m",
            "pytest",
            "source_proxy/tests/test_cartographer_api.py",
            "source_proxy/tests/test_cartographer_safety_audit.py",
        ],
        timeout=180,
    )
    return _check_result(
        "cartographer_pytest",
        "python -m pytest source_proxy/tests/test_cartographer_api.py source_proxy/tests/test_cartographer_safety_audit.py",
        result.returncode,
        result.stdout,
        result.stderr,
        "Cartographer tests passed.",
    )


def _check_result(
    check_id: str,
    label: str,
    returncode: int,
    stdout: str,
    stderr: str,
    passed_summary: str,
) -> dict[str, Any]:
    output = (stdout or stderr or "").strip()
    if returncode == 0:
        return {
            "id": check_id,
            "label": label,
            "required": True,
            "status": "passed",
            "summary": output or passed_summary,
        }
    return {
        "id": check_id,
        "label": label,
        "required": True,
        "status": "failed",
        "summary": output or f"{label} failed.",
    }


def _append_approval_record(event: dict[str, Any]) -> None:
    project_root = _project_root(str(event["project_id"]))
    if project_root is None:
        raise CartographerGitApprovalError(
            "Project root for approval item was not found.",
            "project_not_found",
        )
    path = _approval_record_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def _validate_safe_branch_name(branch_name: str) -> None:
    if not _SAFE_BRANCH_PATTERN.fullmatch(branch_name):
        raise CartographerGitApprovalError(
            "Recommended branch name contains unsafe characters.",
            "unsafe_branch_name",
        )
    if (
        ".." in branch_name
        or "@{" in branch_name
        or "\\" in branch_name
        or branch_name.endswith("/")
        or branch_name.endswith(".")
        or branch_name.endswith(".lock")
        or "//" in branch_name
    ):
        raise CartographerGitApprovalError(
            "Recommended branch name is not a valid safe Git branch name.",
            "unsafe_branch_name",
        )
    if any(part in {"", ".", ".."} or part.endswith(".lock") for part in branch_name.split("/")):
        raise CartographerGitApprovalError(
            "Recommended branch name contains an unsafe path segment.",
            "unsafe_branch_name",
        )


def _branch_exists(project_root: Path, branch_name: str) -> bool:
    result = _git(project_root, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch_name}")
    return result.returncode == 0


def _current_branch(project_root: Path) -> str | None:
    result = _git(project_root, "branch", "--show-current")
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _git(project_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run(project_root, ["git", *args])


def _run(
    project_root: Path,
    command: list[str],
    *,
    timeout: int = _GIT_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            command,
            returncode=124,
            stdout="",
            stderr="command_timeout",
        )


def _project_root(project_id: str) -> Path | None:
    for project in discover_projects():
        if project.project_id == project_id:
            return Path(project.root)
    return None


def _approval_record_path(project_root: Path) -> Path:
    configured = os.getenv("SOURCE_PROXY_CARTOGRAPHER_GIT_APPROVAL_LOG")
    if configured:
        return Path(configured)
    return project_root / "data" / "cartographer_git_approvals.audit.jsonl"


def _next_step_for_kind(kind: ApprovalKind) -> str:
    if kind == "branch":
        return "Branch approval recorded; branch creation still requires a separate executor."
    if kind == "commit":
        return "Commit approval recorded; commit creation still requires a separate executor."
    return "Push approval recorded; push still requires a separate executor."


def _now_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
