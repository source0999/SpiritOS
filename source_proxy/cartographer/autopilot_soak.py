from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from source_proxy.cartographer.autopilot_apply import AUDIT_PATH
from source_proxy.cartographer.autopilot_config import docs_autopilot_config
from source_proxy.cartographer.drift import detect_blueprint_drift
from source_proxy.cartographer.project_discovery import discover_projects
from source_proxy.cartographer.proposals import proposal_visibility_summary

MIN_GREEN_DAYS = 7


def build_docs_autopilot_soak_report() -> dict[str, object]:
    config = docs_autopilot_config()
    project = _first_project()
    records = _autopilot_records(Path(project.root)) if project else []
    unique_days = sorted(
        {
            str(record.get("approved_at") or "")[:10]
            for record in records
            if str(record.get("approved_at") or "")[:10]
        }
    )
    checks = _checks(records)
    proposal_summary = proposal_visibility_summary()
    drift_count = len(detect_blueprint_drift())
    duplicate_count = int(proposal_summary["duplicate_proposals_suppressed"])
    noisy_drift_loops = drift_count > 0 and duplicate_count > 0
    checks.extend(
        [
            _check("no_duplicate_proposals", duplicate_count == 0, duplicate_count=duplicate_count),
            _check("no_noisy_drift_loops", not noisy_drift_loops, drift_count=drift_count),
            _check("minimum_repeated_cycles", len(unique_days) >= MIN_GREEN_DAYS, observed_days=len(unique_days)),
        ]
    )
    passed = all(bool(check["passed"]) for check in checks)
    return {
        "status": "observing",
        "write_actions_enabled": False,
        "docs_autopilot_enabled": config["docs_autopilot_enabled"],
        "docs_autopilot_daily_cap": config["docs_autopilot_daily_cap"],
        "autopilot_kill_switch": config["autopilot_kill_switch"],
        "autopilot_action_available": False,
        "soak_required_days": MIN_GREEN_DAYS,
        "observed_days": len(unique_days),
        "cycle_count": len(records),
        "soak_grade": "green" if passed else "not_ready",
        "level9_status": "GREEN" if passed else "YELLOW",
        "checks": checks,
        "actions_taken": False,
    }


def _first_project() -> Any | None:
    projects = discover_projects()
    if projects:
        return projects[0]
    cwd = Path.cwd()
    if (cwd / ".git").exists():
        return type("CurrentProject", (), {"root": str(cwd)})()
    return None


def _autopilot_records(root: Path) -> list[dict[str, Any]]:
    audit_path = root / AUDIT_PATH
    if not audit_path.exists():
        return []
    try:
        lines = audit_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    records: list[dict[str, Any]] = []
    for line in lines:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("event") == "autopilot_docs_apply":
            records.append(payload)
    return records


def _checks(records: list[dict[str, Any]]) -> list[dict[str, object]]:
    changed_files = [
        str(path)
        for record in records
        for path in _list_value(record.get("changed_files"))
    ]
    return [
        _check("no_app_code_touched", not any(_is_app_path(path) for path in changed_files), files=changed_files),
        _check("no_safety_code_touched", not any(_is_safety_path(path) for path in changed_files)),
        _check("no_approval_code_touched", not any(_is_approval_path(path) for path in changed_files)),
        _check("no_secrets_touched", not any(_is_secret_path(path) for path in changed_files)),
        _check("no_commits_without_approval", not any(bool(record.get("committed")) for record in records)),
        _check("no_pushes_without_approval", not any(bool(record.get("pushed")) for record in records)),
        _check("all_actions_audited", bool(records), audited_actions=len(records)),
    ]


def _check(code: str, passed: bool, **details: object) -> dict[str, object]:
    return {"code": code, "passed": passed, **details}


def _list_value(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _is_app_path(path: str) -> bool:
    return path.startswith(("src/", "app/"))


def _is_safety_path(path: str) -> bool:
    return path.startswith(("source_proxy/safety/", "source_proxy/cartographer/safety.py"))


def _is_approval_path(path: str) -> bool:
    return path.startswith("source_proxy/approval/") or path in {
        "source_proxy/cartographer/git_approvals.py",
        "source_proxy/cartographer/apply.py",
        "source_proxy/cartographer/push_queue.py",
    }


def _is_secret_path(path: str) -> bool:
    lowered = path.lower()
    return ".env" in lowered or any(token in lowered for token in ("secret", "token", "credential"))
