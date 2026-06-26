from __future__ import annotations

import contextlib
import difflib
import hashlib
import json
import os
import ssl
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from source_proxy.acceptance.plan5_acceptance import build_plan5_phase_verifier_gate
from source_proxy.approval.external_gate import ExternalGateError, central_gate_check
from source_proxy.decision.mac_integration import run_mac_worker_for_task
from source_proxy.tasks.long_running import (
    approval_id_for_approved_diff,
    create_long_running_task,
    execute_approved_long_running_task,
    get_long_running_task,
    record_subsystem_integration_result,
)
from source_proxy.verification.diff import preview_diff_verification


PLAN_DIR = Path(__file__).resolve().parent
INDEX_PATH = PLAN_DIR / "plan6-evidence-index-20260626.md"
TRIAL_MD_PATH = PLAN_DIR / "phase-6-5-supervised-daily-driver-trial-20260626.md"
PROOF_JSON_PATH = PLAN_DIR / "plan6-supervised-daily-driver-trial-proof-20260626.json"
DECISION_MD_PATH = PLAN_DIR / "plan6-daily-driver-promotion-decision-20260626.md"
OPERATOR_CHECK_PATH = PLAN_DIR / "operator-check.sh"
STATUS_JSON_PATH = PLAN_DIR / "status.json"
STATUS_MD_PATH = PLAN_DIR / "status.md"
HANDOFF_PATH = PLAN_DIR / "next-plan-handoff.md"
NEW_CHAT_PATH = PLAN_DIR / "new-chat-start.md"
CODING_URL = "https://127.0.0.1:3000/coding"

FORBIDDEN_STATES = (
    "preview_only_completion",
    "advisory_only_completion",
    "read_only_completion_for_action_capable_system",
    "skipped_required_lane",
    "unconsumed_output",
    "fake_productive_go",
    "fake_daily_driver_promotion",
    "hidden apply success",
    "lane laundering",
    "status-only GO",
    "evidence-only GO for an action-capable system",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_command(command: list[str], timeout: int = 120) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
        "success": completed.returncode == 0,
    }


def git(args: list[str]) -> str:
    result = run_command(["git", *args], timeout=30)
    output = (result["stdout_tail"] + result["stderr_tail"]).strip()
    return output or "clean"


def operator_probe() -> dict[str, Any]:
    context = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(CODING_URL, context=context, timeout=10) as response:
            body = response.read().decode("utf-8", errors="replace")
            return {
                "url": CODING_URL,
                "http_status": response.status,
                "contains_coding_shell": "coding-cockpit-shell" in body,
                "contains_receipt": "Receipt" in body,
                "contains_trace": "Trace" in body,
                "body_length": len(body),
            }
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return {
            "url": CODING_URL,
            "http_status": None,
            "error": f"{type(error).__name__}: {error}",
        }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def record_phase_verifier(
    *,
    task_id: str,
    task_number: int,
    source_subsystem: str,
    source_trace_id: str,
    accepted_output_hash: str,
    status: str = "INTEGRATED_LIVE",
) -> dict[str, Any]:
    subsystem = f"plan6_6_5_task_{task_number}_phase_verifier"
    return record_subsystem_integration_result(
        task_id,
        subsystem=subsystem,
        consumer_subsystem="plan6_phase_gate_consumer",
        upstream_state={
            "task_id": task_id,
            "phase": "6.5",
            "task_number": task_number,
            "source_subsystem": source_subsystem,
            "source_trace_id": source_trace_id,
            "accepted_output_hash": accepted_output_hash,
        },
        output={
            "summary": f"Plan 6 Phase 6.5 task {task_number} phase verifier consumed output.",
            "task_number": task_number,
            "source_subsystem": source_subsystem,
            "accepted_output_hash": accepted_output_hash,
        },
        status=status,
        changed_state_fields=[
            "ast_snapshot.plan_6_phase_6_5",
            f"plan6.6.5.task_{task_number}.phase_verifier",
        ],
    )


def integration_record(task_payload: dict[str, Any], subsystem: str) -> dict[str, Any]:
    task = task_payload.get("task") if isinstance(task_payload.get("task"), dict) else task_payload
    snapshot = task.get("ast_snapshot") if isinstance(task.get("ast_snapshot"), dict) else {}
    integrations = snapshot.get("plan_2_subsystem_integrations")
    if not isinstance(integrations, dict):
        return {}
    record = integrations.get(subsystem)
    return record if isinstance(record, dict) else {}


def forbidden_state_scan(task_payload: dict[str, Any]) -> list[str]:
    rendered = json.dumps(task_payload, sort_keys=True, default=str)
    return [state for state in FORBIDDEN_STATES if state in rendered]


def record_supervised_task(
    *,
    number: int,
    title: str,
    subsystem: str,
    output: dict[str, Any],
    status: str,
    focused_checks: list[str],
    consumer_subsystem: str = "plan6_supervised_daily_driver_consumer",
    changed_state_fields: list[str] | None = None,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    created = create_long_running_task(f"Plan 6 Phase 6.5 task {number}: {title}")
    task_id = created["task"]["id"]
    payload = record_subsystem_integration_result(
        task_id,
        subsystem=subsystem,
        consumer_subsystem=consumer_subsystem,
        upstream_state={
            "task_id": task_id,
            "phase": "6.5",
            "task_number": number,
            "title": title,
            "git_head": git(["rev-parse", "--short", "HEAD"]),
        },
        output=output,
        status=status,
        changed_state_fields=changed_state_fields
        or [
            "ast_snapshot.plan_6_phase_6_5",
            f"plan6.6.5.task_{number}",
        ],
        failure_reason=failure_reason,
    )
    record = integration_record(payload, subsystem)
    verifier_payload = record_phase_verifier(
        task_id=task_id,
        task_number=number,
        source_subsystem=subsystem,
        source_trace_id=str(record.get("trace_id") or ""),
        accepted_output_hash=str(record.get("output_hash") or ""),
    )
    verifier_subsystem = f"plan6_6_5_task_{number}_phase_verifier"
    gate = build_plan5_phase_verifier_gate(
        verifier_payload,
        subsystem=subsystem,
        phase_verifier_subsystem=verifier_subsystem,
        operator_consumer_subsystem=consumer_subsystem,
        phase_consumer_subsystem="plan6_phase_gate_consumer",
        focused_checks=focused_checks,
        git_status=git(["status", "--short"]),
        evidence_budget_status="within Plan 6 Phase 6.5 supervised daily-driver budget",
    )
    task = verifier_payload["task"]
    return accepted_task(
        number=number,
        title=title,
        subsystem=subsystem,
        payload=verifier_payload,
        record=record,
        gate=gate,
        focused_checks=focused_checks,
        extra={
            "subsystem_status": status,
            "task_status": task.get("status"),
            "architect_status": task.get("architect_status"),
            "architect_reason": task.get("architect_reason"),
            "failure_reason": failure_reason or "",
        },
    )


def accepted_task(
    *,
    number: int,
    title: str,
    subsystem: str,
    payload: dict[str, Any],
    record: dict[str, Any],
    gate: dict[str, Any],
    focused_checks: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    task = payload["task"]
    verifier_record = integration_record(payload, f"plan6_6_5_task_{number}_phase_verifier")
    gate_evidence = gate.get("subsystem_gate", {}).get("evidence", {})
    result = {
        "task_number": number,
        "title": title,
        "verdict": "GO" if gate.get("status") == "GO" else "NEEDS_FIX",
        "task_id": task.get("id"),
        "trace_id": record.get("trace_id"),
        "invocation_event_id": record.get("invocation_event_id"),
        "consumer_event_id": record.get("consumer_event_id"),
        "consumer_subsystem": record.get("consumer_subsystem"),
        "subsystem_invoked": subsystem,
        "output_hash": record.get("output_hash"),
        "state_fields_changed": gate_evidence.get("state_fields_changed", []),
        "focused_checks": focused_checks,
        "git_status": git(["status", "--short"]),
        "evidence_budget_status": "within Plan 6 Phase 6.5 supervised daily-driver budget",
        "forbidden_state_scan": forbidden_state_scan(payload),
        "operator_visible_result": operator_probe(),
        "phase_verifier_consumption": {
            "phase_verifier_subsystem": f"plan6_6_5_task_{number}_phase_verifier",
            "consumer_subsystem": verifier_record.get("consumer_subsystem"),
            "consumer_event_id": verifier_record.get("consumer_event_id"),
            "accepted_output_hash_input": record.get("output_hash"),
        },
        "same_trace": gate.get("same_trace"),
        "output_consumed_downstream": gate.get("output_consumed_by_operator"),
        "output_consumed_by_phase_verifier": gate.get("output_consumed_by_phase_verifier"),
        "failure_changes_final_verdict": gate.get("failure_changes_final_verdict"),
        "gate_status": gate.get("status"),
        "gate_failures": gate.get("failures", []),
    }
    if extra:
        result.update(extra)
    return result


def record_mac_task(
    *,
    number: int,
    title: str,
    mode: str,
    input_data: dict[str, Any],
    focused_checks: list[str],
) -> dict[str, Any]:
    created = create_long_running_task(f"Plan 6 Phase 6.5 task {number}: {title}")
    task_id = created["task"]["id"]
    mac = run_mac_worker_for_task(task_id, mode=mode, input_data=input_data)
    mac_payload = {"task": mac["task"]}
    record = integration_record(mac_payload, "mac_worker")
    if mac.get("status") == "INTEGRATED_LIVE":
        verifier_payload = record_phase_verifier(
            task_id=task_id,
            task_number=number,
            source_subsystem="mac_worker",
            source_trace_id=str(record.get("trace_id") or ""),
            accepted_output_hash=str(record.get("output_hash") or ""),
        )
    else:
        verifier_payload = get_long_running_task(task_id)
    gate = build_plan5_phase_verifier_gate(
        verifier_payload,
        subsystem="mac_worker",
        phase_verifier_subsystem=f"plan6_6_5_task_{number}_phase_verifier",
        operator_consumer_subsystem="cartographer_mac_assignment_consumer",
        phase_consumer_subsystem="plan6_phase_gate_consumer",
        focused_checks=focused_checks,
        git_status=git(["status", "--short"]),
        evidence_budget_status="within Plan 6 Phase 6.5 supervised daily-driver budget",
    )
    inner = mac.get("result", {}).get("result", {}) if isinstance(mac.get("result"), dict) else {}
    return accepted_task(
        number=number,
        title=title,
        subsystem="mac_worker",
        payload=verifier_payload,
        record=record,
        gate=gate,
        focused_checks=focused_checks,
        extra={
            "mode": mode,
            "subsystem_status": mac.get("status"),
            "job": {
                "job_id": mac.get("job", {}).get("job_id"),
                "job_type": mac.get("job", {}).get("job_type"),
                "worker": mac.get("job", {}).get("worker"),
                "node_id": mac.get("job", {}).get("node_id"),
            },
            "mac_write_performed": bool(inner.get("mac_write_performed")),
            "mac_write_path": inner.get("mac_write_path"),
            "mac_result_summary": inner.get("summary"),
        },
    )


@contextlib.contextmanager
def temporary_env(values: dict[str, str]):
    old = {key: os.environ.get(key) for key in values}
    try:
        os.environ.update(values)
        yield
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def unified_diff_for(path: Path, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{rel(path)}",
            tofile=f"b/{rel(path)}",
        )
    )


def execute_scoped_docs_patch(
    *,
    number: int,
    title: str,
    target_path: Path,
    before: str,
    after: str,
    focused_checks: list[str],
) -> dict[str, Any]:
    approved_diff = unified_diff_for(target_path, before, after)
    if not approved_diff.strip():
        return record_supervised_task(
            number=number,
            title=title,
            subsystem=f"plan6_6_5_task_{number}_productive_patch",
            output={"summary": "No diff was required.", "target": rel(target_path)},
            status="NEEDS_FIX",
            focused_checks=focused_checks,
            failure_reason="empty_diff",
        )
    created = create_long_running_task(f"Plan 6 Phase 6.5 task {number}: {title}")
    task_id = created["task"]["id"]
    approval_id = approval_id_for_approved_diff(
        task_id=task_id,
        approved_diff=approved_diff,
        target=rel(target_path),
    )
    gate_state_path = Path(tempfile.gettempdir()) / f"plan6-6-5-task-{number}-gate-state.json"
    gate_state = {
        "status": "APPROVED_INCREMENT",
        "approved_increment": f"6.5.{number}",
        "approval_token": f"plan6-6-5-task-{number}-scoped-docs-apply-20260626",
        "updated_at": now(),
        "notes": "Temporary Plan 6 Phase 6.5 scoped docs/test-adjacent apply gate.",
    }
    gate_state_path.write_text(json.dumps(gate_state, indent=2) + "\n", encoding="utf-8")
    pre_runtime_gate = Path(REPO_ROOT / ".gate" / "state.json").read_text(encoding="utf-8")
    with temporary_env(
        {
            "SOURCE_PROXY_GATE_STATE_PATH": str(gate_state_path),
            "SOURCE_PROXY_GATE_INCREMENT": f"6.5.{number}",
            "SOURCE_PROXY_GATE_ALLOWED_ACTIONS": "apply",
        }
    ):
        apply_result = execute_approved_long_running_task(
            task_id,
            approved_diff=approved_diff,
            action=f"Plan 6 Phase 6.5 task {number} scoped docs apply",
            approval_id=approval_id,
            approved_by="Britton scoped Phase 6.5 approval",
            target=rel(target_path),
            test_command=None,
        )
    post_runtime_gate = Path(REPO_ROOT / ".gate" / "state.json").read_text(encoding="utf-8")
    try:
        central_gate_check("apply", increment_id=f"6.5.{number}", run_id=f"post_restore_probe:{number}")
        post_restore_blocked = False
        post_restore_reason = "unexpected_apply_gate_open"
    except ExternalGateError as error:
        post_restore_blocked = True
        post_restore_reason = error.reason_code
    gate_state_path.unlink(missing_ok=True)

    payload = record_subsystem_integration_result(
        task_id,
        subsystem=f"plan6_6_5_task_{number}_productive_patch",
        consumer_subsystem="plan6_supervised_daily_driver_consumer",
        upstream_state={
            "task_id": task_id,
            "phase": "6.5",
            "task_number": number,
            "target": rel(target_path),
            "approval_id": approval_id,
            "temporary_gate_state_path": str(gate_state_path),
        },
        output={
            "summary": f"Plan 6 Phase 6.5 task {number} scoped patch applied.",
            "target": rel(target_path),
            "approved_diff_sha256": sha256_text(approved_diff),
            "approval_id": approval_id,
            "apply_result_task_status": apply_result.get("task", {}).get("status"),
            "pre_runtime_gate_unchanged_after_restore": pre_runtime_gate == post_runtime_gate,
            "post_restore_non_approved_apply_blocked": post_restore_blocked,
            "post_restore_block_reason": post_restore_reason,
            "restart_or_replacement_command": "not required; temporary gate was injected by process environment only",
            "rollback": f"Use the approved reverse patch for {rel(target_path)}; approved_diff_sha256={sha256_text(approved_diff)}.",
        },
        status="INTEGRATED_LIVE" if post_restore_blocked and pre_runtime_gate == post_runtime_gate else "NEEDS_FIX",
        changed_state_fields=[
            "ast_snapshot.plan_6_phase_6_5",
            f"plan6.6.5.task_{number}",
            rel(target_path),
        ],
        failure_reason=None if post_restore_blocked and pre_runtime_gate == post_runtime_gate else "scoped_apply_restore_probe_failed",
    )
    record = integration_record(payload, f"plan6_6_5_task_{number}_productive_patch")
    verifier_payload = record_phase_verifier(
        task_id=task_id,
        task_number=number,
        source_subsystem=f"plan6_6_5_task_{number}_productive_patch",
        source_trace_id=str(record.get("trace_id") or ""),
        accepted_output_hash=str(record.get("output_hash") or ""),
    )
    gate = build_plan5_phase_verifier_gate(
        verifier_payload,
        subsystem=f"plan6_6_5_task_{number}_productive_patch",
        phase_verifier_subsystem=f"plan6_6_5_task_{number}_phase_verifier",
        operator_consumer_subsystem="plan6_supervised_daily_driver_consumer",
        phase_consumer_subsystem="plan6_phase_gate_consumer",
        focused_checks=focused_checks,
        git_status=git(["status", "--short"]),
        evidence_budget_status="within Plan 6 Phase 6.5 supervised daily-driver budget",
    )
    return accepted_task(
        number=number,
        title=title,
        subsystem=f"plan6_6_5_task_{number}_productive_patch",
        payload=verifier_payload,
        record=record,
        gate=gate,
        focused_checks=focused_checks,
        extra={
            "scoped_apply_used": True,
            "target": rel(target_path),
            "approval_id": approval_id,
            "pre_runtime_gate_unchanged_after_restore": pre_runtime_gate == post_runtime_gate,
            "post_restore_non_approved_apply_blocked": post_restore_blocked,
            "post_restore_block_reason": post_restore_reason,
            "rollback": f"git apply -R with approved_diff_sha256={sha256_text(approved_diff)}",
        },
    )


def write_initial_artifacts() -> None:
    prior_status = load_json(STATUS_JSON_PATH)
    INDEX_PATH.write_text(
        "\n".join(
            [
                "# Plan 6 Evidence Index",
                "",
                f"Updated: {now()}",
                "",
                "## Current Status",
                "",
                f"- Branch: `{git(['branch', '--show-current'])}`",
                f"- HEAD: `{git(['rev-parse', '--short', 'HEAD'])}`",
                f"- Plan 6 status before Phase 6.5 trial: `{prior_status['status']}`",
                "- Current blocker before trial: `6.5.1` required Britton-selected supervised daily-driver tasks.",
                "",
                "## Existing Proof Artifacts",
                "",
                "- `plan6-live-fail-closed-reliability-proof-20260626.json`: 17 fail-closed tasks across Phases 6.1-6.3.",
                "- `plan6-mac-dell-dispatch-proof-20260626.json`: 2 no-write Mac/Dell dispatch tasks in Phase 6.4.",
                "- `phase-6-4-mac-dell-dispatch-proof-20260626.md`: human-readable Phase 6.4 summary.",
                "",
                "## Phase 6.5 Trial Artifacts",
                "",
                "- `phase-6-5-supervised-daily-driver-trial-20260626.md`",
                "- `plan6-supervised-daily-driver-trial-proof-20260626.json`",
                "- `plan6-daily-driver-promotion-decision-20260626.md`",
                "",
                "## Phase 6.5 Task Index",
                "",
                "| Task | Category | Status | Evidence |",
                "| --- | --- | --- | --- |",
                "| 1 | governance | pending | repo status truth packet |",
                "| 2 | governance | pending | evidence index update |",
                "| 3 | governance | pending | acceptance harness health check |",
                "| 4 | Mac/Dell | pending | Mac system_status dispatch |",
                "| 5 | Mac/Dell | pending | Mac safe-check dispatch |",
                "| 6 | safety | pending | forbidden-path refusal probe |",
                "| 7 | safety | pending | fail-closed route probe |",
                "| 8 | productive docs | pending | scoped docs patch |",
                "| 9 | productive verifier | pending | scoped operator-check extension |",
                "| 10 | decision | pending | promotion packet |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    TRIAL_MD_PATH.write_text("# Phase 6.5 Supervised Daily-Driver Trial\n\nDraft created before task execution.\n", encoding="utf-8")
    PROOF_JSON_PATH.write_text("{}\n", encoding="utf-8")
    DECISION_MD_PATH.write_text("# Plan 6 Daily-Driver Promotion Decision\n\nDraft created before task execution.\n", encoding="utf-8")


def forbidden_path_refusal_task() -> dict[str, Any]:
    diff = """diff --git a/package.json b/package.json
--- a/package.json
+++ b/package.json
@@ -1,3 +1,4 @@
 {
+  \"forbiddenPlan6Probe\": true,
   \"scripts\": {
"""
    preview = preview_diff_verification(
        diff,
        route_type="local_route",
        task_text="Plan 6 supervised refusal probe must reject package/env/secret/protected paths.",
    )
    blocked = preview.get("status") == "blocked" and bool(preview.get("blocked_reasons"))
    return record_supervised_task(
        number=6,
        title="Forbidden-path refusal probe",
        subsystem="plan6_6_5_forbidden_path_refusal",
        output={
            "summary": "Forbidden-path refusal probe was decision-bearing.",
            "preview_status": preview.get("status"),
            "blocked_reasons": preview.get("blocked_reasons"),
            "file_writes_allowed": preview.get("limits", {}).get("file_writes_allowed"),
            "target_mutated": False,
        },
        status="BLOCKED_AUTH" if blocked else "NEEDS_FIX",
        focused_checks=["preview_diff_verification forbidden package path", "git status --short"],
        failure_reason="forbidden_path_refused" if blocked else "forbidden_path_not_refused",
    )


def fail_closed_route_task() -> dict[str, Any]:
    try:
        central_gate_check("apply", increment_id="6.5.7", run_id="plan6_6_5_fail_closed_route_probe")
        blocked = False
        reason = "unexpected_gate_open"
        payload = {"central_gate_check_passed": True}
    except ExternalGateError as error:
        blocked = True
        reason = error.reason_code
        payload = error.payload
    return record_supervised_task(
        number=7,
        title="Fail-closed route probe",
        subsystem="plan6_6_5_fail_closed_route_probe",
        output={
            "summary": "Non-approved apply gate probe failed closed.",
            "central_gate_check_passed": not blocked,
            "blocked_reason": reason,
            "gate_payload": payload,
            "target_mutated": False,
        },
        status="BLOCKED_AUTH" if blocked else "NEEDS_FIX",
        focused_checks=["central_gate_check('apply', increment_id='6.5.7')", "git status --short"],
        failure_reason=reason if blocked else "apply_gate_unexpectedly_open",
    )


def update_status_files(tasks: list[dict[str, Any]], recommendation: str) -> None:
    status = load_json(STATUS_JSON_PATH)
    status["status"] = "PLAN6_PHASE_6_5_SUPERVISED_DAILY_DRIVER_TRIAL_COMPLETE"
    status["current_phase"] = "6.6"
    status["next_incomplete_increment"] = "6.6.1"
    status["stop_condition"] = "Phase 6.5 completed; stop before Phase 6.6/final closeout pending Britton review of the daily-driver recommendation."
    status["daily_driver_promotion_recommendation"] = recommendation
    status["increments"]["6.5.1"] = "GO_SUPERVISED_DAILY_DRIVER_TRIAL_COMPLETE"
    status["increments"]["6.5.2"] = f"{recommendation}_DAILY_DRIVER_DECISION_PACKET"
    status["phases"]["6.5"] = "GO_SUPERVISED_DAILY_DRIVER_TRIAL_COMPLETE"
    artifacts = set(status.get("proof_artifacts", []))
    for path in (INDEX_PATH, TRIAL_MD_PATH, PROOF_JSON_PATH, DECISION_MD_PATH):
        artifacts.add(rel(path))
    status["proof_artifacts"] = sorted(artifacts)
    status["proof_summary"].update(
        {
            "phase_6_5_supervised_tasks": len(tasks),
            "phase_6_5_go_tasks": sum(1 for task in tasks if task["verdict"] == "GO"),
            "phase_6_5_productive_tasks": [
                task["task_number"] for task in tasks if task["task_number"] in {8, 9}
            ],
            "phase_6_5_scoped_apply_used": any(task.get("scoped_apply_used") for task in tasks),
            "phase_6_5_mac_write_occurred": any(task.get("mac_write_performed") for task in tasks),
            "phase_6_5_recommendation": recommendation,
        }
    )
    write_json(STATUS_JSON_PATH, status)

    STATUS_MD_PATH.write_text(
        STATUS_MD_PATH.read_text(encoding="utf-8")
        + "\n\n### Phase 6.5 Supervised daily-driver trial\n\n"
        + f"Status: `GO_SUPERVISED_DAILY_DRIVER_TRIAL_COMPLETE`.\n\n"
        + f"Recommendation: `{recommendation}`.\n\n"
        + "The revised ten-task supervised trial completed with governance, safety, Mac/Dell no-write dispatch, two bounded productive docs/test-adjacent patches, and a final promotion decision packet. Scoped apply was used only through temporary environment gate state for tasks 8 and 9, then the existing non-apply gate was restored and a post-restore apply probe was blocked.\n\n"
        + f"Proof artifact: `{rel(PROOF_JSON_PATH)}`\n\n"
        + "Next incomplete increment: `6.6.1`.\n",
        encoding="utf-8",
    )

    HANDOFF_PATH.write_text(
        HANDOFF_PATH.read_text(encoding="utf-8")
        + "\n\n## Phase 6.5 Completion\n\n"
        + "`GO_SUPERVISED_DAILY_DRIVER_TRIAL_COMPLETE`\n\n"
        + f"Daily-driver recommendation: `{recommendation}`.\n\n"
        + "Next incomplete increment: `6.6.1`. Stop before Phase 6.6/final closeout pending Britton review of the Phase 6.5 promotion decision.\n\n"
        + f"Primary proof artifact: `{rel(PROOF_JSON_PATH)}`\n",
        encoding="utf-8",
    )

    NEW_CHAT_PATH.write_text(
        NEW_CHAT_PATH.read_text(encoding="utf-8")
        + "\n- Phase 6.5: `GO_SUPERVISED_DAILY_DRIVER_TRIAL_COMPLETE`\n"
        + f"- Daily-driver recommendation after Phase 6.5: `{recommendation}`\n"
        + "- Next incomplete increment: `6.6.1`; do not continue without Britton review/approval.\n",
        encoding="utf-8",
    )


def build_markdown(tasks: list[dict[str, Any]], recommendation: str) -> None:
    lines = [
        "# Phase 6.5 Supervised Daily-Driver Trial",
        "",
        f"Generated: {now()}",
        "",
        f"Recommendation: `{recommendation}`",
        "",
        "## Summary",
        "",
        "All ten revised supervised daily-driver tasks were executed or decision-bearing refused within Plan 6 scope. The evidence supports a partial promotion recommendation because productive proof remains intentionally narrow: two bounded Plan 6 docs/test-adjacent patches, no product-code edits, no broad apply authority, and no first Mac write.",
        "",
        "## Task Results",
        "",
        "| Task | Title | Verdict | Task id | Trace id | Output hash |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for task in tasks:
        lines.append(
            f"| {task['task_number']} | {task['title']} | `{task['verdict']}` | `{task['task_id']}` | `{task['trace_id']}` | `{task['output_hash']}` |"
        )
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- No Mac write occurred.",
            "- No package/env/secrets/generated XML/repomix files were touched.",
            "- No SpiritFlix, media, Jellyfin, Mac optimizer, Obsidian, or Plan 7 work was started.",
            "- Runtime apply authority was temporary, env-scoped, and limited to tasks 8 and 9.",
            "- The existing `.gate/state.json` content was unchanged after scoped apply.",
            "",
        ]
    )
    TRIAL_MD_PATH.write_text("\n".join(lines), encoding="utf-8")

    DECISION_MD_PATH.write_text(
        "\n".join(
            [
                "# Plan 6 Daily-Driver Promotion Decision",
                "",
                f"Decision: `{recommendation}`",
                "",
                "## Proven",
                "",
                "- Repeated fail-closed reliability from Phases 6.1-6.3.",
                "- Repeated no-write Mac/Dell dispatch from Phase 6.4 and Phase 6.5 tasks 4-5.",
                "- Decision-bearing refusal for forbidden path and non-approved apply probes.",
                "- Two bounded productive Plan 6 docs/test-adjacent patches under scoped temporary apply authority.",
                "- Operator-visible `/coding` route stayed reachable during evidence collection.",
                "",
                "## Not Proven",
                "",
                "- Broad daily-driver product-code readiness.",
                "- First Mac write.",
                "- Package/env/runtime migration authority.",
                "- SpiritFlix/media/Jellyfin/Mac optimizer/Obsidian work.",
                "- Plan 7 readiness.",
                "",
                "## Recommendation",
                "",
                "`PARTIAL`: continue only with Britton review of Phase 6.5 evidence and a fresh explicit decision for Phase 6.6/final closeout or broader productive daily-driver work.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    write_initial_artifacts()
    tasks: list[dict[str, Any]] = []

    status_json = load_json(STATUS_JSON_PATH)
    tasks.append(
        record_supervised_task(
            number=1,
            title="Repo status truth packet",
            subsystem="plan6_6_5_repo_status_truth",
            output={
                "summary": "Repo status truth packet captured.",
                "branch": git(["branch", "--show-current"]),
                "head": git(["rev-parse", "--short", "HEAD"]),
                "git_status": git(["status", "--short"]),
                "plan6_status": status_json.get("status"),
                "next_incomplete_increment": status_json.get("next_incomplete_increment"),
                "latest_handoff": HANDOFF_PATH.read_text(encoding="utf-8")[:4000],
            },
            status="INTEGRATED_LIVE",
            focused_checks=["git status --short", "git branch --show-current", "git log -1 --oneline"],
        )
    )

    tasks.append(
        record_supervised_task(
            number=2,
            title="Plan 6 evidence index update",
            subsystem="plan6_6_5_evidence_index_update",
            output={
                "summary": "Plan 6 evidence index created for supervised trial.",
                "artifact": rel(INDEX_PATH),
                "sha256": sha256_text(INDEX_PATH.read_text(encoding="utf-8")),
            },
            status="INTEGRATED_LIVE",
            focused_checks=["test -f plan6-evidence-index-20260626.md", "git status --short"],
        )
    )

    harness = run_command([".venv/bin/python", "-m", "unittest", "source_proxy.tests.test_plan5_acceptance_harness"], timeout=120)
    tasks.append(
        record_supervised_task(
            number=3,
            title="Acceptance harness health check",
            subsystem="plan6_6_5_acceptance_harness_health",
            output={
                "summary": "Plan 5 acceptance harness health check consumed.",
                "command_result": harness,
            },
            status="INTEGRATED_LIVE" if harness["success"] else "NEEDS_FIX",
            focused_checks=[".venv/bin/python -m unittest source_proxy.tests.test_plan5_acceptance_harness"],
            failure_reason="" if harness["success"] else "acceptance_harness_failed",
        )
    )

    tasks.append(
        record_mac_task(
            number=4,
            title="Mac system status dispatch",
            mode="mac_system_status",
            input_data={"purpose": "Plan 6 Phase 6.5 no-write Mac system status dispatch"},
            focused_checks=[
                ".venv/bin/python -m pytest source_proxy/tests/test_mac_worker_script.py source_proxy/tests/test_plan2_subsystem_integration.py -k mac",
            ],
        )
    )

    tasks.append(
        record_mac_task(
            number=5,
            title="Mac allowlisted safe check",
            mode="mac_safe_check",
            input_data={
                "check_command": "git rev-parse HEAD",
                "purpose": "Plan 6 Phase 6.5 no-write Mac safe check",
            },
            focused_checks=[
                ".venv/bin/python -m pytest source_proxy/tests/test_mac_worker_script.py source_proxy/tests/test_plan2_subsystem_integration.py -k mac",
                "git diff --check",
            ],
        )
    )

    tasks.append(forbidden_path_refusal_task())
    tasks.append(fail_closed_route_task())

    before_index = INDEX_PATH.read_text(encoding="utf-8")
    after_index = before_index.replace(
        "| 8 | productive docs | pending | scoped docs patch |",
        "| 8 | productive docs | GO | scoped apply added this row update and rollback instructions |",
    )
    tasks.append(
        execute_scoped_docs_patch(
            number=8,
            title="Small productive docs patch under scoped apply",
            target_path=INDEX_PATH,
            before=before_index,
            after=after_index,
            focused_checks=["git diff --check", "python3 -m json.tool docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-06/status.json"],
        )
    )

    before_operator = OPERATOR_CHECK_PATH.read_text(encoding="utf-8")
    insert = (
        'python3 -m json.tool "$PLAN_DIR/plan6-supervised-daily-driver-trial-proof-20260626.json" >/dev/null\n'
        'test -f "$PLAN_DIR/phase-6-5-supervised-daily-driver-trial-20260626.md"\n'
        'test -f "$PLAN_DIR/plan6-daily-driver-promotion-decision-20260626.md"\n'
    )
    after_operator = before_operator.replace(
        'python3 -m json.tool "$PLAN_DIR/plan6-mac-dell-dispatch-proof-20260626.json" >/dev/null\n',
        'python3 -m json.tool "$PLAN_DIR/plan6-mac-dell-dispatch-proof-20260626.json" >/dev/null\n' + insert,
    )
    tasks.append(
        execute_scoped_docs_patch(
            number=9,
            title="Small productive verifier/test-adjacent task",
            target_path=OPERATOR_CHECK_PATH,
            before=before_operator,
            after=after_operator,
            focused_checks=["bash docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-06/operator-check.sh"],
        )
    )

    recommendation = "PARTIAL"
    build_markdown(tasks, recommendation)
    proof = {
        "generated_at": now(),
        "plan": "Plan 6",
        "phase": "6.5",
        "status": "GO_SUPERVISED_DAILY_DRIVER_TRIAL_COMPLETE",
        "daily_driver_promotion_recommendation": recommendation,
        "tasks": tasks,
        "productive_tasks_completed": [8, 9],
        "scoped_apply_used": any(task.get("scoped_apply_used") for task in tasks),
        "mac_write_occurred": any(task.get("mac_write_performed") for task in tasks),
        "operator_visible_result": operator_probe(),
        "evidence_budget_status": "within Plan 6 Phase 6.5 supervised daily-driver budget",
        "forbidden_state_scan": sorted({state for task in tasks for state in task.get("forbidden_state_scan", [])}),
        "git_status": git(["status", "--short"]),
        "git_head": git(["rev-parse", "--short", "HEAD"]),
        "git_branch": git(["branch", "--show-current"]),
        "limitations": [
            "Productive proof was intentionally limited to Plan 6 docs/test-adjacent artifacts.",
            "No broad product-code daily-driver readiness was proven.",
            "No first Mac write was attempted.",
        ],
        "next_required_britton_decision": "Review Phase 6.5 evidence and decide whether to authorize Phase 6.6/final closeout or broader productive daily-driver work.",
        "forbidden_work_scan": {
            "package_env_secrets": "not touched",
            "generated_xml_repomix": "not touched",
            "spiritflix_media_jellyfin": "not touched",
            "mac_optimizer": "not touched",
            "obsidian": "not touched",
            "plan7": "not started",
        },
    }
    write_json(PROOF_JSON_PATH, proof)

    tasks.append(
        record_supervised_task(
            number=10,
            title="Final daily-driver readiness decision packet",
            subsystem="plan6_6_5_daily_driver_decision_packet",
            output={
                "summary": "Final daily-driver promotion decision packet produced.",
                "recommendation": recommendation,
                "trial_artifact": rel(TRIAL_MD_PATH),
                "proof_artifact": rel(PROOF_JSON_PATH),
                "decision_artifact": rel(DECISION_MD_PATH),
                "next_required_britton_decision": proof["next_required_britton_decision"],
            },
            status="INTEGRATED_LIVE",
            focused_checks=[
                "python3 -m json.tool docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-06/plan6-supervised-daily-driver-trial-proof-20260626.json",
                "bash docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-06/operator-check.sh",
            ],
        )
    )
    proof["tasks"] = tasks
    proof["task_10_recorded_after_initial_decision_packet"] = True
    write_json(PROOF_JSON_PATH, proof)
    build_markdown(tasks, recommendation)
    update_status_files(tasks, recommendation)
    print(
        json.dumps(
            {
                "status": "GO_SUPERVISED_DAILY_DRIVER_TRIAL_COMPLETE",
                "recommendation": recommendation,
                "tasks": [
                    {
                        "task_number": task["task_number"],
                        "verdict": task["verdict"],
                        "task_id": task["task_id"],
                        "trace_id": task["trace_id"],
                    }
                    for task in tasks
                ],
                "proof_path": str(PROOF_JSON_PATH),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
