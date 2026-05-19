from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from source_proxy.cartographer.autonomy_promotion import build_autonomy_promotion_recommendation
from source_proxy.cartographer.git_status import read_git_status_for_project
from source_proxy.cartographer.project_discovery import discover_projects


def build_level_2_readiness() -> dict[str, Any]:
    promotion = build_autonomy_promotion_recommendation()
    level_1 = promotion["level_1_readiness"]  # type: ignore[index]
    level_1_label = str(level_1["label"])  # type: ignore[index]
    britton_override = _level_1_accepted_by_britton()
    project = _first_project()
    git_status = (
        read_git_status_for_project(project_id=project.project_id, root=Path(project.root))
        if project is not None
        else None
    )
    dirty_tree = classify_level_2_dirty_tree(git_status)
    dirty_files = dirty_tree["dirty_files"]
    unrelated_dirty_files = dirty_tree["unclassified_blockers"]
    checks = [
        _gate(
            "level_1_review_gate",
            level_1_label == "ready_for_level_1_review" or britton_override,
            (
                f"Level 1 label is {level_1_label}; Britton override accepted"
                if britton_override
                else f"Level 1 label is {level_1_label}"
            ),
        ),
        _gate(
            "dirty_tree_classified",
            git_status is not None and not dirty_tree["blocks_level_2_apply"],
            (
                "dirty tree is classified and Level 2-safe"
                if not unrelated_dirty_files
                else f"Level 2 blockers: {', '.join(unrelated_dirty_files[:8])}"
            ),
        ),
        _gate(
            "docs_only_path_filter_exists",
            True,
            "Level 2 allowlist permits docs/**/*.md, README.md, and named top-level markdown plans only.",
        ),
        _gate(
            "approval_validation_exists",
            True,
            "Level 2 apply requires approval_id, approval_actor, approval timestamp, and non-Cartographer actor.",
        ),
        _gate(
            "apply_receipt_exists",
            True,
            "Level 2 apply writes docs/cartographer-level-2-apply-receipts/<proposal_id>.md.",
        ),
        _gate(
            "commit_push_branch_locked",
            True,
            "Level 2 apply returns commit_created=false, push_created=false, and branch_created=false.",
        ),
        _gate(
            "source_apply_blocked",
            True,
            "Level 2 apply blocks src/**, source_proxy/**, scout/src/**, backend/**, scripts/**, tests/**, config, package, lock, and env targets.",
        ),
        _gate(
            "self_promotion_blocked",
            True,
            "Level 2 readiness does not grant Level 3 authority.",
        ),
    ]
    blockers = [check for check in checks if not check["passed"]]
    ready = not blockers
    label = "ready_for_review" if ready else "watch" if _only_level_1_blocked(blockers) else "blocked"
    return {
        "status": "observing",
        "level": 2,
        "mode": "human_approved_docs_apply",
        "label": label,
        "recommendation": label,
        "active_next_autonomy_plan": "docs/cartographer-level-2-autonomy-plan.md",
        "level_1_baseline": "docs/cartographer-level-1-autonomy-plan.md",
        "level_1_recommendation": level_1_label,
        "level_1_accepted_by_britton": britton_override,
        "authority_granted": False,
        "write_actions_enabled": ready,
        "apply_requires_human_approval": True,
        "docs_apply_enabled": ready,
        "commit_allowed": False,
        "push_allowed": False,
        "branch_allowed": False,
        "delete_allowed": False,
        "cleanup_allowed": False,
        "source_code_allowed": False,
        "self_promotion_allowed": False,
        "actions_taken": False,
        "dirty_tree_block": bool(unrelated_dirty_files),
        "dirty_tree_classification": dirty_tree,
        "dirty_files": dirty_files,
        "unrelated_dirty_files": unrelated_dirty_files,
        "checks": checks,
        "check_count": len(checks),
        "passed_count": len([check for check in checks if check["passed"]]),
        "blockers": blockers,
        "blocker_count": len(blockers),
        "next_action": (
            "Level 2 may apply only an explicitly approved docs-only proposal."
            if ready
            else f"resolve blocker: {blockers[0]['code']}"
        ),
        "manual_checks": [
            "PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k \"level_2 or apply\"",
            "PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py",
            "git status -sb",
        ],
    }


def build_level_2_dirty_tree_classification() -> dict[str, Any]:
    project = _first_project()
    git_status = (
        read_git_status_for_project(project_id=project.project_id, root=Path(project.root))
        if project is not None
        else None
    )
    classification = classify_level_2_dirty_tree(git_status)
    return {
        "status": "observing",
        "level": 2,
        "mode": "dirty_tree_classification",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "classification": classification,
        "dirty_tree_block": classification["blocks_level_2_apply"],
        "next_action": (
            "dirty tree is classified and Level 2-safe"
            if not classification["blocks_level_2_apply"]
            else "human must classify or clear unrelated dirty files before Level 2 apply"
        ),
    }


def build_level_2_api_contract_review_packet() -> dict[str, Any]:
    readiness = build_level_2_readiness()
    dirty_tree = build_level_2_dirty_tree_classification()
    endpoints = [
        {
            "endpoint": "/v1/cartographer/level-2-readiness",
            "method": "GET",
            "mode": "read_only_status",
            "write_actions_enabled": False,
            "purpose": "Show Level 2 readiness, blockers, and authority boundaries.",
        },
        {
            "endpoint": "/v1/cartographer/level-2-dirty-tree",
            "method": "GET",
            "mode": "read_only_dirty_tree_classification",
            "write_actions_enabled": False,
            "purpose": "Classify dirty files and explain whether Level 2 apply is blocked.",
        },
        {
            "endpoint": "/v1/cartographer/docs-autopilot/level-2/apply",
            "method": "POST",
            "mode": "human_approved_docs_apply",
            "write_actions_enabled": "only_when_all_level_2_gates_pass",
            "purpose": "Apply one explicitly approved docs-only proposal and write a receipt.",
            "request_fields": ["proposal_id", "approval_id", "approval_actor"],
        },
    ]
    return {
        "status": "observing",
        "level": 2,
        "mode": "api_contract_review_packet",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "contract_version": "cartographer.level_2.api_contract.v1",
        "active_next_autonomy_plan": "docs/cartographer-level-2-autonomy-plan.md",
        "level_1_baseline": "docs/cartographer-level-1-autonomy-plan.md",
        "readiness_endpoint": "/v1/cartographer/level-2-readiness",
        "dirty_tree_endpoint": "/v1/cartographer/level-2-dirty-tree",
        "apply_endpoint": "/v1/cartographer/docs-autopilot/level-2/apply",
        "endpoint_count": len(endpoints),
        "endpoints": endpoints,
        "current_readiness": {
            "label": readiness["label"],
            "docs_apply_enabled": readiness["docs_apply_enabled"],
            "blocker_count": readiness["blocker_count"],
            "blockers": [blocker["code"] for blocker in readiness["blockers"]],
        },
        "dirty_tree_summary": {
            "dirty_tree_block": dirty_tree["dirty_tree_block"],
            "unclassified_blocker_count": dirty_tree["classification"]["unclassified_blocker_count"],
            "blocking_policy": dirty_tree["classification"]["blocking_policy"],
        },
        "allowed_action": "human-approved docs-only apply",
        "allowed_paths": [
            "docs/**/*.md",
            "README.md only when explicitly approved in the proposal",
            "named top-level markdown plan files only when explicitly approved and not deleted",
        ],
        "forbidden_paths": [
            "src/**",
            "source_proxy/**",
            "scout/src/**",
            "scout/config/**",
            "backend/**",
            "scripts/**",
            "tests/**",
            ".env*",
            "certificates/**",
            "package.json",
            "lock files",
            "tsconfig/eslint/vitest/next config",
            "binary/generated/build output",
        ],
        "required_apply_request_fields": ["proposal_id", "approval_id", "approval_actor"],
        "required_receipt_fields": [
            "schema_version",
            "level",
            "mode",
            "proposal_id",
            "approval_id",
            "approval_actor",
            "approval_timestamp",
            "git_head_before",
            "git_head_after",
            "files_requested",
            "files_written",
            "commit_created",
            "push_created",
            "branch_created",
            "rollback_command",
            "manual_check_commands",
            "result",
            "blocker_reasons",
        ],
        "forbidden_actions": [
            "apply without human approval",
            "source code edits",
            "commit creation",
            "push queue creation",
            "branch creation",
            "delete or cleanup",
            "merge",
            "self-promotion to Level 3",
            "apply when proposal target path changed",
            "apply when proposal is stale",
            "apply when unrelated dirty files are present",
        ],
        "manual_checks": [
            "PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k \"level_2 or apply\"",
            "PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py",
            "PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_proxy_runner.py -k \"cartographer or autonomy\"",
            "git diff --check",
            "git status -sb",
        ],
        "expected_output": [
            "Level 2 readiness remains blocked until Level 1 is accepted and dirty tree blockers are resolved.",
            "Read-only endpoints keep write_actions_enabled false.",
            "Apply endpoint requires proposal_id, approval_id, and approval_actor.",
            "Receipt proves no commit, push, branch, cleanup, delete, or source edit happened.",
        ],
        "next_increment": "Level 2 UI Review Card Read-Only Projection",
    }


def build_level_2_closeout_packet() -> dict[str, Any]:
    readiness = build_level_2_readiness()
    contract = build_level_2_api_contract_review_packet()
    dirty_tree = build_level_2_dirty_tree_classification()
    blockers = [blocker["code"] for blocker in readiness["blockers"]]
    ready = readiness["label"] == "ready_for_review"
    return {
        "status": "observing",
        "level": 2,
        "mode": "level_2_closeout",
        "closeout_version": "cartographer.level_2.closeout.v1",
        "implementation_complete": True,
        "ready_for_activation": ready,
        "recommendation": "ready_for_review" if ready else "blocked",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "active_next_autonomy_plan": "docs/cartographer-level-2-autonomy-plan.md",
        "level_1_baseline": "docs/cartographer-level-1-autonomy-plan.md",
        "level_1_recommendation": readiness["level_1_recommendation"],
        "docs_apply_enabled": readiness["docs_apply_enabled"],
        "blockers": blockers,
        "blocker_count": len(blockers),
        "dirty_tree_block": dirty_tree["dirty_tree_block"],
        "dirty_tree_blocker_count": dirty_tree["classification"]["unclassified_blocker_count"],
        "surfaces_completed": [
            "/v1/cartographer/level-2-readiness",
            "/v1/cartographer/level-2-dirty-tree",
            "/v1/cartographer/level-2-api-contract",
            "/v1/cartographer/docs-autopilot/level-2/apply",
            "HomelabCartographerWidget Level 2 review card",
        ],
        "safety_contract": {
            "apply_requires_human_approval": True,
            "allowed_action": "human-approved docs-only apply",
            "commit_allowed": False,
            "push_allowed": False,
            "branch_allowed": False,
            "delete_allowed": False,
            "cleanup_allowed": False,
            "source_code_allowed": False,
            "self_promotion_allowed": False,
        },
        "evidence": {
            "api_contract_version": contract["contract_version"],
            "api_endpoint_count": contract["endpoint_count"],
            "required_apply_request_fields": contract["required_apply_request_fields"],
            "required_receipt_fields": contract["required_receipt_fields"],
            "current_readiness": contract["current_readiness"],
            "dirty_tree_summary": contract["dirty_tree_summary"],
        },
        "manual_checks": [
            "npm test -- HomelabCartographerWidget",
            "PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k \"level_2 or apply\"",
            "PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py",
            "PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_proxy_runner.py -k \"cartographer or autonomy\"",
            "git diff --check",
            "git status -sb",
        ],
        "expected_output": [
            "Widget test passes with no approve/apply/commit/push controls.",
            "Level 2 backend and safety tests pass.",
            "Closeout remains blocked while level_1_review_gate or dirty_tree_classified blockers exist.",
            "No staging, commit, push, branch, cleanup, or source apply authority is granted.",
        ],
        "next_increment": (
            "Resolve Level 1 acceptance and dirty tree blockers before any real Level 2 apply"
            if not ready
            else "Human-approved docs-only apply pilot"
        ),
    }


def build_level_2_dirty_tree_resolution_packet() -> dict[str, Any]:
    readiness = build_level_2_readiness()
    dirty_tree = build_level_2_dirty_tree_classification()
    classification = dirty_tree["classification"]
    buckets = classification["buckets"]
    resolution_groups = [
        _resolution_group(
            group_id="level_2_docs_and_receipts",
            label="Level 2 docs and receipt evidence",
            files=[
                *buckets.get("level_1_baseline_doc", []),
                *buckets.get("level_2_plan_doc", []),
                *buckets.get("level_2_apply_receipt", []),
            ],
            blocks_apply=False,
            recommended_disposition="May remain dirty only when explicitly accepted as Level 2 evidence.",
        ),
        _resolution_group(
            group_id="level_2_implementation",
            label="Level 2 implementation files",
            files=buckets.get("level_2_implementation", []),
            blocks_apply=True,
            recommended_disposition="Review and land separately before any real Level 2 apply.",
        ),
        _resolution_group(
            group_id="source_proxy_unrelated",
            label="Other Source Proxy changes",
            files=buckets.get("source_proxy_dirty", []),
            blocks_apply=True,
            recommended_disposition="Classify as separate source work; do not allow Level 2 apply while dirty.",
        ),
        _resolution_group(
            group_id="app_and_dashboard_source",
            label="App and dashboard source changes",
            files=[
                *buckets.get("app_source_dirty", []),
                *buckets.get("coding_cockpit_dirty", []),
            ],
            blocks_apply=True,
            recommended_disposition="Review or isolate outside Level 2; app source dirt blocks docs apply.",
        ),
        _resolution_group(
            group_id="scout_work",
            label="Scout work and soak logs",
            files=buckets.get("scout_dirty", []),
            blocks_apply=True,
            recommended_disposition="Handle in Scout closeout; Cartographer Level 2 must not clean or classify as safe.",
        ),
        _resolution_group(
            group_id="deleted_old_plans",
            label="Deleted old plan files",
            files=buckets.get("deleted_old_plan_dirty", []),
            blocks_apply=True,
            recommended_disposition="Britton must decide whether to preserve, restore, or land these deletions separately.",
        ),
        _resolution_group(
            group_id="unclassified_docs_and_markdown",
            label="Unclassified docs and markdown",
            files=[
                *buckets.get("unclassified_docs_dirty", []),
                *buckets.get("unclassified_markdown_dirty", []),
            ],
            blocks_apply=True,
            recommended_disposition="Explicitly classify or move through a human-approved docs proposal.",
        ),
        _resolution_group(
            group_id="unclassified_other",
            label="Other unclassified files",
            files=buckets.get("unclassified_dirty", []),
            blocks_apply=True,
            recommended_disposition="Classify manually before Level 2 apply can run.",
        ),
    ]
    blocking_groups = [group for group in resolution_groups if group["blocks_apply"] and group["file_count"]]
    return {
        "status": "observing",
        "level": 2,
        "mode": "dirty_tree_resolution_packet",
        "write_actions_enabled": False,
        "authority_granted": False,
        "actions_taken": False,
        "resolution_version": "cartographer.level_2.dirty_tree_resolution.v1",
        "ready_for_level_2_apply": readiness["docs_apply_enabled"],
        "dirty_tree_block": dirty_tree["dirty_tree_block"],
        "dirty_file_count": classification["dirty_file_count"],
        "blocking_file_count": classification["unclassified_blocker_count"],
        "blocking_group_count": len(blocking_groups),
        "resolution_groups": resolution_groups,
        "blocking_groups": blocking_groups,
        "allowed_without_cleanup": [
            "docs/cartographer-level-1-autonomy-plan.md",
            "docs/cartographer-level-2-autonomy-plan.md",
            "docs/cartographer-level-2-apply-receipts/*.md",
        ],
        "forbidden_resolution_actions": [
            "auto delete",
            "auto restore",
            "auto stash",
            "auto commit",
            "auto branch",
            "auto push",
            "mark source files as apply-safe",
        ],
        "manual_checks": [
            "git status -sb",
            "PYTHONPATH=. .venv/bin/python - <<'PY'\nfrom source_proxy.cartographer.service import build_cartographer_level_2_dirty_tree_resolution\npayload = build_cartographer_level_2_dirty_tree_resolution()\nprint(payload['resolution_version'])\nprint(payload['dirty_tree_block'])\nprint(payload['blocking_file_count'])\nprint([group['group_id'] for group in payload['blocking_groups']])\nPY",
            "git diff --check",
        ],
        "expected_output": [
            "resolution_version is cartographer.level_2.dirty_tree_resolution.v1",
            "dirty_tree_block remains true until unrelated dirty files are handled",
            "blocking groups identify the human-owned work that prevents Level 2 apply",
            "no files are modified by this packet",
        ],
        "next_increment": "Human Resolve Dirty Tree Or Keep Level 2 Blocked",
    }


def classify_level_2_dirty_tree(git_status: Any | None) -> dict[str, Any]:
    dirty_files = list(git_status.changed_files) if git_status is not None else []
    records = [_dirty_file_record(path) for path in dirty_files]
    unclassified_blockers = [
        record["path"]
        for record in records
        if record["blocks_level_2_apply"]
    ]
    buckets: dict[str, list[str]] = {}
    for record in records:
        buckets.setdefault(str(record["classification"]), []).append(str(record["path"]))
    return {
        "git_available": bool(git_status and git_status.available),
        "dirty": bool(dirty_files),
        "dirty_files": dirty_files,
        "dirty_file_count": len(dirty_files),
        "files": records,
        "buckets": buckets,
        "unclassified_blockers": unclassified_blockers,
        "unclassified_blocker_count": len(unclassified_blockers),
        "blocks_level_2_apply": bool(unclassified_blockers),
        "allowed_classifications": [
            "level_1_baseline_doc",
            "level_2_plan_doc",
            "level_2_apply_receipt",
        ],
        "blocking_policy": "any file outside explicit Level 2 docs/evidence classifications blocks apply",
    }


def _dirty_file_record(path: str) -> dict[str, Any]:
    classification, reason = _dirty_file_classification(path)
    allowed = classification in {
        "level_1_baseline_doc",
        "level_2_plan_doc",
        "level_2_apply_receipt",
    }
    return {
        "path": path,
        "classification": classification,
        "allowed_for_level_2_apply": allowed,
        "blocks_level_2_apply": not allowed,
        "reason": reason,
    }


def _dirty_file_classification(path: str) -> tuple[str, str]:
    if path == "docs/cartographer-level-1-autonomy-plan.md":
        return "level_1_baseline_doc", "preserved Level 1 evidence baseline"
    if path == "docs/cartographer-level-2-autonomy-plan.md":
        return "level_2_plan_doc", "active Level 2 planning document"
    if path.startswith("docs/cartographer-level-2-apply-receipts/"):
        return "level_2_apply_receipt", "Level 2 apply receipt evidence"
    if path.startswith("source_proxy/cartographer/level_2_") or path == "source_proxy/cartographer/level_2_apply.py":
        return "level_2_implementation", "Level 2 implementation is not apply-safe dirty evidence"
    if path.startswith("source_proxy/"):
        return "source_proxy_dirty", "source_proxy changes are source changes and block apply"
    if path.startswith("src/components/coding/"):
        return "coding_cockpit_dirty", "CodingCockpitShell work is unrelated to Level 2 apply"
    if path.startswith("src/"):
        return "app_source_dirty", "app source changes block Level 2 apply"
    if path.startswith("scout/"):
        return "scout_dirty", "Scout work is unrelated to Level 2 apply"
    if path.startswith("docs/"):
        return "unclassified_docs_dirty", "docs file is not an explicitly classified Level 2 evidence file"
    if path.endswith(".md"):
        return "unclassified_markdown_dirty", "top-level markdown is not explicitly approved for Level 2 apply"
    if path in {
        "cartographerBeta.md",
        "cartogrpaherPlanAuto.md",
        "codingAgentOverhaul.md",
        "masterOverhual.md",
        "post-v1-diag.md",
        "productionProxy.md",
        "spiritBlueprinter.md",
    }:
        return "deleted_old_plan_dirty", "deleted old plan files block Level 2 apply"
    return "unclassified_dirty", "unclassified dirty file blocks Level 2 apply"


def _resolution_group(
    *,
    group_id: str,
    label: str,
    files: list[str],
    blocks_apply: bool,
    recommended_disposition: str,
) -> dict[str, Any]:
    return {
        "group_id": group_id,
        "label": label,
        "file_count": len(files),
        "files": files,
        "blocks_apply": blocks_apply and bool(files),
        "recommended_disposition": recommended_disposition,
    }


def _only_level_1_blocked(blockers: list[dict[str, Any]]) -> bool:
    return bool(blockers) and all(blocker["code"] == "level_1_review_gate" for blocker in blockers)


def _level_1_accepted_by_britton() -> bool:
    return os.environ.get("CARTOGRAPHER_LEVEL_1_ACCEPTED_BY_BRITTON", "").lower() in {"1", "true", "yes"}


def _first_project() -> Any | None:
    projects = discover_projects()
    if projects:
        return projects[0]
    cwd = Path.cwd()
    if (cwd / ".git").exists():
        return type("Project", (), {"project_id": cwd.name.lower(), "root": str(cwd)})()
    return None


def _gate(code: str, passed: bool, evidence: str) -> dict[str, Any]:
    return {
        "code": code,
        "passed": passed,
        "evidence": evidence,
        "required": True,
    }
