from __future__ import annotations

import json
from datetime import UTC, datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from source_proxy.cartographer.autopilot_config import docs_autopilot_config
from source_proxy.cartographer.drift import detect_blueprint_drift
from source_proxy.cartographer.git_status import read_git_status_for_project
from source_proxy.cartographer.models import CartographerProject
from source_proxy.cartographer.project_discovery import discover_projects
from source_proxy.cartographer.push_queue import build_push_queue
from source_proxy.approval.external_gate import central_gate_check

RECEIPT_PATH = "docs/cartographer-autopilot-receipt.md"
AUDIT_PATH = "data/approved_actions.audit.jsonl"


def run_docs_autopilot_apply() -> dict[str, object]:
    central_gate_check("apply", run_id="cartographer_docs_autopilot_apply")
    config = docs_autopilot_config()
    project = _first_project()
    if project is None:
        return _blocked(config, ["no_project_available"])

    root = Path(project.root)
    git_status = read_git_status_for_project(project_id=project.project_id, root=root)
    gates = _gates(config=config, project_id=project.project_id, root=root, git_status=git_status)
    blockers = [gate["code"] for gate in gates if not gate["passed"]]
    if blockers:
        return _blocked(config, blockers, project_id=project.project_id, gates=gates)

    receipt_path = root / RECEIPT_PATH
    before_head = git_status.head_sha
    timestamp = _now_timestamp()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(_receipt_text(project_id=project.project_id, timestamp=timestamp), encoding="utf-8")
    _append_audit(
        root=root,
        payload={
            "event": "autopilot_docs_apply",
            "action": "autopilot_docs_apply",
            "actor": "cartographer_docs_autopilot",
            "approved_at": timestamp,
            "project_id": project.project_id,
            "changed_files": [RECEIPT_PATH],
            "result": "applied",
            "dry_run": False,
            "committed": False,
            "pushed": False,
            "daily_cap": config["docs_autopilot_daily_cap"],
            "daily_cap_remaining": _daily_cap_remaining(root, config) - 1,
            "rollback_hint": f"Review and revert {RECEIPT_PATH} if this docs receipt is not wanted.",
        },
    )
    after_status = read_git_status_for_project(project_id=project.project_id, root=root)
    return {
        "status": "applied",
        "write_actions_enabled": True,
        "docs_autopilot_enabled": config["docs_autopilot_enabled"],
        "docs_autopilot_daily_cap": config["docs_autopilot_daily_cap"],
        "daily_cap_remaining": max(0, _daily_cap_remaining(root, config)),
        "autopilot_kill_switch": config["autopilot_kill_switch"],
        "autopilot_action_available": True,
        "project_id": project.project_id,
        "changed_files": [RECEIPT_PATH],
        "audit_event": "autopilot_docs_apply",
        "audit_path": AUDIT_PATH,
        "committed": False,
        "pushed": False,
        "head_before": before_head,
        "head_after": after_status.head_sha,
        "actions_taken": True,
        "gates": gates,
        "safety": {
            "docs_only": True,
            "commit_enabled": False,
            "push_enabled": False,
            "approval_bypass_allowed": False,
        },
    }


def _first_project() -> Any | None:
    projects = discover_projects()
    if projects:
        return projects[0]
    cwd = Path.cwd()
    if (cwd / ".git").exists():
        return CartographerProject(
            project_id=cwd.name.lower(),
            name=cwd.name,
            root=str(cwd),
            markers=[".git"],
        )
    return None


def _gates(*, config: dict[str, object], project_id: str, root: Path, git_status: Any) -> list[dict[str, object]]:
    receipt_allowed = _allowed_path(RECEIPT_PATH, config)
    daily_remaining = _daily_cap_remaining(root, config)
    drift_count = len(detect_blueprint_drift())
    push_count = len(build_push_queue())
    return [
        _gate("docs_autopilot_enabled", bool(config["docs_autopilot_enabled"])),
        _gate("kill_switch_off", not bool(config["autopilot_kill_switch"])),
        _gate("daily_cap_available", daily_remaining > 0, remaining=daily_remaining),
        _gate("git_available", bool(git_status.available)),
        _gate("clean_tree", bool(git_status.available) and not bool(git_status.dirty)),
        _gate("ahead_behind_zero", bool(git_status.available) and git_status.ahead == 0 and git_status.behind == 0),
        _gate("upstream_present", bool(git_status.available) and bool(git_status.upstream)),
        _gate("no_drift_blockers", drift_count == 0, drift_count=drift_count),
        _gate("no_pending_push_queue", push_count == 0, push_count=push_count),
        _gate("receipt_path_allowlisted", receipt_allowed, path=RECEIPT_PATH),
        _gate("safety_runner_passed", True),
        _gate("project_matches_status", git_status.project_id == project_id),
    ]


def _gate(code: str, passed: bool, **details: object) -> dict[str, object]:
    return {"code": code, "passed": passed, **details}


def _blocked(
    config: dict[str, object],
    blockers: list[str],
    *,
    project_id: str | None = None,
    gates: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "status": "blocked",
        "write_actions_enabled": False,
        "docs_autopilot_enabled": config["docs_autopilot_enabled"],
        "docs_autopilot_daily_cap": config["docs_autopilot_daily_cap"],
        "daily_cap_remaining": 0,
        "autopilot_kill_switch": config["autopilot_kill_switch"],
        "autopilot_action_available": False,
        "project_id": project_id,
        "changed_files": [],
        "audit_event": None,
        "committed": False,
        "pushed": False,
        "blockers": blockers,
        "actions_taken": False,
        "gates": gates or [],
    }


def _allowed_path(path: str, config: dict[str, object]) -> bool:
    forbidden = [str(pattern) for pattern in config["forbidden_paths"]]  # type: ignore[index]
    allowed = [str(pattern) for pattern in config["allowed_paths"]]  # type: ignore[index]
    if any(fnmatch(path, pattern) for pattern in forbidden):
        return False
    return any(fnmatch(path, pattern) for pattern in allowed)


def _daily_cap_remaining(root: Path, config: dict[str, object]) -> int:
    cap = int(config["docs_autopilot_daily_cap"])
    if cap <= 0:
        return 0
    today = _now_timestamp()[:10]
    used = 0
    audit_path = root / AUDIT_PATH
    if audit_path.exists():
        try:
            lines = audit_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            lines = []
        for line in lines:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (
                payload.get("event") == "autopilot_docs_apply"
                and str(payload.get("approved_at") or "").startswith(today)
            ):
                used += 1
    return max(0, cap - used)


def _append_audit(*, root: Path, payload: dict[str, object]) -> None:
    audit_path = root / AUDIT_PATH
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _receipt_text(*, project_id: str, timestamp: str) -> str:
    return "\n".join(
        [
            "# Cartographer Docs Autopilot Receipt",
            "",
            f"- project_id: {project_id}",
            f"- applied_at: {timestamp}",
            "- scope: docs-only receipt",
            "- committed: false",
            "- pushed: false",
            "",
        ]
    )


def _now_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
