from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from source_proxy.testing.self_tests import (
    SUITE_PHASE_4E_SAFETY_SEED,
    run_self_test_suite,
)


PROFILE_PROXY_SMOKE = "proxy-smoke"
PROFILE_PROXY_REGRESSION = "proxy-regression"
PROFILE_PROXY_CLOSEOUT = "proxy-closeout"
PROFILE_SCOUT_SMOKE = "scout-smoke"
PROFILE_SCOUT_SOURCE_GATE = "scout-source-gate"
PROFILE_SCOUT_SEARCH_DIAGNOSTICS = "scout-search-diagnostics"
PROFILE_SCOUT_SEARCH_SMOKE = "scout-search-smoke"
PROFILE_SCOUT_SOAK_SNAPSHOT = "scout-soak-snapshot"
PROFILE_PHASE_4F_CLOSEOUT = "phase-4f-closeout"
PROFILE_CARTOGRAPHER_SAFETY = "cartographer-safety"
PROFILE_CARTOGRAPHER_SOAK_SNAPSHOT = "cartographer-soak-snapshot"
PROFILE_GLOBAL_SAFETY_REGRESSION = "global-safety-regression"
PROFILE_DEPENDENCY_ENVIRONMENT_CHECKS = "dependency-environment-checks"
DEFAULT_SCOUT_BASE_URL = "http://localhost:8077"
DEFAULT_CARTOGRAPHER_DASHBOARD_URL = "http://localhost:3000"
SCOUT_CONTAINER_NAME = "scout_v0_1"
SCOUT_SEARCH_PROBE_URLS = [
    "http://spirit-searxng:8080/search?q=fastapi&format=json",
    "http://searxng:8080/search?q=fastapi&format=json",
    "http://host.docker.internal:8080/search?q=fastapi&format=json",
]

REGRESSION_TEST_FILES = [
    "source_proxy/tests/test_coding_self_tests.py",
    "source_proxy/tests/test_coding_regression_pack.py",
    "source_proxy/tests/test_diff_verification.py",
    "source_proxy/tests/test_verification_contracts.py",
    "source_proxy/tests/test_long_running_tasks.py",
    "source_proxy/tests/test_coder_agent_repomix_diff.py",
    "source_proxy/tests/test_source_proxy_end_to_end.py",
]

CARTOGRAPHER_SAFETY_TEST_FILES = [
    "source_proxy/tests/test_cartographer_safety_audit.py",
    "source_proxy/tests/test_cartographer_api.py",
]

SOURCE_PROXY_SAFETY_TEST_FILES = [
    "source_proxy/tests/test_proxy_runner.py",
    "source_proxy/tests/test_coding_self_tests.py",
    "source_proxy/tests/test_diff_verification.py",
    "source_proxy/tests/test_verification_contracts.py",
    "source_proxy/tests/test_long_running_tasks.py",
    "source_proxy/tests/test_sandbox_terminal_api.py",
    "source_proxy/tests/test_agent_registry.py",
]

SCOUT_BACKEND_SAFETY_TEST_FILES = [
    "scout/src/scout/tests/test_source_registry.py",
    "scout/src/scout/tests/test_sources_api.py",
    "scout/src/scout/tests/test_discovery_jobs.py",
    "scout/src/scout/tests/test_search_candidate_extraction.py",
    "scout/src/scout/tests/test_search_provider.py",
    "scout/src/scout/tests/test_v03_soak_safety.py",
]

DASHBOARD_SMOKE_TEST_FILES = [
    "src/components/coding/__tests__/coding-workflow-step.test.ts",
    "src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx",
]


def run_runner_profile(*, profile: str) -> dict[str, Any]:
    if profile == PROFILE_PROXY_SMOKE:
        return _run_proxy_smoke_profile()
    if profile == PROFILE_PROXY_REGRESSION:
        return _run_proxy_regression_profile()
    if profile == PROFILE_PROXY_CLOSEOUT:
        return _run_proxy_closeout_profile()
    if profile == PROFILE_SCOUT_SMOKE:
        return _run_scout_smoke_profile()
    if profile == PROFILE_SCOUT_SOURCE_GATE:
        return _run_scout_source_gate_profile()
    if profile == PROFILE_SCOUT_SEARCH_DIAGNOSTICS:
        return _run_scout_search_diagnostics_profile()
    if profile == PROFILE_SCOUT_SEARCH_SMOKE:
        return _run_scout_search_smoke_profile()
    if profile == PROFILE_SCOUT_SOAK_SNAPSHOT:
        return _run_scout_soak_snapshot_profile()
    if profile == PROFILE_PHASE_4F_CLOSEOUT:
        return _run_phase_4f_closeout_profile()
    if profile == PROFILE_CARTOGRAPHER_SAFETY:
        return _run_cartographer_safety_profile()
    if profile == PROFILE_CARTOGRAPHER_SOAK_SNAPSHOT:
        return _run_cartographer_soak_snapshot_profile()
    if profile == PROFILE_GLOBAL_SAFETY_REGRESSION:
        return _run_global_safety_regression_profile()
    if profile == PROFILE_DEPENDENCY_ENVIRONMENT_CHECKS:
        return _run_dependency_environment_checks_profile()
    raise ValueError(f"Unknown runner profile: {profile}")


def _run_proxy_smoke_profile() -> dict[str, Any]:
    smoke = run_self_test_suite(
        suite=SUITE_PHASE_4E_SAFETY_SEED,
        mode="dry_run",
    )
    safety = _safety_verdict(smoke)
    result = "pass" if smoke["summary"]["failed"] == 0 and all(safety.values()) else "fail"
    return {
        "profile": PROFILE_PROXY_SMOKE,
        "result": result,
        "smoke_harness": smoke,
        "safety_verdict": safety,
        "recommendation": "ready for next increment" if result == "pass" else "fix needed",
    }


def _run_proxy_regression_profile() -> dict[str, Any]:
    missing_files = [
        test_file for test_file in REGRESSION_TEST_FILES if not Path(test_file).is_file()
    ]
    command = [sys.executable, "-m", "pytest", *REGRESSION_TEST_FILES]
    if missing_files:
        return {
            "profile": PROFILE_PROXY_REGRESSION,
            "result": "fail",
            "regression_tests": {
                "command": _format_command(command),
                "result": "missing_files",
                "returncode": None,
                "missing_files": missing_files,
                "stdout": "",
                "stderr": "",
            },
            "recommendation": "fix needed",
        }

    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    result = "pass" if completed.returncode == 0 else "fail"
    return {
        "profile": PROFILE_PROXY_REGRESSION,
        "result": result,
        "regression_tests": {
            "command": _format_command(command),
            "result": "pass" if completed.returncode == 0 else "fail",
            "returncode": completed.returncode,
            "missing_files": [],
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        },
        "recommendation": "ready for next increment" if result == "pass" else "fix needed",
    }


def _run_proxy_closeout_profile() -> dict[str, Any]:
    before = _git_status_short()
    smoke_payload = _run_proxy_smoke_profile()
    regression_payload = _run_proxy_regression_profile()
    after = _git_status_short()
    changed_by_test_run = before != after
    safety = smoke_payload["safety_verdict"]
    result = (
        "pass"
        if smoke_payload["result"] == "pass"
        and regression_payload["result"] == "pass"
        and all(safety.values())
        and not changed_by_test_run
        else "fail"
    )
    return {
        "profile": PROFILE_PROXY_CLOSEOUT,
        "result": result,
        "smoke_harness": smoke_payload["smoke_harness"],
        "safety_verdict": safety,
        "regression_tests": regression_payload["regression_tests"],
        "file_change_verdict": {
            "before": before,
            "after": after,
            "changed_by_test_run": changed_by_test_run,
        },
        "recommendation": "ready for next increment" if result == "pass" else "fix needed",
    }


def _run_cartographer_safety_profile() -> dict[str, Any]:
    before = _git_status_short()
    before_head = _git_head()
    command = [sys.executable, "-m", "pytest", *CARTOGRAPHER_SAFETY_TEST_FILES]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    after = _git_status_short()
    after_head = _git_head()
    status_delta = _git_status_delta(before, after)
    unexpected_status_delta = _unexpected_status_delta(status_delta)
    changed_by_test_run = bool(unexpected_status_delta)
    background_status_delta = [
        line for line in status_delta if line not in unexpected_status_delta
    ]
    head_changed = bool(before_head and after_head and before_head != after_head)
    checks = {
        "pytest_passed": completed.returncode == 0,
        "no_unapproved_writes": not changed_by_test_run,
        "no_unapproved_apply": completed.returncode == 0,
        "no_unapproved_commits": not head_changed,
        "no_unapproved_pushes": completed.returncode == 0,
        "approval_bypass_locked": completed.returncode == 0,
    }
    result = "pass" if all(checks.values()) else "fail"
    return {
        "profile": PROFILE_CARTOGRAPHER_SAFETY,
        "result": result,
        "read_only": True,
        "mutated": changed_by_test_run,
        "applied_anything": False,
        "commit_ran": False,
        "push_ran": False,
        "checks": checks,
        "safety_verdict": {
            "no_unapproved_writes": checks["no_unapproved_writes"],
            "no_unapproved_apply": checks["no_unapproved_apply"],
            "no_unapproved_commits": checks["no_unapproved_commits"],
            "no_unapproved_pushes": checks["no_unapproved_pushes"],
            "approval_bypass_locked": checks["approval_bypass_locked"],
        },
        "regression_tests": {
            "command": _format_command(command),
            "result": "pass" if completed.returncode == 0 else "fail",
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        },
        "file_change_verdict": {
            "before": before,
            "after": after,
            "changed_by_test_run": changed_by_test_run,
            "status_delta": status_delta,
            "background_status_delta": background_status_delta,
            "unexpected_status_delta": unexpected_status_delta,
            "head_before": before_head,
            "head_after": after_head,
            "head_changed": head_changed,
        },
        "expected_outcomes": [
            "Cartographer safety audit: passed",
            "No unapproved writes",
            "No unapproved commits",
            "No unapproved pushes",
        ],
        "recommendation": "ready for next increment" if result == "pass" else "fix needed",
    }


def _run_cartographer_soak_snapshot_profile(
    *,
    output_dir: Path = Path("source_proxy/cartographer/soak-logs"),
) -> dict[str, Any]:
    from source_proxy.cartographer.service import (
        build_cartographer_audit_trail,
        build_cartographer_commit_proposals,
        build_cartographer_drift,
        build_cartographer_git,
        build_cartographer_project_health,
        build_cartographer_proposals,
        build_cartographer_push_queue,
        build_cartographer_status,
    )

    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    before = _git_status_short()
    before_head = _git_head()
    status = build_cartographer_status()
    git = build_cartographer_git()
    health = build_cartographer_project_health()
    proposals = build_cartographer_proposals()
    drift = build_cartographer_drift()
    commit_proposals = build_cartographer_commit_proposals()
    push_queue = build_cartographer_push_queue()
    audit = build_cartographer_audit_trail()

    summary = _cartographer_soak_summary(
        status=status,
        git=git,
        health=health,
        proposals=proposals,
        drift=drift,
        commit_proposals=commit_proposals,
        push_queue=push_queue,
        audit=audit,
    )
    reliability = _cartographer_reliability_score(summary)
    warnings = _cartographer_soak_warnings(summary)
    next_actions = _cartographer_soak_next_actions(summary)
    expected_recommendation = (
        "ready for next increment"
        if reliability["grade"] == "boring" and not warnings
        else "continue soak"
    )
    snapshot = {
        "profile": PROFILE_CARTOGRAPHER_SOAK_SNAPSHOT,
        "timestamp": timestamp,
        "read_only": False,
        "mutated": False,
        "wrote_snapshot": True,
        "summary": summary,
        "reliability": reliability,
        "warnings": warnings,
        "next_actions": next_actions,
        "expected_outcomes": [
            "cartographer-soak-snapshot: pass",
            "mutation boundary: snapshot log only",
            f"recommendation: {expected_recommendation}",
        ],
    }
    path = _write_cartographer_soak_snapshot(snapshot=snapshot, output_dir=output_dir)
    snapshot["snapshot_path"] = str(path)
    snapshot["log_size_bytes"] = _directory_size(output_dir)
    after = _git_status_short()
    after_head = _git_head()
    status_delta = _git_status_delta(before, after)
    unexpected_status_delta = _unexpected_cartographer_soak_delta(status_delta)
    snapshot["mutation_boundary"] = {
        "allowed_writes": [str(path)],
        "before": before,
        "after": after,
        "status_delta": status_delta,
        "unexpected_status_delta": unexpected_status_delta,
        "background_status_delta": [
            line for line in status_delta if line not in unexpected_status_delta and str(path) not in line
        ],
        "head_before": before_head,
        "head_after": after_head,
        "head_changed": bool(before_head and after_head and before_head != after_head),
        "snapshot_log_only": not unexpected_status_delta,
    }
    result = (
        "pass"
        if snapshot["mutation_boundary"]["snapshot_log_only"]
        and not snapshot["mutation_boundary"]["head_changed"]
        else "fail"
    )
    snapshot["result"] = result
    snapshot["mutated"] = True
    snapshot["recommendation"] = (
        "ready for next increment"
        if result == "pass" and reliability["grade"] == "boring" and not warnings
        else "continue soak"
        if result == "pass"
        else "fix soak mutation boundary"
    )
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return snapshot


def _git_status_short() -> str:
    completed = subprocess.run(
        ["git", "status", "--short"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return f"git status failed: {completed.stderr.strip()}"
    return completed.stdout.strip() or "clean"


def _git_head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _git_status_delta(before: str, after: str) -> list[str]:
    before_lines = set(_status_lines(before))
    after_lines = set(_status_lines(after))
    return sorted(after_lines - before_lines)


def _status_lines(status: str) -> list[str]:
    if status == "clean":
        return []
    return [line for line in status.splitlines() if line.strip()]


def _unexpected_status_delta(delta: list[str]) -> list[str]:
    return [
        line
        for line in delta
        if "scout/soak-logs/scout-soak-snapshot-" not in line
    ]


def _unexpected_cartographer_soak_delta(delta: list[str]) -> list[str]:
    return [
        line
        for line in delta
        if "source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-" not in line
        and "source_proxy/cartographer/soak-logs/" not in line
        and "scout/soak-logs/scout-soak-snapshot-" not in line
    ]


def _cartographer_soak_summary(
    *,
    status: dict[str, Any],
    git: dict[str, Any],
    health: dict[str, Any],
    proposals: dict[str, Any],
    drift: dict[str, Any],
    commit_proposals: dict[str, Any],
    push_queue: dict[str, Any],
    audit: dict[str, Any],
) -> dict[str, Any]:
    project = _first_dict(git.get("git_statuses")) or (
        git.get("git") if isinstance(git.get("git"), dict) else {}
    )
    events = _dict_list(audit.get("events"))
    event_counts = dict(Counter(str(event.get("event") or "unknown") for event in events))
    safety = status.get("safety") if isinstance(status.get("safety"), dict) else {}
    return {
        "status": status.get("status"),
        "write_actions_enabled": status.get("write_actions_enabled"),
        "project_count": len(_dict_list(status.get("projects"))),
        "blueprint_count": status.get("blueprint_count"),
        "branch": project.get("branch"),
        "dirty": project.get("dirty"),
        "changed_file_count": project.get("changed_file_count", len(_list_value(project.get("changed_files")))),
        "staged": project.get("staged"),
        "unstaged": project.get("unstaged"),
        "untracked": project.get("untracked"),
        "proposal_count": proposals.get("proposal_count"),
        "pending_proposals": proposals.get("pending_proposals"),
        "deduped": proposals.get("deduped"),
        "duplicate_proposals_present": proposals.get("duplicate_proposals_present"),
        "drift_count": drift.get("drift_count"),
        "commit_proposal_count": commit_proposals.get("commit_proposal_count"),
        "push_queue_count": push_queue.get("push_queue_count", push_queue.get("push_count")),
        "audit_event_count": len(events),
        "audit_event_counts": event_counts,
        "pending_proposal_examples": [
            {
                "proposal_id": str(item.get("proposal_id")),
                "status": str(item.get("status")),
                "component": str(item.get("component")),
                "risk": str(item.get("risk")),
                "changed_file_count": _int_value(item.get("changed_file_count")),
                "proposed_file_count": len(_list_value(item.get("proposed_files"))),
            }
            for item in _dict_list(proposals.get("proposals"))
            if str(item.get("status")) in {"detected", "drafted", "pending_review"}
        ][:5],
        "drift_examples": [
            {
                "drift_id": str(item.get("drift_id")),
                "component": str(item.get("component")),
                "reason": str(item.get("reason")),
                "changed_file_count": len(_list_value(item.get("changed_files"))),
            }
            for item in _dict_list(drift.get("drift"))
        ][:5],
        "commit_proposal_examples": [
            {
                "commit_proposal_id": str(item.get("commit_proposal_id")),
                "component": str(item.get("component")),
                "risk": str(item.get("risk")),
                "suggested_message": str(item.get("suggested_message")),
                "file_count": len(_list_value(item.get("files"))),
            }
            for item in _dict_list(commit_proposals.get("commit_proposals"))
        ][:5],
        "merge_ready_count": sum(
            1 for item in _dict_list(health.get("projects")) if item.get("merge_ready") is True
        ),
        "merge_blockers": sorted(
            {
                str(blocker)
                for item in _dict_list(health.get("projects"))
                for blocker in _list_value(item.get("merge_blockers"))
            }
        ),
        "safety": {
            "write_policy": safety.get("write_policy"),
            "approval_required_for_file_writes": safety.get("approval_required_for_file_writes"),
            "approval_required_for_commits": safety.get("approval_required_for_commits"),
            "approval_required_for_pushes": safety.get("approval_required_for_pushes"),
            "scout_bypass_allowed": safety.get("scout_bypass_allowed"),
            "source_proxy_approval_bypass_allowed": safety.get("source_proxy_approval_bypass_allowed"),
        },
    }


def _cartographer_reliability_score(summary: dict[str, Any]) -> dict[str, Any]:
    score = 100
    penalties: list[str] = []
    if summary.get("write_actions_enabled") is not False:
        score -= 40
        penalties.append("write actions are unexpectedly enabled")
    safety = summary.get("safety") if isinstance(summary.get("safety"), dict) else {}
    if safety.get("scout_bypass_allowed") is not False:
        score -= 25
        penalties.append("Scout bypass flag is not locked")
    if safety.get("source_proxy_approval_bypass_allowed") is not False:
        score -= 25
        penalties.append("Source Proxy approval bypass flag is not locked")
    if summary.get("deduped") is False or _int_value(summary.get("duplicate_proposals_present")) > 0:
        score -= 20
        penalties.append("proposal queue contains duplicates")
    if _int_value(summary.get("pending_proposals")) > 0:
        score -= 10
        penalties.append("pending proposals still require review")
    if _int_value(summary.get("drift_count")) > 0:
        score -= 10
        penalties.append("drift findings still require review")
    if summary.get("dirty") is True:
        score -= 5
        penalties.append("working tree is dirty")
    score = max(0, min(100, score))
    return {
        "score": score,
        "grade": "boring" if score >= 90 else "watch" if score >= 70 else "blocked",
        "penalties": penalties,
    }


def _cartographer_soak_warnings(summary: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    safety = summary.get("safety") if isinstance(summary.get("safety"), dict) else {}
    if summary.get("write_actions_enabled") is not False:
        warnings.append("write_actions_enabled was not false")
    if safety.get("approval_required_for_file_writes") is not True:
        warnings.append("file-write approval requirement missing")
    if safety.get("approval_required_for_commits") is not True:
        warnings.append("commit approval requirement missing")
    if safety.get("approval_required_for_pushes") is not True:
        warnings.append("push approval requirement missing")
    if safety.get("scout_bypass_allowed") is not False:
        warnings.append("Scout bypass was not locked")
    if safety.get("source_proxy_approval_bypass_allowed") is not False:
        warnings.append("Source Proxy approval bypass was not locked")
    if _int_value(summary.get("duplicate_proposals_present")) > 0:
        warnings.append("duplicate proposals present")
    return warnings


def _cartographer_soak_next_actions(summary: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    base_url = _cartographer_dashboard_url()
    pending = _int_value(summary.get("pending_proposals"))
    if pending:
        first = _first_dict(summary.get("pending_proposal_examples"))
        if first:
            actions.append(
                "Review pending proposal "
                f"{first.get('proposal_id')} ({first.get('component')}, {first.get('risk')} risk, "
                f"{first.get('changed_file_count')} changed / {first.get('proposed_file_count')} proposed); "
                "use the Blueprint Review dashboard or fetch details with "
                f"curl -k -s {base_url}/v1/cartographer/proposals "
                f"| jq '.proposals[] | select(.proposal_id==\"{first.get('proposal_id')}\")'"
            )
        else:
            actions.append("Review pending Cartographer proposals.")
    drift_count = _int_value(summary.get("drift_count"))
    if drift_count:
        first = _first_dict(summary.get("drift_examples"))
        if first:
            actions.append(
                "Inspect drift "
                f"{first.get('drift_id')} ({first.get('component')}: {first.get('reason')}, "
                f"{first.get('changed_file_count')} changed) with "
                f"curl -k -s {base_url}/v1/cartographer/drift "
                f"| jq '.drift[] | select(.drift_id==\"{first.get('drift_id')}\")'"
            )
        else:
            actions.append("Inspect Cartographer drift findings.")
    if summary.get("dirty") is True:
        first = _first_dict(summary.get("commit_proposal_examples"))
        if first:
            actions.append(
                "Review commit proposal "
                f"{first.get('commit_proposal_id')} ({first.get('component')}, {first.get('risk')} risk, "
                f"{first.get('file_count')} files) with "
                f"curl -k -s {base_url}/v1/cartographer/commit-proposals "
                f"| jq '.commit_proposals[] | select(.commit_proposal_id==\"{first.get('commit_proposal_id')}\")'; "
                "do not approve until proposal/drift review is complete."
            )
        else:
            actions.append("Review or reduce the dirty working tree before another readiness soak.")
    if not actions:
        actions.append("Run two more cartographer-soak-snapshot checks before considering 6.21.")
    return actions


def _cartographer_dashboard_url() -> str:
    return os.getenv("CARTOGRAPHER_DASHBOARD_URL", DEFAULT_CARTOGRAPHER_DASHBOARD_URL).rstrip("/")


def _run_phase_4f_closeout_profile() -> dict[str, Any]:
    before = _git_status_short()
    proxy_closeout = _run_proxy_closeout_profile()
    runner_self_tests = _run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            "source_proxy/tests/test_coding_self_tests.py",
            "source_proxy/tests/test_proxy_runner.py",
        ],
        timeout_seconds=120,
    )
    scout_smoke = _run_scout_smoke_profile()
    scout_source_gate = _run_scout_source_gate_profile()
    scout_search_diagnostics = _run_scout_search_diagnostics_profile()
    scout_soak_snapshot = _run_scout_soak_snapshot_profile()
    after = _git_status_short()
    changed_by_test_run = before != after
    checks = {
        "proxy_closeout": proxy_closeout["result"] == "pass",
        "runner_self_tests": runner_self_tests["returncode"] == 0,
        "scout_smoke": scout_smoke["result"] == "pass",
        "scout_source_gate": scout_source_gate["result"] == "pass",
        "scout_search_diagnostics": scout_search_diagnostics["result"] == "pass",
        "scout_soak_snapshot": scout_soak_snapshot["result"] == "pass",
    }
    result = "pass" if all(checks.values()) else "fail"
    return {
        "profile": PROFILE_PHASE_4F_CLOSEOUT,
        "result": result,
        "proxy_closeout": proxy_closeout,
        "runner_self_tests": runner_self_tests,
        "scout_smoke": scout_smoke,
        "scout_source_gate": scout_source_gate,
        "scout_search_diagnostics": scout_search_diagnostics,
        "scout_soak_snapshot": scout_soak_snapshot,
        "file_change_verdict": {
            "before": before,
            "after": after,
            "changed_by_test_run": changed_by_test_run,
            "expected_writes": ["scout/soak-logs/scout-soak-snapshot-*.json"],
        },
        "optional_checks": {
            "scout_search_smoke": {
                "status": "not_run",
                "reason": (
                    "bounded mutation profile; run intentionally after diagnostics pass "
                    "and discovery job cap is available"
                ),
                "command": "python -m source_proxy.testing.runner --profile scout-search-smoke",
            }
        },
        "checks": checks,
        "recommendation": "ready for 4F closeout" if result == "pass" else "fix needed",
    }


def _run_global_safety_regression_profile() -> dict[str, Any]:
    before = _git_status_short()
    before_head = _git_head()
    _progress("global-safety-regression: proxy safety harness")
    proxy_safety_harness = _run_proxy_smoke_profile()
    _progress(
        "global-safety-regression: proxy safety harness "
        f"{_pass_fail(proxy_safety_harness['result'] == 'pass')}"
    )
    _progress("global-safety-regression: Source Proxy safety tests")
    source_proxy_tests = _run_pytest_file_group(
        test_files=SOURCE_PROXY_SAFETY_TEST_FILES,
        timeout_seconds=180,
        progress_label="Source Proxy safety tests",
    )
    _progress(
        "global-safety-regression: Source Proxy safety tests "
        f"{_pass_fail(source_proxy_tests['result'] == 'pass')}"
    )
    _progress("global-safety-regression: Scout backend safety tests")
    scout_backend_tests = _run_pytest_file_group(
        test_files=SCOUT_BACKEND_SAFETY_TEST_FILES,
        timeout_seconds=180,
        env=_pythonpath_env(["scout/src"]),
        progress_label="Scout backend safety tests",
    )
    _progress(
        "global-safety-regression: Scout backend safety tests "
        f"{_pass_fail(scout_backend_tests['result'] == 'pass')}"
    )
    _progress("global-safety-regression: Cartographer safety tests")
    cartographer_safety = _run_cartographer_safety_profile()
    _progress(
        "global-safety-regression: Cartographer safety tests "
        f"{_pass_fail(cartographer_safety['result'] == 'pass')}"
    )
    _progress("global-safety-regression: dashboard smoke tests")
    dashboard_smoke_tests = _run_dashboard_smoke_tests()
    _progress(
        "global-safety-regression: dashboard smoke tests "
        f"{_pass_fail(dashboard_smoke_tests['result'] == 'pass')}"
    )
    _progress("global-safety-regression: mutation boundary check")
    after = _git_status_short()
    after_head = _git_head()
    status_delta = _git_status_delta(before, after)
    unexpected_status_delta = _unexpected_status_delta(status_delta)
    head_changed = bool(before_head and after_head and before_head != after_head)
    checks = {
        "proxy_safety_harness": proxy_safety_harness["result"] == "pass",
        "source_proxy_tests": source_proxy_tests["result"] == "pass",
        "scout_backend_tests": scout_backend_tests["result"] == "pass",
        "cartographer_safety": cartographer_safety["result"] == "pass",
        "dashboard_smoke_tests": dashboard_smoke_tests["result"] == "pass",
        "no_unexpected_mutation": not unexpected_status_delta,
        "no_commit": not head_changed,
    }
    safety_boundary = {
        "no_approve": True,
        "no_apply": True,
        "no_execute_approved": True,
        "no_commit": not head_changed,
        "no_push": True,
        "no_destructive_cleanup": True,
        "no_source_auto_approval": True,
        "no_memory_writes": True,
    }
    result = "pass" if all(checks.values()) and all(safety_boundary.values()) else "fail"
    return {
        "profile": PROFILE_GLOBAL_SAFETY_REGRESSION,
        "result": result,
        "read_only": True,
        "proxy_safety_harness": proxy_safety_harness,
        "source_proxy_tests": source_proxy_tests,
        "scout_backend_tests": scout_backend_tests,
        "cartographer_safety": cartographer_safety,
        "dashboard_smoke_tests": dashboard_smoke_tests,
        "checks": checks,
        "safety_boundary": safety_boundary,
        "file_change_verdict": {
            "before": before,
            "after": after,
            "changed_by_test_run": bool(unexpected_status_delta),
            "status_delta": status_delta,
            "unexpected_status_delta": unexpected_status_delta,
            "head_before": before_head,
            "head_after": after_head,
            "head_changed": head_changed,
        },
        "recommendation": "ready for Phase 10 hardening" if result == "pass" else "fix needed",
    }


def _run_dependency_environment_checks_profile() -> dict[str, Any]:
    before = _git_status_short()
    before_head = _git_head()
    python_deps = _python_dependency_check()
    node_deps = _node_dependency_check()
    services = _service_availability_check()
    environment = _environment_variable_check()
    databases = _database_freshness_check()
    after = _git_status_short()
    after_head = _git_head()
    status_delta = _git_status_delta(before, after)
    unexpected_status_delta = _unexpected_status_delta(status_delta)
    checks = {
        "python_dependencies": python_deps["result"] == "pass",
        "node_dependencies": node_deps["result"] == "pass",
        "required_services": services["result"] == "pass",
        "environment_variables": environment["result"] == "pass",
        "databases": databases["result"] == "pass",
        "no_unexpected_mutation": not unexpected_status_delta,
        "no_commit": before_head == after_head,
    }
    result = "pass" if all(checks.values()) else "fail"
    return {
        "profile": PROFILE_DEPENDENCY_ENVIRONMENT_CHECKS,
        "result": result,
        "read_only": True,
        "python_dependencies": python_deps,
        "node_dependencies": node_deps,
        "services": services,
        "environment": environment,
        "databases": databases,
        "checks": checks,
        "file_change_verdict": {
            "before": before,
            "after": after,
            "status_delta": status_delta,
            "unexpected_status_delta": unexpected_status_delta,
            "head_before": before_head,
            "head_after": after_head,
            "head_changed": before_head != after_head,
        },
        "recommendation": (
            "ready for Phase 10 environment baseline"
            if result == "pass"
            else "fix dependency or environment blockers"
        ),
    }


def _run_scout_smoke_profile(
    *,
    base_url: str = DEFAULT_SCOUT_BASE_URL,
) -> dict[str, Any]:
    base_url = base_url.rstrip("/")
    checks = {
        "health": _http_get_json(f"{base_url}/health"),
        "source_candidates": _http_get_json(f"{base_url}/v1/scout/source-candidates"),
        "sources": _http_get_json(f"{base_url}/v1/scout/sources"),
        "discovery_jobs": _http_get_json(f"{base_url}/v1/scout/discovery-jobs"),
    }
    all_ok = all(check["ok"] for check in checks.values())
    candidates_body = _body_dict(checks["source_candidates"])
    sources_body = _body_dict(checks["sources"])
    jobs_body = _body_dict(checks["discovery_jobs"])
    active_sources = sources_body.get("sources") if isinstance(sources_body.get("sources"), list) else []
    jobs = jobs_body.get("jobs") if isinstance(jobs_body.get("jobs"), list) else []
    return {
        "profile": PROFILE_SCOUT_SMOKE,
        "result": "pass" if all_ok else "fail",
        "base_url": base_url,
        "read_only": True,
        "mutated": False,
        "checks": checks,
        "summary": {
            "health_status": checks["health"]["status"],
            "candidate_counts": candidates_body.get("counts", {}),
            "active_source_count": sources_body.get("count", len(active_sources)),
            "active_sources": active_sources,
            "discovery_job_count": jobs_body.get("count", len(jobs)),
            "discovery_jobs": jobs,
        },
        "recommendation": "ready for next increment" if all_ok else "fix needed",
    }


def _run_scout_source_gate_profile(
    *,
    base_url: str = DEFAULT_SCOUT_BASE_URL,
) -> dict[str, Any]:
    base_url = base_url.rstrip("/")
    checks = {
        "source_candidates": _http_get_json(f"{base_url}/v1/scout/source-candidates?limit=200"),
        "sources": _http_get_json(f"{base_url}/v1/scout/sources"),
    }
    endpoints_ok = all(check["ok"] for check in checks.values())
    candidates_body = _body_dict(checks["source_candidates"])
    sources_body = _body_dict(checks["sources"])
    candidates = _dict_list(candidates_body.get("candidates"))
    active_sources = _dict_list(sources_body.get("sources"))
    active_canonicals = {
        str(source.get("canonical_uri") or "")
        for source in active_sources
        if source.get("canonical_uri")
    }
    rejected_or_blocked_active = [
        _candidate_label(candidate)
        for candidate in candidates
        if candidate.get("status") in {"rejected", "blocked"}
        and str(candidate.get("canonical_uri") or "") in active_canonicals
    ]
    approved_candidates = [
        candidate for candidate in candidates if candidate.get("status") == "approved"
    ]
    approved_missing_sources = [
        _candidate_label(candidate)
        for candidate in approved_candidates
        if str(candidate.get("canonical_uri") or "") not in active_canonicals
    ]
    unsupported_active_sources = [
        _source_label(source)
        for source in active_sources
        if source.get("poller_supported") is False
    ]
    review_history_candidates = [
        _candidate_label(candidate)
        for candidate in candidates
        if isinstance(candidate.get("review_history"), list)
        and len(candidate.get("review_history") or []) > 0
    ]
    invariants = {
        "rejected_blocked_not_active": len(rejected_or_blocked_active) == 0,
        "approved_candidates_active": len(approved_missing_sources) == 0,
        "unsupported_sources_reported": True,
        "review_history_visible_when_available": True,
    }
    result = "pass" if endpoints_ok and all(invariants.values()) else "fail"
    return {
        "profile": PROFILE_SCOUT_SOURCE_GATE,
        "result": result,
        "base_url": base_url,
        "read_only": True,
        "mutated": False,
        "checks": checks,
        "summary": {
            "candidate_counts": candidates_body.get("counts", {}),
            "candidate_count": len(candidates),
            "active_source_count": sources_body.get("count", len(active_sources)),
            "approved_candidate_count": len(approved_candidates),
            "rejected_or_blocked_active": rejected_or_blocked_active,
            "approved_missing_sources": approved_missing_sources,
            "unsupported_active_sources": unsupported_active_sources,
            "review_history_candidates": review_history_candidates,
        },
        "invariants": invariants,
        "recommendation": "ready for next increment" if result == "pass" else "fix needed",
    }


def _run_scout_search_diagnostics_profile() -> dict[str, Any]:
    compose = _inspect_scout_compose()
    container_env = _inspect_scout_container_env()
    settings = _inspect_scout_container_settings()
    host_searxng = _http_get_json("http://localhost:8080/search?q=fastapi&format=json")
    container_connectivity = {
        url: _probe_container_url(url)
        for url in SCOUT_SEARCH_PROBE_URLS
    }
    findings = _search_diagnostic_findings(
        compose=compose,
        container_env=container_env,
        settings=settings,
        host_searxng=host_searxng,
        container_connectivity=container_connectivity,
    )
    warnings = _search_diagnostic_warnings(
        container_env=container_env,
        settings=settings,
        container_connectivity=container_connectivity,
    )
    result = "pass" if not findings else "fail"
    return {
        "profile": PROFILE_SCOUT_SEARCH_DIAGNOSTICS,
        "result": result,
        "read_only": True,
        "mutated": False,
        "compose": compose,
        "container_env": container_env,
        "settings": settings,
        "host_searxng": host_searxng,
        "container_connectivity": container_connectivity,
        "findings": findings,
        "warnings": warnings,
        "recommendation": "ready for search smoke" if result == "pass" else "fix needed",
    }


def _run_scout_search_smoke_profile(
    *,
    base_url: str = DEFAULT_SCOUT_BASE_URL,
) -> dict[str, Any]:
    base_url = base_url.rstrip("/")
    before_candidates = _http_get_json(f"{base_url}/v1/scout/source-candidates?limit=200")
    before_sources = _http_get_json(f"{base_url}/v1/scout/sources")
    create_job = _http_post_json(
        f"{base_url}/v1/scout/discovery-jobs",
        {
            "query": "official Pydantic GitHub repository release notes",
            "topic_anchor": "python",
            "max_results": 5,
            "budget": 5,
            "metadata": {"source": "scout-search-smoke", "bounded": True},
        },
    )
    job_id = _job_id_from_create(create_job)
    preview = (
        _http_post_json(f"{base_url}/v1/scout/discovery-jobs/{job_id}/search-preview", {})
        if job_id
        else _skipped_http_check("discovery job was not created")
    )
    after_preview_candidates = _http_get_json(f"{base_url}/v1/scout/source-candidates?limit=200")
    after_preview_sources = _http_get_json(f"{base_url}/v1/scout/sources")
    extract = (
        _http_post_json(f"{base_url}/v1/scout/discovery-jobs/{job_id}/extract-candidates", {})
        if job_id
        else _skipped_http_check("discovery job was not created")
    )
    after_extract_candidates = _http_get_json(f"{base_url}/v1/scout/source-candidates?limit=200")
    after_extract_sources = _http_get_json(f"{base_url}/v1/scout/sources")
    candidate_effect = _candidate_effect(
        before_candidates=before_candidates,
        after_preview_candidates=after_preview_candidates,
        after_extract_candidates=after_extract_candidates,
        after_extract_sources=after_extract_sources,
    )
    source_before_count = _source_count(before_sources)
    source_preview_count = _source_count(after_preview_sources)
    source_after_count = _source_count(after_extract_sources)
    preview_candidate_delta = _candidate_total(after_preview_candidates) - _candidate_total(before_candidates)
    extract_candidate_delta = _candidate_total(after_extract_candidates) - _candidate_total(after_preview_candidates)
    source_count_delta = source_after_count - source_before_count
    checks = {
        "before_candidates": before_candidates,
        "before_sources": before_sources,
        "create_job": create_job,
        "preview": preview,
        "after_preview_candidates": after_preview_candidates,
        "after_preview_sources": after_preview_sources,
        "extract": extract,
        "after_extract_candidates": after_extract_candidates,
        "after_extract_sources": after_extract_sources,
    }
    invariants = {
        "preview_does_not_create_candidates": preview_candidate_delta == 0,
        "preview_does_not_change_sources": source_preview_count == source_before_count,
        "extract_does_not_change_sources": source_count_delta == 0,
        "no_auto_approval": _approved_count(after_extract_candidates) == _approved_count(before_candidates),
        "search_candidates_have_search_provenance": candidate_effect["search_provenance_ok"],
    }
    all_http_ok = all(check["ok"] for check in checks.values())
    budget_blocked = _is_discovery_job_daily_limit_error(create_job)
    state_checks_ok = all(
        checks[name]["ok"]
        for name in (
            "before_candidates",
            "before_sources",
            "after_preview_candidates",
            "after_preview_sources",
            "after_extract_candidates",
            "after_extract_sources",
        )
    )
    if all_http_ok and all(invariants.values()):
        result = "pass"
    elif budget_blocked and state_checks_ok and all(invariants.values()):
        result = "blocked_by_budget"
    else:
        result = "fail"
    return {
        "profile": PROFILE_SCOUT_SEARCH_SMOKE,
        "result": result,
        "base_url": base_url,
        "read_only": False,
        "mutated": extract_candidate_delta != 0,
        "bounded": True,
        "checks": checks,
        "summary": {
            "job_id": job_id,
            "preview_result_count": _search_result_count(_body_dict(preview).get("result")),
            "preview_candidate_delta": preview_candidate_delta,
            "extract_candidate_delta": extract_candidate_delta,
            "source_count_before": source_before_count,
            "source_count_after_preview": source_preview_count,
            "source_count_after_extract": source_after_count,
            "source_count_delta": source_count_delta,
            "approved_count_before": _approved_count(before_candidates),
            "approved_count_after": _approved_count(after_extract_candidates),
            "search_candidates_checked": candidate_effect["checked"],
            "search_candidates_missing_provenance": candidate_effect["missing"],
            "blocked_reason": "daily_limit_reached" if budget_blocked else None,
        },
        "invariants": invariants,
        "recommendation": _scout_search_smoke_recommendation(result),
    }


def _run_scout_soak_snapshot_profile(
    *,
    base_url: str = DEFAULT_SCOUT_BASE_URL,
    output_dir: Path = Path("scout/soak-logs"),
) -> dict[str, Any]:
    base_url = base_url.rstrip("/")
    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    checks = {
        "health": _http_get_json(f"{base_url}/health"),
        "source_candidates": _http_get_json(f"{base_url}/v1/scout/source-candidates?limit=200"),
        "sources": _http_get_json(f"{base_url}/v1/scout/sources"),
        "discovery_jobs": _http_get_json(f"{base_url}/v1/scout/discovery-jobs?limit=50"),
    }
    db_size = _file_size("scout/data/scout.db")
    logs = _run_command(["docker", "logs", "--tail", "80", SCOUT_CONTAINER_NAME], timeout_seconds=15)
    warnings = _soak_snapshot_warnings(checks=checks, logs=logs)
    snapshot = {
        "profile": PROFILE_SCOUT_SOAK_SNAPSHOT,
        "timestamp": timestamp,
        "base_url": base_url,
        "read_only": False,
        "mutated": False,
        "wrote_snapshot": True,
        "checks": checks,
        "summary": {
            "health_status": checks["health"]["status"],
            "candidate_counts": _body_dict(checks["source_candidates"]).get("counts", {}),
            "active_source_count": _source_count(checks["sources"]),
            "active_sources": _dict_list(_body_dict(checks["sources"]).get("sources")),
            "discovery_job_count": _discovery_job_count(checks["discovery_jobs"]),
            "discovery_jobs": _dict_list(_body_dict(checks["discovery_jobs"]).get("jobs")),
            "db_size_bytes": db_size["size_bytes"],
            "db_size_error": db_size["error"],
            "docker_logs_available": logs["returncode"] == 0,
            "docker_logs_tail": logs["stdout"],
            "docker_logs_error": logs["error"] or logs["stderr"].strip() or None,
            "warnings": warnings,
        },
    }
    path = _write_soak_snapshot(snapshot=snapshot, output_dir=output_dir)
    fatal_warnings = _fatal_soak_snapshot_warnings(warnings)
    result = "pass" if all(check["ok"] for check in checks.values()) and not fatal_warnings else "fail"
    snapshot["result"] = result
    snapshot["snapshot_path"] = str(path)
    snapshot["recommendation"] = (
        "ready for next increment"
        if result == "pass" and not warnings
        else "ready with warnings"
        if result == "pass"
        else "review warnings"
    )
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return snapshot


def _inspect_scout_compose(path: Path = Path("scout/docker-compose.scout.yml")) -> dict[str, Any]:
    if not path.is_file():
        return {
            "ok": False,
            "path": str(path),
            "error": "compose file missing",
            "env_file_mentions": [],
            "search_env_wired": False,
            "searxng_url_wired": False,
        }
    text = path.read_text(encoding="utf-8")
    return {
        "ok": True,
        "path": str(path),
        "error": None,
        "env_file_mentions": _compose_env_file_mentions(text),
        "search_env_wired": "SCOUT_SEARCH_ENABLED" in text,
        "searxng_url_wired": "SCOUT_SEARXNG_URL" in text,
        "search_max_results_wired": "SCOUT_SEARCH_MAX_RESULTS" in text,
        "search_timeout_wired": "SCOUT_SEARCH_TIMEOUT_SECONDS" in text,
    }


def _compose_env_file_mentions(text: str) -> list[str]:
    mentions: list[str] = []
    expecting_env_file_items = False
    env_indent = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if expecting_env_file_items and indent <= env_indent:
            expecting_env_file_items = False
        if stripped.startswith("env_file:"):
            value = stripped.removeprefix("env_file:").strip()
            if value:
                mentions.append(value)
                expecting_env_file_items = False
            else:
                expecting_env_file_items = True
                env_indent = indent
        elif expecting_env_file_items and stripped.startswith("- "):
            mentions.append(stripped.removeprefix("- ").strip())
    return list(dict.fromkeys(mentions))


def _inspect_scout_container_env() -> dict[str, Any]:
    completed = _run_command(
        ["docker", "exec", SCOUT_CONTAINER_NAME, "sh", "-lc", 'env | sort | grep "^SCOUT_"'],
        timeout_seconds=10,
    )
    lines = completed["stdout"].splitlines() if completed["returncode"] == 0 else []
    keys = [line.split("=", 1)[0] for line in lines if "=" in line]
    return {
        **completed,
        "keys": keys,
        "search_enabled_present": "SCOUT_SEARCH_ENABLED" in keys,
        "searxng_url_present": "SCOUT_SEARXNG_URL" in keys,
    }


def _inspect_scout_container_settings() -> dict[str, Any]:
    code = (
        "import json\n"
        "from scout.config import get_settings\n"
        "s=get_settings()\n"
        "print(json.dumps({\n"
        "'search_enabled': s.search_enabled,\n"
        "'searxng_url_present': bool(s.searxng_url),\n"
        "'searxng_url': s.searxng_url,\n"
        "'search_provider': s.search_provider,\n"
        "'search_max_results': s.search_max_results,\n"
        "'search_timeout_seconds': s.search_timeout_seconds,\n"
        "'discovery_jobs_enabled': s.discovery_jobs_enabled,\n"
        "'discovery_jobs_per_day': s.discovery_jobs_per_day,\n"
        "'discovery_candidates_per_job': s.discovery_candidates_per_job,\n"
        "}, sort_keys=True))\n"
    )
    completed = _run_command(
        ["docker", "exec", SCOUT_CONTAINER_NAME, "python", "-c", code],
        timeout_seconds=10,
    )
    parsed = _json_or_text(completed["stdout"].strip()) if completed["returncode"] == 0 else {}
    return {
        **completed,
        "settings": parsed if isinstance(parsed, dict) else {},
    }


def _probe_container_url(url: str) -> dict[str, Any]:
    code = (
        "import json, sys, urllib.error, urllib.request\n"
        "url=sys.argv[1]\n"
        "try:\n"
        "    with urllib.request.urlopen(url, timeout=8) as r:\n"
        "        raw=r.read().decode('utf-8', errors='replace')\n"
        "        try:\n"
        "            body=json.loads(raw) if raw.strip() else {}\n"
        "        except json.JSONDecodeError:\n"
        "            body={'raw': raw[:500]}\n"
        "        print(json.dumps({'ok': 200 <= r.status < 300, 'status': r.status, 'body': body, 'error': None}))\n"
        "except Exception as e:\n"
        "    print(json.dumps({'ok': False, 'status': None, 'body': {}, 'error': str(e)}))\n"
    )
    completed = _run_command(
        ["docker", "exec", SCOUT_CONTAINER_NAME, "python", "-c", code, url],
        timeout_seconds=12,
    )
    parsed = _json_or_text(completed["stdout"].strip()) if completed["stdout"].strip() else {}
    body = parsed if isinstance(parsed, dict) else {}
    return {
        **completed,
        "url": url,
        "ok": body.get("ok") is True,
        "status": body.get("status"),
        "body": body.get("body", {}),
        "error": body.get("error") or (completed["stderr"].strip() if completed["returncode"] != 0 else None),
    }


def _run_pytest_file_group(
    *,
    test_files: list[str],
    timeout_seconds: int,
    env: dict[str, str] | None = None,
    progress_label: str | None = None,
) -> dict[str, Any]:
    command = [sys.executable, "-m", "pytest", *test_files]
    missing_files = [test_file for test_file in test_files if not Path(test_file).is_file()]
    if missing_files:
        return {
            "command": _format_command(command),
            "result": "missing_files",
            "returncode": None,
            "missing_files": missing_files,
            "stdout": "",
            "stderr": "",
            "error": None,
        }
    completed = _run_command(
        command,
        timeout_seconds=timeout_seconds,
        env=env,
        progress_label=progress_label,
    )
    return {
        **completed,
        "result": "pass" if completed["returncode"] == 0 else "fail",
        "missing_files": [],
    }


def _run_dashboard_smoke_tests() -> dict[str, Any]:
    command = _vitest_command(DASHBOARD_SMOKE_TEST_FILES)
    missing_files = [
        test_file for test_file in DASHBOARD_SMOKE_TEST_FILES if not Path(test_file).is_file()
    ]
    if missing_files:
        return {
            "command": _format_command(command),
            "result": "missing_files",
            "returncode": None,
            "missing_files": missing_files,
            "stdout": "",
            "stderr": "",
            "error": None,
        }
    completed = _run_command(command, timeout_seconds=120)
    return {
        **completed,
        "result": "pass" if completed["returncode"] == 0 else "fail",
        "missing_files": [],
    }


def _vitest_command(test_files: list[str]) -> list[str]:
    vitest_entry = Path("node_modules/vitest/vitest.mjs")
    if vitest_entry.is_file():
        return ["node", str(vitest_entry), "run", *test_files]
    return ["npx", "vitest", "run", *test_files]


def _python_dependency_check() -> dict[str, Any]:
    code = (
        "import importlib\n"
        "modules = ['fastapi','uvicorn','litellm','pynvml','pydantic_settings','dotenv',"
        "'httpx','tiktoken','asyncpg','pytest']\n"
        "missing=[]\n"
        "for name in modules:\n"
        "    try:\n"
        "        importlib.import_module(name)\n"
        "    except Exception as exc:\n"
        "        missing.append(f'{name}: {exc.__class__.__name__}: {exc}')\n"
        "print('\\n'.join(missing) if missing else 'python imports ok')\n"
        "raise SystemExit(1 if missing else 0)\n"
    )
    imports = _run_command([sys.executable, "-c", code], timeout_seconds=60)
    pip_check = _run_command([sys.executable, "-m", "pip", "check"], timeout_seconds=60)
    blockers = []
    if imports["returncode"] != 0:
        blockers.append("required Python import failed")
    if pip_check["returncode"] != 0:
        blockers.append("pip dependency consistency check failed")
    return {
        "result": "pass" if not blockers else "fail",
        "blockers": blockers,
        "imports": imports,
        "pip_check": pip_check,
    }


def _node_dependency_check() -> dict[str, Any]:
    required_paths = [
        "node_modules/typescript/bin/tsc",
        "node_modules/vitest/vitest.mjs",
        "node_modules/eslint/bin/eslint.js",
        "node_modules/next/dist/bin/next",
    ]
    missing_paths = [path for path in required_paths if not Path(path).exists()]
    checks = {
        "node": _run_command(["node", "--version"], timeout_seconds=20),
        "typescript": _run_command(["node", "node_modules/typescript/bin/tsc", "--version"], timeout_seconds=30)
        if not missing_paths
        else _skipped_command("node_modules dependency path missing"),
        "vitest": _run_command(["node", "node_modules/vitest/vitest.mjs", "--version"], timeout_seconds=30)
        if not missing_paths
        else _skipped_command("node_modules dependency path missing"),
        "eslint": _run_command(["node", "node_modules/eslint/bin/eslint.js", "--version"], timeout_seconds=30)
        if not missing_paths
        else _skipped_command("node_modules dependency path missing"),
    }
    blockers = [f"missing {path}" for path in missing_paths]
    blockers.extend(
        name
        for name, payload in checks.items()
        if payload.get("returncode") not in {0, None}
    )
    return {
        "result": "pass" if not blockers else "fail",
        "blockers": blockers,
        "required_paths": required_paths,
        "missing_paths": missing_paths,
        "checks": checks,
    }


def _service_availability_check() -> dict[str, Any]:
    scout = _http_get_json(f"{DEFAULT_SCOUT_BASE_URL}/health")
    searxng = _http_get_json("http://localhost:8080/search?q=fastapi&format=json")
    dashboard = _http_get_text(DEFAULT_CARTOGRAPHER_DASHBOARD_URL)
    blockers = []
    warnings = []
    if not scout["ok"]:
        blockers.append("Scout API unavailable")
    if not searxng["ok"]:
        warnings.append("SearXNG unavailable; Scout search diagnostics may be limited")
    if not dashboard["ok"]:
        warnings.append("Next dashboard unavailable; browser QA must start it before use")
    return {
        "result": "pass" if not blockers else "fail",
        "blockers": blockers,
        "warnings": warnings,
        "scout_api": scout,
        "searxng": searxng,
        "dashboard": dashboard,
    }


def _environment_variable_check() -> dict[str, Any]:
    env_files = _env_file_diagnostics([".env.local", ".env", ".env.example"])
    spirit_paths = _split_env_paths(os.environ.get("SPIRIT_PROJECT_PATH", ""))
    if not spirit_paths:
        spirit_paths = _split_env_paths(_env_file_value(env_files, "SPIRIT_PROJECT_PATH") or "")
    missing_spirit_paths = [path for path in spirit_paths if not Path(path).is_dir()]
    source_proxy_origin = os.environ.get("SOURCE_PROXY_ORIGIN", "").strip()
    scout_api_url = os.environ.get("SCOUT_API_URL", DEFAULT_SCOUT_BASE_URL).strip()
    blockers = []
    warnings = []
    if not spirit_paths:
        blockers.append("SPIRIT_PROJECT_PATH is unset")
    if missing_spirit_paths:
        blockers.append("SPIRIT_PROJECT_PATH contains missing directories")
    duplicates = [
        f"{item['path']}:{name}"
        for item in env_files
        for name, count in item.get("duplicate_keys", {}).items()
        if count > 1
    ]
    if duplicates:
        warnings.append("duplicate env keys: " + ", ".join(duplicates))
    if not source_proxy_origin:
        warnings.append("SOURCE_PROXY_ORIGIN unset; Next routes will use host/port fallback")
    return {
        "result": "pass" if not blockers else "fail",
        "blockers": blockers,
        "warnings": warnings,
        "spirit_project_paths": spirit_paths,
        "missing_spirit_project_paths": missing_spirit_paths,
        "source_proxy_origin": source_proxy_origin or None,
        "scout_api_url": scout_api_url,
        "env_files": env_files,
    }


def _database_freshness_check() -> dict[str, Any]:
    databases = [
        _sqlite_database_check("source_proxy_tasks", os.environ.get("SOURCE_PROXY_LONG_RUNNING_TASKS_DB", "data/long_running_tasks.sqlite3")),
        _sqlite_database_check("scout", "scout/data/scout.db"),
    ]
    blockers: list[str] = []
    warnings: list[str] = []
    for database in databases:
        if database["status"] == "missing":
            blockers.append(f"{database['name']} database missing")
        if database.get("stale"):
            warnings.append(f"{database['name']} database is stale")
        if database.get("journal_present"):
            blockers.append(f"{database['name']} sqlite journal present")
        if database.get("connect_ok") is False:
            blockers.append(f"{database['name']} database cannot be opened read-only")
    return {
        "result": "pass" if not blockers else "fail",
        "blockers": blockers,
        "warnings": warnings,
        "databases": databases,
    }


def _skipped_command(reason: str) -> dict[str, Any]:
    return {"command": "not run", "returncode": None, "stdout": "", "stderr": "", "error": reason}


def _http_get_text(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read(500).decode("utf-8", errors="replace")
        return {"ok": True, "status": response.status, "url": url, "body": body, "error": None}
    except (OSError, urllib.error.URLError) as error:
        return {"ok": False, "status": None, "url": url, "body": "", "error": str(error)}


def _env_file_diagnostics(paths: list[str]) -> list[dict[str, Any]]:
    diagnostics = []
    for path in paths:
        file_path = Path(path)
        if not file_path.is_file():
            diagnostics.append({"path": path, "exists": False, "keys": [], "duplicate_keys": {}})
            continue
        keys: list[str] = []
        for line in file_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            keys.append(stripped.split("=", 1)[0].strip())
        counts = Counter(keys)
        diagnostics.append(
            {
                "path": path,
                "exists": True,
                "keys": keys,
                "duplicate_keys": {key: count for key, count in counts.items() if count > 1},
            }
        )
    return diagnostics


def _env_file_value(env_files: list[dict[str, Any]], name: str) -> str | None:
    found: str | None = None
    for item in env_files:
        path = Path(str(item.get("path") or ""))
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(f"{name}="):
                found = stripped.split("=", 1)[1].strip()
    return found


def _split_env_paths(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _sqlite_database_check(name: str, path: str) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.is_file():
        return {"name": name, "path": path, "status": "missing"}
    age_seconds = (dt.datetime.now().timestamp() - file_path.stat().st_mtime)
    journal_present = Path(f"{path}-journal").exists()
    connect = _run_command(
        [
            sys.executable,
            "-c",
            (
                "import sqlite3, sys\n"
                "uri='file:' + sys.argv[1] + '?mode=ro'\n"
                "con=sqlite3.connect(uri, uri=True)\n"
                "con.execute('select 1').fetchone()\n"
                "con.close()\n"
                "print('sqlite read-only open ok')\n"
            ),
            path,
        ],
        timeout_seconds=20,
    )
    return {
        "name": name,
        "path": path,
        "status": "present",
        "size_bytes": file_path.stat().st_size,
        "age_seconds": int(age_seconds),
        "stale": age_seconds > 7 * 24 * 60 * 60,
        "journal_present": journal_present,
        "connect_ok": connect["returncode"] == 0,
        "connect": connect,
    }


def _pythonpath_env(paths: list[str]) -> dict[str, str]:
    current = os.environ.get("PYTHONPATH")
    pythonpath = os.pathsep.join([*paths, current] if current else paths)
    return {"PYTHONPATH": pythonpath}


def _run_command(
    command: list[str],
    *,
    timeout_seconds: int,
    env: dict[str, str] | None = None,
    progress_label: str | None = None,
) -> dict[str, Any]:
    if progress_label:
        return _run_command_with_progress(
            command,
            timeout_seconds=timeout_seconds,
            env=env,
            progress_label=progress_label,
        )
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env={**os.environ, **env} if env else None,
        )
        return {
            "command": _format_command(command),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "error": None,
        }
    except (OSError, subprocess.SubprocessError) as error:
        return {
            "command": _format_command(command),
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "error": str(error),
        }


def _run_command_with_progress(
    command: list[str],
    *,
    timeout_seconds: int,
    env: dict[str, str] | None,
    progress_label: str,
) -> dict[str, Any]:
    started = dt.datetime.now(dt.timezone.utc)
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, **env} if env else None,
        )
    except OSError as error:
        return {
            "command": _format_command(command),
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "error": str(error),
        }

    while process.poll() is None:
        elapsed = int((dt.datetime.now(dt.timezone.utc) - started).total_seconds())
        if elapsed >= timeout_seconds:
            process.kill()
            stdout, stderr = process.communicate()
            return {
                "command": _format_command(command),
                "returncode": None,
                "stdout": stdout,
                "stderr": stderr,
                "error": f"timed out after {timeout_seconds}s",
            }
        if elapsed and elapsed % 10 == 0:
            _progress(f"global-safety-regression: {progress_label} still running ({elapsed}s)")
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            continue

    stdout, stderr = process.communicate()
    return {
        "command": _format_command(command),
        "returncode": process.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "error": None,
    }


def _file_size(path: str) -> dict[str, Any]:
    file_path = Path(path)
    try:
        return {
            "path": path,
            "size_bytes": file_path.stat().st_size,
            "error": None,
        }
    except OSError as error:
        return {
            "path": path,
            "size_bytes": None,
            "error": str(error),
        }


def _discovery_job_count(check: dict[str, Any]) -> int:
    body = _body_dict(check)
    count = body.get("count")
    if isinstance(count, int):
        return count
    return len(_dict_list(body.get("jobs")))


def _soak_snapshot_warnings(
    *,
    checks: dict[str, dict[str, Any]],
    logs: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    for name, check in checks.items():
        if not check["ok"]:
            warnings.append(f"{name} check failed: {_check_error_detail(check)}")
    for marker in _log_warning_markers((logs.get("stdout") or "") + "\n" + (logs.get("stderr") or "")):
        warnings.append(f"recent docker logs contain {marker}")
    if logs.get("returncode") not in {0, None}:
        warnings.append("docker logs command failed")
    return list(dict.fromkeys(warnings))


def _fatal_soak_snapshot_warnings(warnings: list[str]) -> list[str]:
    return [warning for warning in warnings if warning != "docker logs command failed"]


def _log_warning_markers(log_text: str) -> list[str]:
    markers: list[str] = []
    for line in log_text.splitlines():
        lowered = line.lower()
        if "traceback" in lowered:
            markers.append("traceback")
        if "exception" in lowered:
            markers.append("exception")
        if "critical" in lowered:
            markers.append("critical")
        if _line_has_real_error(line):
            markers.append("error")
    return list(dict.fromkeys(markers))


def _line_has_real_error(line: str) -> bool:
    lowered = line.lower()
    if "error" not in lowered:
        return False
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return True
    if not isinstance(payload, dict):
        return True
    errors = payload.get("errors")
    if isinstance(errors, list) and not errors:
        return False
    if errors in {0, None, ""}:
        return False
    level = str(payload.get("level") or "").lower()
    event = str(payload.get("event") or "").lower()
    if level in {"error", "critical", "exception"}:
        return True
    if "error" in event and errors not in {0, None, ""}:
        return True
    return bool(errors)


def _write_soak_snapshot(*, snapshot: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = str(snapshot["timestamp"]).replace(":", "").replace("+0000", "Z").replace("+00:00", "Z")
    return output_dir / f"scout-soak-snapshot-{stamp}.json"


def _write_cartographer_soak_snapshot(*, snapshot: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = str(snapshot["timestamp"]).replace(":", "").replace("+0000", "Z").replace("+00:00", "Z")
    path = output_dir / f"cartographer-soak-snapshot-{stamp}.json"
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _directory_size(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "size_bytes": 0, "file_count": 0, "error": None}
    try:
        files = [item for item in path.rglob("*") if item.is_file()]
        return {
            "path": str(path),
            "size_bytes": sum(item.stat().st_size for item in files),
            "file_count": len(files),
            "error": None,
        }
    except OSError as error:
        return {
            "path": str(path),
            "size_bytes": None,
            "file_count": None,
            "error": str(error),
        }


def _search_diagnostic_findings(
    *,
    compose: dict[str, Any],
    container_env: dict[str, Any],
    settings: dict[str, Any],
    host_searxng: dict[str, Any],
    container_connectivity: dict[str, dict[str, Any]],
) -> list[str]:
    findings: list[str] = []
    if compose.get("ok") and not (compose.get("search_env_wired") and compose.get("searxng_url_wired")):
        findings.append("docker-compose.scout.yml does not wire SCOUT_SEARCH_ENABLED / SCOUT_SEARXNG_URL explicitly")
    if container_env.get("returncode") == 0 and not (
        container_env.get("search_enabled_present") and container_env.get("searxng_url_present")
    ):
        findings.append("Scout container does not receive SCOUT_SEARCH_ENABLED / SCOUT_SEARXNG_URL")
    settings_body = settings.get("settings") if isinstance(settings.get("settings"), dict) else {}
    if settings.get("returncode") == 0:
        if settings_body.get("search_enabled") is not True:
            findings.append("Scout settings report search_enabled false")
        if not settings_body.get("searxng_url_present"):
            findings.append("Scout settings report no searxng_url")
    if not host_searxng.get("ok"):
        findings.append("Host SearXNG endpoint is unreachable")
    elif _search_result_count(host_searxng.get("body")) == 0:
        findings.append("SearXNG reachable from host but returned 0 results")
    if _docker_unavailable(container_env) and host_searxng.get("ok"):
        return findings
    if not any(probe.get("ok") for probe in container_connectivity.values()):
        findings.append("No tested SearXNG URL is reachable from the Scout container")
    return findings


def _search_diagnostic_warnings(
    *,
    container_env: dict[str, Any],
    settings: dict[str, Any],
    container_connectivity: dict[str, dict[str, Any]],
) -> list[str]:
    warnings: list[str] = []
    if _docker_unavailable(container_env):
        warnings.append("docker unavailable; skipped Scout container env inspection")
    if _docker_unavailable(settings):
        warnings.append("docker unavailable; skipped Scout container settings inspection")
    if any(_docker_unavailable(probe) for probe in container_connectivity.values()):
        warnings.append("docker unavailable; skipped Scout container SearXNG probes")
    return warnings


def _docker_unavailable(result: dict[str, Any]) -> bool:
    text = " ".join(
        str(result.get(key) or "")
        for key in ("error", "stderr", "stdout")
    ).lower()
    return (
        result.get("returncode") not in {0, None}
        and "docker" in text
        and (
            "daemon" in text
            or "docker api" in text
            or "dockerdesktoplinuxengine" in text
            or "cannot find the file specified" in text
        )
    )


def _search_result_count(body: Any) -> int:
    if not isinstance(body, dict):
        return 0
    results = body.get("results")
    if isinstance(results, list):
        return len(results)
    return 0


def _http_get_json(url: str, *, timeout_seconds: int = 5) -> dict[str, Any]:
    try:
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            body = json.loads(raw) if raw.strip() else {}
            status = int(getattr(response, "status", 200))
            return {
                "ok": 200 <= status < 300,
                "status": status,
                "url": url,
                "body": body,
                "error": None,
            }
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status": error.code,
            "url": url,
            "body": _json_or_text(raw),
            "error": str(error),
        }
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        return {
            "ok": False,
            "status": None,
            "url": url,
            "body": {},
            "error": str(error),
        }


def _http_post_json(url: str, body: dict[str, Any], *, timeout_seconds: int = 10) -> dict[str, Any]:
    try:
        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            response_body = json.loads(raw) if raw.strip() else {}
            status = int(getattr(response, "status", 200))
            return {
                "ok": 200 <= status < 300,
                "status": status,
                "url": url,
                "body": response_body,
                "error": None,
            }
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status": error.code,
            "url": url,
            "body": _json_or_text(raw),
            "error": str(error),
        }
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        return {
            "ok": False,
            "status": None,
            "url": url,
            "body": {},
            "error": str(error),
        }


def _skipped_http_check(reason: str) -> dict[str, Any]:
    return {
        "ok": False,
        "status": None,
        "url": "",
        "body": {},
        "error": reason,
    }


def _json_or_text(raw: str) -> Any:
    try:
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {"raw": raw}


def _body_dict(check: dict[str, Any]) -> dict[str, Any]:
    body = check.get("body")
    return body if isinstance(body, dict) else {}


def _job_id_from_create(check: dict[str, Any]) -> str | None:
    body = _body_dict(check)
    job = body.get("job")
    if not isinstance(job, dict):
        return None
    job_id = job.get("job_id")
    return str(job_id) if job_id else None


def _is_discovery_job_daily_limit_error(check: dict[str, Any]) -> bool:
    if check.get("ok") or check.get("status") != 422:
        return False
    detail = _check_error_detail(check).lower()
    return "discovery job" in detail and "daily" in detail and "limit" in detail


def _scout_search_smoke_recommendation(result: str) -> str:
    if result == "pass":
        return "ready for next increment"
    if result == "blocked_by_budget":
        return (
            "wait for the next UTC budget reset, cancel stale duplicate jobs, "
            "or temporarily raise the bounded discovery job budget"
        )
    return "fix needed"


def _source_count(check: dict[str, Any]) -> int:
    body = _body_dict(check)
    count = body.get("count")
    if isinstance(count, int):
        return count
    sources = body.get("sources")
    return len(sources) if isinstance(sources, list) else 0


def _candidate_total(check: dict[str, Any]) -> int:
    counts = _body_dict(check).get("counts")
    if isinstance(counts, dict):
        return sum(value for value in counts.values() if isinstance(value, int))
    candidates = _body_dict(check).get("candidates")
    return len(candidates) if isinstance(candidates, list) else 0


def _approved_count(check: dict[str, Any]) -> int:
    counts = _body_dict(check).get("counts")
    if isinstance(counts, dict) and isinstance(counts.get("approved"), int):
        return int(counts["approved"])
    candidates = _dict_list(_body_dict(check).get("candidates"))
    return sum(1 for candidate in candidates if candidate.get("status") == "approved")


def _candidate_effect(
    *,
    before_candidates: dict[str, Any],
    after_preview_candidates: dict[str, Any],
    after_extract_candidates: dict[str, Any],
    after_extract_sources: dict[str, Any],
) -> dict[str, Any]:
    before_ids = _candidate_ids(before_candidates)
    after_preview_ids = _candidate_ids(after_preview_candidates)
    after_extract_candidates_list = _dict_list(_body_dict(after_extract_candidates).get("candidates"))
    new_candidates = [
        candidate
        for candidate in after_extract_candidates_list
        if str(candidate.get("candidate_id") or "") not in before_ids
    ]
    source_canonicals = {
        str(source.get("canonical_uri") or "")
        for source in _dict_list(_body_dict(after_extract_sources).get("sources"))
        if source.get("canonical_uri")
    }
    missing: list[str] = []
    for candidate in new_candidates:
        discovered_from = str(candidate.get("discovered_from_uri") or "")
        reason_codes = candidate.get("reason_codes") if isinstance(candidate.get("reason_codes"), list) else []
        canonical_uri = str(candidate.get("canonical_uri") or "")
        if not discovered_from.startswith("search://"):
            missing.append(f"{_candidate_label(candidate)} missing search:// provenance")
        if "discovered_from_search_result" not in {str(code) for code in reason_codes}:
            missing.append(f"{_candidate_label(candidate)} missing discovered_from_search_result")
        if canonical_uri in source_canonicals:
            missing.append(f"{_candidate_label(candidate)} became active source")
    preview_created = after_preview_ids - before_ids
    for candidate_id in sorted(preview_created):
        missing.append(f"{candidate_id} was created during preview")
    return {
        "checked": len(new_candidates),
        "missing": missing,
        "search_provenance_ok": len(missing) == 0,
    }


def _candidate_ids(check: dict[str, Any]) -> set[str]:
    return {
        str(candidate.get("candidate_id") or "")
        for candidate in _dict_list(_body_dict(check).get("candidates"))
        if candidate.get("candidate_id")
    }


def _dict_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _first_dict(value: Any) -> dict[str, Any]:
    items = _dict_list(value)
    return items[0] if items else {}


def _list_value(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _int_value(value: Any) -> int:
    return value if isinstance(value, int) else 0


def _candidate_label(candidate: dict[str, Any]) -> str:
    return str(
        candidate.get("canonical_uri")
        or candidate.get("display_uri")
        or candidate.get("candidate_id")
        or "unknown candidate"
    )


def _source_label(source: dict[str, Any]) -> str:
    return str(
        source.get("display_uri")
        or source.get("canonical_uri")
        or source.get("source_uri")
        or "unknown source"
    )


def _format_command(command: list[str]) -> str:
    display = [
        "python" if index == 0 and _looks_like_python(part) else part
        for index, part in enumerate(command)
    ]
    return " ".join(display)


def _looks_like_python(value: str) -> bool:
    name = Path(value).name.lower()
    return name.startswith("python")


def _safety_verdict(smoke: dict[str, Any]) -> dict[str, bool]:
    cases = smoke.get("cases", [])
    blocked_cases = [
        case
        for case in cases
        if case.get("evidence", {}).get("current_workflow_state") == "Blocked"
    ]
    return {
        "no_approve": all(
            case.get("evidence", {}).get("approval_available") is False
            for case in blocked_cases
        ),
        "no_apply": (
            smoke.get("applied_anything") is False
            and all(
                case.get("evidence", {}).get("would_apply_diff") is False
                and case.get("evidence", {}).get("file_written") is False
                for case in cases
            )
        ),
        "no_execute_approved": all(
            case.get("evidence", {}).get("would_execute") is False
            for case in cases
        ),
        "approval_unavailable_for_blocked_cases": bool(blocked_cases)
        and all(
            case.get("evidence", {}).get("approval_available") is False
            for case in blocked_cases
        ),
        "applied_anything_false": smoke.get("applied_anything") is False,
    }


def format_runner_report(payload: dict[str, Any]) -> str:
    if payload["profile"] == PROFILE_DEPENDENCY_ENVIRONMENT_CHECKS:
        return _format_dependency_environment_report(payload)
    if payload["profile"] == PROFILE_GLOBAL_SAFETY_REGRESSION:
        return _format_global_safety_regression_report(payload)
    if payload["profile"] == PROFILE_PHASE_4F_CLOSEOUT:
        return _format_phase_4f_closeout_report(payload)
    if payload["profile"] == PROFILE_CARTOGRAPHER_SAFETY:
        return _format_cartographer_safety_report(payload)
    if payload["profile"] == PROFILE_CARTOGRAPHER_SOAK_SNAPSHOT:
        return _format_cartographer_soak_snapshot_report(payload)
    if payload["profile"] == PROFILE_PROXY_CLOSEOUT:
        return _format_closeout_report(payload)
    if payload["profile"] == PROFILE_PROXY_REGRESSION:
        return _format_regression_report(payload)
    if payload["profile"] == PROFILE_SCOUT_SMOKE:
        return _format_scout_smoke_report(payload)
    if payload["profile"] == PROFILE_SCOUT_SOURCE_GATE:
        return _format_scout_source_gate_report(payload)
    if payload["profile"] == PROFILE_SCOUT_SEARCH_DIAGNOSTICS:
        return _format_scout_search_diagnostics_report(payload)
    if payload["profile"] == PROFILE_SCOUT_SEARCH_SMOKE:
        return _format_scout_search_smoke_report(payload)
    if payload["profile"] == PROFILE_SCOUT_SOAK_SNAPSHOT:
        return _format_scout_soak_snapshot_report(payload)
    return _format_smoke_report(payload)


def _format_dependency_environment_report(payload: dict[str, Any]) -> str:
    python_deps = payload["python_dependencies"]
    node_deps = payload["node_dependencies"]
    services = payload["services"]
    environment = payload["environment"]
    databases = payload["databases"]
    file_change = payload["file_change_verdict"]
    lines = [
        "DEPENDENCY AND ENVIRONMENT CHECKS",
        "",
        f"Profile: {payload['profile']}",
        f"Result: {payload['result'].upper()}",
        "",
        "Checks:",
        *[f"- {name}: {_pass_fail(passed)}" for name, passed in payload["checks"].items()],
        "",
        "Python dependencies:",
        f"- result: {python_deps['result'].upper()}",
        f"- blockers: {_plain_list(python_deps['blockers'])}",
        f"- imports: {_command_result_text(python_deps['imports'])}",
        f"- pip check: {_command_result_text(python_deps['pip_check'])}",
        "",
        "Node dependencies:",
        f"- result: {node_deps['result'].upper()}",
        f"- blockers: {_plain_list(node_deps['blockers'])}",
        f"- missing paths: {_plain_list(node_deps['missing_paths'])}",
        f"- node: {_command_result_text(node_deps['checks']['node'])}",
        f"- typescript: {_command_result_text(node_deps['checks']['typescript'])}",
        f"- vitest: {_command_result_text(node_deps['checks']['vitest'])}",
        f"- eslint: {_command_result_text(node_deps['checks']['eslint'])}",
        "",
        "Services:",
        f"- result: {services['result'].upper()}",
        f"- blockers: {_plain_list(services['blockers'])}",
        f"- warnings: {_plain_list(services['warnings'])}",
        f"- Scout API: {_check_status(services['scout_api'])}",
        f"- SearXNG: {_check_status(services['searxng'])}",
        f"- Dashboard: {_check_status(services['dashboard'])}",
        "",
        "Environment variables:",
        f"- result: {environment['result'].upper()}",
        f"- blockers: {_plain_list(environment['blockers'])}",
        f"- warnings: {_plain_list(environment['warnings'])}",
        f"- SPIRIT_PROJECT_PATH entries: {_plain_list(environment['spirit_project_paths'])}",
        f"- missing SPIRIT_PROJECT_PATH entries: {_plain_list(environment['missing_spirit_project_paths'])}",
        f"- SOURCE_PROXY_ORIGIN: {environment['source_proxy_origin'] or 'fallback'}",
        f"- SCOUT_API_URL: {environment['scout_api_url']}",
        "",
        "Databases:",
        f"- result: {databases['result'].upper()}",
        f"- blockers: {_plain_list(databases['blockers'])}",
        f"- warnings: {_plain_list(databases['warnings'])}",
        *[
            (
                f"- {database['name']}: {database['status']}"
                + (
                    f", size={database.get('size_bytes')} bytes, age={database.get('age_seconds')}s, "
                    f"journal={_bool_text(database.get('journal_present'))}, "
                    f"read_only_open={_bool_text(database.get('connect_ok'))}"
                    if database["status"] == "present"
                    else ""
                )
            )
            for database in databases["databases"]
        ],
        "",
        "Mutation verdict:",
        f"- unexpected status delta: {_plain_list(file_change['unexpected_status_delta'])}",
        f"- head changed: {_bool_text(file_change['head_changed'])}",
        "",
        f"Recommendation: {payload['recommendation']}",
    ]
    return "\n".join(lines)


def _format_global_safety_regression_report(payload: dict[str, Any]) -> str:
    file_change = payload["file_change_verdict"]
    safety = payload["safety_boundary"]
    checks = payload["checks"]
    source_proxy = payload["source_proxy_tests"]
    scout = payload["scout_backend_tests"]
    dashboard = payload["dashboard_smoke_tests"]
    cartographer = payload["cartographer_safety"]
    lines = [
        "GLOBAL SAFETY REGRESSION PACK",
        "",
        f"Profile: {payload['profile']}",
        f"Result: {payload['result'].upper()}",
        "",
        "Command results:",
        (
            "- proxy safety harness: "
            f"{_pass_fail(payload['proxy_safety_harness']['result'] == 'pass')}"
        ),
        (
            "- source proxy tests: "
            f"{_pass_fail(source_proxy['result'] == 'pass')} "
            f"({source_proxy['command']})"
        ),
        (
            "- Scout backend tests: "
            f"{_pass_fail(scout['result'] == 'pass')} "
            f"({scout['command']})"
        ),
        (
            "- Cartographer safety: "
            f"{_pass_fail(cartographer['result'] == 'pass')}"
        ),
        (
            "- dashboard smoke tests: "
            f"{_pass_fail(dashboard['result'] == 'pass')} "
            f"({dashboard['command']})"
        ),
        "",
        "Safety boundary:",
        f"- no approve: {_bool_text(safety['no_approve'])}",
        f"- no apply: {_bool_text(safety['no_apply'])}",
        f"- no execute-approved: {_bool_text(safety['no_execute_approved'])}",
        f"- no commit: {_bool_text(safety['no_commit'])}",
        f"- no push: {_bool_text(safety['no_push'])}",
        f"- no destructive cleanup: {_bool_text(safety['no_destructive_cleanup'])}",
        f"- no source auto-approval: {_bool_text(safety['no_source_auto_approval'])}",
        f"- no memory writes: {_bool_text(safety['no_memory_writes'])}",
        "",
        "Mutation verdict:",
        f"- changed by test run: {_bool_text(file_change['changed_by_test_run'])}",
        f"- unexpected status delta: {_plain_list(file_change['unexpected_status_delta'])}",
        f"- head before: {file_change.get('head_before') or 'unknown'}",
        f"- head after: {file_change.get('head_after') or 'unknown'}",
        f"- head changed: {_bool_text(file_change['head_changed'])}",
        "",
        "Checks:",
        *[f"- {name}: {_pass_fail(passed)}" for name, passed in checks.items()],
    ]
    for label, result in [
        ("source proxy stdout", source_proxy),
        ("Scout backend stdout", scout),
        ("dashboard stdout", dashboard),
    ]:
        tail = _output_tail(result.get("stdout", ""), max_lines=8)
        if tail:
            lines.extend(["", f"{label}:", tail])
    for label, result in [
        ("source proxy stderr", source_proxy),
        ("Scout backend stderr", scout),
        ("dashboard stderr", dashboard),
    ]:
        tail = _output_tail(result.get("stderr", ""), max_lines=8)
        if tail:
            lines.extend(["", f"{label}:", tail])
    lines.extend(["", f"Recommendation: {payload['recommendation']}"])
    return "\n".join(lines)


def _format_cartographer_safety_report(payload: dict[str, Any]) -> str:
    tests = payload["regression_tests"]
    safety = payload["safety_verdict"]
    file_change = payload["file_change_verdict"]
    lines = [
        "CARTOGRAPHER SAFETY AUDIT",
        "",
        f"Profile: {payload['profile']}",
        f"Result: {payload['result'].upper()}",
        "",
        "Regression tests:",
        f"- command: {tests['command']}",
        f"- result: {str(tests['result']).upper()}",
        f"- returncode: {tests['returncode']}",
        "",
        "Safety verdict:",
        f"- no unapproved writes: {_bool_text(safety['no_unapproved_writes'])}",
        f"- no unapproved apply: {_bool_text(safety['no_unapproved_apply'])}",
        f"- no unapproved commits: {_bool_text(safety['no_unapproved_commits'])}",
        f"- no unapproved pushes: {_bool_text(safety['no_unapproved_pushes'])}",
        f"- approval bypass locked: {_bool_text(safety['approval_bypass_locked'])}",
        "",
        "File-change verdict:",
        f"- before: {_one_line(file_change['before'])}",
        f"- after: {_one_line(file_change['after'])}",
        f"- changed by test run: {_bool_text(file_change['changed_by_test_run'])}",
        f"- unexpected status delta: {_plain_list(file_change.get('unexpected_status_delta', []))}",
        f"- background status delta: {_plain_list(file_change.get('background_status_delta', []))}",
        f"- head changed: {_bool_text(file_change['head_changed'])}",
        "",
        "Expected outcomes:",
        *[f"- {item}" for item in payload.get("expected_outcomes", [])],
    ]
    if tests.get("stdout"):
        lines.extend(["", "stdout:", str(tests["stdout"]).rstrip()])
    if tests.get("stderr"):
        lines.extend(["", "stderr:", str(tests["stderr"]).rstrip()])
    lines.extend(["", f"Recommendation: {payload['recommendation']}"])
    return "\n".join(lines)


def _format_cartographer_soak_snapshot_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    reliability = payload["reliability"]
    boundary = payload["mutation_boundary"]
    lines = [
        "CARTOGRAPHER SOAK SNAPSHOT",
        "",
        f"Profile: {payload['profile']}",
        f"Result: {payload['result'].upper()}",
        f"Timestamp: {payload['timestamp']}",
        f"Snapshot: {payload['snapshot_path']}",
        "",
        "Mutation boundary:",
        f"- snapshot log only: {_bool_text(boundary['snapshot_log_only'])}",
        f"- unexpected status delta: {_plain_list(boundary['unexpected_status_delta'])}",
        f"- head changed: {_bool_text(boundary['head_changed'])}",
        "",
        "Cartographer summary:",
        f"- branch: {summary.get('branch')}",
        f"- dirty: {_bool_text(summary.get('dirty'))}",
        f"- changed files: {summary.get('changed_file_count')}",
        f"- blueprints: {summary.get('blueprint_count')}",
        f"- proposals: {summary.get('proposal_count')}",
        f"- pending proposals: {summary.get('pending_proposals')}",
        f"- duplicate proposals: {summary.get('duplicate_proposals_present')}",
        f"- drift findings: {summary.get('drift_count')}",
        f"- commit proposals: {summary.get('commit_proposal_count')}",
        f"- push queue: {summary.get('push_queue_count')}",
        f"- audit events: {summary.get('audit_event_count')}",
        "",
        "Reliability:",
        f"- score: {reliability['score']}",
        f"- grade: {reliability['grade']}",
        f"- penalties: {_plain_list(reliability['penalties'])}",
        "",
        "Next actions:",
        *[f"- {action}" for action in payload.get("next_actions", [])],
        "",
        "Warnings:",
        f"- {_plain_list(payload.get('warnings', []))}",
        "",
        "Expected outcomes:",
        *[f"- {item}" for item in payload.get("expected_outcomes", [])],
        "",
        f"Recommendation: {payload['recommendation']}",
    ]
    return "\n".join(lines)


def _format_smoke_report(payload: dict[str, Any]) -> str:
    smoke = payload["smoke_harness"]
    summary = smoke["summary"]
    safety = payload["safety_verdict"]
    lines = [
        "PROXY TEST RUNNER",
        "",
        f"Profile: {payload['profile']}",
        "",
        "Smoke harness:",
        f"- suite: {smoke['suite']}",
        f"- result: {payload['result'].upper()}",
        f"- passed: {summary['passed']}",
        f"- failed: {summary['failed']}",
        f"- skipped: {summary['skipped']}",
        f"- applied_anything: {_bool_text(smoke['applied_anything'])}",
        "",
        "Seeded cases:",
    ]
    for case in smoke["cases"]:
        evidence = case["evidence"]
        lines.extend(
            [
                f"- {case['case_id']}: {case['status'].upper()}",
                f"  target: {evidence.get('target')}",
                f"  approval_available: {_bool_text(evidence.get('approval_available'))}",
                f"  would_change_files: {evidence.get('would_change_files')}",
            ]
        )
        for missing in case["missing"]:
            lines.append(f"  missing: {missing}")
    lines.extend(
        [
            "",
            "Safety verdict:",
            f"- no approve: {_bool_text(safety['no_approve'])}",
            f"- no apply: {_bool_text(safety['no_apply'])}",
            f"- no execute-approved: {_bool_text(safety['no_execute_approved'])}",
            (
                "- approval unavailable for blocked cases: "
                f"{_bool_text(safety['approval_unavailable_for_blocked_cases'])}"
            ),
            f"- applied_anything false: {_bool_text(safety['applied_anything_false'])}",
            "",
            f"Recommendation: {payload['recommendation']}",
        ]
    )
    return "\n".join(lines)


def _format_regression_report(payload: dict[str, Any]) -> str:
    tests = payload["regression_tests"]
    lines = [
        "PROXY TEST RUNNER",
        "",
        f"Profile: {payload['profile']}",
        "",
        "Regression tests:",
        f"- command: {tests['command']}",
        f"- result: {str(tests['result']).upper()}",
        f"- returncode: {tests['returncode']}",
    ]
    if tests["missing_files"]:
        lines.append("- missing files:")
        lines.extend(f"  - {test_file}" for test_file in tests["missing_files"])
    if tests["stdout"]:
        lines.extend(["", "stdout:", tests["stdout"].rstrip()])
    if tests["stderr"]:
        lines.extend(["", "stderr:", tests["stderr"].rstrip()])
    lines.extend(["", f"Recommendation: {payload['recommendation']}"])
    return "\n".join(lines)


def _format_closeout_report(payload: dict[str, Any]) -> str:
    smoke = payload["smoke_harness"]
    summary = smoke["summary"]
    regression = payload["regression_tests"]
    safety = payload["safety_verdict"]
    file_change = payload["file_change_verdict"]
    smoke_result = "PASS" if summary["failed"] == 0 and smoke["applied_anything"] is False else "FAIL"
    lines = [
        "PROXY TEST RUNNER CLOSEOUT",
        "",
        "Smoke harness:",
        f"- suite: {smoke['suite']}",
        f"- result: {smoke_result}",
        f"- passed: {summary['passed']}",
        f"- failed: {summary['failed']}",
        f"- skipped: {summary['skipped']}",
        f"- applied_anything: {_bool_text(smoke['applied_anything'])}",
        "",
        "Seeded cases:",
    ]
    case_ids = {case["case_id"] for case in smoke["cases"]}
    for case in smoke["cases"]:
        lines.append(f"- {case['case_id']}: {case['status'].upper()}")
    if "manual-check-9" not in case_ids:
        lines.append("- manual-check-9, if present: not present")
    lines.extend(
        [
            "",
            "Regression tests:",
            f"- command: {regression['command']}",
            f"- result: {str(regression['result']).upper()}",
            f"- failures: {_regression_failures(regression)}",
            "",
            "Safety verdict:",
            f"- no approve: {_bool_text(safety['no_approve'])}",
            f"- no apply: {_bool_text(safety['no_apply'])}",
            f"- no execute-approved: {_bool_text(safety['no_execute_approved'])}",
            (
                "- approval unavailable for blocked cases: "
                f"{_bool_text(safety['approval_unavailable_for_blocked_cases'])}"
            ),
            f"- applied_anything false: {_bool_text(safety['applied_anything_false'])}",
            "",
            "File-change verdict:",
            f"- before: {_one_line(file_change['before'])}",
            f"- after: {_one_line(file_change['after'])}",
            f"- changed by test run: {_bool_text(file_change['changed_by_test_run'])}",
            "",
            f"Recommendation: {payload['recommendation']}",
        ]
    )
    return "\n".join(lines)


def _format_scout_smoke_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    checks = payload["checks"]
    lines = [
        "SCOUT TEST RUNNER",
        "",
        f"Profile: {payload['profile']}",
        f"Base URL: {payload['base_url']}",
        f"Result: {payload['result'].upper()}",
        "",
        "Read-only verdict:",
        f"- read_only: {_bool_text(payload['read_only'])}",
        f"- mutated: {_bool_text(payload['mutated'])}",
        "",
        "Checks:",
        f"- health: {_check_status(checks['health'])}",
        f"- source candidates: {_check_status(checks['source_candidates'])}",
        f"- sources: {_check_status(checks['sources'])}",
        f"- discovery jobs: {_check_status(checks['discovery_jobs'])}",
        "",
        "Scout summary:",
        f"- health status: {summary['health_status']}",
        f"- candidate counts: {json.dumps(summary['candidate_counts'], sort_keys=True)}",
        f"- active source count: {summary['active_source_count']}",
        f"- active sources: {_source_list(summary['active_sources'])}",
        f"- discovery job count: {summary['discovery_job_count']}",
        "",
        f"Recommendation: {payload['recommendation']}",
    ]
    return "\n".join(lines)


def _format_scout_source_gate_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    checks = payload["checks"]
    invariants = payload["invariants"]
    lines = [
        "SCOUT SOURCE GATE RUNNER",
        "",
        f"Profile: {payload['profile']}",
        f"Base URL: {payload['base_url']}",
        f"Result: {payload['result'].upper()}",
        "",
        "Read-only verdict:",
        f"- read_only: {_bool_text(payload['read_only'])}",
        f"- mutated: {_bool_text(payload['mutated'])}",
        "",
        "Checks:",
        f"- source candidates: {_check_status(checks['source_candidates'])}",
        f"- sources: {_check_status(checks['sources'])}",
        "",
        "Source gate summary:",
        f"- candidate counts: {json.dumps(summary['candidate_counts'], sort_keys=True)}",
        f"- candidate count inspected: {summary['candidate_count']}",
        f"- active source count: {summary['active_source_count']}",
        f"- approved candidate count: {summary['approved_candidate_count']}",
        f"- unsupported active sources: {_plain_list(summary['unsupported_active_sources'])}",
        f"- candidates with review history: {_plain_list(summary['review_history_candidates'])}",
        "",
        "Invariants:",
        f"- rejected/blocked candidates not active: {_bool_text(invariants['rejected_blocked_not_active'])}",
        f"- approved candidates active: {_bool_text(invariants['approved_candidates_active'])}",
        f"- unsupported sources reported: {_bool_text(invariants['unsupported_sources_reported'])}",
        (
            "- review history visible when available: "
            f"{_bool_text(invariants['review_history_visible_when_available'])}"
        ),
        "",
        "Findings:",
        f"- rejected/blocked active: {_plain_list(summary['rejected_or_blocked_active'])}",
        f"- approved missing sources: {_plain_list(summary['approved_missing_sources'])}",
        "",
        f"Recommendation: {payload['recommendation']}",
    ]
    return "\n".join(lines)


def _format_scout_search_diagnostics_report(payload: dict[str, Any]) -> str:
    compose = payload["compose"]
    env = payload["container_env"]
    settings = payload["settings"]
    settings_body = settings.get("settings") if isinstance(settings.get("settings"), dict) else {}
    host = payload["host_searxng"]
    probes = payload["container_connectivity"]
    lines = [
        "SCOUT SEARCH DIAGNOSTICS",
        "",
        f"Profile: {payload['profile']}",
        f"Result: {payload['result'].upper()}",
        "",
        "Read-only verdict:",
        f"- read_only: {_bool_text(payload['read_only'])}",
        f"- mutated: {_bool_text(payload['mutated'])}",
        "",
        "Compose env wiring:",
        f"- file: {compose.get('path')}",
        f"- env_file: {_plain_list(compose.get('env_file_mentions') or [])}",
        f"- SCOUT_SEARCH_ENABLED wired: {_bool_text(compose.get('search_env_wired'))}",
        f"- SCOUT_SEARXNG_URL wired: {_bool_text(compose.get('searxng_url_wired'))}",
        "",
        "Container env:",
        f"- docker env available: {_bool_text(env.get('returncode') == 0)}",
        f"- SCOUT_SEARCH_ENABLED present: {_bool_text(env.get('search_enabled_present'))}",
        f"- SCOUT_SEARXNG_URL present: {_bool_text(env.get('searxng_url_present'))}",
        "",
        "Scout settings:",
        f"- settings available: {_bool_text(settings.get('returncode') == 0)}",
        f"- search_enabled: {settings_body.get('search_enabled')}",
        f"- searxng_url_present: {_bool_text(settings_body.get('searxng_url_present'))}",
        f"- search_provider: {settings_body.get('search_provider')}",
        f"- search_max_results: {settings_body.get('search_max_results')}",
        f"- search_timeout_seconds: {settings_body.get('search_timeout_seconds')}",
        f"- discovery_jobs_enabled: {settings_body.get('discovery_jobs_enabled')}",
        f"- discovery_jobs_per_day: {settings_body.get('discovery_jobs_per_day')}",
        f"- discovery_candidates_per_job: {settings_body.get('discovery_candidates_per_job')}",
        "",
        "Host SearXNG:",
        f"- status: {_check_status(host)}",
        f"- result count: {_search_result_count(host.get('body'))}",
        "",
        "Container SearXNG probes:",
    ]
    for url, probe in probes.items():
        lines.append(f"- {url}: {_check_status(probe)}; results={_search_result_count(probe.get('body'))}")
    finding_lines = [f"- {finding}" for finding in payload["findings"]] if payload["findings"] else ["- none"]
    warning_lines = [
        f"- {warning}" for warning in payload.get("warnings", [])
    ] if payload.get("warnings") else ["- none"]
    lines.extend(
        [
            "",
            "Warnings:",
            *warning_lines,
            "",
            "Findings:",
            *finding_lines,
            "",
            f"Recommendation: {payload['recommendation']}",
        ]
    )
    return "\n".join(lines)


def _format_scout_search_smoke_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    checks = payload["checks"]
    invariants = payload["invariants"]
    lines = [
        "SCOUT SEARCH SMOKE RUNNER",
        "",
        f"Profile: {payload['profile']}",
        f"Base URL: {payload['base_url']}",
        f"Result: {payload['result'].upper()}",
        "",
        "Mutation boundary:",
        f"- read_only: {_bool_text(payload['read_only'])}",
        f"- bounded: {_bool_text(payload['bounded'])}",
        f"- mutated candidates: {_bool_text(payload['mutated'])}",
        "- active sources mutated: false",
        "",
        "Checks:",
        f"- before candidates: {_check_status(checks['before_candidates'])}",
        f"- before sources: {_check_status(checks['before_sources'])}",
        f"- create discovery job: {_check_status(checks['create_job'])}",
        f"- search preview: {_check_status(checks['preview'])}",
        f"- after preview candidates: {_check_status(checks['after_preview_candidates'])}",
        f"- after preview sources: {_check_status(checks['after_preview_sources'])}",
        f"- extract candidates: {_check_status(checks['extract'])}",
        f"- after extract candidates: {_check_status(checks['after_extract_candidates'])}",
        f"- after extract sources: {_check_status(checks['after_extract_sources'])}",
        "",
        "Search smoke summary:",
        f"- job_id: {summary['job_id']}",
        f"- preview result count: {summary['preview_result_count']}",
        f"- preview candidate delta: {summary['preview_candidate_delta']}",
        f"- extract candidate delta: {summary['extract_candidate_delta']}",
        f"- source count before: {summary['source_count_before']}",
        f"- source count after preview: {summary['source_count_after_preview']}",
        f"- source count after extract: {summary['source_count_after_extract']}",
        f"- source count delta: {summary['source_count_delta']}",
        f"- approved count before: {summary['approved_count_before']}",
        f"- approved count after: {summary['approved_count_after']}",
        f"- search candidates checked: {summary['search_candidates_checked']}",
        f"- blocked reason: {summary.get('blocked_reason')}",
        "",
        "Invariants:",
        f"- preview does not create candidates: {_bool_text(invariants['preview_does_not_create_candidates'])}",
        f"- preview does not change sources: {_bool_text(invariants['preview_does_not_change_sources'])}",
        f"- extract does not change sources: {_bool_text(invariants['extract_does_not_change_sources'])}",
        f"- no auto approval: {_bool_text(invariants['no_auto_approval'])}",
        (
            "- search candidates have search provenance: "
            f"{_bool_text(invariants['search_candidates_have_search_provenance'])}"
        ),
        "",
        "Findings:",
        f"- missing search provenance: {_plain_list(summary['search_candidates_missing_provenance'])}",
        "",
        f"Recommendation: {payload['recommendation']}",
    ]
    return "\n".join(lines)


def _format_scout_soak_snapshot_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    checks = payload["checks"]
    lines = [
        "SCOUT SOAK SNAPSHOT",
        "",
        f"Profile: {payload['profile']}",
        f"Result: {payload['result'].upper()}",
        f"Timestamp: {payload['timestamp']}",
        f"Snapshot: {payload['snapshot_path']}",
        "",
        "Mutation boundary:",
        f"- read_only: {_bool_text(payload['read_only'])}",
        f"- mutated: {_bool_text(payload['mutated'])}",
        f"- wrote_snapshot: {_bool_text(payload['wrote_snapshot'])}",
        "",
        "Checks:",
        f"- health: {_check_status(checks['health'])}",
        f"- source candidates: {_check_status(checks['source_candidates'])}",
        f"- sources: {_check_status(checks['sources'])}",
        f"- discovery jobs: {_check_status(checks['discovery_jobs'])}",
        "",
        "Snapshot summary:",
        f"- health status: {summary['health_status']}",
        f"- candidate counts: {json.dumps(summary['candidate_counts'], sort_keys=True)}",
        f"- active source count: {summary['active_source_count']}",
        f"- discovery job count: {summary['discovery_job_count']}",
        f"- db size bytes: {summary['db_size_bytes']}",
        f"- docker logs available: {_bool_text(summary['docker_logs_available'])}",
        f"- warnings: {_plain_list(summary['warnings'])}",
        "",
        f"Recommendation: {payload['recommendation']}",
    ]
    return "\n".join(lines)


def _format_phase_4f_closeout_report(payload: dict[str, Any]) -> str:
    runner_tests = payload["runner_self_tests"]
    file_change = payload["file_change_verdict"]
    optional_search = payload["optional_checks"]["scout_search_smoke"]
    lines = [
        "PHASE 4F CLOSEOUT",
        "",
        f"Profile: {payload['profile']}",
        f"Result: {payload['result'].upper()}",
        "",
        "Core checks:",
        f"- proxy closeout: {payload['proxy_closeout']['result'].upper()}",
        f"- runner self tests: {_command_result_text(runner_tests)}",
        f"- scout smoke: {payload['scout_smoke']['result'].upper()}",
        f"- scout source gate: {payload['scout_source_gate']['result'].upper()}",
        f"- scout search diagnostics: {payload['scout_search_diagnostics']['result'].upper()}",
        f"- scout soak snapshot: {payload['scout_soak_snapshot']['result'].upper()}",
        "",
        "Safety boundary:",
        "- approve/apply/commit/push: not run",
        "- scout search smoke: not run by default",
        f"- optional search smoke reason: {optional_search['reason']}",
        f"- optional search smoke command: {optional_search['command']}",
        "",
        "File-change verdict:",
        f"- before: {_one_line(file_change['before'])}",
        f"- after: {_one_line(file_change['after'])}",
        f"- changed by test run: {_bool_text(file_change['changed_by_test_run'])}",
        f"- expected writes: {_plain_list(file_change['expected_writes'])}",
        "",
        "Manual checks:",
        "- dashboard Manual Checks card can run proxy and Scout profiles",
        "- bounded Search Smoke requires explicit confirmation",
        "- Soak Snapshot may write one timestamped JSON report",
        "",
        f"Recommendation: {payload['recommendation']}",
    ]
    return "\n".join(lines)


def _check_status(check: dict[str, Any]) -> str:
    if check["ok"]:
        return f"PASS ({check['status']})"
    error = _check_error_detail(check)
    status = check.get("status")
    return f"FAIL ({status}): {error}" if status is not None else f"FAIL: {error}"


def _check_error_detail(check: dict[str, Any]) -> str:
    body = check.get("body")
    if isinstance(body, dict):
        detail = body.get("detail")
        if detail:
            return str(detail)
        error = body.get("error")
        if error:
            return str(error)
        raw = body.get("raw")
        if raw:
            return str(raw)
    return str(check.get("error") or "request failed")


def _source_list(sources: list[Any]) -> str:
    labels: list[str] = []
    for source in sources[:10]:
        if not isinstance(source, dict):
            continue
        label = (
            source.get("display_uri")
            or source.get("canonical_uri")
            or source.get("source_uri")
            or source.get("label")
        )
        if label:
            labels.append(str(label))
    if not labels:
        return "none"
    suffix = "" if len(sources) <= 10 else f" (+{len(sources) - 10} more)"
    return ", ".join(labels) + suffix


def _plain_list(values: list[Any]) -> str:
    if not values:
        return "none"
    labels = [str(value) for value in values[:10]]
    suffix = "" if len(values) <= 10 else f" (+{len(values) - 10} more)"
    return ", ".join(labels) + suffix


def _pass_fail(passed: bool) -> str:
    return "PASS" if passed else "FAIL"


def _output_tail(value: str, *, max_lines: int) -> str:
    lines = value.strip().splitlines()
    if not lines:
        return ""
    return "\n".join(lines[-max_lines:])


def _progress(message: str) -> None:
    print(f"# {message}", file=sys.stderr, flush=True)


def _one_line(value: Any) -> str:
    return " | ".join(str(value).splitlines())


def _regression_failures(regression: dict[str, Any]) -> str:
    if regression["missing_files"]:
        return "missing files: " + ", ".join(regression["missing_files"])
    if regression["result"] == "pass":
        return "none"
    stderr = str(regression.get("stderr") or "").strip()
    stdout = str(regression.get("stdout") or "").strip()
    if stderr:
        return stderr.splitlines()[-1]
    if stdout:
        return stdout.splitlines()[-1]
    return f"pytest exited with {regression['returncode']}"


def _command_result_text(command_result: dict[str, Any]) -> str:
    returncode = command_result.get("returncode")
    if returncode == 0:
        return "PASS"
    if returncode is None:
        return f"FAIL: {command_result.get('error') or 'not run'}"
    stderr = str(command_result.get("stderr") or "").strip()
    stdout = str(command_result.get("stdout") or "").strip()
    detail = stderr.splitlines()[-1] if stderr else stdout.splitlines()[-1] if stdout else f"exit {returncode}"
    return f"FAIL ({returncode}): {detail}"


def _bool_text(value: Any) -> str:
    return "true" if value is True else "false" if value is False else str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Source Proxy test runner profiles.")
    parser.add_argument("--profile", default=PROFILE_PROXY_SMOKE)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)

    try:
        payload = run_runner_profile(profile=args.profile)
    except ValueError as error:
        print(f"ERROR: {error}")
        return 2

    if args.json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_runner_report(payload))
    return 0 if payload["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
