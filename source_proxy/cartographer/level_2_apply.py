from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from source_proxy.cartographer.git_status import read_git_status_for_project
from source_proxy.cartographer.project_discovery import discover_projects
from source_proxy.approval.external_gate import central_gate_check

RECEIPT_DIR = "docs/cartographer-level-2-apply-receipts"
FORBIDDEN_PREFIXES = (
    "src/",
    "source_proxy/",
    "scout/src/",
    "scout/config/",
    "backend/",
    "scripts/",
    "tests/",
    "certificates/",
)
FORBIDDEN_EXACT_PATHS = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "tsconfig.json",
    "eslint.config.mjs",
    "vitest.config.mjs",
    "next.config.ts",
    "middleware.ts",
}


def run_level_2_docs_apply(
    *,
    proposal_id: str,
    approval_id: str | None = None,
    approval_actor: str | None = None,
) -> dict[str, Any]:
    central_gate_check("apply", run_id=f"cartographer_level_2_docs_apply:{proposal_id}")
    project = _first_project()
    if project is None:
        return _blocked(proposal_id=proposal_id, blockers=["no_project_available"])

    root = Path(project.root)
    proposal = _load_proposal(root, proposal_id)
    if proposal is None:
        return _blocked(proposal_id=proposal_id, project_id=project.project_id, blockers=["proposal_not_found"])

    git_status_before = read_git_status_for_project(project_id=project.project_id, root=root)
    blockers = _proposal_blockers(
        proposal=proposal,
        approval_id=approval_id,
        approval_actor=approval_actor,
        git_head=git_status_before.head_sha,
    )
    patch = str(proposal.get("approved_diff") or proposal.get("patch") or proposal.get("diff_preview") or "")
    target_paths = _target_paths(proposal=proposal, patch=patch)
    if "diff_target_mismatch" in target_paths:
        blockers.append("proposal_target_path_changed")
    forbidden_paths = [path for path in target_paths if not _is_allowed_level_2_path(path)]
    if forbidden_paths:
        blockers.append("forbidden_paths_detected")
    if _has_dirty_unrelated_files(git_status_before.changed_files, target_paths):
        blockers.append("dirty_tree_unclassified")
    if not git_status_before.available:
        blockers.append("git_unavailable")

    diff_check_before = _git_apply_check(root, patch) if patch.strip() and not forbidden_paths else _skip_check()
    if not diff_check_before["ok"]:
        blockers.append("patch_check_failed")

    if blockers:
        return _receipt_payload(
            result="blocked",
            proposal=proposal,
            proposal_id=proposal_id,
            approval_id=approval_id,
            approval_actor=approval_actor,
            git_status_before=git_status_before,
            git_status_after=git_status_before,
            files_requested=target_paths,
            files_allowed=[path for path in target_paths if _is_allowed_level_2_path(path)],
            files_written=[],
            files_blocked=forbidden_paths,
            forbidden_paths_detected=forbidden_paths,
            diff_check_before=diff_check_before,
            diff_check_after=_skip_check(),
            receipt_path=None,
            blocker_reasons=_unique(blockers),
        )

    _git_apply(root, patch)
    git_status_after_patch = read_git_status_for_project(project_id=project.project_id, root=root)
    diff_check_after = _git_diff_check(root, target_paths)
    receipt_path = _write_receipt(
        root=root,
        proposal=proposal,
        proposal_id=proposal_id,
        approval_id=approval_id,
        approval_actor=approval_actor,
        git_status_before=git_status_before,
        git_status_after=git_status_after_patch,
        files_requested=target_paths,
        files_allowed=target_paths,
        files_written=target_paths,
        diff_check_before=diff_check_before,
        diff_check_after=diff_check_after,
    )
    git_status_after = read_git_status_for_project(project_id=project.project_id, root=root)
    payload = _receipt_payload(
        result="applied",
        proposal=proposal,
        proposal_id=proposal_id,
        approval_id=approval_id,
        approval_actor=approval_actor,
        git_status_before=git_status_before,
        git_status_after=git_status_after,
        files_requested=target_paths,
        files_allowed=target_paths,
        files_written=[*target_paths, receipt_path],
        files_blocked=[],
        forbidden_paths_detected=[],
        diff_check_before=diff_check_before,
        diff_check_after=diff_check_after,
        receipt_path=receipt_path,
        blocker_reasons=[],
    )
    return payload


def _proposal_blockers(
    *,
    proposal: dict[str, Any],
    approval_id: str | None,
    approval_actor: str | None,
    git_head: str | None,
) -> list[str]:
    blockers: list[str] = []
    status = str(proposal.get("status") or "")
    if status not in {"approved", "pending_human_approval"}:
        blockers.append("proposal_not_pending_human_approval")
    if not approval_id or str(proposal.get("approval_id") or "") != approval_id:
        blockers.append("human_approval_id_required")
    approved_by = str(proposal.get("approved_by") or proposal.get("approval_actor") or "")
    if not approved_by:
        blockers.append("approval_actor_required")
    if approved_by.lower() == "cartographer" or approved_by.startswith("cartographer_"):
        blockers.append("cartographer_self_approval_blocked")
    if approval_actor and approved_by and approval_actor != approved_by:
        blockers.append("approval_actor_mismatch")
    if not proposal.get("approved_at") and not proposal.get("approval_timestamp"):
        blockers.append("approval_timestamp_required")
    if not proposal.get("created_at"):
        blockers.append("created_at_required")
    proposal_head = str(proposal.get("git_head_at_creation") or "")
    if not proposal_head:
        blockers.append("git_head_at_creation_required")
    elif git_head and proposal_head != git_head:
        blockers.append("proposal_head_mismatch")
    if not (proposal.get("rollback_hint") or proposal.get("rollback_command")):
        blockers.append("rollback_hint_required")
    if not (proposal.get("manual_check_command") or proposal.get("manual_check_commands")):
        blockers.append("manual_check_required")
    patch = str(proposal.get("approved_diff") or proposal.get("patch") or proposal.get("diff_preview") or "")
    if not patch.strip():
        blockers.append("patch_required")
    return blockers


def _target_paths(*, proposal: dict[str, Any], patch: str) -> list[str]:
    paths = [
        _normalize_repo_path(str(path))
        for path in proposal.get("target_paths") or proposal.get("proposed_files") or []
        if str(path)
    ]
    diff_paths = _changed_paths_from_unified_diff(patch)
    if paths and diff_paths and sorted(set(paths)) != sorted(set(diff_paths)):
        return _unique([*paths, *diff_paths, "diff_target_mismatch"])
    return _unique(diff_paths or paths)


def _is_allowed_level_2_path(path: str) -> bool:
    normalized = _normalize_repo_path(path)
    if not normalized or normalized.startswith("/") or normalized == ".":
        return False
    if normalized == "diff_target_mismatch":
        return False
    if normalized.startswith("../") or "/../" in f"/{normalized}/":
        return False
    if normalized.startswith(".env") or "/.env" in normalized:
        return False
    if normalized in FORBIDDEN_EXACT_PATHS:
        return False
    if any(normalized.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return False
    if normalized == "README.md":
        return True
    if normalized.startswith("docs/") and normalized.endswith(".md"):
        return True
    return "/" not in normalized and normalized.endswith(".md")


def _has_dirty_unrelated_files(changed_files: list[str], target_paths: list[str]) -> bool:
    allowed_dirty = set(target_paths)
    return any(
        path not in allowed_dirty
        and not path.startswith("_blueprints/proposals/")
        and not path.startswith(RECEIPT_DIR + "/")
        for path in changed_files
    )


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


def _load_proposal(root: Path, proposal_id: str) -> dict[str, Any] | None:
    proposal_root = root / "_blueprints" / "proposals"
    if not proposal_root.exists():
        return None
    for path in sorted(proposal_root.rglob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and str(payload.get("proposal_id") or "") == proposal_id:
            return payload
    return None


def _first_project() -> Any | None:
    projects = discover_projects()
    if projects:
        return projects[0]
    cwd = Path.cwd()
    if (cwd / ".git").exists():
        return type("Project", (), {"project_id": cwd.name.lower(), "root": str(cwd)})()
    return None


def _git_apply_check(root: Path, patch: str) -> dict[str, Any]:
    return _run_patch_command(root, ["git", "apply", "--check", "-"], patch)


def _git_apply(root: Path, patch: str) -> None:
    result = _run_patch_command(root, ["git", "apply", "-"], patch)
    if not result["ok"]:
        raise RuntimeError(str(result["summary"]))


def _git_diff_check(root: Path, paths: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        ["git", "diff", "--check", "--", *paths],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    return {"ok": result.returncode == 0, "summary": output or "git diff --check passed"}


def _run_patch_command(root: Path, command: list[str], patch: str) -> dict[str, Any]:
    result = subprocess.run(
        command,
        input=patch,
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    return {"ok": result.returncode == 0, "summary": output or "patch check passed"}


def _skip_check() -> dict[str, Any]:
    return {"ok": False, "summary": "not run"}


def _write_receipt(
    *,
    root: Path,
    proposal: dict[str, Any],
    proposal_id: str,
    approval_id: str | None,
    approval_actor: str | None,
    git_status_before: Any,
    git_status_after: Any,
    files_requested: list[str],
    files_allowed: list[str],
    files_written: list[str],
    diff_check_before: dict[str, Any],
    diff_check_after: dict[str, Any],
) -> str:
    receipt_path = f"{RECEIPT_DIR}/{proposal_id}.md"
    receipt = _receipt_payload(
        result="applied",
        proposal=proposal,
        proposal_id=proposal_id,
        approval_id=approval_id,
        approval_actor=approval_actor,
        git_status_before=git_status_before,
        git_status_after=git_status_after,
        files_requested=files_requested,
        files_allowed=files_allowed,
        files_written=[*files_written, receipt_path],
        files_blocked=[],
        forbidden_paths_detected=[],
        diff_check_before=diff_check_before,
        diff_check_after=diff_check_after,
        receipt_path=receipt_path,
        blocker_reasons=[],
    )
    target = root / receipt_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_receipt_markdown(receipt), encoding="utf-8")
    return receipt_path


def _receipt_payload(
    *,
    result: str,
    proposal: dict[str, Any],
    proposal_id: str,
    approval_id: str | None,
    approval_actor: str | None,
    git_status_before: Any,
    git_status_after: Any,
    files_requested: list[str],
    files_allowed: list[str],
    files_written: list[str],
    files_blocked: list[str],
    forbidden_paths_detected: list[str],
    diff_check_before: dict[str, Any],
    diff_check_after: dict[str, Any],
    receipt_path: str | None,
    blocker_reasons: list[str],
) -> dict[str, Any]:
    head_before = git_status_before.head_sha
    head_after = git_status_after.head_sha
    return {
        "schema_version": "cartographer.level_2.apply_receipt.v1",
        "level": 2,
        "mode": "approved_docs_apply",
        "status": result,
        "result": result,
        "proposal_id": proposal_id,
        "approval_id": approval_id,
        "approval_actor": approval_actor or proposal.get("approved_by") or proposal.get("approval_actor"),
        "approval_timestamp": proposal.get("approved_at") or proposal.get("approval_timestamp"),
        "approval_validated": result == "applied",
        "apply_requires_human_approval": True,
        "cartographer_self_approval": False,
        "git_head_before": head_before,
        "git_head_after": head_after,
        "head_changed": head_before != head_after,
        "dirty_status_before": list(git_status_before.changed_files),
        "dirty_status_after": list(git_status_after.changed_files),
        "files_requested": files_requested,
        "files_allowed": files_allowed,
        "files_written": files_written,
        "files_blocked": files_blocked,
        "forbidden_paths_detected": forbidden_paths_detected,
        "diff_check_before": diff_check_before,
        "diff_check_after": diff_check_after,
        "commit_created": False,
        "push_created": False,
        "branch_created": False,
        "committed": False,
        "pushed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "branch_allowed": False,
        "delete_allowed": False,
        "cleanup_allowed": False,
        "source_code_allowed": False,
        "self_promotion_allowed": False,
        "receipt_path": receipt_path,
        "audit_receipt_written": result == "applied" and receipt_path is not None,
        "rollback_command": proposal.get("rollback_command") or proposal.get("rollback_hint") or "",
        "manual_check_commands": _manual_check_commands(proposal),
        "created_at": _now_timestamp(),
        "blocker_reasons": blocker_reasons,
        "write_actions_enabled": result == "applied",
        "actions_taken": result == "applied",
    }


def _blocked(*, proposal_id: str, blockers: list[str], project_id: str | None = None) -> dict[str, Any]:
    return {
        "level": 2,
        "mode": "approved_docs_apply",
        "status": "blocked",
        "result": "blocked",
        "project_id": project_id,
        "proposal_id": proposal_id,
        "write_actions_enabled": False,
        "actions_taken": False,
        "commit_created": False,
        "push_created": False,
        "branch_created": False,
        "committed": False,
        "pushed": False,
        "files_written": [],
        "blocker_reasons": blockers,
    }


def _receipt_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Cartographer Level 2 Apply Receipt",
            "",
            "```json",
            json.dumps(payload, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )


def _normalize_repo_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    if normalized.startswith("a/") or normalized.startswith("b/"):
        normalized = normalized[2:]
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _manual_check_commands(proposal: dict[str, Any]) -> list[str]:
    commands = proposal.get("manual_check_commands")
    if isinstance(commands, list):
        return [str(command) for command in commands if str(command)]
    command = proposal.get("manual_check_command")
    return [str(command)] if command else []


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _now_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
