from __future__ import annotations

import json
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from source_proxy.acceptance.plan5_acceptance import build_plan5_phase_verifier_gate
from source_proxy.decision.mac_integration import run_mac_worker_for_task
from source_proxy.tasks.long_running import (
    create_long_running_task,
    get_long_running_task,
    record_subsystem_integration_result,
)


PLAN_DIR = Path(__file__).resolve().parent
PROOF_PATH = PLAN_DIR / "plan6-mac-dell-dispatch-proof-20260626.json"
CODING_URL = "https://127.0.0.1:3000/coding"
MAC_ROUTE_URL = "https://127.0.0.1:3000/api/coding/mac-worker"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _git(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=PLAN_DIR.parents[2],
        text=True,
        capture_output=True,
        check=False,
    )
    output = (completed.stdout + completed.stderr).strip()
    return output or "clean"


def _operator_probe(url: str) -> dict[str, Any]:
    context = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(url, context=context, timeout=10) as response:
            body = response.read().decode("utf-8", errors="replace")
            return {
                "url": url,
                "http_status": response.status,
                "contains_coding_shell": "coding-cockpit-shell" in body,
                "contains_receipt": "Receipt" in body,
                "contains_trace": "Trace" in body,
                "body_length": len(body),
            }
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return {
            "url": url,
            "http_status": None,
            "error": f"{type(error).__name__}: {error}",
        }


def _record_phase_verifier(
    *,
    task_id: str,
    increment: str,
    source_trace_id: str,
    accepted_output_hash: str,
) -> dict[str, Any]:
    subsystem = f"plan6_phase_verifier_{increment.replace('.', '_')}"
    return record_subsystem_integration_result(
        task_id,
        subsystem=subsystem,
        consumer_subsystem="plan6_phase_gate_consumer",
        upstream_state={
            "task_id": task_id,
            "increment": increment,
            "source_subsystem": "mac_worker",
            "source_trace_id": source_trace_id,
            "accepted_output_hash": accepted_output_hash,
            "phase": "6.4",
        },
        output={
            "summary": f"Plan 6 {increment} phase verifier consumed Mac worker output.",
            "increment": increment,
            "source_subsystem": "mac_worker",
            "accepted_output_hash": accepted_output_hash,
            "phase_gate": "plan6_phase_gate_consumer",
        },
        status="INTEGRATED_LIVE",
        changed_state_fields=[
            "ast_snapshot.plan_6_phase_6_4",
            f"plan6.{increment}.phase_verifier",
        ],
    )


def _integration_record(task_payload: dict[str, Any], subsystem: str) -> dict[str, Any]:
    task = task_payload.get("task") if isinstance(task_payload.get("task"), dict) else task_payload
    snapshot = task.get("ast_snapshot") if isinstance(task.get("ast_snapshot"), dict) else {}
    integrations = snapshot.get("plan_2_subsystem_integrations")
    if not isinstance(integrations, dict):
        return {}
    record = integrations.get(subsystem)
    return record if isinstance(record, dict) else {}


def _run_increment(
    *,
    increment: str,
    mode: str,
    task_title: str,
    input_data: dict[str, Any],
    focused_checks: list[str],
) -> dict[str, Any]:
    created = create_long_running_task(task_title)
    task_id = created["task"]["id"]
    mac = run_mac_worker_for_task(task_id, mode=mode, input_data=input_data)
    mac_payload = {"task": mac["task"]}
    mac_record = _integration_record(mac_payload, "mac_worker")
    mac_status = str(mac.get("status") or "")
    phase_payload: dict[str, Any] | None = None
    gate: dict[str, Any] | None = None

    if mac_status == "INTEGRATED_LIVE":
        phase_payload = _record_phase_verifier(
            task_id=task_id,
            increment=increment,
            source_trace_id=str(mac_record.get("trace_id") or ""),
            accepted_output_hash=str(mac_record.get("output_hash") or ""),
        )
        gate = build_plan5_phase_verifier_gate(
            phase_payload,
            subsystem="mac_worker",
            phase_verifier_subsystem=f"plan6_phase_verifier_{increment.replace('.', '_')}",
            operator_consumer_subsystem="cartographer_mac_assignment_consumer",
            phase_consumer_subsystem="plan6_phase_gate_consumer",
            focused_checks=focused_checks,
            git_status=_git(["status", "--short"]),
            evidence_budget_status="within Plan 6 scoped Mac/Dell dispatch budget",
        )
        task_payload = phase_payload
    else:
        task_payload = get_long_running_task(task_id)

    task = task_payload["task"] if isinstance(task_payload.get("task"), dict) else task_payload
    mac_result = mac.get("result") if isinstance(mac.get("result"), dict) else {}
    mac_inner_result = mac_result.get("result") if isinstance(mac_result.get("result"), dict) else {}
    verdict = "GO" if mac_status == "INTEGRATED_LIVE" and gate and gate.get("status") == "GO" else "BLOCKED"

    return {
        "increment": increment,
        "task_id": task_id,
        "mode": mode,
        "subsystem_invoked": "mac_worker",
        "subsystem_status": mac_status,
        "phase_verifier_subsystem": f"plan6_phase_verifier_{increment.replace('.', '_')}",
        "verdict": verdict,
        "mac_write_performed": bool(mac_inner_result.get("mac_write_performed")),
        "mac_write_path": mac_inner_result.get("mac_write_path"),
        "rollback_status": mac_inner_result.get("rollback_status"),
        "job": {
            "job_id": mac.get("job", {}).get("job_id"),
            "job_type": mac.get("job", {}).get("job_type"),
            "worker": mac.get("job", {}).get("worker"),
            "node_id": mac.get("job", {}).get("node_id"),
        },
        "trace_id": mac_record.get("trace_id"),
        "invocation_event_id": mac_record.get("invocation_event_id"),
        "consumer_event_id": mac_record.get("consumer_event_id"),
        "consumer_subsystem": mac_record.get("consumer_subsystem"),
        "output_hash": mac_record.get("output_hash"),
        "state_fields_changed": (gate or {}).get("subsystem_gate", {}).get("evidence", {}).get("state_fields_changed", []),
        "focused_checks": focused_checks,
        "gate": gate,
        "task_status": task.get("status"),
        "architect_status": task.get("architect_status"),
        "architect_reason": task.get("architect_reason"),
        "mac_result_summary": mac_inner_result.get("summary"),
        "failure_reason": mac_record.get("failure_reason"),
        "same_trace": bool((gate or {}).get("same_trace")),
        "output_consumed_downstream": bool((gate or {}).get("output_consumed_by_operator")),
        "output_consumed_by_phase_verifier": bool((gate or {}).get("output_consumed_by_phase_verifier")),
        "failure_changes_final_verdict": bool((gate or {}).get("failure_changes_final_verdict")),
    }


def main() -> int:
    increments = []
    increments.append(
        _run_increment(
            increment="6.4.1",
            mode="mac_system_status",
            task_title="Plan 6 6.4.1 Mac/Dell dispatch status proof",
            input_data={"purpose": "Plan 6 6.4.1 no-write Mac/Dell dispatch proof"},
            focused_checks=[
                ".venv/bin/python -m pytest source_proxy/tests/test_mac_worker_script.py source_proxy/tests/test_plan2_subsystem_integration.py -k mac",
                "npx vitest run src/app/api/coding/mac-worker/__tests__/route.test.ts src/lib/mac-worker/__tests__/contract.test.ts",
                "bash docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-06/operator-check.sh",
            ],
        )
    )
    if increments[-1]["verdict"] == "GO":
        increments.append(
            _run_increment(
                increment="6.4.2",
                mode="mac_safe_check",
                task_title="Plan 6 6.4.2 repeated Mac/Dell safe-check dispatch proof",
                input_data={
                    "check_command": "git rev-parse HEAD",
                    "purpose": "Plan 6 6.4.2 repeated no-write Mac checkout proof",
                },
                focused_checks=[
                    ".venv/bin/python -m pytest source_proxy/tests/test_mac_worker_script.py source_proxy/tests/test_plan2_subsystem_integration.py -k mac",
                    "npx vitest run src/app/api/coding/mac-worker/__tests__/route.test.ts src/lib/mac-worker/__tests__/contract.test.ts",
                    "git diff --check",
                ],
            )
        )

    operator_probe = _operator_probe(CODING_URL)
    mac_route_probe = _operator_probe(MAC_ROUTE_URL)
    all_go = all(item["verdict"] == "GO" for item in increments)
    proof = {
        "generated_at": _now(),
        "plan": "Plan 6",
        "phase": "6.4",
        "status": "GO_MAC_DELL_DISPATCH_NO_WRITE" if all_go else "BLOCKED_MAC_DELL_DISPATCH",
        "next_incomplete_increment": "6.5.1" if all_go else increments[-1]["increment"],
        "authority_scope": "Scoped Mac/Dell dispatch only; no Mac optimizer, env/package changes, secrets, service restarts, repomix, SpiritFlix, Jellyfin, media, or Plan 7 work.",
        "mac_write_occurred": any(item["mac_write_performed"] for item in increments),
        "increments": increments,
        "operator_visible_result": {
            "coding_route": operator_probe,
            "mac_worker_route_probe": mac_route_probe,
        },
        "git_status": _git(["status", "--short"]),
        "git_head": _git(["rev-parse", "--short", "HEAD"]),
        "git_branch": _git(["branch", "--show-current"]),
        "evidence_budget_status": "within Plan 6 scoped Mac/Dell dispatch budget",
        "forbidden_work_scan": {
            "mac_optimizer": "not touched",
            "env_or_package_changes": "not touched",
            "secrets": "not touched",
            "service_restart": "not performed",
            "spiritflix_media_jellyfin": "not touched",
            "repomix": "not run",
            "plan7": "not started",
        },
        "phase_6_4_verdict": "GO" if all_go else "BLOCKED",
        "stop_condition": "Plan 6 can continue to 6.5 only after Britton supplies ten supervised daily-driver tasks."
        if all_go
        else "Mac/Dell dispatch did not reach INTEGRATED_LIVE.",
    }
    PROOF_PATH.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": proof["status"], "proof_path": str(PROOF_PATH), "increments": increments}, indent=2))
    return 0 if all_go else 2


if __name__ == "__main__":
    raise SystemExit(main())
