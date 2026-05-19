from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import dataclass
from typing import Any

from pathlib import Path

from source_proxy.safety.paths import (
    normalize_repo_path_candidate,
    path_escapes_workspace,
    unsafe_target_finding,
)

_PROPOSAL_FENCED_JSON_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True)
class BoundedProposal:
    task: str
    mode: str
    target_file: str
    allowed_files: tuple[str, ...]
    forbidden_files: tuple[str, ...]
    expected_checks: tuple[str, ...]
    rollback_hint: str


def parse_bounded_proposal_task(task: str) -> BoundedProposal | None:
    text = (task or "").strip()
    if "proposal task:" not in text.lower():
        return None
    match = _PROPOSAL_FENCED_JSON_RE.search(text)
    if not match:
        return None
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return _bounded_proposal_from_payload(payload)


def _bounded_proposal_from_payload(payload: dict[str, Any]) -> BoundedProposal | None:
    task_text = str(payload.get("task") or "").strip()
    target_raw = payload.get("target_file")
    target_file = ""
    if isinstance(target_raw, str):
        target_file = normalize_repo_path_candidate(target_raw)
    mode = "readonly" if str(payload.get("mode") or "").strip().lower() == "readonly" else "proposal"
    allowed_files = _normalize_path_list(payload.get("allowed_files"))
    forbidden_files = _normalize_path_list(payload.get("forbidden_files"))
    expected_checks = _normalize_string_list(payload.get("expected_checks"))
    rollback_hint = str(payload.get("rollback_hint") or "").strip()
    if not task_text and not target_file:
        return None
    return BoundedProposal(
        task=task_text,
        mode=mode,
        target_file=target_file,
        allowed_files=tuple(allowed_files),
        forbidden_files=tuple(forbidden_files),
        expected_checks=tuple(expected_checks),
        rollback_hint=rollback_hint,
    )


def path_matches_forbidden(path: str, forbidden_files: tuple[str, ...] | list[str]) -> bool:
    normalized = normalize_repo_path_candidate(path)
    if not normalized:
        return False
    base = normalized.split("/")[-1]
    for pattern in forbidden_files:
        blocked = normalize_repo_path_candidate(str(pattern))
        if not blocked:
            continue
        if blocked.endswith("/*"):
            if normalized.startswith(blocked[:-1]):
                return True
            continue
        if blocked.endswith("/"):
            if normalized.startswith(blocked):
                return True
            continue
        if normalized == blocked or base == blocked:
            return True
        if fnmatch.fnmatch(normalized, blocked) or fnmatch.fnmatch(base, blocked):
            return True
    return False


def _normalize_path_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        path = normalize_repo_path_candidate(item)
        if path:
            out.append(path)
    return out


def _normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


_PROPOSAL_TASK_MARKER_RE = re.compile(
    r"(?im)^\s*proposal\s+task\s*:\s*$",
)


def _text_before_proposal_marker(task: str) -> str:
    match = _PROPOSAL_TASK_MARKER_RE.search(task or "")
    if not match:
        return (task or "").strip()
    return (task or "")[: match.start()].rstrip()


def effective_planning_task_text(task: str) -> str:
    """Use bounded proposal task body for length/heuristics, not the full fenced JSON envelope."""
    proposal = parse_bounded_proposal_task(task)
    if proposal is None:
        return (task or "").strip()
    if proposal.task:
        return proposal.task
    before = _text_before_proposal_marker(task)
    if before.strip():
        return before.strip()
    if proposal.target_file:
        return f"Target file: {proposal.target_file}"
    return ""


def bounded_proposal_create_allowed(
    proposal: BoundedProposal,
    *,
    workspace_root: Path,
) -> tuple[bool, str]:
    if proposal.mode != "proposal":
        return False, "readonly_mode"
    target = normalize_repo_path_candidate(proposal.target_file)
    if not target:
        return False, "missing_target_file"
    if not proposal.allowed_files:
        return False, "missing_allowed_files"
    if target not in proposal.allowed_files:
        return False, "target_not_in_allowed_files"
    if path_matches_forbidden(target, proposal.forbidden_files):
        return False, "target_forbidden"
    if path_escapes_workspace(target, workspace_root=workspace_root):
        return False, "path_escape"
    unsafe = unsafe_target_finding(target, workspace_root=workspace_root)
    if unsafe is not None:
        return False, unsafe.reason_code
    root = workspace_root.resolve()
    target_abs = (root / target).resolve()
    if not _is_relative_to(target_abs, root):
        return False, "outside_workspace"
    if target_abs.is_file():
        return False, "target_already_exists"
    parent = target_abs.parent
    if parent != root and not parent.exists():
        try:
            parent.relative_to(root)
        except ValueError:
            return False, "invalid_parent_directory"
    return True, ""


def merge_proposal_forbidden_paths(
    proposal: BoundedProposal,
    *,
    context_defaults: list[str] | tuple[str, ...],
) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for path in (*proposal.forbidden_files, *context_defaults):
        normalized = normalize_repo_path_candidate(str(path))
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        merged.append(normalized)
    return merged


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
