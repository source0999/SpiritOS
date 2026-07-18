"""Production handlers for retained Campaign 3 coding lanes.

Every handler is advisory/read-only except the canonical coding executor.  A
handler may only contribute a bounded receipt to an existing long-running task;
it never applies a diff, creates an approval, or changes repository state.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
from datetime import UTC, datetime
from typing import Any, Callable

import httpx

from source_proxy.context.obsidian import query_obsidian_context
from source_proxy.decision.advisory_broker import (
    build_advisory_context_packet,
    validate_subagent_advisory_packet,
)
from source_proxy.decision.campaign_3_conflicts import resolve_coding_lane_conflicts_for_task
from source_proxy.decision.mac_integration import run_bound_mac_verification_for_task
from source_proxy.decision.scout_research import run_canonical_coding_research
from source_proxy.tasks.long_running import (
    begin_subsystem_integration_invocation,
    finish_subsystem_integration_result,
)

SCHEMA = "campaign-3/extended-lane-output/v1"


def _hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def _persist(task_id: str, *, lane_id: str, consumer: str, upstream: dict[str, Any], output: dict[str, Any], status: str) -> dict[str, Any]:
    invocation = begin_subsystem_integration_invocation(task_id, subsystem=lane_id.replace(".", "_"), upstream_state=upstream)
    body = {"schema_version": SCHEMA, "summary": str(output.get("summary") or output.get("reason") or status), "lane_id": lane_id, "invocation": invocation, "output": output, "output_hash": _hash(output), "mutation_authority": False}
    envelope = finish_subsystem_integration_result(task_id, subsystem=lane_id.replace(".", "_"), consumer_subsystem=consumer, upstream_state=upstream, output=body, status=status, changed_state_fields=[f"ast_snapshot.{lane_id.replace('.', '_')}_consumed"], failure_reason=None if status == "INTEGRATED_LIVE" else str(output.get("reason") or status))
    return {"status": status, "lane_id": lane_id, "receipt": body, "task": envelope["task"]}


async def invoke_scout(task_id: str, *, query: str, required: bool = True) -> dict[str, Any]:
    result = await run_canonical_coding_research(task_id=task_id, query=query)
    used = result.get("status") == "used" and bool(result.get("sources"))
    status = "INTEGRATED_LIVE" if used else ("BLOCKED_ENV" if required else "DEGRADED")
    return _persist(task_id, lane_id="extended.scout-research", consumer="canonical_context_broker", upstream={"task_id": task_id, "query_hash": _hash(query), "required": required}, output={"summary": result.get("reason"), "research": result, "source_count": len(result.get("sources") or [])}, status=status)


def invoke_obsidian(task_id: str, *, query: str, required: bool = True) -> dict[str, Any]:
    result = query_obsidian_context(query)
    used = result.get("status") == "used" and bool(result.get("notes"))
    status = "INTEGRATED_LIVE" if used else ("BLOCKED_ENV" if required else "DEGRADED")
    return _persist(task_id, lane_id="extended.obsidian-knowledge", consumer="canonical_context_broker", upstream={"task_id": task_id, "query_hash": _hash(query), "required": required}, output={"summary": result.get("status"), "obsidian": result, "note_count": len(result.get("notes") or [])}, status=status)


def invoke_mac(task_id: str, *, source_commit: str, source_worktree: str, timeout_seconds: int = 120) -> dict[str, Any]:
    result = run_bound_mac_verification_for_task(task_id, source_commit=source_commit, source_worktree=source_worktree, timeout_seconds=timeout_seconds)
    # The Mac integration itself persists a causal record; this wrapper supplies
    # the registry's explicit verifier-consumption record.
    return _persist(task_id, lane_id="extended.mac-worker", consumer="platform_verifier", upstream={"task_id": task_id, "source_commit": source_commit, "source_worktree": source_worktree}, output={"summary": result["status"], "mac": {"status": result.get("status"), "receipt": result.get("receipt")}}, status="INTEGRATED_LIVE" if result["status"] == "INTEGRATED_LIVE" else "BLOCKED_ENV")


async def _ollama(prompt: str, *, model: str, timeout_seconds: float) -> dict[str, Any]:
    base=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    payload={"model":model,"prompt":prompt,"stream":False,"options":{"temperature":0}}
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response=await client.post(base+"/api/generate",json=payload)
            response.raise_for_status(); data=response.json()
    except Exception as error:
        return {"status":"blocked","reason":"context_model_unavailable","error_type":type(error).__name__,"endpoint":base}
    text=str(data.get("response") or "").strip()
    return {"status":"used" if text else "blocked","reason":"context_model_output_observed" if text else "context_model_empty_output","model":model,"response_sha256":_hash(text),"response_chars":len(text),"endpoint":base}


async def invoke_context_model(task_id: str, *, task: str, model: str = "qwen2.5-coder:14b", required: bool = True) -> dict[str, Any]:
    result=await _ollama("Provide a concise read-only implementation risk assessment for this coding task:\n"+task, model=model, timeout_seconds=180)
    status="INTEGRATED_LIVE" if result["status"] == "used" else ("BLOCKED_ENV" if required else "DEGRADED")
    return _persist(task_id,lane_id="extended.context-model",consumer="canonical_context_broker",upstream={"task_id":task_id,"task_hash":_hash(task),"model":model,"required":required},output={"summary":result["reason"],"model_receipt":result},status=status)


async def invoke_subagent(task_id: str, *, task: str, model: str = "qwen2.5-coder:14b", required: bool = True) -> dict[str, Any]:
    result=await _ollama("Act as the retained safety reviewer. Return a concise advisory-only safety finding for:\n"+task, model=model, timeout_seconds=180)
    packet={"packet_id":"campaign3-safety-"+hashlib.sha256(task_id.encode()).hexdigest()[:16],"packet_type":"safety_review","role":"safety_reviewer","summary":result.get("reason","subagent unavailable"),"findings":["model_output_sha256="+str(result.get("response_sha256") or "unavailable")],"requested_actions":[]}
    validation=validate_subagent_advisory_packet(packet).to_dict()
    advisory=build_advisory_context_packet([validate_subagent_advisory_packet(packet)])
    status="INTEGRATED_LIVE" if result["status"] == "used" and validation["status"] == "accepted" else ("BLOCKED_ENV" if required else "DEGRADED")
    return _persist(task_id,lane_id="extended.retained-sub-agent",consumer="independent_reviewer",upstream={"task_id":task_id,"task_hash":_hash(task),"role":"safety_reviewer","required":required},output={"summary":result["reason"],"model_receipt":result,"validation":validation,"advisory_context":advisory},status=status)


def invoke_platform_verifier(task_id: str, *, mac_receipt: dict[str, Any], local_diff_check: bool) -> dict[str, Any]:
    passed=bool(mac_receipt.get("status") == "INTEGRATED_LIVE" and local_diff_check)
    return _persist(task_id,lane_id="extended.platform-verifier",consumer="independent_verifier",upstream={"task_id":task_id,"mac_receipt_hash":_hash(mac_receipt),"local_diff_check":local_diff_check},output={"summary":"platform_evidence_reconciled" if passed else "platform_evidence_incomplete","mac_status":mac_receipt.get("status"),"local_diff_check":local_diff_check},status="INTEGRATED_LIVE" if passed else "BLOCKED_ENV")


def resolve_conflict(task_id: str, *, claims: list[dict[str, Any]]) -> dict[str, Any]:
    return resolve_coding_lane_conflicts_for_task(task_id, claims=claims)


def build_diagnosis(task_id: str, *, lane_receipts: list[dict[str, Any]]) -> dict[str, Any]:
    statuses={str(item.get("lane_id") or item.get("status") or "unknown"):str(item.get("status") or "unknown") for item in lane_receipts}
    output={"summary":"campaign_3_diagnosis_envelope","created_at":datetime.now(UTC).isoformat(),"lane_statuses":statuses,"receipt_hashes":[_hash(item.get("receipt") or item) for item in lane_receipts],"mutation_authority":False}
    return _persist(task_id,lane_id="extended.diagnosis-envelope",consumer="campaign_3_read_only_diagnosis",upstream={"task_id":task_id,"lane_count":len(lane_receipts)},output=output,status="INTEGRATED_LIVE")


def run(coro: Any) -> Any:
    """Small synchronous boundary for API handlers; rejects nested event loops."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    raise RuntimeError("extended_lane_async_call_requires_await")
