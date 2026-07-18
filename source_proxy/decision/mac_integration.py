from __future__ import annotations

import json
import os
import subprocess
import time
import hashlib
import shlex
from typing import Any
from uuid import uuid4

MAC_INTEGRATION_VERSION = "source-proxy-plan2-mac-integration-v1"
MAC_WORKER_NODE_ID = "spirit-mac-mini"
DEFAULT_MAC_REPO = "$HOME/spiritos-worker/SpiritOS"


def _ssh_alias() -> str:
    return os.environ.get("SPIRIT_MACMINI_SSH_ALIAS", "spirit-mac-mini").strip() or "spirit-mac-mini"


def _remote_repo() -> str:
    return os.environ.get("SPIRIT_MACMINI_REPO_PATH", DEFAULT_MAC_REPO).strip() or DEFAULT_MAC_REPO


def _tailscale_host() -> str:
    return os.environ.get("SPIRIT_MACMINI_TAILSCALE_HOST", "").strip()


def _known_host_alias() -> str:
    return os.environ.get("SPIRIT_MACMINI_HOSTKEY_ALIAS", "10.0.0.147").strip()


def _gateway_ssh_alias() -> str:
    """Optional registered relay when the control plane lacks the Mac key."""
    return os.environ.get("SPIRIT_MACMINI_GATEWAY_SSH_ALIAS", "").strip()


def _run_mac_worker_job(job: dict[str, Any], timeout_seconds: int = 45) -> dict[str, Any]:
    if timeout_seconds <= 0:
        raise ValueError("mac_worker_timeout_invalid")
    remote_repo = _remote_repo()
    mac_command = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=8",
        "-o",
        "HostKeyAlias=" + _known_host_alias(),
    ]
    if _tailscale_host():
        mac_command.extend(["-o", "HostName=" + _tailscale_host()])
    mac_command.extend([
        _ssh_alias(),
        f"cd {shlex.quote(remote_repo)} && python3 scripts/mac-worker/spirit_mac_worker.py",
    ])
    gateway = _gateway_ssh_alias()
    command = (
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", gateway, shlex.join(mac_command)]
        if gateway
        else mac_command
    )
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            input=json.dumps(job),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        return {"job_id": job["job_id"], "job_type": job["job_type"], "success": False, "error": "mac_worker_timeout", "stdout": str(error.stdout or ""), "stderr": str(error.stderr or ""), "duration_ms": int((time.monotonic() - started) * 1000)}
    except OSError as error:
        return {"job_id": job["job_id"], "job_type": job["job_type"], "success": False, "error": f"mac_worker_process_error:{type(error).__name__}", "stdout": "", "stderr": str(error), "duration_ms": int((time.monotonic() - started) * 1000)}
    elapsed_ms = int((time.monotonic() - started) * 1000)
    if completed.returncode != 0:
        return {
            "job_id": job["job_id"],
            "job_type": job["job_type"],
            "success": False,
            "error": completed.stderr.strip() or completed.stdout.strip() or f"Mac worker exited {completed.returncode}",
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "duration_ms": elapsed_ms,
        }
    try:
        parsed = json.loads(completed.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as error:
        return {
            "job_id": job["job_id"],
            "job_type": job["job_type"],
            "success": False,
            "error": f"mac_worker_json_parse_failed:{type(error).__name__}",
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "duration_ms": elapsed_ms,
        }
    return parsed


def _status_for_result(result: dict[str, Any]) -> str:
    if result.get("success") is True:
        return "INTEGRATED_LIVE"
    error = str(result.get("error") or "").lower()
    if "ssh" in error or "connect" in error or "timed out" in error:
        return "BLOCKED_ENV"
    return "NEEDS_FIX"


def run_mac_worker_for_task(
    task_id: str,
    *,
    mode: str,
    input_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from source_proxy.tasks.long_running import (
        begin_subsystem_integration_invocation,
        finish_subsystem_integration_result,
    )
    job_type_by_mode = {
        "mac_system_status": "system_status",
        "mac_safe_check": "run_safe_check",
        "mac_search_packet": "repo_context_search",
        "mac_isolated_write_proof": "mac_isolated_write_proof",
    }
    job_type = job_type_by_mode.get(mode)
    if job_type is None:
        raise ValueError(f"Unsupported Mac integration mode: {mode}")
    upstream_state = {
        "task_id": task_id,
        "worker": "mac",
        "mode": mode,
        "job_type": job_type,
        "input_keys": sorted((input_data or {}).keys()),
        "integration_version": MAC_INTEGRATION_VERSION,
    }
    invocation = begin_subsystem_integration_invocation(
        task_id,
        subsystem="mac_worker",
        upstream_state=upstream_state,
    )
    job = {
        "job_id": f"mac-{mode}-{uuid4().hex[:12]}",
        "job_type": job_type,
        "input": input_data or {},
        "node_id": MAC_WORKER_NODE_ID,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
        "job_envelope_version": "source-proxy-mac-worker-job-v1",
        "trace_id": invocation["trace_id"],
        "invocation_event_id": invocation["invocation_event_id"],
        "consumer_subsystem": "cartographer_mac_assignment_consumer",
        "task_id": task_id,
        "worker": "mac",
    }
    result = _run_mac_worker_job(job)
    status = _status_for_result(result)
    summary = {
        "summary": "Mac worker result consumed downstream.",
        "mode": mode,
        "worker": "mac",
        "job_id": job["job_id"],
        "job_type": job_type,
        "trace_id": invocation["trace_id"],
        "invocation_event_id": invocation["invocation_event_id"],
        "result": result,
        "mac_write_performed": bool((result.get("result") or {}).get("mac_write_performed")),
        "mac_write_path": (result.get("result") or {}).get("mac_write_path"),
        "rollback_status": (result.get("result") or {}).get("rollback_status"),
    }
    payload = finish_subsystem_integration_result(
        task_id,
        subsystem="mac_worker",
        consumer_subsystem="cartographer_mac_assignment_consumer",
        upstream_state=upstream_state,
        output=summary,
        status=status,
        changed_state_fields=["ast_snapshot.plan_2_mac_worker"],
        failure_reason=None if status == "INTEGRATED_LIVE" else str(result.get("error") or status),
    )
    return {
        "status": status,
        "job": job,
        "result": result,
        "task": payload["task"],
    }


def run_bound_mac_verification(
    task_id: str,
    *,
    source_commit: str,
    source_worktree: str,
    check_command: str = "git diff --check",
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    """Dispatch a source-bound macOS check without granting write authority.

    The returned result is deliberately not a successful lane claim unless the
    Mac worker reports the exact source commit and a content hash for its logs.
    """
    if len(source_commit) != 40 or any(char not in "0123456789abcdef" for char in source_commit):
        raise ValueError("mac_worker_source_commit_invalid")
    if not task_id.strip() or not source_worktree.strip():
        raise ValueError("mac_worker_source_binding_missing")
    if check_command not in {"git diff --check", "git rev-parse HEAD", "npx --no-install tsc --noEmit --pretty false"}:
        raise ValueError("mac_worker_check_not_allowlisted")
    job = {
        "job_id": f"mac-platform-{uuid4().hex}", "job_type": "run_safe_check",
        "node_id": MAC_WORKER_NODE_ID, "task_id": task_id,
        "job_envelope_version": "campaign-3/mac-worker/v1",
        "input": {"repo_path": _remote_repo(), "check_command": check_command, "expected_source_commit": source_commit, "source_worktree": source_worktree, "write_authority": False},
    }
    result = _run_mac_worker_job(job, timeout_seconds=timeout_seconds)
    result_body = result.get("result") if isinstance(result.get("result"), dict) else {}
    observed_commit = str(result_body.get("head") or result_body.get("source_commit") or "")
    serialized = json.dumps(result, sort_keys=True, separators=(",", ":"), default=str)
    log_hash = "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    bound = result.get("success") is True and observed_commit == source_commit
    return {"schema_version": "campaign-3/mac-verification-receipt/v1", "task_id": task_id, "job": job, "result": result, "source_commit": source_commit, "observed_commit": observed_commit, "log_hash": log_hash, "source_bound": bound, "verdict_effect": "mac_verification_passed" if bound else "mac_verification_unavailable_or_source_mismatch", "write_authority": False}


def run_bound_mac_verification_for_task(
    task_id: str,
    *,
    source_commit: str,
    source_worktree: str,
    check_command: str = "git diff --check",
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    """Persist an exact Mac receipt and its verifier consumption with task truth."""
    from source_proxy.tasks.long_running import (
        begin_subsystem_integration_invocation,
        finish_subsystem_integration_result,
    )
    upstream = {
        "task_id": task_id,
        "source_commit": source_commit,
        "source_worktree": source_worktree,
        "check_command": check_command,
        "transport": "registered_tailscale",
    }
    invocation = begin_subsystem_integration_invocation(
        task_id, subsystem="campaign_3_mac_worker", upstream_state=upstream
    )
    receipt = run_bound_mac_verification(
        task_id,
        source_commit=source_commit,
        source_worktree=source_worktree,
        check_command=check_command,
        timeout_seconds=timeout_seconds,
    )
    receipt["invocation"] = invocation
    status = "INTEGRATED_LIVE" if receipt["source_bound"] else "BLOCKED_ENV"
    envelope = finish_subsystem_integration_result(
        task_id,
        subsystem="campaign_3_mac_worker",
        consumer_subsystem="coding_verifier_mac_evidence_consumer",
        upstream_state=upstream,
        output={
            "summary": receipt["verdict_effect"],
            "mac_receipt": receipt,
            "source_commit": source_commit,
            "log_hash": receipt["log_hash"],
        },
        status=status,
        changed_state_fields=["ast_snapshot.campaign_3_mac_worker"],
        failure_reason="" if status == "INTEGRATED_LIVE" else str(receipt["verdict_effect"]),
    )
    return {"status": status, "receipt": receipt, "task": envelope["task"]}


def run_mac_platform_preflight_for_task(
    task_id: str,
    *,
    source_commit: str,
    source_worktree: str,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    """Persist real, read-only Apple-tool evidence bound to an exact source."""
    if len(source_commit) != 40 or any(char not in "0123456789abcdef" for char in source_commit):
        raise ValueError("mac_worker_source_commit_invalid")
    from source_proxy.tasks.long_running import (
        begin_subsystem_integration_invocation,
        finish_subsystem_integration_result,
    )
    upstream = {
        "task_id": task_id, "source_commit": source_commit,
        "source_worktree": source_worktree, "transport": "registered_tailscale",
        "job_type": "mac_platform_preflight",
    }
    invocation = begin_subsystem_integration_invocation(
        task_id, subsystem="campaign_3_mac_platform_preflight", upstream_state=upstream
    )
    job = {
        "job_id": f"mac-platform-preflight-{uuid4().hex}",
        "job_type": "mac_platform_preflight", "node_id": MAC_WORKER_NODE_ID,
        "task_id": task_id, "job_envelope_version": "campaign-3/mac-worker/v1",
        "input": {"repo_path": _remote_repo(), "expected_source_commit": source_commit,
                  "source_worktree": source_worktree, "write_authority": False},
    }
    result = _run_mac_worker_job(job, timeout_seconds=timeout_seconds)
    body = result.get("result") if isinstance(result.get("result"), dict) else {}
    observed_commit = str(body.get("head") or "")
    serialized = json.dumps(result, sort_keys=True, separators=(",", ":"), default=str)
    receipt = {
        "schema_version": "campaign-3/mac-platform-preflight-receipt/v1",
        "task_id": task_id, "job": job, "result": result,
        "source_commit": source_commit, "observed_commit": observed_commit,
        "log_hash": "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        "source_bound": result.get("success") is True and observed_commit == source_commit,
        "write_authority": False, "invocation": invocation,
    }
    status = "INTEGRATED_LIVE" if receipt["source_bound"] else "BLOCKED_ENV"
    envelope = finish_subsystem_integration_result(
        task_id, subsystem="campaign_3_mac_platform_preflight",
        consumer_subsystem="coding_verifier_mac_evidence_consumer", upstream_state=upstream,
        output={"summary": "mac_platform_preflight_passed" if receipt["source_bound"] else "mac_platform_preflight_unavailable", "mac_receipt": receipt},
        status=status, changed_state_fields=["ast_snapshot.campaign_3_mac_platform_preflight"],
        failure_reason="" if status == "INTEGRATED_LIVE" else "mac_platform_preflight_unavailable",
    )
    return {"status": status, "receipt": receipt, "task": envelope["task"]}


def run_mac_cancellation_probe_for_task(
    task_id: str,
    *,
    source_commit: str,
    timeout_seconds: int = 1,
    delay_seconds: int = 3,
) -> dict[str, Any]:
    """Persist a controlled no-write timeout; a timeout never becomes success."""
    from source_proxy.tasks.long_running import (
        begin_subsystem_integration_invocation,
        finish_subsystem_integration_result,
    )
    upstream = {"task_id": task_id, "source_commit": source_commit, "transport": "registered_tailscale", "job_type": "mac_cancellation_probe"}
    invocation = begin_subsystem_integration_invocation(task_id, subsystem="campaign_3_mac_cancellation", upstream_state=upstream)
    job = {"job_id": f"mac-cancel-{uuid4().hex}", "job_type": "mac_cancellation_probe", "node_id": MAC_WORKER_NODE_ID, "task_id": task_id, "job_envelope_version": "campaign-3/mac-worker/v1", "input": {"delay_seconds": delay_seconds, "expected_source_commit": source_commit, "write_authority": False}}
    result = _run_mac_worker_job(job, timeout_seconds=timeout_seconds)
    serialized = json.dumps(result, sort_keys=True, separators=(",", ":"), default=str)
    timed_out = result.get("error") == "mac_worker_timeout"
    receipt = {"schema_version": "campaign-3/mac-cancellation-receipt/v1", "task_id": task_id, "job": job, "result": result, "source_commit": source_commit, "log_hash": "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest(), "timed_out": timed_out, "write_authority": False, "invocation": invocation}
    status = "BLOCKED_ENV" if timed_out else "NEEDS_FIX"
    envelope = finish_subsystem_integration_result(
        task_id, subsystem="campaign_3_mac_cancellation", consumer_subsystem="coding_verifier_mac_evidence_consumer", upstream_state=upstream,
        output={"summary": "mac_cancellation_timeout_observed" if timed_out else "mac_cancellation_probe_unexpected_result", "mac_receipt": receipt}, status=status,
        changed_state_fields=["ast_snapshot.campaign_3_mac_cancellation"], failure_reason="mac_worker_timeout" if timed_out else "mac_cancellation_probe_unexpected_result",
    )
    return {"status": status, "receipt": receipt, "task": envelope["task"]}
