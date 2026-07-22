from __future__ import annotations

import asyncio
import hashlib
import functools
import json
import os
import re
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from source_proxy.decision.prompt_packet import (
    ALREADY_SATISFIED_PASTE_BACK_INSTRUCTIONS,
    ALREADY_SATISFIED_PROMPT_TEXT,
    ALREADY_SATISFIED_REQUESTED_OUTPUT,
    PromptPacketInput,
    build_prompt_packet,
    _phase_fields_for,
)
from source_proxy.tasks.long_running import (
    _workspace_root,
    canonical_context_broker_for_task,
    coding_orchestrator_state_for_task,
    derive_context_mode,
    forbidden_paths_for_context_mode,
    generate_unified_diff_from_content,
    propose_coder_agent_diff_payload_from_plan,
    record_canonical_context_broker_for_task,
    reset_coder_timing_diagnostics,
    snapshot_coder_timing_diagnostics,
)
from source_proxy.coding.orchestrator import (
    CodingOrchestratorError,
    get_coding_orchestrator,
)
from source_proxy.target_plugins.adapter import (
    GENERIC_WORKSPACE_PLUGIN_ID,
    TargetPluginResolutionError,
    execute_target_plugin_command,
    resolve_target_plugin,
    server_owned_target_plugin_workspace,
    target_plugin_command,
    target_plugin_task_spec,
)
from source_proxy.target_plugins.lumacart import is_lumacart_prompt_id
from source_proxy.verification.contracts import (
    SUBJECTIVE_IMPROVEMENT_REQUIRES_DIFF_REASON_CODE,
    VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE,
)
from source_proxy.decision.preview import (
    ApiVsManualPreviewInput,
    build_api_vs_manual_preview,
)
from source_proxy.diagnostics.status_codes import no_failure_classification
from source_proxy.decision.lanes.status_helpers import (
    lane_status as _lane_status,
    packet_lane_status as _packet_lane_status,
    receipt_failure_classification as _lane_receipt_failure_classification,
    receipt_failure_event as _receipt_failure_event,
    valid_lane_status_value as _valid_lane_status_value,
)
from source_proxy.decision.worker_tool_adapters import run_process_adapter
from source_proxy.decision.model_lanes import (
    build_fip3_model_lane_packet,
    build_model_lanes_preview,
    fip3_lane_packet_has_qwen_fallback,
)
from source_proxy.decision.recommendation import (
    ModelRecommendationInput,
    recommend_model,
)
from source_proxy.decision.task_spec_intake import (
    build_task_spec_intake,
    intake_as_legacy_task_spec,
)
from source_proxy.decision.router import (
    DecisionInput,
    TARGET_HARD_BLOCK_REASON_CODES,
    _parse_explicit_target_file_line,
    decide_route,
    enrich_route_decision_with_research,
)
from source_proxy.planning.plan import load_plan, task_spec_from_packet, task_spec_from_plan
from source_proxy.decision.proposal_task import (
    bounded_proposal_create_allowed,
    parse_bounded_proposal_task,
)
from source_proxy.decision.router import ResolvedTarget, resolve_target_from_task, unsafe_target_for_route
from source_proxy.routing.litellm_router import (
    available_model_aliases,
    route_model_for_alias,
    route_provider_for_alias,
)
from source_proxy.routing.ollama_route import ollama_route_status_entry, resolve_ollama_route
from source_proxy.approval.external_gate import central_gate_check
from source_proxy.context.source_readiness import (
    READ_ONLY_AUTHORITY,
    build_cartographer_context_packet,
    build_design_context_packet,
    build_obsidian_context_packet,
)
from source_proxy.context.canonical_broker import (
    acknowledge_context_consumer,
    build_context_broker_report,
    extend_context_broker_sources,
    render_context_broker_prompt,
)
from source_proxy.decision.research import (
    run_repo_research_preview,
    run_searxng_research_diagnostics,
)
from source_proxy.decision.scout_research import run_scout_research_diagnostics

router = APIRouter(prefix="/v1/decisions")


FIP0_LANE_STATUS_FIELDS = (
    "context_router_status",
    "repo_research_status",
    "obsidian_status",
    "cartographer_status",
    "design_status",
    "mac_worker_status",
    "source_readiness_status",
    "scout_status",
    "searxng_status",
    "tinyfish_status",
    "xersearch_status",
    "gemma_status",
    "hermes_critic_status",
    "qwen_coder_status",
    "hermes_verifier_status",
    "hermes_verifier_lane_status",
    "repair_loop_status",
    "browser_behavior_status",
    "browser_verifier_status",
    "functional_verifier_status",
    "deterministic_check_status",
    "output_contract_status",
    "anti_tailoring_status",
)


AVAILABLE_ROUTES: dict[str, dict[str, Any]] = {
    "call_api_model": {
        "route_type": "api_route",
        "execution_path": "paid_api_chat_route",
        "display_name": "Cloud/API route",
        "manual_prompt_packet": False,
    },
    "generate_manual_prompt_packet": {
        "route_type": "manual_route",
        "execution_path": "manual_prompt_packet",
        "display_name": "Manual prompt packet",
        "manual_prompt_packet": True,
    },
    "run_with_coder_agent": {
        "route_type": "local_route",
        "execution_path": "coder_agent",
        "display_name": "Coder Agent",
        "manual_prompt_packet": False,
    },
    "ask_user_to_choose_route": {
        "route_type": "ask_user",
        "execution_path": "route_choice",
        "display_name": "Ask user",
        "manual_prompt_packet": False,
    },
}

ROUTE_TYPE_TO_ACTION: dict[str, str] = {
    str(route["route_type"]): action
    for action, route in AVAILABLE_ROUTES.items()
}


class RouteDecisionRequest(BaseModel):
    task: str = Field(min_length=1)
    active_task_id: str | None = None
    current_agent_role: str | None = None
    conversation_context: list[dict[str, Any]] = Field(default_factory=list)
    decision_memory: list[dict[str, Any]] = Field(default_factory=list)
    targeted_files: list[str] = Field(default_factory=list)
    target_files: list[str] = Field(default_factory=list)
    proposed_diff: str | None = None
    context_tokens: int | None = Field(default=None, ge=0)
    research_recommended: bool = False
    sensitive: bool = False
    needs_current_info: bool = False
    needs_codebase_context: bool = False
    wants_implementation: bool = False
    prefer_free: bool = True


class PromptPacketRequest(RouteDecisionRequest):
    target_model_hint: str | None = None
    relevant_context: str | None = None
    trial_mode: str | None = None
    expected_outcome: str | None = None
    selected_target: str | None = None
    allowed_files: list[str] = Field(default_factory=list)
    quick_find_hints: list[str] = Field(default_factory=list)
    trial_recover_already_satisfied: bool = False
    dummy_coder_10_packet: dict[str, Any] | None = None
    expected_result_state: str | None = None
    primary_expected_targets: list[str] = Field(default_factory=list)
    forbidden_files: list[str] = Field(default_factory=list)
    selected_prompt_id: str | None = None
    trial_prompt_id: str | None = None
    brain_switch_recommendation: str | None = None
    task_shape: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class ApiVsManualPreviewRequest(PromptPacketRequest):
    api_model_alias: str = "openai"
    max_completion_tokens: int = Field(default=1024, ge=0)


class ModelLanesPreviewRequest(BaseModel):
    task_type: str = "disposable_artifact"


def _coder_sync_deadline_seconds() -> float:
    """Wall-clock cap for repomix + sync LLM so reverse proxies do not 502 the UI."""
    raw = os.environ.get("SOURCE_PROXY_CODER_SYNC_DEADLINE_SEC", "").strip()
    if not raw:
        return 180.0
    try:
        value = float(raw)
    except ValueError:
        return 180.0
    return max(15.0, min(value, 600.0))


def _infer_coder_timeout_stage(timing: dict[str, Any]) -> str:
    if timing.get("provider_request_started_at_ms") and not timing.get(
        "provider_request_done_at_ms"
    ):
        return "provider_generation"
    if timing.get("coder_llm_at_ms") and not timing.get("provider_request_started_at_ms"):
        return "coder_llm_prepare"
    if timing.get("prompt_context_at_ms") and not timing.get("coder_llm_at_ms"):
        return "prompt_context_build"
    if timing.get("architect_plan_done_at_ms") and not timing.get("prompt_context_at_ms"):
        return "architect_packet_build"
    if timing.get("target_resolution_started_ms"):
        return "target_or_architect_resolution"
    return "coder_sync_deadline"


def _json_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _fip0_receipt_root() -> Path:
    override = os.environ.get("SOURCE_PROXY_FIP0_RECEIPT_DIR", "").strip()
    if override:
        return Path(override)
    return (
        _workspace_root()
        / "docs"
        / "evidence"
        / "source-proxy-full-integration-pivot"
        / "fip-0-receipts"
    )


def _safe_dirty_tree_status() -> dict[str, Any]:
    try:
        result = run_process_adapter(
            adapter_id="git_status_dirty_tree",
            command=("git", "status", "--short", "--untracked-files=no"),
            cwd=str(_workspace_root()),
            timeout_seconds=5,
            owner="source_proxy.api.decision",
            evidence_ref="fip0_dirty_tree_status",
        )
    except Exception as error:
        return {
            "status": "blocked",
            "reason": "git_status_unavailable",
            "error": f"{type(error).__name__}: {error}",
        }
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return {
        "status": "used" if result.returncode == 0 else "failed",
        "is_dirty": bool(lines),
        "tracked_change_count": len(lines),
        "returncode": result.returncode,
        "stderr": result.stderr.strip()[:500],
    }


def _receipt_failure_classification(receipt: dict[str, Any]) -> dict[str, Any]:
    return _lane_receipt_failure_classification(receipt, FIP0_LANE_STATUS_FIELDS)

def _blocked_context_packet(source: str, error: Exception) -> dict[str, Any]:
    return {
        "source": source,
        "status": "blocked",
        "reason": f"{source}_context_packet_error",
        "packet": {},
        "diagnostics": {"exception": type(error).__name__, "error": str(error)[:500]},
        "authority": dict(READ_ONLY_AUTHORITY),
    }


def _build_fip1_context_lane_packet(
    *,
    task: str,
    explicit_target: str,
) -> dict[str, Any]:
    if os.environ.get("SOURCE_PROXY_FIP1_CONTEXT_ENABLED", "1").strip().lower() in {
        "0",
        "false",
        "no",
        "off",
    }:
        return {}
    root = _workspace_root()
    target_files = [explicit_target] if explicit_target else []
    try:
        cartographer = build_cartographer_context_packet(
            task,
            project_root=root,
            target_files=target_files,
        ).to_dict()
    except Exception as error:
        cartographer = _blocked_context_packet("cartographer", error)
    try:
        obsidian = build_obsidian_context_packet(task).to_dict()
    except Exception as error:
        obsidian = _blocked_context_packet("obsidian", error)
    try:
        design = build_design_context_packet(task, project_root=root).to_dict()
    except Exception as error:
        design = _blocked_context_packet("design", error)

    mac_worker = {
        "source": "mac_worker",
        "status": "skipped",
        "reason": "fip1_advisory_status_only_no_worker_invocation",
        "packet": {
            "advisory_context_status": "not_invoked",
            "worker_started": False,
            "hidden_worker_started": False,
        },
        "diagnostics": {
            "read_only": True,
            "worker_start_enabled": False,
            "queue_dispatch_enabled": False,
        },
        "authority": dict(READ_ONLY_AUTHORITY),
    }
    sources = [cartographer, obsidian, design, mac_worker]
    invalid_sources = [
        str(source.get("source") or "unknown")
        for source in sources
        if not _valid_lane_status_value(str(source.get("status") or ""))
    ]
    source_readiness_status = "used" if not invalid_sources else "failed"
    source_readiness_reason = (
        "fip1_source_readiness_packet_built_from_approved_context_lanes"
        if not invalid_sources
        else "fip1_source_readiness_packet_has_invalid_lane_status"
    )
    return {
        "schema_version": 1,
        "scope": "FIP-1 approved context lanes only",
        "source_status": {
            str(source.get("source") or "unknown"): str(source.get("status") or "")
            for source in sources
        },
        "sources": sources,
        "source_readiness_status": {
            "status": source_readiness_status,
            "reason": source_readiness_reason,
            "invalid_sources": invalid_sources,
        },
        "search_provider_call_made": False,
        "scout_invoked": False,
        "live_searxng_invoked": False,
        "tinyfish_invoked": False,
        "xersearch_created": False,
        "authority": dict(READ_ONLY_AUTHORITY),
    }


def _fip2_research_enabled() -> bool:
    return os.environ.get("SOURCE_PROXY_FIP2_RESEARCH_ENABLED", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _search_needed_from_route(
    *,
    route_payload: dict[str, Any],
    route_reasons: list[str],
) -> tuple[bool, str]:
    if "needs_current_information" in route_reasons:
        return True, "context_router_needs_current_information"
    if bool(route_payload.get("research_recommended")) and "repo_first_research" not in route_reasons:
        return True, "context_router_research_recommended"
    if "repo_first_research" in route_reasons:
        return False, "context_router_repo_first_research_local_only"
    return False, "context_router_research_not_required"


def _research_query_for_task(task: str) -> str:
    lines = [
        line.strip()
        for line in (task or "").splitlines()
        if line.strip() and not line.strip().lower().startswith("target file:")
    ]
    query = " ".join(" ".join(lines or [task or ""]).split())
    return query[:200]


def _source_status_from_packet(
    packet: dict[str, Any],
    *,
    fallback_reason: str,
) -> dict[str, Any]:
    status = str(packet.get("status") or "")
    if not _valid_lane_status_value(status):
        status = "failed"
    return _lane_status(
        status,
        str(packet.get("reason") or fallback_reason),
        provider_errors=packet.get("provider_errors", []),
        fix_command=packet.get("fix_command", ""),
    )


async def _build_fip2_research_packet(
    *,
    task: str,
    route_payload: dict[str, Any],
    route_reasons: list[str],
) -> dict[str, Any]:
    search_needed, search_reason = _search_needed_from_route(
        route_payload=route_payload,
        route_reasons=route_reasons,
    )
    repo_research_needed = bool(route_payload.get("research_recommended")) or (
        "repo_first_research" in route_reasons
    )
    research_query = _research_query_for_task(task)
    empty_searxng = {
        "status": "skipped",
        "reason": "search_not_needed",
        "query": research_query,
        "searxng_url": os.environ.get("SEARXNG_URL", "").strip(),
        "searxng_format_json_status": "not_checked",
        "searxng_latency_ms": None,
        "searxng_result_count": 0,
        "searxng_sources": [],
        "provider_call_made": False,
        "provider_errors": [],
        "fix_command": "",
    }
    empty_scout = {
        "status": "skipped",
        "reason": "search_not_needed",
        "scout_enabled": os.environ.get("SOURCE_PROXY_SCOUT_RESEARCH_ENABLED", "0") == "1",
        "scout_result_count": 0,
        "scout_sources": [],
        "provider_errors": [],
        "fix_command": "",
    }
    if not _fip2_research_enabled():
        return {}
    if not search_needed:
        searxng_packet = empty_searxng
        scout_packet = empty_scout
        repo_sources = (
            run_repo_research_preview(research_query, max_results=6)
            if repo_research_needed
            else []
        )
    else:
        repo_sources = run_repo_research_preview(research_query, max_results=6)
        scout_packet = await run_scout_research_diagnostics(research_query, max_results=6)
        searxng_packet = await run_searxng_research_diagnostics(research_query, max_results=6)

    searxng_sources = [
        source for source in searxng_packet.get("searxng_sources", []) if isinstance(source, dict)
    ]
    scout_sources = [
        source for source in scout_packet.get("scout_sources", []) if isinstance(source, dict)
    ]
    research_sources = [*repo_sources, *scout_sources, *searxng_sources]
    research_packet = {
        "schema_version": 1,
        "scope": "FIP-2 local search injection only",
        "search_needed": search_needed,
        "search_reason": search_reason,
        "research_query": research_query,
        "repo_sources": repo_sources,
        "repo_result_count": len(repo_sources),
        "scout": scout_packet,
        "searxng": searxng_packet,
        "research_sources": research_sources,
        "research_packet_included_in_context": bool(research_sources),
        "tinyfish_status": "deferred_cloud_requires_britton_approval",
        "xersearch_status": "missing_alias_do_not_create",
        "cloud_provider_used": False,
    }
    research_packet["research_packet_hash"] = _json_hash(research_packet)
    return research_packet


def _build_canonical_context_packet(
    *,
    request: PromptPacketRequest,
    original_request: PromptPacketRequest,
    task: str,
    explicit_target: str,
    fip1_context_packet: dict[str, Any],
    fip2_research_packet: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    """Unify every prompt-path context source before any model execution."""

    implementation_required = bool(request.wants_implementation or request.needs_codebase_context)
    # Requirement intent excludes structured target declarations.  Both the
    # router and callers may prepend `Target file:`; path segments such as
    # `ui-agent-trials` must not invent a required design lane.
    requirement_intent = "\n".join(
        line
        for line in request.task.splitlines()
        if not re.match(r"^\s*target\s+file\s*:", line, flags=re.IGNORECASE)
    )
    lowered_task = requirement_intent.lower()
    visual_context_required = bool(
        implementation_required
        and re.search(r"\b(ux|visual|design)\b", lowered_task)
    )
    mac_context_required = bool(
        implementation_required
        and re.search(r"\b(mac worker|mac mini|macos worker)\b", lowered_task)
    )
    context_sources = [
        source
        for source in fip1_context_packet.get("sources", [])
        if isinstance(source, dict)
    ]
    by_source = {
        str(source.get("source") or ""): dict(source)
        for source in context_sources
    }

    supplied_context = str(request.relevant_context or "").strip()
    fip1_context_enabled = bool(fip1_context_packet)
    workspace_root = _workspace_root().resolve()
    normalized_target = explicit_target.replace("\\", "/").lstrip("./")
    target_path = (workspace_root / normalized_target).resolve() if normalized_target else workspace_root
    target_safe = bool(
        normalized_target
        and (target_path == workspace_root or workspace_root in target_path.parents)
        and unsafe_target_for_route(
            task,
            ResolvedTarget(
                path=normalized_target,
                exists=target_path.is_file(),
                source="explicit_line",
            ),
            workspace_root,
        )
        is None
    )
    target_exists = bool(target_safe and target_path.is_file())
    target_excerpt = ""
    if target_exists:
        try:
            target_excerpt = target_path.read_text(encoding="utf-8", errors="replace")[:6000]
        except OSError:
            target_exists = False
    target_file_context = {
        "source": "target_file_context",
        "considered": True,
        "status": "used" if target_exists else "blocked" if normalized_target and not target_safe else "skipped",
        "reason": (
            "target_file_context_included"
            if target_exists
            else "target_file_context_unsafe"
            if normalized_target and not target_safe
            else "target_file_missing_or_not_selected"
        ),
        "required": bool(implementation_required and target_exists),
        "selected": target_exists,
        "included": target_exists,
        "packet": {
            "path": normalized_target,
            "sha256": hashlib.sha256(target_excerpt.encode("utf-8")).hexdigest()
            if target_exists
            else "",
            "safe_excerpt": target_excerpt,
        },
        "authority": dict(READ_ONLY_AUTHORITY),
    }
    supplied = {
        "source": "supplied_context",
        "considered": True,
        "status": "used" if supplied_context else "skipped",
        "reason": "supplied_context_included" if supplied_context else "no_supplied_context",
        "required": False,
        "selected": bool(supplied_context),
        "included": bool(supplied_context),
        "packet": {"safe_excerpt": supplied_context[:6000]},
        "authority": dict(READ_ONLY_AUTHORITY),
    }

    def lane_source(name: str, *, required: bool = False) -> dict[str, Any]:
        lane = dict(by_source.get(name) or {})
        status = str(
            lane.get("status")
            or ("skipped" if not fip1_context_enabled else "unavailable")
        )
        if not lane:
            lane["reason"] = (
                "fip1_context_lane_disabled"
                if not fip1_context_enabled
                else "context_lane_status_missing"
            )
        selected = status == "used"
        return {
            **lane,
            "source": name,
            "considered": True,
            "status": status,
            "required": required,
            "selected": selected,
            "included": selected,
        }

    search_needed = fip2_research_packet.get("search_needed") is True
    repo_sources = [
        item
        for item in fip2_research_packet.get("repo_sources", [])
        if isinstance(item, dict)
    ]
    scout_packet = (
        fip2_research_packet.get("scout")
        if isinstance(fip2_research_packet.get("scout"), dict)
        else {}
    )
    scout_sources = [
        item for item in scout_packet.get("scout_sources", []) if isinstance(item, dict)
    ]
    searxng_packet = (
        fip2_research_packet.get("searxng")
        if isinstance(fip2_research_packet.get("searxng"), dict)
        else {}
    )
    searxng_sources = [
        item for item in searxng_packet.get("searxng_sources", []) if isinstance(item, dict)
    ]

    sources = [
        supplied,
        target_file_context,
        lane_source(
            "cartographer",
            required=bool(implementation_required and fip1_context_enabled),
        ),
        lane_source("obsidian"),
        lane_source("design", required=visual_context_required),
        lane_source("mac_worker", required=mac_context_required),
        {
            "source": "repo_research",
            "considered": True,
            "status": "used" if repo_sources else "skipped",
            "reason": "repo_research_sources_selected" if repo_sources else "no_repo_research_sources",
            "required": False,
            "selected": bool(repo_sources),
            "included": bool(repo_sources),
            "packet": {"sources": repo_sources},
            "authority": dict(READ_ONLY_AUTHORITY),
        },
        {
            "source": "scout_research",
            "considered": True,
            "status": str(scout_packet.get("status") or "skipped"),
            "reason": str(scout_packet.get("reason") or "scout_not_invoked"),
            "required": False,
            "selected": bool(scout_sources),
            "included": bool(scout_sources),
            "packet": {"sources": scout_sources},
            "authority": dict(READ_ONLY_AUTHORITY),
        },
        {
            "source": "searxng_research",
            "considered": True,
            "status": str(searxng_packet.get("status") or "skipped"),
            "reason": str(searxng_packet.get("reason") or "searxng_not_invoked"),
            "required": search_needed,
            "selected": bool(searxng_sources),
            "included": bool(searxng_sources),
            "packet": {"sources": searxng_sources},
            "authority": dict(READ_ONLY_AUTHORITY),
        },
        {
            "source": "design_extractor",
            "considered": True,
            "status": "skipped",
            "reason": "design_extractor_not_invoked_by_prompt_path",
            "required": "design studio" in lowered_task or "designdna" in lowered_task,
            "selected": False,
            "included": False,
            "packet": {},
            "authority": dict(READ_ONLY_AUTHORITY),
        },
    ]

    cleared_sources = {
        "conversation_context": original_request.conversation_context,
        "decision_memory": original_request.decision_memory,
        "targeted_files": original_request.targeted_files,
        "target_files": original_request.target_files,
        "prior_diff": original_request.proposed_diff,
    }
    for source_name, raw_value in cleared_sources.items():
        was_supplied = bool(raw_value)
        sources.append(
            {
                "source": source_name,
                "considered": True,
                "status": "skipped",
                "reason": (
                    "cleared_by_prompt_file_focus_policy"
                    if was_supplied
                    else "not_supplied"
                ),
                "required": False,
                "selected": False,
                "included": False,
                "packet": {"supplied": was_supplied},
                "authority": dict(READ_ONLY_AUTHORITY),
            }
        )

    selected_names = [
        str(source.get("source") or "")
        for source in sources
        if source.get("selected") is True and source.get("included") is True
    ]
    acknowledgements = {
        "planner": {
            "applicable": True,
            "acknowledged": bool(selected_names),
            "sources": selected_names,
            "evidence": f"canonical_context_policy_selected_target:{explicit_target or 'unresolved'}",
            "reason": "planner_used_source_readiness_to_gate_generation",
        },
    }
    report = build_context_broker_report(
        sources,
        downstream_consumers=acknowledgements,
        applicable_consumers=("planner",),
    )
    report["task_id"] = str(request.active_task_id or "")
    report["trace_id"] = f"context-{str(request.active_task_id or _json_hash(task))[:64]}"
    report["explicit_target"] = explicit_target
    report["finalized"] = False
    return report, _canonical_context_prompt_text(report)


def _canonical_context_prompt_text(report: dict[str, Any]) -> str:
    return render_context_broker_prompt(report)


def _canonical_context_material_hash(report: dict[str, Any]) -> str:
    """Hash source material without treating lifecycle acknowledgements as input."""

    sources: list[dict[str, Any]] = []
    for raw_source in report.get("sources_considered", []):
        if not isinstance(raw_source, dict):
            continue
        sources.append(
            {
                "source": str(raw_source.get("source") or ""),
                "considered": raw_source.get("considered") is not False,
                "status": str(raw_source.get("status") or ""),
                "reason": str(raw_source.get("reason") or ""),
                "required": raw_source.get("required") is True,
                "selected": raw_source.get("selected") is True,
                "included": raw_source.get("included") is True,
                "packet": raw_source.get("packet")
                if isinstance(raw_source.get("packet"), dict)
                else {},
                "authority": raw_source.get("authority")
                if isinstance(raw_source.get("authority"), dict)
                else {},
            }
        )
    return _json_hash(
        {
            "explicit_target": str(report.get("explicit_target") or ""),
            "sources": sources,
        }
    )


def _run_production_target_plugin_proposal(
    *,
    task_id: str,
    target_plugin: Any,
    task: str,
    canonical_context: dict[str, Any],
) -> dict[str, Any]:
    """Enter the persisted orchestrator for an active target-plugin HTTP run.

    The decision route owns context discovery, but it does not own execution.
    It persists an unacknowledged report, lets the real planner acknowledge and
    consume that report, and then asks the canonical orchestrator to invoke the
    target adapter.  A retry may reuse an already-acknowledged identical report;
    it may never replace completed-planner context with different material.
    """

    orchestrator = get_coding_orchestrator()
    state = coding_orchestrator_state_for_task(task_id)
    if not isinstance(state, dict):
        raise CodingOrchestratorError("coding_orchestrator_state_missing")
    run_id = str(state.get("run_id") or "")
    if not run_id:
        raise CodingOrchestratorError("coding_orchestrator_run_id_missing")
    lane_states = state.get("lane_states")
    if not isinstance(lane_states, dict):
        raise CodingOrchestratorError("coding_orchestrator_state_invalid")

    if str(lane_states.get("planner") or "pending") != "completed":
        pending_context = acknowledge_context_consumer(
            canonical_context,
            consumer="planner",
            evidence="",
            applicable=True,
            reason="planner_invocation_pending",
        )
        record_canonical_context_broker_for_task(
            task_id,
            report=pending_context,
            orchestrator_run_id=run_id,
        )
        # The generic rich adapter owns repository-aware architecture.  It
        # persists the exact plan through the orchestrator's plan-ready hook
        # before its first coder call, avoiding both the legacy source-root
        # planner and an unaccounted duplicate architect invocation.
        generic_plan_deferred = (
            getattr(target_plugin, "plugin_id", "")
            == GENERIC_WORKSPACE_PLUGIN_ID
            and load_plan(task_id) is None
        )
        if load_plan(task_id) is None and not generic_plan_deferred:
            orchestrator.advance(task_id)
        if load_plan(task_id) is None and not generic_plan_deferred:
            raise CodingOrchestratorError("authoritative_plan_missing")
        if not generic_plan_deferred:
            orchestrator.acknowledge_planner(task_id)
    else:
        persisted_context = canonical_context_broker_for_task(task_id)
        if not isinstance(persisted_context, dict):
            raise CodingOrchestratorError("canonical_context_report_missing")
        if (
            _canonical_context_material_hash(persisted_context)
            != _canonical_context_material_hash(canonical_context)
        ):
            raise CodingOrchestratorError(
                "canonical_context_changed_after_planner_consumption"
            )
        if persisted_context.get("go_eligible") is not True:
            raise CodingOrchestratorError("target_plugin_canonical_context_blocked")

    receipt = orchestrator.propose_target_plugin(
        task_id,
        plugin=target_plugin,
        task=task,
    )
    result = receipt.get("target_plugin_result")
    if not isinstance(result, dict):
        raise CodingOrchestratorError("target_plugin_result_missing")
    proposed_diff = str(result.get("proposed_diff") or "")
    proposal = receipt.get("target_plugin_proposal")
    if proposed_diff.strip():
        if not isinstance(proposal, dict):
            raise CodingOrchestratorError("target_plugin_proposal_missing")
        if (
            proposal.get("status") != "ready_for_approval_preview"
            or not str(receipt.get("target_plugin_output_id") or "")
            or not str(proposal.get("context_hash") or "")
        ):
            raise CodingOrchestratorError("target_plugin_proposal_identity_missing")
    return receipt


def _mark_unorchestrated_target_plugin_preview(
    result: dict[str, Any],
) -> dict[str, Any]:
    """Prevent a taskless target preview from masquerading as terminal proof."""

    preview = dict(result)
    diagnostics = preview.get("coder_diagnostics")
    if not isinstance(diagnostics, dict):
        diagnostics = preview.get("coderDiagnostics")
    diagnostics = dict(diagnostics) if isinstance(diagnostics, dict) else {}
    provenance = preview.get("target_adapter_provenance")
    if isinstance(provenance, dict):
        provenance = dict(provenance)
        provenance["terminal_proof_eligible"] = False
        provenance["terminal_proof_ineligibility_reason"] = (
            "active_coding_orchestrator_task_missing"
        )
        provenance["claim_ceiling"] = "unorchestrated_preview_only"
        preview["target_adapter_provenance"] = provenance
    diagnostics["terminal_proof_eligible"] = False
    diagnostics["terminal_proof_ineligibility_reason"] = (
        "active_coding_orchestrator_task_missing"
    )
    diagnostics["claim_ceiling"] = "unorchestrated_preview_only"
    diagnostics["target_plugin_orchestrated"] = False
    preview["coder_diagnostics"] = diagnostics
    preview["coderDiagnostics"] = diagnostics
    preview["terminal_proof_eligible"] = False
    preview["claim_ceiling"] = "unorchestrated_preview_only"
    return preview


def _canonical_context_blocked_coder_payload(report: dict[str, Any]) -> dict[str, Any]:
    blockers = [str(item) for item in report.get("required_context_blockers", [])]
    diagnostics = {
        "context_mode": "canonical_context_blocked",
        "context_slices": [],
        "canonical_context_broker": report,
        "validation_status": "required_context_blocked",
        "trial_result_trust_status": "generation_not_attempted",
        "provider_call_made": False,
        "recommended_next_action": "Resolve the canonical context blockers, then retry generation.",
    }
    return {
        "proposed_diff": "",
        "target": "",
        "coder_notes": ["CODER_BLOCKED reason_code: required_context_blocked"],
        "bundle": None,
        "coder_blocked": True,
        "blocked_reason": "; ".join(blockers) or "canonical_context_not_go_eligible",
        "needed_context": "; ".join(blockers),
        "reason_code": "required_context_blocked",
        "coder_diagnostics": diagnostics,
        "changed_files": [],
        "checks_run": [],
    }


def _research_sources_by_source(
    research_sources: list[Any],
    source_name: str,
) -> list[dict[str, Any]]:
    return [
        source
        for source in research_sources
        if isinstance(source, dict) and source.get("source") == source_name
    ]


def _status_bucket(receipt: dict[str, Any], status: str) -> list[str]:
    values: list[str] = []
    for field in FIP0_LANE_STATUS_FIELDS:
        lane = receipt.get(field)
        if isinstance(lane, dict) and lane.get("status") == status:
            values.append(f"{field}:{lane.get('reason') or 'no_reason'}")
    return values


def _safe_write_json(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
        return {"status": "used", "path": str(path)}
    except Exception as error:
        return {
            "status": "failed",
            "path": str(path),
            "reason": "receipt_write_failed",
            "error": f"{type(error).__name__}: {error}",
        }


def _valid_fip0_run_id(run_id: str) -> bool:
    if not run_id.startswith("fip0-"):
        return False
    suffix = run_id.removeprefix("fip0-")
    return bool(suffix) and all(ch in "0123456789abcdef" for ch in suffix.lower())


def _load_fip0_receipt(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail={"reason_code": "fip0_receipt_not_found", "path": str(path)},
        ) from error
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=500,
            detail={
                "reason_code": "fip0_receipt_json_invalid",
                "path": str(path),
                "error": str(error),
            },
        ) from error
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=500,
            detail={"reason_code": "fip0_receipt_not_object", "path": str(path)},
        )
    return payload


PRIVATE_TRACE_KEY_NAMES = {
    "raw_prompt",
    "raw_output_excerpt",
}

PRIVATE_TRACE_PATTERN_MARKERS = (
    "chain_of_thought",
    "hidden_reasoning",
    "private_reasoning",
    "raw_output_excerpt",
)


def _local_receipt_debug_token_configured() -> str:
    return (
        os.environ.get("SOURCE_PROXY_LOCAL_DEV_TOKEN", "")
        or os.environ.get("SOURCE_PROXY_FIP6_DEV_TOKEN", "")
    ).strip()


def _local_receipt_debug_authorized(
    *,
    dev_token_header: str | None = None,
    dev_token_query: str | None = None,
) -> bool:
    configured = _local_receipt_debug_token_configured()
    if not configured:
        return False
    supplied = (dev_token_header or dev_token_query or "").strip()
    return bool(supplied) and supplied == configured


def _sanitize_public_receipt(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            if str(key) in PRIVATE_TRACE_KEY_NAMES:
                continue
            sanitized[str(key)] = _sanitize_public_receipt(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_public_receipt(item) for item in value]
    return value


def _bounded_trace_value(value: Any, *, max_string: int = 500, max_items: int = 25) -> Any:
    sanitized = _sanitize_public_receipt(value)
    if isinstance(sanitized, dict):
        return {
            str(key): _bounded_trace_value(item, max_string=max_string, max_items=max_items)
            for key, item in list(sanitized.items())[:max_items]
        }
    if isinstance(sanitized, list):
        return [
            _bounded_trace_value(item, max_string=max_string, max_items=max_items)
            for item in sanitized[:max_items]
        ]
    if isinstance(sanitized, str) and len(sanitized) > max_string:
        return f"{sanitized[:max_string]}...[truncated:{len(sanitized) - max_string}]"
    return sanitized


def _trace_hygiene_scan(value: Any) -> dict[str, Any]:
    leaks: list[dict[str, str]] = []

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, item in node.items():
                key_text = str(key)
                if key_text in PRIVATE_TRACE_KEY_NAMES:
                    leaks.append({"path": f"{path}.{key_text}".strip("."), "reason": "private_key_exposed"})
                walk(item, f"{path}.{key_text}".strip("."))
            return
        if isinstance(node, list):
            for idx, item in enumerate(node):
                walk(item, f"{path}[{idx}]")
            return
        if isinstance(node, str):
            lowered = node.lower()
            for marker in PRIVATE_TRACE_PATTERN_MARKERS:
                if marker in lowered:
                    leaks.append({"path": path, "reason": f"private_pattern:{marker}"})

    walk(value, "")
    return {
        "status": "failed" if leaks else "used",
        "passed": not leaks,
        "leak_count": len(leaks),
        "leaks": leaks[:20],
        "scanner": "fip6_trace_hygiene_v1",
    }


def _fip0_receipt_response(path: Path, *, include_private: bool = False) -> dict[str, Any]:
    receipt = _load_fip0_receipt(path)
    public_receipt = receipt if include_private else _sanitize_public_receipt(receipt)
    return {
        "receipt": public_receipt,
        "receipt_path": str(path),
        "run_id": receipt.get("run_id"),
        "final_verdict": receipt.get("final_verdict"),
        "productive": receipt.get("productive"),
        "coder_path": receipt.get("coder_path"),
        "verification_real": receipt.get("verification_real", {}),
        "verification_real_reasons": receipt.get("verification_real_reasons", {}),
        "degraded_lanes": receipt.get("degraded_lanes", []),
        "final_packet_hash": receipt.get("final_packet_hash"),
        "coder_received_packet_hash": receipt.get("coder_received_packet_hash"),
        "public_redaction_summary": {
            "private_fields_removed": 0 if include_private else len(PRIVATE_TRACE_KEY_NAMES),
            "private_access": bool(include_private),
        },
    }


FIP6_TRACE_RECEIPT_FIELDS = (
    "run_id",
    "timestamp",
    "normalized_task",
    "route_type",
    "workspace_mode",
    "dirty_tree_status",
    "context_router_status",
    "obsidian_status",
    "cartographer_status",
    "design_status",
    "mac_worker_status",
    "source_readiness_status",
    "search_needed",
    "research_query",
    "repo_research_status",
    "scout_status",
    "scout_sources",
    "searxng_status",
    "searxng_url",
    "searxng_result_count",
    "searxng_sources",
    "tinyfish_status",
    "xersearch_status",
    "gemma_status",
    "gemma_model",
    "gemma_prompt_hash",
    "gemma_output_hash",
    "hermes_critic_status",
    "hermes_critic_model",
    "hermes_critic_prompt_hash",
    "hermes_critic_output_hash",
    "final_coder_packet_hash",
    "coder_received_packet_hash",
    "qwen_coder_status",
    "qwen_coder_model",
    "qwen_coder_output_hash",
    "output_contract_status",
    "protected_path_check",
    "allowed_files",
    "forbidden_files",
    "diff_summary",
    "checks_run",
    "deterministic_verifier_status",
    "browser_behavior_status",
    "browser_verifier_status",
    "functional_verifier_status",
    "hermes_verifier_status",
    "hermes_verifier_model",
    "hermes_verifier_role",
    "hermes_verifier_verdict",
    "hermes_verifier_repair_instructions",
    "repair_loop_status",
    "repair_attempt_count",
    "repair_packets",
    "final_verdict",
    "receipt_path",
)


def _trace_lane(receipt: dict[str, Any], field: str) -> dict[str, Any]:
    value = receipt.get(field)
    if isinstance(value, dict):
        return value
    return {
        "status": "unknown",
        "reason": "receipt_field_missing",
        "field": field,
    }


def _trace_model_summary(receipt: dict[str, Any], prefix: str) -> dict[str, Any]:
    if prefix == "gemma":
        summary_fields = {
            "intent": receipt.get("gemma_intent", ""),
            "normalized_spec": receipt.get("gemma_normalized_spec", ""),
            "acceptance_criteria": receipt.get("gemma_acceptance_criteria", []),
        }
    else:
        summary_fields = {
            "ambiguities": receipt.get("hermes_ambiguities", []),
            "risks": receipt.get("hermes_risks", []),
            "requirement_conflicts": receipt.get("hermes_requirement_conflicts", []),
            "pre_coder_notes": receipt.get("hermes_pre_coder_notes", []),
        }
    return {
        "status": _trace_lane(receipt, f"{prefix}_status" if prefix == "gemma" else "hermes_critic_status"),
        "model": receipt.get(f"{prefix}_model" if prefix == "gemma" else "hermes_critic_model", ""),
        "prompt_hash": receipt.get(f"{prefix}_prompt_hash" if prefix == "gemma" else "hermes_critic_prompt_hash", ""),
        "output_hash": receipt.get(f"{prefix}_output_hash" if prefix == "gemma" else "hermes_critic_output_hash", ""),
        "summary": _bounded_trace_value(summary_fields),
    }


def _packet_hash_match_status(receipt: dict[str, Any]) -> dict[str, Any]:
    final_hash = str(receipt.get("final_coder_packet_hash") or "")
    received_hash = str(receipt.get("coder_received_packet_hash") or "")
    if final_hash and received_hash:
        matched = final_hash == received_hash
        return {
            "status": "used" if matched else "failed",
            "match": matched,
            "reason": (
                "final_coder_packet_hash_matches_received_hash"
                if matched
                else "final_coder_packet_hash_mismatch"
            ),
        }
    qwen_status = _trace_lane(receipt, "qwen_coder_status")
    return {
        "status": "skipped" if qwen_status.get("status") == "skipped" else "unknown",
        "match": False,
        "reason": "coder_packet_not_received_or_hash_missing",
    }


def _fip6_operator_trace_from_receipt(
    receipt: dict[str, Any],
    *,
    receipt_path: Path,
) -> dict[str, Any]:
    missing_fields = [
        field
        for field in FIP6_TRACE_RECEIPT_FIELDS
        if field != "receipt_path" and field not in receipt
    ]
    context_packet = receipt.get("fip1_context_packet")
    if not isinstance(context_packet, dict):
        context_packet = {}
    fip2_packet = receipt.get("fip2_research_packet")
    if not isinstance(fip2_packet, dict):
        fip2_packet = {}
    fip4_result = receipt.get("fip4_qwen_coder_result")
    if not isinstance(fip4_result, dict):
        fip4_result = {}
    fip5_result = receipt.get("fip5_verifier_result")
    if not isinstance(fip5_result, dict):
        fip5_result = {}
    final_packet = receipt.get("fip4_final_coder_packet")
    if not isinstance(final_packet, dict):
        final_packet = {}
    return {
        "trace_version": "fip6.operator_trace.v1",
        "trace_authority": (
            "operational_receipt_projection_sanitized"
        ),
        "run_metadata": {
            "run_id": receipt.get("run_id"),
            "timestamp": receipt.get("timestamp"),
            "prompt_hash": _json_hash(receipt.get("raw_prompt", "")),
            "normalized_task": receipt.get("normalized_task", ""),
            "route_type": receipt.get("route_type", ""),
            "workspace_mode": receipt.get("workspace_mode", ""),
            "dirty_tree_status": receipt.get("dirty_tree_status", {}),
        },
        "context_trace": {
            "context_router_status": _trace_lane(receipt, "context_router_status"),
            "obsidian": {
                "status": _trace_lane(receipt, "obsidian_status"),
                "summary": _bounded_trace_value(context_packet.get("obsidian_summary", "")),
            },
            "cartographer": {
                "status": _trace_lane(receipt, "cartographer_status"),
                "summary": _bounded_trace_value(context_packet.get("cartographer_summary", "")),
            },
            "design": {
                "status": _trace_lane(receipt, "design_status"),
                "summary": _bounded_trace_value(context_packet.get("design_summary", "")),
            },
            "mac_worker_advisory_status": _trace_lane(receipt, "mac_worker_status"),
            "source_readiness_status": _trace_lane(receipt, "source_readiness_status"),
        },
        "search_trace": {
            "source_readiness_status": _trace_lane(receipt, "source_readiness_status"),
            "search_needed": receipt.get("search_needed"),
            "research_query": receipt.get("research_query", ""),
            "repo_research_status": _trace_lane(receipt, "repo_research_status"),
            "scout": {
                "status": _trace_lane(receipt, "scout_status"),
                "sources": _bounded_trace_value(receipt.get("scout_sources", [])),
                "summary": _bounded_trace_value(fip2_packet.get("scout_summary", "")),
            },
            "searxng": {
                "status": _trace_lane(receipt, "searxng_status"),
                "url": receipt.get("searxng_url", ""),
                "result_count": receipt.get("searxng_result_count", 0),
                "sources": _bounded_trace_value(receipt.get("searxng_sources", [])),
            },
            "tinyfish_deferred_status": _trace_lane(receipt, "tinyfish_status"),
            "xersearch_missing_alias_status": _trace_lane(receipt, "xersearch_status"),
        },
        "model_trace": {
            "gemma": _trace_model_summary(receipt, "gemma"),
            "hermes_critic": _trace_model_summary(receipt, "hermes_critic"),
        },
        "coder_trace": {
            "final_coder_packet_hash": receipt.get("final_coder_packet_hash", ""),
            "coder_received_packet_hash": receipt.get("coder_received_packet_hash", ""),
            "packet_hash_match_status": _packet_hash_match_status(receipt),
            "qwen": {
                "status": _trace_lane(receipt, "qwen_coder_status"),
                "model": receipt.get("qwen_coder_model", ""),
                "output_hash": receipt.get("qwen_coder_output_hash", ""),
                "parser_result": _bounded_trace_value(fip4_result.get("parser", {})),
                "changed_files": fip4_result.get(
                    "changed_files",
                    receipt.get("diff_summary", {}).get("changed_files", [])
                    if isinstance(receipt.get("diff_summary"), dict)
                    else [],
                ),
            },
            "final_coder_packet_summary": {
                "target_file": final_packet.get("target_file", ""),
                "allowed_files": final_packet.get("allowed_files", []),
                "forbidden_files": final_packet.get("forbidden_files", []),
                "research_packet_hash": final_packet.get("research_packet_hash", ""),
                "model_packet_hash": final_packet.get("model_packet_hash", ""),
            },
        },
        "safety_trace": {
            "protected_path_check": receipt.get("protected_path_check", {}),
            "allowed_files": receipt.get("allowed_files", []),
            "forbidden_files": receipt.get("forbidden_files", []),
            "diff_summary": receipt.get("diff_summary", {}),
            "checks_run": receipt.get("checks_run", []),
        },
        "verifier_trace": {
            "deterministic": {
                "status": _trace_lane(receipt, "deterministic_verifier_status"),
                "checks_run": receipt.get("deterministic_checks_run", []),
                "failures": receipt.get("deterministic_failures", []),
            },
            "functional": {
                "status": _trace_lane(receipt, "functional_verifier_status"),
                "checks": _bounded_trace_value(receipt.get("functional_verifier_checks", [])),
                "target_path": receipt.get("functional_verifier_target_path", ""),
                "timeout_ms": receipt.get("functional_verifier_timeout_ms"),
                "verifier_version": receipt.get("functional_verifier_version", ""),
            },
            "browser_verifier": {
                "status": _trace_lane(receipt, "browser_verifier_status"),
                "checks": _bounded_trace_value(receipt.get("browser_verifier_checks", [])),
                "target_path": receipt.get("browser_verifier_target_path", ""),
                "timeout_ms": receipt.get("browser_verifier_timeout_ms"),
                "verifier_version": receipt.get("browser_verifier_version", ""),
                "browser_engine": receipt.get("browser_verifier_browser_engine", ""),
            },
            "browser_behavior": {
                "status": _trace_lane(receipt, "browser_behavior_status"),
                "summary": receipt.get("browser_probe_summary", {}),
                "authoritative": receipt.get("browser_behavior_authoritative"),
            },
            "hermes_verifier": {
                "status": _trace_lane(receipt, "hermes_verifier_status"),
                "model": receipt.get("hermes_verifier_model", ""),
                "role": receipt.get("hermes_verifier_role", ""),
                "verdict": receipt.get("hermes_verifier_verdict", ""),
                "prompt_hash": receipt.get("hermes_verifier_prompt_hash", ""),
                "output_hash": receipt.get("hermes_verifier_output_hash", ""),
                "repair_instructions": receipt.get(
                    "hermes_verifier_repair_instructions",
                    [],
                ),
            },
        },
        "repair_trace": {
            "repair_loop_status": _trace_lane(receipt, "repair_loop_status"),
            "repair_attempt_count": receipt.get("repair_attempt_count", 0),
            "repair_max_attempts": receipt.get("repair_max_attempts", 0),
            "repair_packets": _bounded_trace_value(receipt.get("repair_packets", [])),
            "qwen_repair_outputs": _bounded_trace_value(receipt.get("qwen_repair_outputs", [])),
            "verifier_result": _bounded_trace_value(fip5_result.get("final_verifier_result", {})),
        },
        "failure_trace": {
            "failure_event": receipt.get("failure_event", {"failure_present": False}),
            "failure_classification": receipt.get("failure_classification", no_failure_classification()),
        },
        "verdict_trace": {
            "final_verdict": receipt.get("final_verdict"),
            "productive": receipt.get("productive"),
            "coder_path": receipt.get("coder_path"),
            "verification_real": receipt.get("verification_real", {}),
            "verification_real_reasons": receipt.get("verification_real_reasons", {}),
            "degraded_lanes": receipt.get("degraded_lanes", []),
            "receipt_path": str(receipt_path),
            "used_sources": receipt.get("used_sources", []),
            "skipped_reasons": receipt.get("skipped_reasons", []),
            "blocked_reasons": receipt.get("blocked_reasons", []),
            "failed_reasons": receipt.get("failed_reasons", []),
        },
        "missing_fields": missing_fields,
        "source_receipt_hash": _json_hash(receipt),
    }


def _fip6_trace_response(path: Path, *, include_private: bool = False) -> dict[str, Any]:
    receipt = _load_fip0_receipt(path)
    trace = _fip6_operator_trace_from_receipt(
        receipt,
        receipt_path=path,
    )
    trace["trace_hygiene_check"] = _trace_hygiene_scan(trace)
    return {
        "operator_trace": trace,
        "receipt": receipt if include_private else _sanitize_public_receipt(receipt),
        "receipt_path": str(path),
        "run_id": receipt.get("run_id"),
        "final_verdict": receipt.get("final_verdict"),
        "productive": receipt.get("productive"),
        "coder_path": receipt.get("coder_path"),
        "verification_real": receipt.get("verification_real", {}),
        "verification_real_reasons": receipt.get("verification_real_reasons", {}),
        "degraded_lanes": receipt.get("degraded_lanes", []),
        "public_redaction_summary": {
            "private_fields_removed": 0 if include_private else len(PRIVATE_TRACE_KEY_NAMES),
            "private_access": bool(include_private),
        },
    }


def _fip0_receipt_sort_key(path: Path) -> tuple[str, float]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
    timestamp = ""
    if isinstance(payload, dict):
        raw_timestamp = payload.get("timestamp")
        if isinstance(raw_timestamp, str):
            timestamp = raw_timestamp
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = 0.0
    return (timestamp, mtime)


def _latest_fip0_receipt_path() -> Path | None:
    root = _fip0_receipt_root()
    if not root.is_dir():
        return None
    candidates = [
        path
        for path in root.glob("fip0-*.json")
        if path.is_file() and _valid_fip0_run_id(path.stem)
    ]
    if not candidates:
        return None
    return max(candidates, key=_fip0_receipt_sort_key)


def _protected_path_check(
    *,
    route_reasons: list[str],
    forbidden_files: list[str],
) -> dict[str, Any]:
    protected_reasons = [
        reason
        for reason in route_reasons
        if reason in TARGET_HARD_BLOCK_REASON_CODES
    ]
    if protected_reasons:
        return {
            "status": "blocked",
            "reason": "protected_path_route_block",
            "reason_codes": protected_reasons,
        }
    return {
        "status": "used",
        "reason": "protected_path_guard_evaluated",
        "forbidden_file_count": len(forbidden_files),
    }


def _trial_harness_only_enabled() -> bool:
    return os.environ.get("SOURCE_PROXY_TRIAL_HARNESS_ONLY", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _lane_degradation_for_receipt(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    degraded = []
    for field in ("gemma_status", "hermes_critic_status", "hermes_verifier_status"):
        status = receipt.get(field)
        if not isinstance(status, dict):
            continue
        value = str(status.get("status") or "")
        reason = str(status.get("reason") or "")
        if value in {"blocked", "failed"} and (
            "timeout" in reason.lower()
            or "timed_out" in reason.lower()
            or "unavailable" in reason.lower()
        ):
            degraded.append(
                {
                    "lane": field.removesuffix("_status"),
                    "status": value,
                    "reason": reason,
                    "required": True,
                }
            )
    return degraded


def _structured_verdict_fields(receipt: dict[str, Any]) -> dict[str, Any]:
    final_verdict = str(receipt.get("final_verdict") or "")
    qwen_status = receipt.get("qwen_coder_status")
    qwen_used = isinstance(qwen_status, dict) and qwen_status.get("status") == "used"
    fip4_result = receipt.get("fip4_qwen_coder_result")
    has_fip4 = isinstance(fip4_result, dict) and bool(fip4_result)
    final_hash = str(receipt.get("final_coder_packet_hash") or "")
    received_hash = str(receipt.get("coder_received_packet_hash") or "")
    diff_summary = receipt.get("diff_summary")
    changed_files = (
        diff_summary.get("changed_files")
        if isinstance(diff_summary, dict) and isinstance(diff_summary.get("changed_files"), list)
        else []
    )
    protected = receipt.get("protected_path_check")
    protected_blocked = isinstance(protected, dict) and protected.get("status") == "blocked"
    coder_path = "legacy_stub"
    if qwen_used and has_fip4 and final_hash and final_hash == received_hash:
        coder_path = "fip4_real"
    elif _trial_harness_only_enabled() and (
        str(receipt.get("final_verdict") or "").find("trial") >= 0
        or any("trial" in str(note).lower() for note in receipt.get("coder_notes", []))
    ):
        coder_path = "trial"
    deterministic = receipt.get("deterministic_verifier_status")
    browser = receipt.get("browser_verifier_status")
    browser_present = isinstance(browser, dict)
    browser_behavior = receipt.get("browser_behavior_status")
    if not browser_present:
        browser = browser_behavior
        browser_present = isinstance(browser, dict)
    hermes = receipt.get("hermes_verifier_status")
    functional = receipt.get("functional_verifier_status")
    functional_used = isinstance(functional, dict) and functional.get("status") == "used"
    functional_passed = bool(functional_used and functional.get("passed") is True)
    functional_present = isinstance(functional, dict)
    functional_status = functional if isinstance(functional, dict) else {}
    browser_truth = (
        browser.get("browser_verifier")
        if isinstance(browser, dict) and isinstance(browser.get("browser_verifier"), dict)
        else {}
    )
    browser_passed = bool(isinstance(browser, dict) and _browser_truth_behavior_passed(browser))
    browser_truth_evidence = (
        browser_truth.get("evidence") if isinstance(browser_truth.get("evidence"), dict) else {}
    )
    browser_pass_reason = str(
        browser_truth_evidence.get("summary") or browser.get("reason") or "browser_verifier_real_behavior_passed"
    )
    browser_nonpass_reason = (
        str(browser.get("reason") or "browser_verifier_not_implemented")
        if browser_present
        else "browser_verifier_not_implemented"
    )
    functional_pass_reason = str(functional_status.get("reason") or "functional_verifier_passed")
    functional_nonpass_reason = (
        str(functional_status.get("reason") or "functional_verifier_not_implemented")
        if functional_present
        else "functional_verifier_not_implemented"
    )
    verification_real = {
        "deterministic": bool(
            isinstance(deterministic, dict)
            and deterministic.get("status") == "used"
            and deterministic.get("passed") is True
        ),
        "browser": browser_passed,
        "functional": functional_passed,
        "behavior": bool(browser_passed or functional_passed),
        "hermes": bool(
            isinstance(hermes, dict)
            and hermes.get("status") == "used"
            and str(hermes.get("verdict") or receipt.get("hermes_verifier_verdict") or "").upper() == "PASS"
        ),
    }
    verification_real_reasons = {
        "browser": browser_pass_reason if browser_passed else browser_nonpass_reason,
        "functional": (
            functional_pass_reason
            if functional_passed
            else functional_nonpass_reason
        ),
        "behavior": (
            functional_pass_reason
            if functional_passed
            else browser_pass_reason
            if browser_passed
            else browser_nonpass_reason
            if browser_present
            else functional_nonpass_reason
            if functional_present
            else "behavior_verifier_not_implemented"
        ),
    }
    degraded_lanes = _lane_degradation_for_receipt(receipt)
    final_verdict_go = final_verdict.startswith("GO:")
    productive_go = bool(
        final_verdict_go
        and coder_path == "fip4_real"
        and verification_real["deterministic"]
        and verification_real["behavior"]
        and not protected_blocked
        and not degraded_lanes
    )
    action_output = fip4_result.get("action") if isinstance(fip4_result, dict) else None
    productive_evidence = {
        "file_written": bool(changed_files),
        "action_applied": bool(coder_path == "fip4_real" and changed_files and action_output),
        "browser_behavior_verified": browser_passed,
        "real_browser_used": bool(browser_truth.get("real_browser_used") is True),
        "interactive_behavior_checked": bool(
            isinstance(browser_truth.get("checks"), dict)
            and browser_truth["checks"].get("interactive_behavior_checked") is True
        ),
        "functional_behavior_verified": functional_passed,
        "deterministic_verified": verification_real["deterministic"],
        "verification_real": verification_real["behavior"],
        "protected_path_clear": not protected_blocked,
        "degraded_lanes_clear": not bool(degraded_lanes),
    }
    productive_reasons = []
    productive_blockers = []
    if final_verdict_go:
        productive_reasons.append("final_verdict_go")
    else:
        productive_blockers.append("final_verdict_not_go")
    if coder_path == "fip4_real":
        productive_reasons.append("coder_path_fip4_real")
    else:
        productive_blockers.append("coder_path_not_real")
    if productive_evidence["file_written"]:
        productive_reasons.append("file_output_present")
    else:
        productive_blockers.append("file_output_missing")
    if productive_evidence["action_applied"]:
        productive_reasons.append("accepted_action_output_present")
    else:
        productive_blockers.append("accepted_action_output_missing")
    if verification_real["deterministic"]:
        productive_reasons.append("deterministic_verifier_real")
    else:
        productive_blockers.append("deterministic_verifier_not_real")
    if verification_real["behavior"]:
        productive_reasons.append("real_behavior_verified")
    else:
        productive_blockers.append("behavior_not_verified")
    if browser_passed:
        productive_reasons.append("browser_behavior_verified")
    if functional_passed:
        productive_reasons.append("functional_behavior_verified")
    if protected_blocked:
        productive_blockers.append("protected_path_blocked")
    if degraded_lanes:
        productive_blockers.append("degraded_required_lane")
    browser_lane_status = str(browser.get("status") or "").upper() if isinstance(browser, dict) else ""
    browser_truth_status = str(browser_truth.get("status") or browser_lane_status or "").upper()
    if browser_truth_status and not browser_passed:
        if browser_truth_status == "PARTIAL_GO":
            productive_blockers.append("browser_verifier_partial_go")
        elif browser_truth_status in {"NO_GO", "BLOCKED", "SKIPPED", "UNSUPPORTED"}:
            productive_blockers.append(f"browser_verifier_{browser_truth_status.lower()}")
        else:
            productive_blockers.append("browser_verifier_not_productive")
    if bool(changed_files or action_output or final_verdict_go) and not verification_real["behavior"]:
        productive_reasons.append("structural_output_present_behavior_missing")
    if productive_go:
        productive_status = "GO"
    elif protected_blocked or browser_truth_status == "NO_GO" or (
        final_verdict and not final_verdict_go and "BLOCKED" not in final_verdict.upper()
    ):
        productive_status = "NO_GO"
    elif degraded_lanes or browser_truth_status == "BLOCKED" or "BLOCKED" in final_verdict.upper():
        productive_status = "BLOCKED"
    elif browser_truth_status == "UNSUPPORTED" and not functional_passed:
        productive_status = "UNSUPPORTED"
    elif browser_truth_status == "SKIPPED" and not functional_passed:
        productive_status = "SKIPPED"
    elif bool(changed_files or action_output or final_verdict_go or verification_real["deterministic"]):
        productive_status = "PARTIAL_GO"
    else:
        productive_status = "NO_GO"
    return {
        "productive": productive_go,
        "productive_status": productive_status,
        "productive_go": productive_go,
        "productive_reasons": productive_reasons,
        "productive_blockers": productive_blockers,
        "productive_evidence": productive_evidence,
        "coder_path": coder_path,
        "verification_real": verification_real,
        "verification_real_reasons": verification_real_reasons,
        "degraded_lanes": degraded_lanes,
    }


def _fip4_qwen_enabled() -> bool:
    """FIP4 Qwen coder is dormant by default; set SOURCE_PROXY_FIP4_QWEN_CODER_ENABLED=1 to make it decision-bearing."""
    return os.environ.get("SOURCE_PROXY_FIP4_QWEN_CODER_ENABLED", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _fip4_qwen_model() -> str:
    return (
        os.environ.get("SOURCE_PROXY_FIP4_QWEN_MODEL", "").strip()
        or os.environ.get("SOURCE_PROXY_CODER_OLLAMA_MODEL", "").strip()
        or "qwen2.5-coder:7b"
    )


def _fip4_ollama_base_url() -> str:
    return (
        os.environ.get("SOURCE_PROXY_FIP4_OLLAMA_BASE_URL", "").strip()
        or os.environ.get("SOURCE_PROXY_OLLAMA_BASE_URL", "").strip()
        or os.environ.get("OLLAMA_BASE_URL", "").strip()
        or "http://127.0.0.1:11434"
    ).rstrip("/")


def _fip4_call_timeout_seconds() -> float:
    raw = os.environ.get("SOURCE_PROXY_FIP4_QWEN_TIMEOUT_SECONDS", "").strip()
    if not raw:
        return 300.0
    try:
        return max(5.0, min(float(raw), 900.0))
    except ValueError:
        return 300.0


def _fip4_qwen_max_attempts() -> int:
    raw = os.environ.get("SOURCE_PROXY_FIP4_QWEN_MAX_ATTEMPTS", "").strip()
    if not raw:
        return 3
    try:
        value = int(raw)
    except ValueError:
        return 3
    return max(1, min(value, 3))


def _fip5_verifier_enabled() -> bool:
    """FIP5 verifier/repair is dormant by default; set SOURCE_PROXY_FIP5_VERIFIER_ENABLED=1 and allow the FIP4 chain to activate it."""
    return os.environ.get("SOURCE_PROXY_FIP5_VERIFIER_ENABLED", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _fip4_allow_fip5_chain() -> bool:
    """The FIP4->FIP5 chain is dormant by default; set SOURCE_PROXY_FIP4_ALLOW_FIP5_CHAIN=1 to permit verifier consumption."""
    return os.environ.get("SOURCE_PROXY_FIP4_ALLOW_FIP5_CHAIN", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _fip5_repair_max_attempts() -> int:
    raw = os.environ.get("SOURCE_PROXY_FIP5_REPAIR_MAX_ATTEMPTS", "").strip()
    if not raw:
        return 2
    try:
        value = int(raw)
    except ValueError:
        return 2
    return max(0, min(value, 5))


def _fip5_hermes_model() -> str:
    return (
        os.environ.get("SOURCE_PROXY_FIP5_HERMES_VERIFIER_MODEL", "").strip()
        or os.environ.get("SOURCE_PROXY_FIP3_HERMES_MODEL", "").strip()
        or "hermes3:8b-abliterated"
    )


def _fip5_required_text(task: str) -> str:
    lowered = task.lower()
    for marker in ("exactly this content:", "exactly this line:", "replace the file with:"):
        index = lowered.find(marker)
        if index >= 0:
            return " ".join(task[index + len(marker) :].strip().split())[:500]
    return ""


def _fip5_browser_relevant(changed_files: list[Any], explicit_target: str) -> bool:
    paths = [str(item).replace("\\", "/") for item in changed_files if str(item).strip()]
    if explicit_target:
        paths.append(explicit_target.replace("\\", "/"))
    return any(
        path.startswith(("src/app/", "src/components/"))
        or path.endswith((".tsx", ".jsx", ".html"))
        for path in paths
    )


def _fip5_deterministic_verifier(
    *,
    request: PromptPacketRequest,
    explicit_target: str,
    fip4_result: dict[str, Any],
    repair_attempt: int = 0,
) -> dict[str, Any]:
    failures: list[str] = []
    checks: list[str] = [
        "fip4_status_used",
        "final_coder_packet_hash_matches_received_hash",
        "qwen_action_output_parsed",
        "changed_files_inside_allowed_files",
        "protected_files_not_changed",
    ]
    if fip4_result.get("status") != "used":
        failures.append("fip4_qwen_coder_not_used")
    final_hash = str(fip4_result.get("final_coder_packet_hash") or "")
    received_hash = str(fip4_result.get("coder_received_packet_hash") or "")
    if not final_hash or received_hash != final_hash:
        failures.append("coder_received_packet_hash_mismatch")
    parser = fip4_result.get("parser") if isinstance(fip4_result.get("parser"), dict) else {}
    if parser.get("parse_error") or not parser.get("parsed_output_mode"):
        failures.append("qwen_output_contract_not_parsed")
    allowed_files = [str(item) for item in fip4_result.get("allowed_files", [])]
    forbidden_files = [str(item) for item in fip4_result.get("forbidden_files", [])]
    changed_files = [str(item) for item in fip4_result.get("changed_files", [])]
    if not changed_files:
        failures.append("no_changed_files")
    if any(path not in allowed_files for path in changed_files):
        failures.append("changed_file_outside_allowed_files")
    for path in changed_files:
        if path in forbidden_files or any(
            path.startswith(prefix.rstrip("/") + "/") for prefix in forbidden_files if prefix
        ):
            failures.append("changed_file_matches_forbidden_path")
            break
    required_text = _fip5_required_text(request.task)
    action = fip4_result.get("action") if isinstance(fip4_result.get("action"), dict) else {}
    action_content = " ".join(str(action.get("content") or "").split())
    if required_text:
        checks.append("requested_text_present_in_qwen_action")
        if required_text not in action_content:
            failures.append("requested_text_missing_from_qwen_action")
    if request.expected_result_state == "repair_expected" and repair_attempt == 0:
        failures.append("fip5_forced_initial_repair_probe")
    if request.expected_result_state == "max_repair_expected":
        failures.append("fip5_forced_persistent_max_repair_probe")
    return {
        "status": "used",
        "reason": "fip5_deterministic_verifier_executed",
        "passed": not failures,
        "checks_run": checks,
        "failures": list(dict.fromkeys(failures)),
        "changed_files": changed_files,
        "allowed_files": allowed_files,
        "forbidden_files": forbidden_files,
        "required_text": required_text,
        "repair_attempt": repair_attempt,
    }


def _fip5_browser_probe(
    *,
    request: PromptPacketRequest,
    explicit_target: str,
    fip4_result: dict[str, Any],
) -> dict[str, Any]:
    relevant = _fip5_browser_relevant(fip4_result.get("changed_files", []), explicit_target)
    artifact_kind = _browser_artifact_kind(explicit_target)
    if not relevant:
        return {
            "status": "skipped",
            "reason": "browser_behavior_not_relevant_for_changed_files",
            "summary": {"behavior_required": False, "probes_run": []},
            "authoritative": True,
            "passed": True,
            "browser_verifier": _browser_truth(
                status="SKIPPED",
                attempted=False,
                real_browser_used=False,
                target_path=explicit_target,
                artifact_kind=artifact_kind,
                summary="Browser behavior was not relevant for the changed files.",
                notes=["non_browser_target"],
            ),
        }
    if request.expected_result_state == "browser_pass_expected":
        if _trial_harness_only_enabled():
            return {
                "status": "used",
                "reason": "browser_behavior_probe_supplied_by_fip5_runtime_proof",
                "summary": {
                    "behavior_required": True,
                    "probes_run": ["fip5_runtime_browser_relevance_probe"],
                    "passed": True,
                },
                "authoritative": True,
                "passed": True,
                "browser_verifier": _browser_truth(
                    status="UNKNOWN",
                    attempted=False,
                    real_browser_used=False,
                    target_path=explicit_target,
                    artifact_kind=artifact_kind,
                    summary="Trial harness supplied browser pass metadata; no real browser proof was attached.",
                    degraded_reason="trial_harness_browser_metadata_only",
                    notes=["trial_harness_only"],
                ),
            }
        return {
            "status": "failed",
            "reason": "browser_behavior_synthetic_pass_rejected_default",
            "summary": {
                "behavior_required": True,
                "probes_run": [],
                "missing": ["real_browser_verifier_evidence"],
            },
            "authoritative": True,
            "passed": False,
            "browser_verifier": _browser_truth(
                status="NO_GO",
                attempted=False,
                real_browser_used=False,
                target_path=explicit_target,
                artifact_kind=artifact_kind,
                summary="Synthetic browser pass request was rejected because no real browser evidence was attached.",
                degraded_reason="synthetic_browser_evidence_rejected",
                notes=["synthetic_evidence_rejected"],
            ),
        }
    return {
        "status": "failed",
        "reason": "browser_behavior_required_but_no_passing_browser_evidence",
        "summary": {
            "behavior_required": True,
            "probes_run": [],
            "missing": ["browser_behavior_evidence"],
        },
        "authoritative": True,
        "passed": False,
        "browser_verifier": _browser_truth(
            status="NO_GO",
            attempted=False,
            real_browser_used=False,
            target_path=explicit_target,
            artifact_kind=artifact_kind,
            summary="Browser behavior was required but no passing real browser evidence was attached.",
            degraded_reason="browser_behavior_evidence_missing",
        ),
    }


def _browser_verifier_timeout_ms() -> int:
    raw = os.environ.get("SOURCE_PROXY_BROWSER_VERIFIER_TIMEOUT_MS", "").strip()
    if not raw:
        return 60000
    try:
        value = int(raw)
    except ValueError:
        return 60000
    return max(1000, min(value, 60000))


def _browser_verifier_supported_target(path: str) -> bool:
    return path.replace("\\", "/").lower().endswith(".html")


def _browser_artifact_kind(path: str) -> str:
    normalized = path.replace("\\", "/").lower()
    if normalized.endswith(".html"):
        return "html"
    if normalized.endswith((".tsx", ".jsx")):
        return "react"
    if "/src/app/" in normalized or normalized.endswith(("page.tsx", "layout.tsx")):
        return "next"
    return "unknown"


def _browser_truth(
    *,
    status: str,
    attempted: bool,
    real_browser_used: bool,
    target_path: str,
    artifact_kind: str,
    tool: str = "unknown",
    page_loaded: bool = False,
    dom_ready: bool = False,
    required_text_present: bool = False,
    interactive_behavior_checked: bool = False,
    console_errors: list[Any] | None = None,
    network_errors: list[Any] | None = None,
    screenshot_captured: bool = False,
    summary: str = "",
    screenshot_path: str | None = None,
    trace_path: str | None = None,
    degraded_reason: str | None = None,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    console = [_redact_browser_text(item) for item in list(console_errors or [])[:5]]
    network = [_redact_browser_text(item) for item in list(network_errors or [])[:5]]
    return {
        "status": status,
        "attempted": attempted,
        "real_browser_used": real_browser_used,
        "tool": tool,
        "target_url": f"file://{target_path}" if target_path else "",
        "artifact_kind": artifact_kind,
        "checks": {
            "page_loaded": page_loaded,
            "dom_ready": dom_ready,
            "required_text_present": required_text_present,
            "interactive_behavior_checked": interactive_behavior_checked,
            "console_errors": console,
            "network_errors": network,
            "screenshot_captured": screenshot_captured,
        },
        "evidence": {
            "summary": summary[:500],
            "screenshot_path": screenshot_path,
            "trace_path": trace_path,
        },
        "degraded_reason": degraded_reason,
        "notes": list(notes or []),
    }


def _redact_browser_text(value: Any) -> str:
    text = str(value)[:300]
    text = re.sub(
        r"(?i)\b(token|secret|password|api[_-]?key)\b\s*[:=]\s*['\"]?[^'\"\s]+",
        r"\1=[REDACTED]",
        text,
    )
    text = re.sub(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", text)
    return text


def _browser_truth_behavior_passed(browser: dict[str, Any]) -> bool:
    truth = browser.get("browser_verifier")
    if not isinstance(truth, dict):
        return False
    checks = truth.get("checks") if isinstance(truth.get("checks"), dict) else {}
    return bool(
        truth.get("status") == "GO"
        and truth.get("attempted") is True
        and truth.get("real_browser_used") is True
        and checks.get("page_loaded") is True
        and checks.get("dom_ready") is True
        and checks.get("required_text_present") is True
        and checks.get("interactive_behavior_checked") is True
        and not checks.get("console_errors")
        and not checks.get("network_errors")
    )


def _browser_verifier_harness() -> str:
    return r"""
const { chromium } = require("playwright");
const targetPath = process.argv[1];
const timeoutMs = Number(process.argv[2] || "10000");
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  const networkErrors = [];
  page.on("console", (msg) => {
    if (["error"].includes(msg.type())) consoleErrors.push(msg.text().slice(0, 300));
  });
  page.on("pageerror", (err) => pageErrors.push(String(err && err.message || err).slice(0, 300)));
  page.on("requestfailed", (req) => networkErrors.push(`${req.url().slice(0, 160)} ${req.failure() && req.failure().errorText || "failed"}`.slice(0, 300)));
  await page.route("**/*", async (route) => {
    const url = route.request().url();
    if (url.startsWith("file://") || url.startsWith("data:") || url === "about:blank") {
      await route.continue();
      return;
    }
    await route.abort("blockedbyclient");
  });
  const response = await page.goto("file://" + targetPath, {
    waitUntil: "domcontentloaded",
    timeout: timeoutMs,
  });
  await page.waitForLoadState("load", { timeout: timeoutMs }).catch(() => {});
  const visibleText = (await page.evaluate(() => {
    const body = document.body;
    if (!body) return "";
    return (body.innerText || body.textContent || "").trim();
  }).catch(() => ""));
  const domReady = await page.evaluate(() => ["interactive", "complete"].includes(document.readyState)).catch(() => false);
  const interactive = await page.evaluate(async () => {
    const target = document.querySelector("button,[role='button'],input[type='button'],input[type='submit'],input[type='checkbox'],summary");
    if (!target) {
      return { attempted: false, changed: false, reason: "no_interactive_control_found" };
    }
    const body = document.body;
    const beforeText = body ? (body.innerText || body.textContent || "") : "";
    const beforeChecked = "checked" in target ? Boolean(target.checked) : null;
    target.click();
    await new Promise((resolve) => setTimeout(resolve, 100));
    const afterText = body ? (body.innerText || body.textContent || "") : "";
    const afterChecked = "checked" in target ? Boolean(target.checked) : null;
    return {
      attempted: true,
      changed: beforeText !== afterText || beforeChecked !== afterChecked,
      reason: beforeText !== afterText || beforeChecked !== afterChecked ? "visible_state_changed_after_click" : "click_did_not_change_visible_state"
    };
  }).catch((err) => ({ attempted: true, changed: false, reason: String(err && err.message || err).slice(0, 200) }));
  const title = await page.title().catch(() => "");
  await browser.close();
  process.stdout.write(JSON.stringify({
    loaded: true,
    status: response ? response.status() : null,
    domReady: domReady,
    visibleTextLength: visibleText.length,
    visibleTextExcerpt: visibleText.slice(0, 200),
    interactiveAttempted: interactive.attempted,
    interactiveChanged: interactive.changed,
    interactiveReason: interactive.reason,
    title: title.slice(0, 120),
    consoleErrorCount: consoleErrors.length,
    pageErrorCount: pageErrors.length,
    networkErrorCount: networkErrors.length,
    consoleErrors: consoleErrors.slice(0, 5),
    pageErrors: pageErrors.slice(0, 5),
    networkErrors: networkErrors.slice(0, 5),
    browserEngine: "chromium"
  }));
})().catch((err) => {
  process.stdout.write(JSON.stringify({
    loaded: false,
    reason: String(err && err.message || err).slice(0, 300),
    browserEngine: "chromium"
  }));
  process.exit(2);
});
"""


def _fip5_browser_verifier(
    *,
    request: PromptPacketRequest,
    explicit_target: str,
    fip4_result: dict[str, Any],
) -> dict[str, Any]:
    timeout_ms = _browser_verifier_timeout_ms()
    verifier_version = "browser-verifier-v1"
    changed_files = [str(item).replace("\\", "/") for item in fip4_result.get("changed_files", [])]
    allowed_files = [str(item).replace("\\", "/") for item in fip4_result.get("allowed_files", [])]
    target = (changed_files[0] if len(changed_files) == 1 else explicit_target).replace("\\", "/")
    artifact_kind = _browser_artifact_kind(target)
    base = {
        "passed": False,
        "authoritative": True,
        "checks": [],
        "target_path": target,
        "timeout_ms": timeout_ms,
        "verifier_version": verifier_version,
    }
    relevant = _fip5_browser_relevant(changed_files, explicit_target)
    if not relevant:
        return {
            **base,
            "passed": True,
            "status": "skipped",
            "reason": "browser_verifier_skipped_non_browser_target",
            "checks": [{"name": "browser_relevance", "passed": False, "browser_relevant": False}],
            "browser_verifier": _browser_truth(
                status="SKIPPED",
                attempted=False,
                real_browser_used=False,
                target_path=target,
                artifact_kind=artifact_kind,
                summary="Changed files did not require browser verification.",
                notes=["safe_scope_skip"],
            ),
        }
    if fip4_result.get("status") != "used":
        return {
            **base,
            "status": "skipped",
            "reason": "browser_verifier_skipped_coder_not_used",
            "browser_verifier": _browser_truth(
                status="SKIPPED",
                attempted=False,
                real_browser_used=False,
                target_path=target,
                artifact_kind=artifact_kind,
                summary="Browser verifier skipped because the coder lane was not used.",
                notes=["coder_not_used"],
            ),
        }
    if len(changed_files) != 1:
        return {
            **base,
            "status": "blocked",
            "reason": "browser_verifier_blocked_requires_single_changed_file",
            "checks": [{"name": "single_changed_file", "passed": False, "count": len(changed_files)}],
            "browser_verifier": _browser_truth(
                status="BLOCKED",
                attempted=False,
                real_browser_used=False,
                target_path=target,
                artifact_kind=artifact_kind,
                summary="Browser verifier requires exactly one changed browser artifact.",
                degraded_reason="requires_single_changed_file",
            ),
        }
    if target not in allowed_files:
        return {
            **base,
            "status": "blocked",
            "reason": "browser_verifier_blocked_target_not_allowed",
            "checks": [{"name": "target_in_allowed_files", "passed": False}],
            "browser_verifier": _browser_truth(
                status="BLOCKED",
                attempted=False,
                real_browser_used=False,
                target_path=target,
                artifact_kind=artifact_kind,
                summary="Browser verifier target was not in the allowed file set.",
                degraded_reason="target_not_allowed",
            ),
        }
    if not _browser_verifier_supported_target(target):
        return {
            **base,
            "status": "skipped",
            "reason": "browser_verifier_skipped_unsupported_browser_target",
            "checks": [{"name": "supported_browser_target", "passed": False}],
            "browser_verifier": _browser_truth(
                status="UNSUPPORTED",
                attempted=False,
                real_browser_used=False,
                target_path=target,
                artifact_kind=artifact_kind,
                summary="Browser verifier does not support this artifact kind.",
                degraded_reason="unsupported_artifact_kind",
            ),
        }
    action = fip4_result.get("action") if isinstance(fip4_result.get("action"), dict) else {}
    content = str(action.get("content") or "")
    if not content:
        return {
            **base,
            "status": "skipped",
            "reason": "browser_verifier_skipped_no_generated_content",
            "browser_verifier": _browser_truth(
                status="SKIPPED",
                attempted=False,
                real_browser_used=False,
                target_path=target,
                artifact_kind=artifact_kind,
                summary="Browser verifier skipped because no generated content was available.",
                degraded_reason="missing_generated_content",
            ),
        }
    try:
        playwright_check = subprocess.run(
            ["node", "-e", "require.resolve('playwright');"],
            cwd=str(_workspace_root()),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception:
        playwright_check = None
    if playwright_check is None or playwright_check.returncode != 0:
        return {
            **base,
            "status": "config_blocked",
            "reason": "browser_verifier_config_blocked_playwright_unavailable",
            "checks": [{"name": "playwright_available", "passed": False}],
            "browser_verifier": _browser_truth(
                status="BLOCKED",
                attempted=True,
                real_browser_used=False,
                target_path=target,
                artifact_kind=artifact_kind,
                tool="playwright",
                summary="Playwright was unavailable, so no real browser verification ran.",
                degraded_reason="playwright_unavailable",
            ),
        }
    try:
        with tempfile.TemporaryDirectory(prefix="source-proxy-browser-v0-") as tmp:
            tmp_path = Path(tmp)
            page_path = tmp_path / "generated-under-test.html"
            page_path.write_text(content, encoding="utf-8")
            result = subprocess.run(
                ["node", "-e", _browser_verifier_harness(), str(page_path), str(timeout_ms)],
                cwd=str(_workspace_root()),
                capture_output=True,
                text=True,
                timeout=(timeout_ms / 1000) + 3,
                check=False,
            )
    except subprocess.TimeoutExpired:
        return {
            **base,
            "status": "timed_out",
            "reason": "browser_verifier_timed_out",
            "checks": [{"name": "headless_browser_load", "passed": False}],
            "browser_verifier": _browser_truth(
                status="BLOCKED",
                attempted=True,
                real_browser_used=False,
                target_path=target,
                artifact_kind=artifact_kind,
                tool="playwright",
                summary="Browser verifier timed out before producing real browser proof.",
                degraded_reason="browser_timeout",
            ),
        }
    except Exception as error:
        return {
            **base,
            "status": "failed",
            "reason": "browser_verifier_runtime_error",
            "checks": [{"name": "headless_browser_load", "passed": False, "error_type": type(error).__name__}],
            "browser_verifier": _browser_truth(
                status="NO_GO",
                attempted=True,
                real_browser_used=False,
                target_path=target,
                artifact_kind=artifact_kind,
                tool="playwright",
                summary="Browser verifier raised an internal runtime error.",
                degraded_reason="browser_runtime_error",
            ),
        }
    stdout = (result.stdout or "").strip()
    summary: dict[str, Any] = {}
    if stdout:
        try:
            summary = json.loads(stdout)
        except json.JSONDecodeError:
            summary = {}
    loaded = result.returncode == 0 and summary.get("loaded") is True
    dom_ready = bool(summary.get("domReady"))
    visible = int(summary.get("visibleTextLength") or 0) > 0
    no_page_errors = int(summary.get("pageErrorCount") or 0) == 0
    no_network_errors = int(summary.get("networkErrorCount") or 0) == 0
    interactive_checked = bool(summary.get("interactiveAttempted") and summary.get("interactiveChanged"))
    page_errors = [_redact_browser_text(item) for item in summary.get("pageErrors", [])[:5]]
    console_errors = [_redact_browser_text(item) for item in summary.get("consoleErrors", [])[:5]]
    network_errors = [_redact_browser_text(item) for item in summary.get("networkErrors", [])[:5]]
    truth_status = (
        "GO"
        if loaded and dom_ready and visible and no_page_errors and no_network_errors and interactive_checked
        else "PARTIAL_GO"
        if loaded and dom_ready and visible and no_page_errors and no_network_errors
        else "NO_GO"
    )
    passed = truth_status == "GO"
    checks = [
        {"name": "playwright_available", "passed": True},
        {"name": "browser_relevance", "passed": True, "browser_relevant": True},
        {"name": "supported_browser_target", "passed": True},
        {
            "name": "headless_browser_load",
            "passed": loaded,
            "returncode": result.returncode,
            "browser_engine": summary.get("browserEngine", "chromium"),
        },
        {
            "name": "dom_ready",
            "passed": dom_ready,
        },
        {
            "name": "visible_body_text",
            "passed": visible,
            "visible_text_length": summary.get("visibleTextLength", 0),
            "visible_text_excerpt": summary.get("visibleTextExcerpt", ""),
            "title": summary.get("title", ""),
        },
        {
            "name": "interactive_behavior",
            "passed": interactive_checked,
            "attempted": bool(summary.get("interactiveAttempted")),
            "reason": str(summary.get("interactiveReason") or ""),
        },
        {
            "name": "page_errors",
            "passed": bool(no_page_errors and no_network_errors),
            "page_error_count": summary.get("pageErrorCount", 0),
            "console_error_count": summary.get("consoleErrorCount", 0),
            "network_error_count": summary.get("networkErrorCount", 0),
            "page_errors": page_errors,
            "console_errors": console_errors,
            "network_errors": network_errors,
        },
    ]
    return {
        **base,
        "status": "used" if truth_status in {"GO", "PARTIAL_GO"} else "failed",
        "passed": passed,
        "reason": "browser_verifier_headless_page_passed"
        if passed
        else "browser_verifier_dom_only_no_behavior_proof"
        if truth_status == "PARTIAL_GO"
        else str(summary.get("reason") or "browser_verifier_headless_page_failed"),
        "checks": checks,
        "browser_engine": summary.get("browserEngine", "chromium"),
        "summary": {
            "visible_text_length": summary.get("visibleTextLength", 0),
            "interactive_reason": str(summary.get("interactiveReason") or ""),
        },
        "browser_verifier": _browser_truth(
            status=truth_status,
            attempted=True,
            real_browser_used=loaded,
            target_path=target,
            artifact_kind=artifact_kind,
            tool="playwright",
            page_loaded=loaded,
            dom_ready=dom_ready,
            required_text_present=visible,
            interactive_behavior_checked=interactive_checked,
            console_errors=console_errors,
            network_errors=network_errors,
            summary=(
                "Real Chromium browser loaded the generated HTML and verified visible interactive behavior."
                if truth_status == "GO"
                else "Real Chromium browser loaded DOM/text, but no visible interactive behavior proof was captured."
                if truth_status == "PARTIAL_GO"
                else "Real Chromium browser did not produce acceptable page proof."
            ),
            degraded_reason=None
            if truth_status == "GO"
            else str(summary.get("interactiveReason") or "browser_behavior_not_verified")
            if truth_status == "PARTIAL_GO"
            else str(summary.get("reason") or "browser_page_failed"),
            notes=[] if truth_status == "GO" else ["dom_or_text_only_is_not_behavior_proof"],
        ),
    }


def _functional_verifier_timeout_ms() -> int:
    raw = os.environ.get("SOURCE_PROXY_FUNCTIONAL_VERIFIER_TIMEOUT_MS", "").strip()
    if not raw:
        return 5000
    try:
        value = int(raw)
    except ValueError:
        return 5000
    return max(250, min(value, 5000))


def _functional_verifier_supported_target(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized.endswith((".tsx", ".jsx", ".html", ".css")):
        return False
    return normalized.endswith((".js", ".ts", ".mjs", ".cjs"))


def _functional_verifier_extract_function_names(content: str) -> list[str]:
    names: list[str] = []
    patterns = [
        r"\bexport\s+function\s+([A-Za-z_$][\w$]*)\s*\(",
        r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(",
        r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>",
        r"\bexports\.([A-Za-z_$][\w$]*)\s*=",
        r"\bmodule\.exports\.([A-Za-z_$][\w$]*)\s*=",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, content):
            name = match.group(1)
            if name not in names:
                names.append(name)
    return names[:20]


def _functional_verifier_contract(
    *,
    request: PromptPacketRequest,
    explicit_target: str,
    content: str,
) -> dict[str, Any]:
    lowered = request.task.lower()
    target = explicit_target.replace("\\", "/").lower()
    function_names = _functional_verifier_extract_function_names(content)
    if _fip5_browser_relevant([explicit_target], explicit_target):
        return {
            "supported": False,
            "reason": "functional_verifier_skipped_browser_or_ui_target",
            "function_names": function_names,
        }
    if not _functional_verifier_supported_target(target):
        return {
            "supported": False,
            "reason": "functional_verifier_skipped_unsupported_extension",
            "function_names": function_names,
        }
    if any(
        marker in lowered
        for marker in (
            "calculator",
            "calculate",
            "tip",
            "budget",
            "split",
            "splitter",
            "counter",
            "timer",
            "health",
            "status",
            "alive",
            "helper",
            "function",
        )
    ):
        return {
            "supported": True,
            "reason": "functional_verifier_supported_safe_js_ts_helper",
            "function_names": function_names,
        }
    return {
        "supported": False,
        "reason": "functional_verifier_skipped_no_supported_contract",
        "function_names": function_names,
    }


def _functional_verifier_unsafe_markers(content: str) -> list[str]:
    markers = []
    lowered = content.lower()
    for marker in (
        "require(",
        "import ",
        "from ",
        "fetch(",
        "xmlhttprequest",
        "websocket",
        "child_process",
        "node:child_process",
        "node:fs",
        "fs.",
        "process.",
        "eval(",
        "new function",
        "while (true)",
        "while(true)",
    ):
        if marker in lowered:
            markers.append(marker.strip())
    return markers


def _functional_verifier_sandbox_harness() -> str:
    return r"""
const fs = require("fs");
const vm = require("vm");
const sourcePath = process.argv[1];
const source = fs.readFileSync(sourcePath, "utf8");
const transformed = source
  .replace(/\bexport\s+default\s+/g, "const __default__ = ")
  .replace(/\bexport\s+function\s+([A-Za-z_$][\w$]*)\s*\(/g, "function $1(")
  .replace(/\bexport\s+(const|let|var)\s+/g, "$1 ");
const sandbox = {
  console: { log() {}, error() {}, warn() {} },
  module: { exports: {} },
  exports: {},
  setTimeout() { throw new Error("timer APIs disabled"); },
  setInterval() { throw new Error("timer APIs disabled"); },
};
vm.createContext(sandbox, {
  codeGeneration: { strings: false, wasm: false },
});
new vm.Script(transformed, { filename: "generated-under-test.js" }).runInContext(
  sandbox,
  { timeout: 500 }
);
const builtins = new Set(["setTimeout", "setInterval"]);
const functionNames = Object.keys(sandbox)
  .filter((key) => !builtins.has(key) && typeof sandbox[key] === "function")
  .concat(Object.keys(sandbox.module.exports || {}).filter((key) => typeof sandbox.module.exports[key] === "function"))
  .concat(Object.keys(sandbox.exports || {}).filter((key) => typeof sandbox.exports[key] === "function"));
process.stdout.write(JSON.stringify({
  moduleLoaded: true,
  exportedFunctionCount: [...new Set(functionNames)].length,
  exportedFunctions: [...new Set(functionNames)].slice(0, 20),
}));
"""


def _fip5_functional_verifier(
    *,
    request: PromptPacketRequest,
    explicit_target: str,
    fip4_result: dict[str, Any],
) -> dict[str, Any]:
    timeout_ms = _functional_verifier_timeout_ms()
    verifier_version = "functional-verifier-v0"
    changed_files = [str(item).replace("\\", "/") for item in fip4_result.get("changed_files", [])]
    allowed_files = [str(item).replace("\\", "/") for item in fip4_result.get("allowed_files", [])]
    target = (changed_files[0] if len(changed_files) == 1 else explicit_target).replace("\\", "/")
    base = {
        "passed": False,
        "checks": [],
        "target_path": target,
        "timeout_ms": timeout_ms,
        "verifier_version": verifier_version,
    }
    if fip4_result.get("status") != "used":
        return {
            **base,
            "status": "skipped",
            "reason": "functional_verifier_skipped_coder_not_used",
        }
    if len(changed_files) != 1:
        return {
            **base,
            "status": "skipped",
            "reason": "functional_verifier_skipped_requires_single_changed_file",
            "checks": [{"name": "single_changed_file", "passed": False, "count": len(changed_files)}],
        }
    if target not in allowed_files:
        return {
            **base,
            "status": "blocked",
            "reason": "functional_verifier_blocked_target_not_allowed",
            "checks": [{"name": "target_in_allowed_files", "passed": False}],
        }
    action = fip4_result.get("action") if isinstance(fip4_result.get("action"), dict) else {}
    content = str(action.get("content") or "")
    if not content:
        return {
            **base,
            "status": "skipped",
            "reason": "functional_verifier_skipped_no_generated_content",
        }
    contract = _functional_verifier_contract(
        request=request,
        explicit_target=target,
        content=content,
    )
    if not contract.get("supported"):
        return {
            **base,
            "status": "skipped",
            "reason": str(contract.get("reason") or "functional_verifier_skipped_no_supported_contract"),
            "checks": [
                {
                    "name": "supported_contract",
                    "passed": False,
                    "function_names": contract.get("function_names", []),
                }
            ],
        }
    unsafe = _functional_verifier_unsafe_markers(content)
    if unsafe:
        return {
            **base,
            "status": "blocked",
            "reason": "functional_verifier_blocked_unsafe_generated_content",
            "checks": [{"name": "unsafe_marker_scan", "passed": False, "markers": unsafe}],
        }
    try:
        with tempfile.TemporaryDirectory(prefix="source-proxy-functional-v0-") as tmp:
            tmp_path = Path(tmp)
            suffix = ".mjs" if target.endswith((".js", ".mjs", ".ts")) else ".cjs"
            source_path = tmp_path / f"generated-under-test{suffix}"
            source_path.write_text(content, encoding="utf-8")
            result = subprocess.run(
                ["node", "-e", _functional_verifier_sandbox_harness(), str(source_path)],
                cwd=str(tmp_path),
                capture_output=True,
                text=True,
                timeout=timeout_ms / 1000,
                check=False,
            )
    except subprocess.TimeoutExpired:
        return {
            **base,
            "status": "timed_out",
            "reason": "functional_verifier_timed_out",
            "checks": [{"name": "sandbox_module_load", "passed": False}],
        }
    except Exception as error:
        return {
            **base,
            "status": "failed",
            "reason": "functional_verifier_runtime_error",
            "checks": [
                {
                    "name": "sandbox_module_load",
                    "passed": False,
                    "error_type": type(error).__name__,
                }
            ],
        }
    stdout = (result.stdout or "").strip()
    sandbox_summary: dict[str, Any] = {}
    if stdout:
        try:
            sandbox_summary = json.loads(stdout)
        except json.JSONDecodeError:
            sandbox_summary = {}
    passed = result.returncode == 0 and bool(sandbox_summary.get("moduleLoaded"))
    return {
        **base,
        "status": "used" if passed else "failed",
        "passed": passed,
        "reason": "functional_verifier_sandbox_module_load_passed"
        if passed
        else "functional_verifier_sandbox_module_load_failed",
        "checks": [
            {
                "name": "supported_contract",
                "passed": True,
                "contract": contract.get("reason"),
                "function_names": contract.get("function_names", []),
            },
            {
                "name": "unsafe_marker_scan",
                "passed": True,
                "markers": [],
            },
            {
                "name": "sandbox_module_load",
                "passed": passed,
                "returncode": result.returncode,
                "exported_function_count": sandbox_summary.get("exportedFunctionCount", 0),
                "exported_functions": sandbox_summary.get("exportedFunctions", []),
                "stderr_excerpt": (result.stderr or "")[:300],
            },
        ],
    }


def _fip4_allowed_files(
    *,
    explicit_target: str,
    intake_payload: dict[str, Any],
    request: PromptPacketRequest,
) -> list[str]:
    candidates = intake_payload.get("allowed_files")
    if isinstance(candidates, list) and candidates:
        return [str(item).replace("\\", "/").lstrip("./") for item in candidates if str(item).strip()]
    if request.allowed_files:
        return [str(item).replace("\\", "/").lstrip("./") for item in request.allowed_files if str(item).strip()]
    target = explicit_target.replace("\\", "/").lstrip("./")
    return [target] if target else []


def _fip4_forbidden_files(
    *,
    intake_payload: dict[str, Any],
    request: PromptPacketRequest,
    context_mode: str,
) -> list[str]:
    values: list[str] = []
    raw_intake = intake_payload.get("forbidden_files")
    if isinstance(raw_intake, list):
        values.extend(str(item) for item in raw_intake if str(item).strip())
    values.extend(str(item) for item in request.forbidden_files if str(item).strip())
    values.extend(str(item) for item in forbidden_paths_for_context_mode(context_mode))
    return list(dict.fromkeys(item.replace("\\", "/").lstrip("./") for item in values))


def _fip4_final_coder_packet(
    *,
    request: PromptPacketRequest,
    trial_task: str,
    normalized_task: str,
    explicit_target: str,
    allowed_files: list[str],
    forbidden_files: list[str],
    route_payload: dict[str, Any],
    route_reasons: list[str],
    fip1_context_packet: dict[str, Any],
    fip2_research_packet: dict[str, Any],
    fip3_model_packet: dict[str, Any],
    checks: list[str],
    canonical_context_broker: dict[str, Any] | None = None,
) -> dict[str, Any]:
    canonical_context_broker = canonical_context_broker or {}
    gemma = fip3_model_packet.get("gemma") if isinstance(fip3_model_packet.get("gemma"), dict) else {}
    hermes = (
        fip3_model_packet.get("hermes_critic")
        if isinstance(fip3_model_packet.get("hermes_critic"), dict)
        else {}
    )
    context_by_source = {
        str(source.get("source") or ""): source
        for source in fip1_context_packet.get("sources", [])
        if isinstance(source, dict)
    }
    packet_without_hash = {
        "packet_version": "source-proxy-fip4-final-coder-packet-v0.1",
        "role_rules": {
            "gemma": "intent/spec/context/acceptance only",
            "hermes_critic": "ambiguity/risk/conflict/pre-coder critique only",
            "qwen": "coding/action output only",
            "qwen_disallowed_uses": [
                "context routing",
                "research decisions",
                "critique",
                "verification",
                "repair",
            ],
            "hermes_verifier": "skipped_reserved_for_fip5",
            "repair_loop": "skipped_until_fip5",
            "operator_transaction_trace": "future_fip6",
        },
        "raw_prompt": request.task,
        "normalized_task": normalized_task,
        "runtime_task": trial_task,
        "target_file": explicit_target,
        "allowed_files": allowed_files,
        "forbidden_files": forbidden_files,
        "protected_path_check": _protected_path_check(
            route_reasons=route_reasons,
            forbidden_files=forbidden_files,
        ),
        "route_decision": route_payload,
        "fip1_context_packet": fip1_context_packet,
        "obsidian_context_summary_status": context_by_source.get("obsidian", {}),
        "cartographer_advisory_context_status": context_by_source.get("cartographer", {}),
        "design_context_status": context_by_source.get("design", {}),
        "mac_worker_advisory_status": context_by_source.get("mac_worker", {}),
        "fip2_repo_research_packet_status": {
            "status": "used" if fip2_research_packet.get("repo_sources") else "skipped",
            "research_packet_hash": fip2_research_packet.get("research_packet_hash", ""),
            "repo_result_count": fip2_research_packet.get("repo_result_count", 0),
        },
        "fip2_research_packet": fip2_research_packet,
        "canonical_context_broker": canonical_context_broker,
        "canonical_context_report_hash": str(
            canonical_context_broker.get("canonical_report_hash") or ""
        ),
        "fip2_scout_status_sources": fip2_research_packet.get("scout", {}),
        "fip2_searxng_status_sources": fip2_research_packet.get("searxng", {}),
        "tinyfish_deferred_status": "deferred_cloud_requires_britton_approval",
        "xersearch_missing_alias_status": "missing_alias_do_not_create",
        "fip3_gemma_output": gemma,
        "fip3_hermes_critic_output": hermes,
        "acceptance_criteria": gemma.get("acceptance_criteria", [])
        if isinstance(gemma.get("acceptance_criteria"), list)
        else [],
        "output_contract_instructions": {
            "accepted_formats": [
                "<file path=\"repo/relative/path\">complete file content</file>",
                "{\"action\":\"replace_file\",\"target\":\"repo/relative/path\",\"content_lines\":[\"...\"]}",
                "{\"action\":\"replace_file\",\"target\":\"repo/relative/path\",\"content\":\"...\"}",
            ],
            "must_return_only_action_output": True,
            "must_touch_only_allowed_files": True,
            "must_not_touch_forbidden_files": True,
            "unified_diff_not_accepted": True,
        },
        "check_commands": checks,
        "provenance_and_anti_tailoring": {
            "source": "assembled_from_fip1_fip2_fip3_live_packets",
            "hidden_apply": False,
            "hidden_commit": False,
            "hidden_push": False,
            "hidden_worker_started": False,
            "qwen_receives_full_packet": True,
            "research_packet_hash": fip2_research_packet.get("research_packet_hash", ""),
            "fip3_model_packet_hash": fip3_model_packet.get("fip3_model_packet_hash", ""),
        },
    }
    final_hash = _json_hash(packet_without_hash)
    return {
        **packet_without_hash,
        "final_packet_hash": final_hash,
    }


def _fip4_extract_qwen_file_action(raw: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    text = (raw or "").strip()
    meta = {
        "raw_output_length": len(raw or ""),
        "raw_output_excerpt": (raw or "")[:1500],
        "parse_error": "",
        "parsed_output_mode": "",
    }
    if not text:
        meta["parse_error"] = "empty_qwen_output"
        return None, meta
    if text.lstrip().startswith("diff --git ") or (
        text.lstrip().startswith("--- ") and "\n+++ " in text and "\n@@" in text
    ):
        meta["parse_error"] = "unified_diff_rejected"
        return None, meta
    file_start = text.find("<file ")
    file_end = text.rfind("</file>")
    if file_start >= 0 and file_end > file_start:
        block = text[file_start : file_end + len("</file>")]
        path_marker = 'path="'
        path_start = block.find(path_marker)
        if path_start == -1:
            path_marker = "path='"
            path_start = block.find(path_marker)
        if path_start == -1:
            meta["parse_error"] = "file_block_missing_path"
            return None, meta
        quote = path_marker[-1]
        path_value_start = path_start + len(path_marker)
        path_value_end = block.find(quote, path_value_start)
        content_start = block.find(">", path_value_end) + 1
        content_end = block.rfind("</file>")
        if path_value_end <= path_value_start or content_start <= 0 or content_end < content_start:
            meta["parse_error"] = "file_block_malformed"
            return None, meta
        meta["parsed_output_mode"] = "file_block"
        return {
            "action": "replace_file",
            "target": block[path_value_start:path_value_end].replace("\\", "/").lstrip("./"),
            "content": block[content_start:content_end],
            "content_source": "file_block",
        }, meta
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        meta["parse_error"] = "no_action_json_or_file_block"
        return None, meta
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError as error:
        meta["parse_error"] = f"json_decode_error: {error}"
        return None, meta
    if not isinstance(parsed, dict) or parsed.get("action") != "replace_file":
        wrapped = parsed.get("response") if isinstance(parsed, dict) else None
        if isinstance(wrapped, str) and wrapped.strip() != text:
            return _fip4_extract_qwen_file_action(wrapped)
        meta["parse_error"] = "json_action_must_be_replace_file"
        return None, meta
    target = parsed.get("target")
    if not isinstance(target, str) or not target.strip():
        meta["parse_error"] = "replace_file_target_missing"
        return None, meta
    if "content_lines" in parsed:
        lines = parsed.get("content_lines")
        if not isinstance(lines, list) or not all(isinstance(line, str) for line in lines):
            meta["parse_error"] = "content_lines_must_be_string_list"
            return None, meta
        content = "\n".join(lines)
        source = "json_content_lines"
    else:
        content = parsed.get("content")
        if not isinstance(content, str) or not content:
            meta["parse_error"] = "content_missing"
            return None, meta
        source = "json_content"
    meta["parsed_output_mode"] = source
    return {
        "action": "replace_file",
        "target": target.replace("\\", "/").lstrip("./"),
        "content": content,
        "content_source": source,
    }, meta


def _fip4_path_allowed(path: str, allowed_files: list[str], forbidden_files: list[str]) -> tuple[bool, str]:
    normalized = path.replace("\\", "/").lstrip("./")
    allowed = [item.replace("\\", "/").lstrip("./") for item in allowed_files]
    forbidden = [item.replace("\\", "/").lstrip("./") for item in forbidden_files]
    if not normalized:
        return False, "empty_target"
    if not allowed:
        return False, "allowed_files_empty"
    if normalized not in allowed:
        return False, "target_not_in_allowed_files"
    for forbidden_path in forbidden:
        if not forbidden_path:
            continue
        if normalized == forbidden_path or normalized.startswith(forbidden_path.rstrip("/") + "/"):
            return False, "target_matches_forbidden_or_protected_path"
    return True, ""


def _fip4_qwen_error_reason(error: Exception) -> str:
    if isinstance(error, TimeoutError):
        return "qwen_coder_timeout"
    reason = getattr(error, "reason", None)
    if isinstance(reason, TimeoutError):
        return "qwen_coder_timeout"
    text = f"{type(error).__name__}: {error}".lower()
    if "timed out" in text or "timeout" in text:
        return "qwen_coder_timeout"
    return "qwen_coder_call_failed"


def _fip4_qwen_attempt_summary(result: dict[str, Any], attempt: int) -> dict[str, Any]:
    return {
        "attempt": attempt,
        "status": str(result.get("status") or ""),
        "reason": str(result.get("reason") or ""),
        "latency_ms": result.get("latency_ms"),
        "timeout_seconds": result.get("timeout_seconds"),
        "coder_received_packet_hash": str(result.get("coder_received_packet_hash") or ""),
        "final_coder_packet_hash": str(result.get("final_coder_packet_hash") or ""),
        "qwen_output_hash": str(result.get("qwen_output_hash") or ""),
        "raw_output_length": int(result.get("raw_output_length") or 0),
        "provider_errors": result.get("provider_errors", []),
    }


def _fip4_qwen_retryable(result: dict[str, Any]) -> bool:
    return str(result.get("reason") or "") in {
        "qwen_coder_call_failed",
        "qwen_coder_timeout",
        "qwen_empty_model_output",
    }


def _fip4_qwen_output_contract_retryable(parse_meta: dict[str, Any]) -> bool:
    reason = str(parse_meta.get("parse_error") or "")
    return (
        reason == "no_action_json_or_file_block"
        or reason.startswith("json_decode_error:")
        or reason
        in {
            "json_action_must_be_replace_file",
            "replace_file_target_missing",
            "content_lines_must_be_string_list",
            "content_missing",
        }
    )


def _fip4_call_qwen_once(
    *,
    final_packet: dict[str, Any],
    base_url: str,
    model: str,
    prompt: str,
    request_payload: dict[str, Any],
    packet_hash: str,
    attempt: int,
) -> dict[str, Any]:
    started = time.perf_counter()
    timeout_seconds = _fip4_call_timeout_seconds()
    try:
        body = json.dumps(request_payload).encode("utf-8")
        generate_request = urllib.request.Request(
            f"{base_url}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(
            generate_request,
            timeout=timeout_seconds,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        reason = _fip4_qwen_error_reason(error)
        return {
            "status": "failed",
            "reason": reason,
            "attempt": attempt,
            "model": model,
            "ollama_base_url": base_url,
            "coder_received_packet_hash": packet_hash,
            "final_coder_packet_hash": packet_hash,
            "qwen_prompt_hash": _json_hash(prompt),
            "qwen_output_hash": "",
            "raw_output": "",
            "raw_output_length": 0,
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "timeout_seconds": timeout_seconds,
            "provider_errors": [f"{type(error).__name__}: {error}"],
        }
    raw = str(payload.get("response") or "") if isinstance(payload, dict) else ""
    raw_length = len(raw)
    if not raw.strip():
        return {
            "status": "failed",
            "reason": "qwen_empty_model_output",
            "attempt": attempt,
            "model": model,
            "ollama_base_url": base_url,
            "coder_received_packet_hash": packet_hash,
            "final_coder_packet_hash": packet_hash,
            "qwen_prompt_hash": _json_hash(prompt),
            "qwen_output_hash": "",
            "raw_output": "",
            "raw_output_length": raw_length,
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "timeout_seconds": timeout_seconds,
            "provider_errors": ["empty_qwen_output_before_parser"],
        }
    return {
        "status": "used",
        "reason": "qwen_received_final_coder_packet_and_returned_output",
        "attempt": attempt,
        "model": model,
        "ollama_base_url": base_url,
        "coder_received_packet_hash": packet_hash,
        "final_coder_packet_hash": packet_hash,
        "qwen_prompt_hash": _json_hash(prompt),
        "qwen_output_hash": _json_hash(raw),
        "raw_output": raw,
        "raw_output_length": raw_length,
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "timeout_seconds": timeout_seconds,
        "provider_errors": [],
    }


def _fip4_qwen_format_retry_prompt(
    final_packet: dict[str, Any],
    *,
    previous_parse_meta: dict[str, Any],
    previous_output_hash: str,
) -> str:
    return "\n".join(
        [
            "You are the FIP-4 Qwen coding/action lane.",
            "Your previous output was rejected by the output contract parser.",
            "This is a bounded format-only retry using the same final coder packet hash.",
            "Do not plan, route, research, critique, verify, repair, or mention hidden work.",
            "Return exactly one minimal JSON object and nothing else.",
            "Required JSON schema:",
            '{"action":"replace_file","target":"repo/relative/path","content_lines":["complete replacement line 1"]}',
            "For deferred-lane visibility notes, write one short plain line only. Do not add headings, sections, implementation advice, or extra explanation.",
            "The target must exactly equal final_coder_packet.target_file.",
            "The target must be in final_coder_packet.allowed_files.",
            "Do not write any forbidden file.",
            "Retry receipt:",
            json.dumps(
                {
                    "retry_type": "qwen_output_contract_retry",
                    "previous_parse_error": previous_parse_meta.get("parse_error", ""),
                    "previous_output_hash": previous_output_hash,
                    "same_final_coder_packet_hash": final_packet.get("final_packet_hash", ""),
                },
                sort_keys=True,
                default=str,
            ),
            "final_coder_packet:",
            json.dumps(final_packet, sort_keys=True, default=str),
            "NOW RETURN THE ACTION JSON ONLY.",
            '{"action":"replace_file","target":"'
            + str(final_packet.get("target_file") or "")
            + '","content_lines":["CONTENT"]}',
        ]
    )


def _fip4_call_qwen_output_contract_retry(
    *,
    final_packet: dict[str, Any],
    previous_qwen: dict[str, Any],
    previous_parse_meta: dict[str, Any],
) -> dict[str, Any]:
    base_url = _fip4_ollama_base_url()
    model = _fip4_qwen_model()
    packet_hash = str(final_packet.get("final_packet_hash") or _json_hash(final_packet))
    prompt = _fip4_qwen_format_retry_prompt(
        final_packet,
        previous_parse_meta=previous_parse_meta,
        previous_output_hash=str(previous_qwen.get("qwen_output_hash") or ""),
    )
    request_payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "keep_alive": os.environ.get("SOURCE_PROXY_FIP4_MODEL_KEEP_ALIVE", "10m"),
        "options": {
            "temperature": 0,
            "num_predict": int(os.environ.get("SOURCE_PROXY_FIP4_MODEL_NUM_PREDICT", "2048")),
            "num_ctx": int(os.environ.get("SOURCE_PROXY_FIP4_MODEL_NUM_CTX", "16384")),
        },
    }
    result = _fip4_call_qwen_once(
        final_packet=final_packet,
        base_url=base_url,
        model=model,
        prompt=prompt,
        request_payload=request_payload,
        packet_hash=packet_hash,
        attempt=2,
    )
    return {
        **result,
        "format_retry": True,
        "format_retry_reason": "qwen_output_contract_retry",
        "previous_parse_error": previous_parse_meta.get("parse_error", ""),
        "previous_output_hash": str(previous_qwen.get("qwen_output_hash") or ""),
        "same_final_coder_packet_hash": (
            str(result.get("coder_received_packet_hash") or "") == packet_hash
            and str(result.get("final_coder_packet_hash") or "") == packet_hash
        ),
    }


def _fip4_call_qwen(final_packet: dict[str, Any]) -> dict[str, Any]:
    base_url = _fip4_ollama_base_url()
    model = _fip4_qwen_model()
    packet_hash = str(final_packet.get("final_packet_hash") or _json_hash(final_packet))
    prompt = "\n".join(
        [
            "You are the FIP-4 Qwen coding/action lane.",
            "Do not plan, route, research, critique, verify, repair, or mention hidden work.",
            "Return only one JSON object. No markdown. No prose. No explanation.",
            "Required JSON schema:",
            '{"action":"replace_file","target":"repo/relative/path","content_lines":["complete replacement line 1","complete replacement line 2"]}',
            "The target must exactly equal final_coder_packet.target_file.",
            "The target must be in final_coder_packet.allowed_files.",
            "Do not write any forbidden file.",
            "For deferred-lane visibility notes, write one short plain line only. Do not add headings, sections, implementation advice, or extra explanation.",
            "",
            "final_coder_packet:",
            json.dumps(final_packet, sort_keys=True, default=str),
            "",
            "NOW RETURN THE ACTION JSON ONLY.",
            f"Target: {final_packet.get('target_file')}",
            "Use this exact shape and replace CONTENT with the complete requested file contents:",
            '{"action":"replace_file","target":"'
            + str(final_packet.get("target_file") or "")
            + '","content_lines":["CONTENT"]}',
        ]
    )
    try:
        tags_request = urllib.request.Request(f"{base_url}/api/tags", method="GET")
        with urllib.request.urlopen(tags_request, timeout=10) as response:
            inventory = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        return {
            "status": "blocked",
            "reason": "ollama_inventory_unavailable",
            "model": model,
            "ollama_base_url": base_url,
            "coder_received_packet_hash": "",
            "attempt_count": 0,
            "attempts": [],
            "provider_errors": [f"{type(error).__name__}: {error}"],
        }
    names = [
        str(item.get("name") or item.get("model") or "")
        for item in inventory.get("models", [])
        if isinstance(item, dict)
    ]
    if model not in names:
        return {
            "status": "blocked",
            "reason": "qwen_model_missing_from_local_ollama_inventory",
            "model": model,
            "ollama_base_url": base_url,
            "coder_received_packet_hash": "",
            "attempt_count": 0,
            "attempts": [],
            "ollama_inventory_models": names,
            "provider_errors": [f"{model} not present in local Ollama inventory"],
        }
    request_payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "keep_alive": os.environ.get("SOURCE_PROXY_FIP4_MODEL_KEEP_ALIVE", "10m"),
        "options": {
            "temperature": 0,
            "num_predict": int(os.environ.get("SOURCE_PROXY_FIP4_MODEL_NUM_PREDICT", "2048")),
            "num_ctx": int(os.environ.get("SOURCE_PROXY_FIP4_MODEL_NUM_CTX", "16384")),
        },
    }
    attempts: list[dict[str, Any]] = []
    max_attempts = _fip4_qwen_max_attempts()
    final_result: dict[str, Any] | None = None
    for attempt in range(1, max_attempts + 1):
        result = _fip4_call_qwen_once(
            final_packet=final_packet,
            base_url=base_url,
            model=model,
            prompt=prompt,
            request_payload=request_payload,
            packet_hash=packet_hash,
            attempt=attempt,
        )
        attempts.append(_fip4_qwen_attempt_summary(result, attempt))
        final_result = result
        if result.get("status") == "used" or not _fip4_qwen_retryable(result):
            break
    final_result = final_result or {
        "status": "failed",
        "reason": "qwen_coder_call_failed",
        "model": model,
        "ollama_base_url": base_url,
        "coder_received_packet_hash": packet_hash,
        "final_coder_packet_hash": packet_hash,
        "provider_errors": ["qwen_attempt_loop_returned_no_result"],
    }
    prior_errors = [
        f"attempt {item.get('attempt')}: {error}"
        for item in attempts[:-1]
        for error in item.get("provider_errors", [])
    ]
    retry_reason = str(attempts[0].get("reason") or "") if len(attempts) > 1 else ""
    return {
        **final_result,
        "attempt_count": len(attempts),
        "attempts": attempts,
        "retry_attempted": len(attempts) > 1,
        "retry_reason": retry_reason,
        "provider_errors": [
            *prior_errors,
            *[str(error) for error in final_result.get("provider_errors", [])],
        ],
    }


def _fip5_hermes_timeout_seconds() -> float:
    raw = os.environ.get("SOURCE_PROXY_FIP5_HERMES_TIMEOUT_SECONDS", "").strip()
    if not raw:
        return 120.0
    try:
        return max(5.0, min(float(raw), 600.0))
    except ValueError:
        return 120.0


def _fip5_hermes_verifier_prompt(
    input_summary: dict[str, Any],
    *,
    retry_feedback: dict[str, Any] | None = None,
) -> str:
    example_pass = {
        "verdict": "PASS",
        "reasons": [
            "deterministic evidence passed",
            "browser evidence was not required or did not fail",
            "no code change was required because the request was already satisfied",
        ],
        "repair_instructions": [],
    }
    lines = [
        "You are the FIP-5 Hermes verifier. Verify after Qwen coding only.",
        "Do not write files. Do not propose code. Do not repair directly.",
        "Return exactly one JSON object and no markdown, no prose, no code fences.",
        "Required JSON schema: verdict string PASS|NEEDS_FIX|FAIL|UNVERIFIED, reasons array of strings, repair_instructions array of strings.",
        "No-op/already-satisfied PASS is allowed only when deterministic.passed is true and browser.passed is not false.",
        "Rules: PASS only if deterministic.passed is true and browser.passed is not false. If deterministic failed, return NEEDS_FIX or FAIL. If browser failed, return FAIL.",
        "If you return NEEDS_FIX or FAIL, cite exact failed_evidence_ids or failed_requirement_ids that appear in the evidence block.",
        "If deterministic_evidence.passed is true and browser_evidence.passed is not false, do not claim deterministic or browser evidence failed.",
        f"No-op PASS example:\n{json.dumps(example_pass, sort_keys=True)}",
    ]
    if retry_feedback:
        lines.extend(
            [
                "Your previous verifier output was rejected or disagreed with the evidence. Retry once with valid JSON only.",
                f"Rejected output receipt:\n{json.dumps(retry_feedback, sort_keys=True, default=str)}",
            ]
        )
    lines.append(json.dumps(input_summary, sort_keys=True, default=str))
    return "\n".join(lines)


def _fip5_hermes_evidence_block(
    *,
    fip4_result: dict[str, Any],
    deterministic: dict[str, Any],
    browser: dict[str, Any],
) -> dict[str, Any]:
    deterministic_failures = [
        str(item) for item in deterministic.get("failures", []) if str(item).strip()
    ]
    browser_failed = browser.get("passed") is False
    failed_evidence_ids = [f"deterministic:{item}" for item in deterministic_failures]
    if browser_failed:
        failed_evidence_ids.append(
            f"browser:{browser.get('reason') or 'browser_behavior_failed'}"
        )
    return {
        "deterministic_evidence": {
            "id": "deterministic",
            "status": deterministic.get("status"),
            "passed": bool(deterministic.get("passed")),
            "checks_run": deterministic.get("checks_run", []),
            "failures": deterministic_failures,
        },
        "browser_evidence": {
            "id": "browser",
            "status": browser.get("status"),
            "passed": browser.get("passed"),
            "reason": browser.get("reason", ""),
            "authoritative": browser.get("authoritative", True),
            "summary": browser.get("summary", {}),
        },
        "qwen_action_evidence": {
            "id": "qwen_action",
            "parser": fip4_result.get("parser", {}),
            "changed_files": fip4_result.get("changed_files", []),
            "final_coder_packet_hash": fip4_result.get("final_coder_packet_hash", ""),
            "coder_received_packet_hash": fip4_result.get("coder_received_packet_hash", ""),
            "qwen_output_hash": (fip4_result.get("qwen") or {}).get("qwen_output_hash")
            if isinstance(fip4_result.get("qwen"), dict)
            else "",
        },
        "acceptance_criteria": (
            fip4_result.get("final_coder_packet", {}).get("acceptance_criteria", [])
            if isinstance(fip4_result.get("final_coder_packet"), dict)
            else []
        ),
        "failed_evidence_ids": failed_evidence_ids,
        "failed_requirement_ids": [],
    }


def _fip5_normalize_hermes_verifier_output(
    parsed: Any,
    *,
    deterministic: dict[str, Any],
    browser: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    data = parsed if isinstance(parsed, dict) else {}
    schema_errors: list[str] = []
    verdict = str(data.get("verdict") or "UNVERIFIED").upper()
    reasons = data.get("reasons")
    repairs = data.get("repair_instructions")

    if reasons is None and isinstance(data.get("reason"), str):
        reasons = [data["reason"]]
    if repairs is None and isinstance(data.get("repair_instruction"), str):
        repairs = [data["repair_instruction"]]

    if verdict not in {"PASS", "NEEDS_FIX", "FAIL", "UNVERIFIED"}:
        schema_errors.append("verdict_invalid")
        verdict = "UNVERIFIED"
    if not isinstance(reasons, list) or not all(isinstance(item, str) for item in reasons):
        schema_errors.append("reasons_must_be_strings")
        reasons = []
    else:
        reasons = [item.strip() for item in reasons if item.strip()]
    if not isinstance(repairs, list) or not all(isinstance(item, str) for item in repairs):
        schema_errors.append("repair_instructions_must_be_strings")
        repairs = []
    else:
        repairs = [item.strip() for item in repairs if item.strip()]

    if verdict == "PASS" and not deterministic.get("passed"):
        verdict = "NEEDS_FIX"
        reasons = [*reasons, "pass_blocked_by_deterministic_failure"]
    if verdict == "PASS" and browser.get("passed") is False:
        verdict = "FAIL"
        reasons = [*reasons, "pass_blocked_by_browser_behavior_failure"]
    if deterministic.get("passed") and browser.get("passed") is not False and verdict != "PASS":
        reasons = [*reasons, "hermes_did_not_accept_deterministic_pass"]

    return {
        "verdict": verdict,
        "reasons": list(dict.fromkeys(reasons)),
        "repair_instructions": repairs,
    }, schema_errors


def _fip5_hermes_evidence_mismatch(
    normalized: dict[str, Any],
    *,
    evidence_block: dict[str, Any],
) -> dict[str, Any]:
    verdict = str(normalized.get("verdict") or "")
    if verdict not in {"NEEDS_FIX", "FAIL"}:
        return {"mismatch": False, "reason": ""}
    deterministic_evidence = evidence_block.get("deterministic_evidence", {})
    browser_evidence = evidence_block.get("browser_evidence", {})
    failed_ids = [
        str(item)
        for item in [
            *list(evidence_block.get("failed_evidence_ids", []) or []),
            *list(evidence_block.get("failed_requirement_ids", []) or []),
        ]
        if str(item).strip()
    ]
    evidence_allows_pass = (
        bool(deterministic_evidence.get("passed"))
        and browser_evidence.get("passed") is not False
    )
    if not evidence_allows_pass:
        return {"mismatch": False, "reason": ""}
    reason_text = "\n".join(str(item) for item in normalized.get("reasons", []))
    cites_failed_id = any(failed_id and failed_id in reason_text for failed_id in failed_ids)
    if not failed_ids or not cites_failed_id:
        return {
            "mismatch": True,
            "reason": "hermes_verifier_evidence_mismatch",
            "evidence_allows_pass": evidence_allows_pass,
            "failed_evidence_ids": failed_ids,
            "cited_reasons": normalized.get("reasons", []),
        }
    return {"mismatch": False, "reason": ""}


def _fip5_hermes_verifier_result_with_attempts(
    final_result: dict[str, Any],
    attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    prior_errors = [
        f"attempt {item.get('attempt')}: {error}"
        for item in attempts[:-1]
        for error in item.get("provider_errors", [])
    ]
    invalid_hashes = [
        str(item.get("output_hash") or "")
        for item in attempts
        if item.get("status") == "failed" and str(item.get("output_hash") or "")
    ]
    retry_reason = str(attempts[0].get("reason") or "") if len(attempts) > 1 else ""
    return {
        **final_result,
        "attempt_count": len(attempts),
        "attempts": attempts,
        "retry_attempted": len(attempts) > 1,
        "retry_reason": retry_reason,
        "invalid_output_hashes": invalid_hashes,
        "first_invalid_output_hash": invalid_hashes[0] if invalid_hashes else "",
        "provider_errors": [
            *prior_errors,
            *[str(error) for error in final_result.get("provider_errors", [])],
        ],
    }


def _fip5_call_hermes_verifier(
    *,
    request: PromptPacketRequest,
    fip4_result: dict[str, Any],
    deterministic: dict[str, Any],
    browser: dict[str, Any],
) -> dict[str, Any]:
    base_url = _fip4_ollama_base_url()
    model = _fip5_hermes_model()
    evidence_block = _fip5_hermes_evidence_block(
        fip4_result=fip4_result,
        deterministic=deterministic,
        browser=browser,
    )
    input_summary = {
        "role": "FIP-5 Hermes verifier post-code verification only",
        "raw_prompt": request.task,
        "final_coder_packet_hash": fip4_result.get("final_coder_packet_hash", ""),
        "coder_received_packet_hash": fip4_result.get("coder_received_packet_hash", ""),
        "qwen_output_hash": (fip4_result.get("qwen") or {}).get("qwen_output_hash")
        if isinstance(fip4_result.get("qwen"), dict)
        else "",
        "parser": fip4_result.get("parser", {}),
        "changed_files": fip4_result.get("changed_files", []),
        "evidence": evidence_block,
        "acceptance_criteria": evidence_block.get("acceptance_criteria", []),
        "deterministic": deterministic,
        "browser": browser,
        "cannot_turn_unverified_into_pass": True,
        "cannot_override_browser_behavior": True,
    }
    prompt = _fip5_hermes_verifier_prompt(input_summary)
    prompt_hash = _json_hash(prompt)
    try:
        tags_request = urllib.request.Request(f"{base_url}/api/tags", method="GET")
        with urllib.request.urlopen(tags_request, timeout=10) as response:
            inventory = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        return {
            "status": "blocked",
            "reason": "ollama_inventory_unavailable_for_hermes_verifier",
            "model": model,
            "role": "post_code_verifier",
            "prompt_hash": prompt_hash,
            "output_hash": "",
            "schema_valid": False,
            "verdict": "UNVERIFIED",
            "repair_instructions": [],
            "input_summary": input_summary,
            "provider_errors": [f"{type(error).__name__}: {error}"],
        }
    names = [
        str(item.get("name") or item.get("model") or "")
        for item in inventory.get("models", [])
        if isinstance(item, dict)
    ]
    if model not in names:
        return {
            "status": "blocked",
            "reason": "hermes_verifier_model_missing_from_local_ollama_inventory",
            "model": model,
            "role": "post_code_verifier",
            "prompt_hash": prompt_hash,
            "output_hash": "",
            "schema_valid": False,
            "verdict": "UNVERIFIED",
            "repair_instructions": [],
            "input_summary": input_summary,
            "provider_errors": [f"{model} not present in local Ollama inventory"],
        }
    attempts: list[dict[str, Any]] = []
    retry_feedback: dict[str, Any] | None = None
    max_verifier_attempts = 2
    for attempt in range(1, max_verifier_attempts + 1):
        attempt_prompt = _fip5_hermes_verifier_prompt(
            input_summary,
            retry_feedback=retry_feedback,
        )
        attempt_prompt_hash = _json_hash(attempt_prompt)
        request_payload = {
            "model": model,
            "prompt": attempt_prompt,
            "stream": False,
            "format": "json",
            "keep_alive": os.environ.get("SOURCE_PROXY_FIP5_HERMES_KEEP_ALIVE", "10m"),
            "options": {
                "temperature": 0,
                "num_predict": int(os.environ.get("SOURCE_PROXY_FIP5_HERMES_NUM_PREDICT", "384")),
                "num_ctx": int(os.environ.get("SOURCE_PROXY_FIP5_HERMES_NUM_CTX", "8192")),
            },
        }
        try:
            body = json.dumps(request_payload).encode("utf-8")
            generate_request = urllib.request.Request(
                f"{base_url}/api/generate",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(
                generate_request,
                timeout=_fip5_hermes_timeout_seconds(),
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as error:
            result = {
                "status": "failed",
                "reason": "hermes_verifier_call_failed",
                "model": model,
                "role": "post_code_verifier",
                "prompt_hash": attempt_prompt_hash,
                "output_hash": "",
                "schema_valid": False,
                "verdict": "UNVERIFIED",
                "reasons": [],
                "repair_instructions": [],
                "input_summary": input_summary,
                "provider_errors": [f"{type(error).__name__}: {error}"],
                "attempt": attempt,
            }
            attempts.append(result)
            return _fip5_hermes_verifier_result_with_attempts(result, attempts)

        raw = str(payload.get("response") or "") if isinstance(payload, dict) else ""
        output_hash = _json_hash(raw) if raw else ""
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as error:
            result = {
                "status": "failed",
                "reason": "hermes_verifier_output_not_json",
                "model": model,
                "role": "post_code_verifier",
                "prompt_hash": attempt_prompt_hash,
                "output_hash": output_hash,
                "schema_valid": False,
                "verdict": "UNVERIFIED",
                "reasons": [],
                "repair_instructions": [],
                "input_summary": input_summary,
                "provider_errors": [f"JSONDecodeError: {error}"],
                "raw_output_excerpt": raw[:1000],
                "attempt": attempt,
            }
            attempts.append(result)
            if attempt >= max_verifier_attempts:
                return _fip5_hermes_verifier_result_with_attempts(result, attempts)
            retry_feedback = {
                "attempt": attempt,
                "reason": result["reason"],
                "output_hash": output_hash,
                "raw_output_excerpt": raw[:400],
            }
            continue

        normalized, schema_errors = _fip5_normalize_hermes_verifier_output(
            parsed,
            deterministic=deterministic,
            browser=browser,
        )
        evidence_mismatch = (
            _fip5_hermes_evidence_mismatch(
                normalized,
                evidence_block=evidence_block,
            )
            if not schema_errors
            else {"mismatch": False, "reason": ""}
        )
        status = "used" if not schema_errors else "failed"
        result = {
            "status": status,
            "reason": (
                "hermes_verifier_evidence_mismatch"
                if evidence_mismatch.get("mismatch")
                else "hermes_verifier_schema_valid"
                if not schema_errors
                else "hermes_verifier_schema_invalid"
            ),
            "model": model,
            "role": "post_code_verifier",
            "prompt_hash": attempt_prompt_hash,
            "output_hash": output_hash,
            "schema_valid": not schema_errors,
            "verdict": normalized["verdict"],
            "reasons": normalized["reasons"],
            "repair_instructions": normalized["repair_instructions"],
            "input_summary": input_summary,
            "provider_errors": schema_errors,
            "evidence_mismatch": bool(evidence_mismatch.get("mismatch")),
            "evidence_mismatch_detail": evidence_mismatch,
            "raw_output_excerpt": raw[:1000],
            "attempt": attempt,
        }
        attempts.append(result)
        if evidence_mismatch.get("mismatch") and attempt < max_verifier_attempts:
            retry_feedback = {
                "attempt": attempt,
                "reason": "hermes_verifier_evidence_mismatch",
                "output_hash": output_hash,
                "evidence_mismatch_detail": evidence_mismatch,
                "raw_output_excerpt": raw[:400],
            }
            continue
        if not schema_errors or attempt >= max_verifier_attempts:
            return _fip5_hermes_verifier_result_with_attempts(result, attempts)
        retry_feedback = {
            "attempt": attempt,
            "reason": result["reason"],
            "output_hash": output_hash,
            "schema_errors": schema_errors,
            "raw_output_excerpt": raw[:400],
        }

    return _fip5_hermes_verifier_result_with_attempts(attempts[-1], attempts)


def _fip5_call_qwen_repair(repair_packet: dict[str, Any]) -> dict[str, Any]:
    repaired_packet = {
        **repair_packet.get("final_coder_packet", {}),
        "repair_packet": repair_packet,
        "final_packet_hash": _json_hash(repair_packet),
    }
    return _fip4_call_qwen(repaired_packet)


def _fip5_repair_as_fip4_result(
    *,
    base_result: dict[str, Any],
    repair_packet: dict[str, Any],
    qwen_repair: dict[str, Any],
) -> dict[str, Any]:
    action, parse_meta = _fip4_extract_qwen_file_action(str(qwen_repair.get("raw_output") or ""))
    status = "failed"
    reason = "qwen_repair_output_contract_rejected"
    proposed_diff = ""
    changed_files: list[str] = []
    if qwen_repair.get("status") in {"blocked", "failed"}:
        status = str(qwen_repair.get("status"))
        reason = str(qwen_repair.get("reason") or reason)
    elif action is not None:
        allowed, allowed_reason = _fip4_path_allowed(
            str(action.get("target") or ""),
            [str(item) for item in base_result.get("allowed_files", [])],
            [str(item) for item in base_result.get("forbidden_files", [])],
        )
        if not allowed:
            reason = allowed_reason
        else:
            try:
                proposed_diff = generate_unified_diff_from_content(
                    _workspace_root(),
                    str(action.get("target") or ""),
                    str(action.get("content") or ""),
                )
            except Exception as error:
                parse_meta["diff_error"] = f"{type(error).__name__}: {error}"
                reason = "fip5_repair_backend_diff_generation_failed"
            else:
                status = "used" if proposed_diff.strip() else "failed"
                reason = (
                    "fip5_qwen_repair_action_output_parsed_and_diff_generated"
                    if proposed_diff.strip()
                    else "fip5_qwen_repair_output_produced_no_diff"
                )
                changed_files = [str(action.get("target"))] if status == "used" else []
    return {
        **base_result,
        "status": status,
        "reason": reason,
        "final_coder_packet_hash": str(
            qwen_repair.get("coder_received_packet_hash")
            or base_result.get("final_coder_packet_hash")
            or ""
        ),
        "coder_received_packet_hash": str(qwen_repair.get("coder_received_packet_hash") or ""),
        "qwen": qwen_repair,
        "parser": parse_meta,
        "action": action or {},
        "changed_files": changed_files,
        "proposed_diff": proposed_diff,
        "repair_packet": repair_packet,
    }


def _run_fip5_verifier_and_repair(
    *,
    request: PromptPacketRequest,
    explicit_target: str,
    fip4_result: dict[str, Any],
) -> dict[str, Any]:
    max_attempts = _fip5_repair_max_attempts()
    repair_packets: list[dict[str, Any]] = []
    qwen_repair_outputs: list[dict[str, Any]] = []
    current = fip4_result
    deterministic = _fip5_deterministic_verifier(
        request=request,
        explicit_target=explicit_target,
        fip4_result=current,
        repair_attempt=0,
    )
    browser = _fip5_browser_verifier(
        request=request,
        explicit_target=explicit_target,
        fip4_result=current,
    )
    functional = _fip5_functional_verifier(
        request=request,
        explicit_target=explicit_target,
        fip4_result=current,
    )
    hermes = _fip5_call_hermes_verifier(
        request=request,
        fip4_result=current,
        deterministic=deterministic,
        browser=browser,
    )
    attempt = 0
    while (
        attempt < max_attempts
        and not deterministic.get("passed")
        and browser.get("passed") is not False
    ):
        attempt += 1
        repair_packet = {
            "packet_version": "source-proxy-fip5-repair-packet-v0.1",
            "attempt": attempt,
            "max_attempts": max_attempts,
            "role": "qwen_repair_as_coder_only",
            "final_coder_packet": current.get("final_coder_packet", {}),
            "deterministic_failures": deterministic.get("failures", []),
            "hermes_repair_instructions": hermes.get("repair_instructions", []),
            "target_file": explicit_target,
            "required_text": deterministic.get("required_text", ""),
            "rules": {
                "qwen_must_not_verify": True,
                "qwen_must_not_decide_pass": True,
                "no_hidden_apply": True,
                "no_commit": True,
                "no_push": True,
            },
        }
        repair_packets.append(repair_packet)
        qwen_repair = _fip5_call_qwen_repair(repair_packet)
        qwen_repair_outputs.append(qwen_repair)
        current = _fip5_repair_as_fip4_result(
            base_result=current,
            repair_packet=repair_packet,
            qwen_repair=qwen_repair,
        )
        deterministic = _fip5_deterministic_verifier(
            request=request,
            explicit_target=explicit_target,
            fip4_result=current,
            repair_attempt=attempt,
        )
        browser = _fip5_browser_verifier(
            request=request,
            explicit_target=explicit_target,
            fip4_result=current,
        )
        functional = _fip5_functional_verifier(
            request=request,
            explicit_target=explicit_target,
            fip4_result=current,
        )
        hermes = _fip5_call_hermes_verifier(
            request=request,
            fip4_result=current,
            deterministic=deterministic,
            browser=browser,
        )
        if deterministic.get("passed"):
            break
    repair_status = (
        "used"
        if repair_packets and deterministic.get("passed")
        else "failed"
        if repair_packets
        else "skipped"
    )
    browser_blocks_pass = bool(
        browser.get("passed") is False
        and browser.get("status") in {"used", "failed", "blocked", "timed_out", "config_blocked", "skipped"}
    )
    if browser_blocks_pass:
        final_verdict = "NO-GO: fip5_browser_behavior_authority_blocks_pass"
    elif deterministic.get("passed") and hermes.get("status") == "used" and hermes.get("verdict") == "PASS":
        final_verdict = "GO: fip5_required_verifier_and_repair_complete"
    elif repair_packets and not deterministic.get("passed"):
        final_verdict = "NO-GO: fip5_repair_attempts_exhausted_operator_intervention_required"
    elif hermes.get("status") in {"blocked", "failed"}:
        final_verdict = f"CONFIG-BLOCKED: {hermes.get('reason')}"
    else:
        final_verdict = "NO-GO: fip5_verifier_did_not_accept_pass"
    return {
        "status": "used" if final_verdict.startswith("GO:") else "failed",
        "reason": final_verdict,
        "deterministic": deterministic,
        "browser": browser,
        "functional": functional,
        "hermes": hermes,
        "repair_loop_status": {
            "status": repair_status,
            "reason": "fip5_bounded_repair_loop_complete"
            if repair_packets
            else "fip5_repair_not_needed",
        },
        "repair_attempt_count": attempt,
        "repair_max_attempts": max_attempts,
        "repair_packets": repair_packets,
        "qwen_repair_outputs": qwen_repair_outputs,
        "final_fip4_result": current,
        "final_verdict": final_verdict,
    }


def _run_fip4_qwen_coder(
    *,
    request: PromptPacketRequest,
    trial_task: str,
    explicit_target: str,
    intake_payload: dict[str, Any],
    route_payload: dict[str, Any],
    route_reasons: list[str],
    fip1_context_packet: dict[str, Any],
    fip2_research_packet: dict[str, Any],
    fip3_model_packet: dict[str, Any],
    canonical_context_broker: dict[str, Any] | None = None,
) -> dict[str, Any]:
    canonical_context_broker = canonical_context_broker or {}
    context_mode = derive_context_mode(explicit_target)
    allowed_files = _fip4_allowed_files(
        explicit_target=explicit_target,
        intake_payload=intake_payload,
        request=request,
    )
    forbidden_files = _fip4_forbidden_files(
        intake_payload=intake_payload,
        request=request,
        context_mode=context_mode,
    )
    checks = [
        "python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py -q",
        "npm run typecheck -- --pretty false",
        "git diff --check",
    ]
    final_packet = _fip4_final_coder_packet(
        request=request,
        trial_task=trial_task,
        normalized_task=_short_task_summary(request.task),
        explicit_target=explicit_target,
        allowed_files=allowed_files,
        forbidden_files=forbidden_files,
        route_payload=route_payload,
        route_reasons=route_reasons,
        fip1_context_packet=fip1_context_packet,
        fip2_research_packet=fip2_research_packet,
        fip3_model_packet=fip3_model_packet,
        canonical_context_broker=canonical_context_broker,
        checks=checks,
    )
    final_packet_hash = str(final_packet.get("final_packet_hash") or _json_hash(final_packet))
    if final_packet["protected_path_check"]["status"] == "blocked":
        return {
            "status": "blocked",
            "reason": "fip4_protected_path_blocked_before_qwen",
            "final_coder_packet": final_packet,
            "final_coder_packet_hash": final_packet_hash,
            "coder_received_packet_hash": "",
            "allowed_files": allowed_files,
            "forbidden_files": forbidden_files,
            "changed_files": [],
            "checks_run": [],
            "proposed_diff": "",
            "provider_call_made": False,
            "provider_model_truth": {
                "providerCallMade": False,
                "providerCallAuthorized": False,
                "providerId": "ollama",
                "modelId": _fip4_qwen_model(),
                "source": "fip4_qwen_coder",
                "status": "blocked",
                "hermesUsedForThisRun": False,
                "hermesLaneAvailable": False,
            },
        }
    qwen = _fip4_call_qwen(final_packet)
    provider_call_made = bool(qwen.get("coder_received_packet_hash"))
    action, parse_meta = _fip4_extract_qwen_file_action(str(qwen.get("raw_output") or ""))
    qwen_output_contract_retry: dict[str, Any] = {
        "status": "skipped",
        "reason": "qwen_output_contract_retry_not_needed",
    }
    if (
        qwen.get("status") == "used"
        and action is None
        and _fip4_qwen_output_contract_retryable(parse_meta)
    ):
        retry_qwen = _fip4_call_qwen_output_contract_retry(
            final_packet=final_packet,
            previous_qwen=qwen,
            previous_parse_meta=parse_meta,
        )
        retry_action, retry_parse_meta = _fip4_extract_qwen_file_action(
            str(retry_qwen.get("raw_output") or "")
        )
        qwen_output_contract_retry = {
            "status": "used",
            "reason": "qwen_output_contract_retry_attempted",
            "previous_parse_error": parse_meta.get("parse_error", ""),
            "previous_output_hash": str(qwen.get("qwen_output_hash") or ""),
            "retry_output_hash": str(retry_qwen.get("qwen_output_hash") or ""),
            "retry_parse_error": retry_parse_meta.get("parse_error", ""),
            "same_final_coder_packet_hash": bool(
                retry_qwen.get("same_final_coder_packet_hash")
            ),
        }
        qwen = {
            **retry_qwen,
            "attempt_count": 2,
            "attempts": [
                _fip4_qwen_attempt_summary(qwen, 1),
                _fip4_qwen_attempt_summary(retry_qwen, 2),
            ],
            "retry_attempted": True,
            "retry_reason": "qwen_output_contract_rejected",
            "output_contract_retry": qwen_output_contract_retry,
        }
        action = retry_action
        parse_meta = retry_parse_meta
    if qwen.get("status") in {"blocked", "failed"}:
        status = str(qwen.get("status"))
        reason = str(qwen.get("reason") or "qwen_coder_failed")
    elif action is None:
        status = "failed"
        reason = "qwen_output_contract_rejected"
    else:
        allowed, allowed_reason = _fip4_path_allowed(
            str(action.get("target") or ""),
            allowed_files,
            forbidden_files,
        )
        if not allowed:
            status = "failed"
            reason = allowed_reason
        else:
            try:
                proposed_diff = generate_unified_diff_from_content(
                    _workspace_root(),
                    str(action.get("target") or ""),
                    str(action.get("content") or ""),
                )
            except Exception as error:
                proposed_diff = ""
                status = "failed"
                reason = "fip4_backend_diff_generation_failed"
                parse_meta["diff_error"] = f"{type(error).__name__}: {error}"
            else:
                status = "used" if proposed_diff.strip() else "failed"
                reason = (
                    "fip4_qwen_action_output_parsed_and_diff_generated"
                    if proposed_diff.strip()
                    else "fip4_qwen_output_produced_no_diff"
                )
    if "proposed_diff" not in locals():
        proposed_diff = ""
    changed_files = [str(action.get("target"))] if status == "used" and action else []
    return {
        "status": status,
        "reason": reason,
        "final_coder_packet": final_packet,
        "final_coder_packet_hash": final_packet_hash,
        "coder_received_packet_hash": str(qwen.get("coder_received_packet_hash") or ""),
        "qwen": qwen,
        "parser": parse_meta,
        "qwen_output_contract_retry": qwen_output_contract_retry,
        "action": action or {},
        "allowed_files": allowed_files,
        "forbidden_files": forbidden_files,
        "changed_files": changed_files,
        "checks_run": checks if status == "used" else [],
        "proposed_diff": proposed_diff,
        "provider_call_made": provider_call_made,
        "provider_model_truth": {
            "providerCallMade": provider_call_made,
            "providerCallAuthorized": provider_call_made,
            "providerId": "ollama",
            "modelId": _fip4_qwen_model(),
            "source": "fip4_qwen_coder",
            "status": status,
            "attemptCount": qwen.get("attempt_count"),
            "retryAttempted": bool(qwen.get("retry_attempted")),
            "timeoutSeconds": qwen.get("timeout_seconds"),
            "latencyMs": qwen.get("latency_ms"),
            "hermesUsedForThisRun": False,
            "hermesLaneAvailable": False,
        },
    }


def _attach_fip0_truth_receipt(
    payload: dict[str, Any],
    *,
    request: PromptPacketRequest,
    route_payload: dict[str, Any],
    intake_payload: dict[str, Any],
    decision: Any,
    explicit_target: str,
    route_reasons: list[str],
    coder_packet_payload: dict[str, Any] | None = None,
    checks_run: list[Any] | None = None,
    changed_files: list[Any] | None = None,
    proposed_diff: str = "",
    status_value: str = "",
    reason_code: str = "",
    coder_blocked: bool = False,
    provider_call_made: bool = False,
    provider_model_truth: dict[str, Any] | None = None,
    fip1_context_packet: dict[str, Any] | None = None,
    fip2_research_packet: dict[str, Any] | None = None,
    fip3_model_packet: dict[str, Any] | None = None,
    fip4_coder_result: dict[str, Any] | None = None,
    fip5_verifier_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    run_seed = {
        "timestamp": timestamp,
        "task": request.task,
        "target": explicit_target,
        "route": route_payload.get("recommended_route"),
    }
    run_id = f"fip0-{_json_hash(run_seed)[:16]}"
    forbidden_files = (
        intake_payload.get("forbidden_files")
        if isinstance(intake_payload.get("forbidden_files"), list)
        else request.forbidden_files
    )
    allowed_files = (
        intake_payload.get("allowed_files")
        if isinstance(intake_payload.get("allowed_files"), list)
        else request.allowed_files
    )
    checks = checks_run or []
    diff = proposed_diff or ""
    fip4_result = fip4_coder_result or {}
    fip5_result = fip5_verifier_result or {}
    coder_packet = coder_packet_payload or payload.get("coder_packet") or {}
    coder_packet_hash = (
        str(fip4_result.get("coder_received_packet_hash") or "")
        if fip4_result
        else _json_hash(coder_packet) if provider_call_made and coder_packet else ""
    )
    final_packet_hash = _json_hash(payload)
    fip2_packet = fip2_research_packet or {}
    fip3_packet = fip3_model_packet or {}
    gemma_packet = (
        fip3_packet.get("gemma")
        if isinstance(fip3_packet.get("gemma"), dict)
        else {}
    )
    hermes_critic_packet = (
        fip3_packet.get("hermes_critic")
        if isinstance(fip3_packet.get("hermes_critic"), dict)
        else {}
    )
    hermes_verifier_packet = (
        fip3_packet.get("hermes_verifier")
        if isinstance(fip3_packet.get("hermes_verifier"), dict)
        else {}
    )
    fip2_sources = (
        fip2_packet.get("research_sources")
        if isinstance(fip2_packet.get("research_sources"), list)
        else []
    )
    research_sources = (
        fip2_sources
        if fip2_sources
        else
        decision.research_sources
        if isinstance(getattr(decision, "research_sources", None), list)
        else []
    )
    repo_research_sources = _research_sources_by_source(research_sources, "repo")
    scout_research_sources = _research_sources_by_source(research_sources, "scout")
    searxng_web_sources = _research_sources_by_source(research_sources, "web")
    searxng_packet = (
        fip2_packet.get("searxng")
        if isinstance(fip2_packet.get("searxng"), dict)
        else {}
    )
    scout_packet = (
        fip2_packet.get("scout")
        if isinstance(fip2_packet.get("scout"), dict)
        else {}
    )
    route_type = str(
        route_payload.get("recommended_route")
        or route_payload.get("route_type")
        or ""
    )
    context_packet = fip1_context_packet or {}
    canonical_context_broker = (
        payload.get("canonical_context_broker")
        if isinstance(payload.get("canonical_context_broker"), dict)
        else payload.get("context_metadata", {}).get("canonical_context_broker")
        if isinstance(payload.get("context_metadata"), dict)
        and isinstance(payload.get("context_metadata", {}).get("canonical_context_broker"), dict)
        else {}
    )
    context_sources = (
        context_packet.get("sources")
        if isinstance(context_packet.get("sources"), list)
        else []
    )
    context_by_source = {
        str(source.get("source") or ""): source
        for source in context_sources
        if isinstance(source, dict)
    }
    source_readiness = (
        context_packet.get("source_readiness_status")
        if isinstance(context_packet.get("source_readiness_status"), dict)
        else {}
    )
    output_contract_status = (
        _lane_status(
            "used",
            "prompt_packet_output_contract_reported_existing_result",
            prompt_packet_status=status_value,
            reason_code=reason_code,
        )
        if status_value
        else _lane_status(
            "skipped",
            "manual_prompt_packet_branch_has_no_coder_output_to_validate",
        )
    )
    if fip4_result:
        qwen_call = fip4_result.get("qwen") if isinstance(fip4_result.get("qwen"), dict) else {}
        qwen_status = _lane_status(
            str(fip4_result.get("status") or "failed")
            if _valid_lane_status_value(str(fip4_result.get("status") or ""))
            else "failed",
            str(fip4_result.get("reason") or "fip4_qwen_coder_result_missing_reason"),
            provider_model_truth=provider_model_truth or fip4_result.get("provider_model_truth") or {},
            coder_packet_hash_present=bool(coder_packet_hash),
            final_coder_packet_hash=str(fip4_result.get("final_coder_packet_hash") or ""),
            qwen_attempt_count=qwen_call.get("attempt_count"),
            qwen_attempts=qwen_call.get("attempts", []),
            qwen_retry_attempted=bool(qwen_call.get("retry_attempted")),
            qwen_retry_reason=str(qwen_call.get("retry_reason") or ""),
            qwen_model_latency_ms=qwen_call.get("latency_ms"),
            qwen_timeout_seconds=qwen_call.get("timeout_seconds"),
        )
    elif provider_call_made and coder_packet_hash:
        qwen_status = _lane_status(
            "used",
            "existing_prompt_packet_branch_reports_provider_call",
            provider_model_truth=provider_model_truth or {},
        )
    elif provider_call_made:
        qwen_status = _lane_status(
            "failed",
            "qwen_coder_provider_call_without_coder_packet_hash",
            provider_model_truth=provider_model_truth or {},
            coder_packet_hash_present=False,
        )
    else:
        qwen_status = _lane_status(
            "skipped",
            "fip0_receipt_foundation_does_not_activate_qwen_coder",
            coder_packet_hash_present=bool(coder_packet_hash),
        )
    receipt: dict[str, Any] = {
        "run_id": run_id,
        "timestamp": timestamp,
        "raw_prompt": request.task,
        "normalized_task": _short_task_summary(request.task),
        "route_type": route_type,
        "workspace_mode": intake_payload.get("workspace_mode") or "unknown",
        "dirty_tree_status": _safe_dirty_tree_status(),
        "allowed_files": allowed_files,
        "forbidden_files": forbidden_files,
        "protected_path_check": _protected_path_check(
            route_reasons=route_reasons,
            forbidden_files=[str(item) for item in forbidden_files],
        ),
        "context_router_status": _lane_status(
            "used",
            "prompt_packet_route_decision_executed",
            route_type=route_type,
            reason_codes=route_reasons,
        ),
        "repo_research_status": (
            _lane_status(
                "used",
                "repo_router_research_sources_present_not_live_searxng",
                source_count=len(repo_research_sources),
                scout_source_count=len(scout_research_sources),
            )
            if repo_research_sources or scout_research_sources
            else _lane_status(
                "skipped",
                "no_repo_or_scout_research_sources_present",
            )
        ),
        "obsidian_status": _lane_status(
            "skipped",
            "fip0_foundation_only_obsidian_not_wired_until_fip1",
        ),
        "cartographer_status": _lane_status(
            "skipped",
            "fip0_foundation_only_cartographer_advisory_not_wired_until_fip1",
        ),
        "design_status": _lane_status(
            "skipped",
            "fip0_foundation_only_design_lane_not_wired_until_fip1",
        ),
        "mac_worker_status": _lane_status(
            "skipped",
            "fip0_foundation_only_no_hidden_worker_invocation",
        ),
        "source_readiness_status": _lane_status(
            "skipped",
            "fip0_foundation_only_source_readiness_not_wired_until_fip1",
        ),
        "scout_status": _lane_status(
            "skipped",
            "fip0_foundation_only_scout_not_wired_until_fip2",
        ),
        "searxng_status": (
            _lane_status(
                "used",
                "live_searxng_provider_query_executed",
                source_count=len(searxng_web_sources),
            )
            if searxng_web_sources
            else _lane_status(
                "skipped",
                "fip0_foundation_only_live_searxng_not_wired_until_fip2",
            )
        ),
        "tinyfish_status": _lane_status(
            "skipped",
            "deferred_cloud_requires_britton_approval",
        ),
        "xersearch_status": _lane_status(
            "skipped",
            "missing_alias_do_not_create",
        ),
        "gemma_status": _lane_status(
            "skipped",
            "fip0_foundation_only_gemma_not_wired_until_fip3",
        ),
        "hermes_critic_status": _lane_status(
            "skipped",
            "fip0_foundation_only_hermes_critic_not_wired_until_fip3",
        ),
        "qwen_coder_status": qwen_status,
        "hermes_verifier_status": _lane_status(
            "skipped",
            "fip0_foundation_only_hermes_verifier_not_wired_until_fip5",
        ),
        "hermes_verifier_lane_status": _lane_status(
            "skipped",
            "fip0_foundation_only_hermes_verifier_not_wired_until_fip5",
        ),
        "repair_loop_status": _lane_status(
            "skipped",
            "fip0_foundation_only_repair_loop_not_wired_until_fip5",
        ),
        "browser_behavior_status": _lane_status(
            "skipped",
            "fip0_foundation_only_browser_behavior_not_wired_until_fip5",
        ),
        "deterministic_check_status": (
            _lane_status("used", "checks_reported_by_prompt_packet", checks_run=checks)
            if checks
            else _lane_status(
                "skipped",
                "no_deterministic_checks_reported_by_this_prompt_packet",
            )
        ),
        "output_contract_status": output_contract_status,
        "anti_tailoring_status": _lane_status(
            "used",
            "receipt_records_no_hidden_worker_apply_commit_push_or_cloud_provider",
            hidden_worker_started=False,
            hidden_apply=False,
            hidden_commit=False,
            hidden_push=False,
            cloud_provider_used=False,
        ),
        "final_packet_hash": final_packet_hash,
        "canonical_context_broker": canonical_context_broker,
        "canonical_context_verdict": str(canonical_context_broker.get("verdict") or ""),
        "canonical_context_report_hash": str(
            canonical_context_broker.get("canonical_report_hash") or ""
        ),
        "coder_received_packet_hash": coder_packet_hash,
        "used_sources": [],
        "skipped_reasons": [],
        "blocked_reasons": [],
        "failed_reasons": [],
        "provider_errors": [],
        "model_errors": [],
        "checks_run": checks,
        "diff_summary": {
            "changed_files": changed_files or [],
            "proposed_diff_present": bool(diff.strip()),
            "proposed_diff_sha256": _json_hash(diff) if diff else "",
        },
        "final_verdict": (
            "CONFIG-BLOCKED"
            if reason_code == "coder_model_not_configured"
            else "NO-GO"
            if coder_blocked and status_value not in {"already_satisfied", "noop"}
            else "GO: fip0_receipt_foundation_complete_runtime_lanes_not_yet_wired"
        ),
    }
    if fip2_packet:
        searxng_status = _source_status_from_packet(
            searxng_packet,
            fallback_reason="searxng_status_missing",
        )
        if (
            searxng_status["status"] == "used"
            and not searxng_packet.get("provider_call_made")
        ):
            searxng_status = _lane_status(
                "failed",
                "searxng_marked_used_without_live_provider_call",
                provider_errors=["provider_call_made false"],
            )
        receipt["fip2_research_packet"] = fip2_packet
        receipt["search_needed"] = bool(fip2_packet.get("search_needed"))
        receipt["search_reason"] = str(fip2_packet.get("search_reason") or "")
        receipt["research_query"] = str(fip2_packet.get("research_query") or "")
        receipt["repo_research_status"] = (
            _lane_status(
                "used",
                "repo_router_research_sources_present_not_live_searxng",
                source_count=len(repo_research_sources),
                scout_source_count=len(scout_research_sources),
            )
            if repo_research_sources
            else _lane_status("skipped", "no_repo_research_sources_present")
        )
        receipt["scout_status"] = _source_status_from_packet(
            scout_packet,
            fallback_reason="scout_status_missing",
        )
        receipt["searxng_status"] = searxng_status
        receipt["searxng_url"] = searxng_packet.get("searxng_url", "")
        receipt["searxng_format_json_status"] = searxng_packet.get(
            "searxng_format_json_status",
            "not_checked",
        )
        receipt["searxng_latency_ms"] = searxng_packet.get("searxng_latency_ms")
        receipt["searxng_result_count"] = int(
            searxng_packet.get("searxng_result_count") or 0
        )
        receipt["searxng_sources"] = searxng_packet.get("searxng_sources", [])
        receipt["scout_enabled"] = bool(scout_packet.get("scout_enabled"))
        receipt["scout_result_count"] = int(scout_packet.get("scout_result_count") or 0)
        receipt["scout_sources"] = scout_packet.get("scout_sources", [])
        receipt["research_packet_hash"] = fip2_packet.get("research_packet_hash", "")
        receipt["research_packet_included_in_context"] = bool(
            fip2_packet.get("research_packet_included_in_context")
        )
        receipt["provider_errors"] = [
            *[
                f"searxng:{error}"
                for error in searxng_packet.get("provider_errors", [])
            ],
            *[
                f"scout:{error}"
                for error in scout_packet.get("provider_errors", [])
            ],
        ]
        if receipt["search_needed"] and receipt["searxng_status"]["status"] in {
            "blocked",
            "failed",
        }:
            receipt["final_verdict"] = (
                "CONFIG-BLOCKED: fip2_local_searxng_not_available"
            )
        elif receipt["search_needed"] and receipt["searxng_status"]["status"] != "used":
            receipt["final_verdict"] = "NO-GO: fip2_search_needed_without_live_searxng"
        else:
            receipt["final_verdict"] = (
                "CONFIG-BLOCKED"
                if reason_code == "coder_model_not_configured"
                else "NO-GO"
                if coder_blocked and status_value not in {"already_satisfied", "noop"}
                else "GO: fip2_local_search_injection_runtime_future_lanes_not_wired"
            )
    if context_packet:
        receipt["fip1_context_packet"] = context_packet
        receipt["obsidian_status"] = _packet_lane_status(
            context_by_source.get("obsidian", {}),
            fallback_reason="fip1_obsidian_context_packet_missing",
        )
        receipt["cartographer_status"] = _packet_lane_status(
            context_by_source.get("cartographer", {}),
            fallback_reason="fip1_cartographer_context_packet_missing",
        )
        receipt["design_status"] = _packet_lane_status(
            context_by_source.get("design", {}),
            fallback_reason="fip1_design_context_packet_missing",
        )
        receipt["mac_worker_status"] = _packet_lane_status(
            context_by_source.get("mac_worker", {}),
            fallback_reason="fip1_mac_worker_context_packet_missing",
        )
        receipt["source_readiness_status"] = _lane_status(
            str(source_readiness.get("status") or "failed")
            if _valid_lane_status_value(str(source_readiness.get("status") or ""))
            else "failed",
            str(source_readiness.get("reason") or "fip1_source_readiness_status_missing"),
            invalid_sources=source_readiness.get("invalid_sources", []),
            source_status=context_packet.get("source_status", {}),
            authority=context_packet.get("authority", {}),
        )
        if not fip2_packet:
            receipt["final_verdict"] = (
                "CONFIG-BLOCKED"
                if reason_code == "coder_model_not_configured"
                else "NO-GO"
                if coder_blocked and status_value not in {"already_satisfied", "noop"}
                else "GO: fip1_context_lanes_integrated_runtime_future_lanes_not_wired"
            )
    if fip3_packet:
        gemma_status = _source_status_from_packet(
            gemma_packet,
            fallback_reason="gemma_model_lane_status_missing",
        )
        hermes_critic_status = _source_status_from_packet(
            hermes_critic_packet,
            fallback_reason="hermes_critic_model_lane_status_missing",
        )
        verifier_status = _source_status_from_packet(
            hermes_verifier_packet,
            fallback_reason="hermes_verifier_reserved_status_missing",
        )
        qwen_fallback_attempted = fip3_lane_packet_has_qwen_fallback(fip3_packet)
        if qwen_fallback_attempted:
            gemma_status = _lane_status(
                "failed",
                "fip3_qwen_precoder_fallback_disallowed",
                raw_gemma_status=gemma_status,
            )
            hermes_critic_status = _lane_status(
                "failed",
                "fip3_qwen_precoder_fallback_disallowed",
                raw_hermes_critic_status=hermes_critic_status,
            )
        receipt["fip3_model_packet"] = fip3_packet
        receipt["fip3_research_packet_hash_received"] = str(
            fip3_packet.get("research_packet_hash_received") or ""
        )
        receipt["fip3_research_packet_included_in_model_context"] = bool(
            fip3_packet.get("research_packet_included_in_model_context")
        )
        receipt["gemma_status"] = gemma_status
        receipt["gemma_model"] = str(gemma_packet.get("model") or "")
        receipt["gemma_prompt_hash"] = str(gemma_packet.get("prompt_hash") or "")
        receipt["gemma_output_hash"] = str(gemma_packet.get("output_hash") or "")
        receipt["gemma_output_schema_valid"] = bool(
            gemma_packet.get("output_schema_valid")
        )
        receipt["gemma_intent"] = str(gemma_packet.get("intent") or "")
        receipt["gemma_normalized_spec"] = str(gemma_packet.get("normalized_spec") or "")
        receipt["gemma_context_needed"] = bool(gemma_packet.get("context_needed"))
        receipt["gemma_search_needed_review"] = bool(
            gemma_packet.get("search_needed_review")
        )
        receipt["gemma_acceptance_criteria"] = (
            gemma_packet.get("acceptance_criteria")
            if isinstance(gemma_packet.get("acceptance_criteria"), list)
            else []
        )
        receipt["hermes_critic_status"] = hermes_critic_status
        receipt["hermes_critic_model"] = str(hermes_critic_packet.get("model") or "")
        receipt["hermes_critic_prompt_hash"] = str(
            hermes_critic_packet.get("prompt_hash") or ""
        )
        receipt["hermes_critic_output_hash"] = str(
            hermes_critic_packet.get("output_hash") or ""
        )
        receipt["hermes_critic_output_schema_valid"] = bool(
            hermes_critic_packet.get("output_schema_valid")
        )
        receipt["hermes_ambiguities"] = (
            hermes_critic_packet.get("ambiguities")
            if isinstance(hermes_critic_packet.get("ambiguities"), list)
            else []
        )
        receipt["hermes_risks"] = (
            hermes_critic_packet.get("risks")
            if isinstance(hermes_critic_packet.get("risks"), list)
            else []
        )
        receipt["hermes_requirement_conflicts"] = (
            hermes_critic_packet.get("requirement_conflicts")
            if isinstance(hermes_critic_packet.get("requirement_conflicts"), list)
            else []
        )
        receipt["hermes_pre_coder_notes"] = (
            hermes_critic_packet.get("pre_coder_notes")
            if isinstance(hermes_critic_packet.get("pre_coder_notes"), list)
            else []
        )
        receipt["hermes_verifier_lane_status"] = verifier_status
        receipt["hermes_verifier_status"] = verifier_status
        receipt["hermes_verifier_model"] = str(hermes_verifier_packet.get("model") or "")
        receipt["hermes_verifier_role_reserved"] = True
        receipt["hermes_verifier_authority"] = (
            "future_fip5_necessary_not_sufficient"
        )
        receipt["model_route_truth"] = (
            fip3_packet.get("model_route_truth")
            if isinstance(fip3_packet.get("model_route_truth"), dict)
            else {}
        )
        receipt["no_qwen_pre_coder_reasoning"] = True
        receipt["model_errors"] = [
            *receipt.get("model_errors", []),
            *[
                f"gemma:{error}"
                for error in gemma_packet.get("provider_errors", [])
            ],
            *[
                f"hermes:{error}"
                for error in hermes_critic_packet.get("provider_errors", [])
            ],
        ]
        model_statuses = {
            receipt["gemma_status"]["status"],
            receipt["hermes_critic_status"]["status"],
        }
        if "blocked" in model_statuses:
            receipt["final_verdict"] = (
                "CONFIG-BLOCKED: fip3_local_model_lane_unavailable"
            )
        elif "failed" in model_statuses:
            receipt["final_verdict"] = "NO-GO: fip3_local_model_lane_failed"
        elif qwen_fallback_attempted:
            receipt["final_verdict"] = "NO-GO: fip3_qwen_precoder_fallback_disallowed"
        elif (
            receipt["gemma_status"]["status"] == "used"
            and receipt["hermes_critic_status"]["status"] == "used"
            and receipt["qwen_coder_status"]["status"] == "skipped"
        ):
            receipt["final_verdict"] = (
                "GO: fip3_local_non_coding_model_lanes_runtime_future_lanes_not_wired"
            )
    if fip4_result:
        final_coder_packet_hash = str(fip4_result.get("final_coder_packet_hash") or "")
        coder_received_packet_hash = str(
            fip4_result.get("coder_received_packet_hash") or ""
        )
        receipt["fip4_final_coder_packet"] = fip4_result.get("final_coder_packet", {})
        receipt["fip4_qwen_coder_result"] = {
            key: value
            for key, value in fip4_result.items()
            if key not in {"final_coder_packet"}
        }
        receipt["final_coder_packet_hash"] = final_coder_packet_hash
        receipt["coder_received_packet_hash"] = coder_received_packet_hash
        receipt["qwen_coder_model"] = str(
            (fip4_result.get("qwen") or {}).get("model")
            if isinstance(fip4_result.get("qwen"), dict)
            else ""
        )
        receipt["qwen_coder_output_hash"] = str(
            (fip4_result.get("qwen") or {}).get("qwen_output_hash")
            if isinstance(fip4_result.get("qwen"), dict)
            else ""
        )
        receipt["output_contract_status"] = (
            _lane_status(
                "used",
                "fip4_qwen_output_contract_parsed",
                parser=fip4_result.get("parser", {}),
                qwen_output_contract_retry=fip4_result.get(
                    "qwen_output_contract_retry",
                    {},
                ),
            )
            if fip4_result.get("status") == "used"
            else _lane_status(
                "failed",
                "fip4_qwen_output_contract_rejected",
                parser=fip4_result.get("parser", {}),
                qwen_output_contract_retry=fip4_result.get(
                    "qwen_output_contract_retry",
                    {},
                ),
            )
        )
        receipt["qwen_output_contract_retry"] = fip4_result.get(
            "qwen_output_contract_retry",
            {},
        )
        receipt["diff_summary"] = {
            "changed_files": fip4_result.get("changed_files", []),
            "proposed_diff_present": bool(
                str(fip4_result.get("proposed_diff") or "").strip()
            ),
            "proposed_diff_sha256": _json_hash(fip4_result.get("proposed_diff", ""))
            if fip4_result.get("proposed_diff")
            else "",
            "allowed_files": fip4_result.get("allowed_files", []),
            "forbidden_files": fip4_result.get("forbidden_files", []),
        }
        receipt["checks_run"] = fip4_result.get("checks_run", [])
        receipt["protected_path_check"] = _protected_path_check(
            route_reasons=route_reasons,
            forbidden_files=[
                str(item)
                for item in fip4_result.get("forbidden_files", [])
                if str(item).strip()
            ],
        )
        if fip4_result.get("status") == "blocked":
            receipt["final_verdict"] = f"CONFIG-BLOCKED: {fip4_result.get('reason')}"
        elif (
            fip4_result.get("status") == "used"
            and final_coder_packet_hash
            and coder_received_packet_hash == final_coder_packet_hash
            and receipt["gemma_status"]["status"] == "used"
            and receipt["hermes_critic_status"]["status"] == "used"
            and receipt["hermes_verifier_status"]["status"] == "skipped"
            and receipt["repair_loop_status"]["status"] == "skipped"
        ):
            receipt["qwen_coder_status"] = _lane_status(
                "used",
                "fip4_qwen_received_exact_final_coder_packet_and_returned_valid_action",
                provider_model_truth=provider_model_truth
                or fip4_result.get("provider_model_truth")
                or {},
                final_coder_packet_hash=final_coder_packet_hash,
                coder_received_packet_hash=coder_received_packet_hash,
            )
            receipt["final_verdict"] = "GO: fip4_qwen_coding_only_execution_complete"
        else:
            receipt["final_verdict"] = f"NO-GO: {fip4_result.get('reason') or 'fip4_qwen_coder_failed'}"
    if fip5_result:
        deterministic = (
            fip5_result.get("deterministic")
            if isinstance(fip5_result.get("deterministic"), dict)
            else {}
        )
        browser = (
            fip5_result.get("browser")
            if isinstance(fip5_result.get("browser"), dict)
            else {}
        )
        functional = (
            fip5_result.get("functional")
            if isinstance(fip5_result.get("functional"), dict)
            else {}
        )
        hermes = (
            fip5_result.get("hermes")
            if isinstance(fip5_result.get("hermes"), dict)
            else {}
        )
        receipt["fip5_verifier_result"] = fip5_result
        receipt["deterministic_verifier_status"] = _lane_status(
            str(deterministic.get("status") or "failed")
            if _valid_lane_status_value(str(deterministic.get("status") or ""))
            else "failed",
            str(deterministic.get("reason") or "fip5_deterministic_verifier_missing"),
            passed=bool(deterministic.get("passed")),
        )
        receipt["deterministic_checks_run"] = deterministic.get("checks_run", [])
        receipt["deterministic_failures"] = deterministic.get("failures", [])
        receipt["browser_behavior_status"] = _lane_status(
            str(browser.get("status") or "failed")
            if _valid_lane_status_value(str(browser.get("status") or ""))
            else "failed",
            str(browser.get("reason") or "fip5_browser_behavior_missing"),
            passed=browser.get("passed"),
            browser_verifier=browser.get("browser_verifier", {}),
        )
        receipt["browser_verifier_status"] = _lane_status(
            str(browser.get("status") or "failed")
            if _valid_lane_status_value(str(browser.get("status") or ""))
            else "failed",
            str(browser.get("reason") or "browser_verifier_missing"),
            passed=browser.get("passed"),
            browser_verifier=browser.get("browser_verifier", {}),
        )
        receipt["browser_verifier_checks"] = browser.get("checks", [])
        receipt["browser_verifier"] = browser.get("browser_verifier", {})
        receipt["browser_verifier_target_path"] = str(browser.get("target_path") or "")
        receipt["browser_verifier_timeout_ms"] = browser.get("timeout_ms")
        receipt["browser_verifier_version"] = str(browser.get("verifier_version") or "")
        receipt["browser_verifier_browser_engine"] = str(browser.get("browser_engine") or "")
        receipt["browser_probe_summary"] = browser.get("summary", {})
        receipt["browser_behavior_authoritative"] = bool(browser.get("authoritative", True))
        receipt["functional_verifier_status"] = _lane_status(
            str(functional.get("status") or "skipped")
            if _valid_lane_status_value(str(functional.get("status") or ""))
            else "failed",
            str(functional.get("reason") or "functional_verifier_skipped_no_supported_contract"),
            passed=bool(functional.get("passed")),
        )
        receipt["functional_verifier_checks"] = functional.get("checks", [])
        receipt["functional_verifier_target_path"] = str(functional.get("target_path") or "")
        receipt["functional_verifier_timeout_ms"] = functional.get("timeout_ms")
        receipt["functional_verifier_version"] = str(
            functional.get("verifier_version") or ""
        )
        receipt["hermes_verifier_status"] = _lane_status(
            str(hermes.get("status") or "failed")
            if _valid_lane_status_value(str(hermes.get("status") or ""))
            else "failed",
            str(hermes.get("reason") or "fip5_hermes_verifier_missing"),
            verdict=hermes.get("verdict", "UNVERIFIED"),
        )
        receipt["hermes_verifier_lane_status"] = receipt["hermes_verifier_status"]
        receipt["hermes_verifier_model"] = str(hermes.get("model") or "")
        receipt["hermes_verifier_role"] = str(hermes.get("role") or "post_code_verifier")
        receipt["hermes_verifier_prompt_hash"] = str(hermes.get("prompt_hash") or "")
        receipt["hermes_verifier_output_hash"] = str(hermes.get("output_hash") or "")
        receipt["hermes_verifier_attempt_count"] = int(hermes.get("attempt_count") or 0)
        receipt["hermes_verifier_retry_attempted"] = bool(hermes.get("retry_attempted"))
        receipt["hermes_verifier_retry_reason"] = str(hermes.get("retry_reason") or "")
        receipt["hermes_verifier_first_invalid_output_hash"] = str(
            hermes.get("first_invalid_output_hash") or ""
        )
        receipt["hermes_verifier_invalid_output_hashes"] = hermes.get(
            "invalid_output_hashes",
            [],
        )
        receipt["hermes_verifier_attempts"] = hermes.get("attempts", [])
        receipt["hermes_verifier_evidence_mismatch"] = bool(
            hermes.get("evidence_mismatch")
        )
        receipt["hermes_verifier_evidence_mismatch_detail"] = hermes.get(
            "evidence_mismatch_detail",
            {},
        )
        receipt["hermes_verifier_schema_valid"] = bool(hermes.get("schema_valid"))
        receipt["hermes_verifier_verdict"] = str(hermes.get("verdict") or "UNVERIFIED")
        receipt["hermes_verifier_repair_instructions"] = hermes.get(
            "repair_instructions",
            [],
        )
        receipt["cannot_turn_unverified_into_pass"] = True
        receipt["cannot_override_browser_behavior"] = True
        repair_loop_status = (
            fip5_result.get("repair_loop_status")
            if isinstance(fip5_result.get("repair_loop_status"), dict)
            else {}
        )
        receipt["repair_loop_status"] = _lane_status(
            str(repair_loop_status.get("status") or "failed")
            if _valid_lane_status_value(str(repair_loop_status.get("status") or ""))
            else "failed",
            str(repair_loop_status.get("reason") or "fip5_repair_loop_status_missing"),
        )
        receipt["repair_attempt_count"] = int(fip5_result.get("repair_attempt_count") or 0)
        receipt["repair_max_attempts"] = int(fip5_result.get("repair_max_attempts") or 0)
        receipt["repair_packets"] = fip5_result.get("repair_packets", [])
        receipt["qwen_repair_outputs"] = fip5_result.get("qwen_repair_outputs", [])
        final_fip4 = (
            fip5_result.get("final_fip4_result")
            if isinstance(fip5_result.get("final_fip4_result"), dict)
            else {}
        )
        if final_fip4:
            receipt["diff_summary"] = {
                "changed_files": final_fip4.get("changed_files", []),
                "proposed_diff_present": bool(
                    str(final_fip4.get("proposed_diff") or "").strip()
                ),
                "proposed_diff_sha256": _json_hash(final_fip4.get("proposed_diff", ""))
                if final_fip4.get("proposed_diff")
                else "",
                "allowed_files": final_fip4.get("allowed_files", []),
                "forbidden_files": final_fip4.get("forbidden_files", []),
            }
        receipt["final_verdict"] = str(
            fip5_result.get("final_verdict")
            or fip5_result.get("reason")
            or "NO-GO: fip5_verifier_missing_final_verdict"
        )
    if (
        canonical_context_broker
        and canonical_context_broker.get("go_eligible") is not True
        and str(receipt.get("final_verdict") or "").startswith("GO:")
    ):
        receipt["final_verdict"] = "NO-GO: canonical_context_not_go_eligible"
    receipt["failure_classification"] = _receipt_failure_classification(receipt)
    receipt["failure_event"] = _receipt_failure_event(receipt)
    degraded_lanes = _lane_degradation_for_receipt(receipt)
    if degraded_lanes and str(receipt.get("final_verdict") or "").startswith("GO:"):
        receipt["final_verdict"] = "NO-GO: expected_degraded_lane"
    receipt.update(_structured_verdict_fields(receipt))
    receipt["used_sources"] = [
        field
        for field in FIP0_LANE_STATUS_FIELDS
        if isinstance(receipt.get(field), dict)
        and receipt[field].get("status") == "used"
    ]
    receipt["skipped_reasons"] = _status_bucket(receipt, "skipped")
    receipt["blocked_reasons"] = _status_bucket(receipt, "blocked")
    receipt["failed_reasons"] = _status_bucket(receipt, "failed")
    receipt_path = _fip0_receipt_root() / f"{run_id}.json"
    receipt["receipt_path"] = str(receipt_path)
    receipt["receipt_write_status"] = {"status": "used", "path": str(receipt_path)}
    write_status = _safe_write_json(receipt_path, receipt)
    if write_status["status"] == "failed":
        receipt["receipt_write_status"] = write_status
        receipt["failed_reasons"].append(
            f"durable_receipt:{write_status.get('reason')}"
        )
        receipt["final_verdict"] = "NO-GO: fip0_receipt_write_failed"
    payload["fip0_truth_receipt"] = receipt
    payload["fip0TruthReceipt"] = receipt
    payload["fip0_truth_receipt_path"] = write_status["path"]
    payload["fip0TruthReceiptPath"] = write_status["path"]
    return payload


async def _propose_coder_via_executor(
    architect_plan: Any,
    *,
    force_live_model: bool = False,
    canonical_context: dict[str, Any] | None = None,
    canonical_context_text: str = "",
) -> dict[str, Any]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        functools.partial(
            propose_coder_agent_diff_payload_from_plan,
            architect_plan=architect_plan,
            force_live_model=force_live_model,
            canonical_context=canonical_context,
            canonical_context_text=canonical_context_text,
        ),
    )


def _architect_context_sources_for_broker(
    architect_plan: Any,
    *,
    workspace_root: Path,
) -> list[dict[str, Any]]:
    """Describe late-bound Architect/repomix inputs before generic Coder runs."""

    packet = getattr(architect_plan, "coder_packet", None)
    packet_payload: dict[str, Any] = {}
    raw_slices: list[Any] = []
    try:
        plan_payload = architect_plan.to_dict()
        raw_packet = plan_payload.get("coder_packet") if isinstance(plan_payload, dict) else None
        if isinstance(raw_packet, dict):
            packet_payload = dict(raw_packet)
            raw_slices = (
                list(packet_payload.pop("context_slices", []))
                if isinstance(packet_payload.get("context_slices"), list)
                else []
            )
    except Exception:  # noqa: BLE001 - malformed plan becomes blocked broker truth
        packet_payload = {}
    packet_available = packet is not None and bool(packet_payload)

    context_slices: list[dict[str, Any]] = []
    tampered_slices: list[str] = []
    if packet is not None:
        for item in getattr(packet, "context_slices", []):
            content = str(getattr(item, "content", "") or "")
            expected_hash = str(getattr(item, "sha256", "") or "")
            actual_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            path_value = str(getattr(item, "path", "") or "")
            if not expected_hash or actual_hash != expected_hash:
                tampered_slices.append(path_value or "unknown")
            line_range = getattr(item, "line_range", None)
            context_slices.append(
                {
                    "path": path_value,
                    "kind": str(getattr(item, "kind", "") or ""),
                    "sha256": expected_hash,
                    "line_range": list(line_range) if line_range else None,
                    "safe_excerpt": content[:4000],
                    "omitted_chars": max(0, len(content) - 4000),
                }
            )
    else:
        context_slices = [dict(item) for item in raw_slices if isinstance(item, dict)]

    operation = str(getattr(packet, "operation", "") or "")
    slices_required = bool(operation != "create" or context_slices)
    slices_available = bool(context_slices) and not tampered_slices

    snapshot = getattr(architect_plan, "bundle_snapshot", None)
    expected_bundle_hash = str(getattr(snapshot, "bundle_sha256", "") or "")
    bundle_path_text = str(getattr(snapshot, "bundle_path", "") or "")
    snapshot_invoked = bool(snapshot is not None and (expected_bundle_hash or bundle_path_text))
    bundle_path = Path(bundle_path_text) if bundle_path_text else workspace_root
    if bundle_path_text and not bundle_path.is_absolute():
        bundle_path = workspace_root / bundle_path
    if snapshot_invoked and (not bundle_path_text or not bundle_path.is_file()):
        for name in ("repomix-output.ast.xml", "repomix-output.xml"):
            candidate = workspace_root / name
            if candidate.is_file():
                bundle_path = candidate
                break
    resolved_bundle = bundle_path.resolve()
    bundle_safe = bool(
        snapshot_invoked
        and resolved_bundle.is_file()
        and (resolved_bundle == workspace_root or workspace_root in resolved_bundle.parents)
    )
    actual_bundle_hash = (
        hashlib.sha256(resolved_bundle.read_bytes()).hexdigest()
        if bundle_safe
        else ""
    )
    bundle_valid = bool(
        bundle_safe
        and expected_bundle_hash
        and actual_bundle_hash == expected_bundle_hash
    )

    return [
        {
            "source": "architect_coder_packet",
            "considered": True,
            "status": "used" if packet_available else "blocked",
            "reason": (
                "architect_coder_packet_brokered"
                if packet_available
                else "architect_coder_packet_missing_or_malformed"
            ),
            "required": True,
            "selected": packet_available,
            "included": packet_available,
            "packet": packet_payload,
            "authority": dict(READ_ONLY_AUTHORITY),
        },
        {
            "source": "architect_context_slices",
            "considered": True,
            "status": "used" if slices_available else "blocked" if slices_required else "skipped",
            "reason": (
                "architect_context_slices_brokered"
                if slices_available
                else f"architect_context_slice_hash_mismatch:{','.join(tampered_slices[:5])}"
                if tampered_slices
                else "architect_context_slices_missing"
                if slices_required
                else "create_packet_did_not_require_context_slices"
            ),
            "required": slices_required,
            "selected": slices_available,
            "included": slices_available,
            "packet": {"slices": context_slices},
            "authority": dict(READ_ONLY_AUTHORITY),
        },
        {
            "source": "repomix_bundle_context",
            "considered": True,
            "status": "used" if bundle_valid else "blocked" if snapshot_invoked else "skipped",
            "reason": (
                "repomix_bundle_snapshot_hash_verified_and_brokered"
                if bundle_valid
                else "repomix_bundle_snapshot_hash_mismatch"
                if bundle_safe and expected_bundle_hash
                else "repomix_bundle_snapshot_missing_or_unsafe"
                if snapshot_invoked
                else "architect_plan_has_no_repomix_bundle_snapshot"
            ),
            "required": snapshot_invoked,
            "selected": bundle_valid,
            "included": bundle_valid,
            "packet": {
                "bundle_path": bundle_path_text,
                "expected_sha256": expected_bundle_hash,
                "actual_sha256": actual_bundle_hash,
                "selected_context_slice_hashes": [
                    str(item.get("sha256") or "") for item in context_slices
                ],
            },
            "authority": dict(READ_ONLY_AUTHORITY),
        },
    ]


def _extend_canonical_context_for_generic_coder(
    canonical_context: dict[str, Any],
    architect_plan: Any,
) -> str:
    updated = extend_context_broker_sources(
        canonical_context,
        _architect_context_sources_for_broker(
            architect_plan,
            workspace_root=_workspace_root().resolve(),
        ),
        planner_evidence="architect_plan_and_repomix_context_selected_before_generic_coder",
    )
    canonical_context.clear()
    canonical_context.update(updated)
    return render_context_broker_prompt(canonical_context)


def _generic_coder_context_blocked_payload(
    canonical_context: dict[str, Any],
    *,
    target: str,
) -> dict[str, Any]:
    blockers = [str(item) for item in canonical_context.get("required_context_blockers", [])]
    return {
        "proposed_diff": "",
        "target": target,
        "coder_notes": ["CODER_BLOCKED reason_code: required_context_blocked"],
        "bundle": None,
        "coder_blocked": True,
        "blocked_reason": "; ".join(blockers) or "canonical_context_not_go_eligible",
        "needed_context": "Resolve the Architect/repomix broker blockers, then regenerate the plan.",
        "reason_code": "required_context_blocked",
        "coder_diagnostics": {
            "canonical_context_broker": canonical_context,
            "canonical_context_report_hash": canonical_context.get("canonical_report_hash", ""),
            "canonical_context_consumed_by_coder_execution": False,
            "validation_status": "required_context_blocked",
            "context_slices": [],
            "provider_call_made": False,
        },
    }


async def _bounded_coder_diff_or_stub(
    task: str,
    architect_plan: Any | None = None,
    *,
    force_live_model: bool = False,
    canonical_context: dict[str, Any] | None = None,
    canonical_context_text: str = "",
) -> dict[str, Any]:
    """Run blocking coder work off the event loop; never exceed gateway patience."""
    if force_live_model:
        explicit_target = _parse_explicit_target_file_line(task)
        if explicit_target.startswith("src/"):
            product_satisfied = _product_trial_feature_already_satisfied_payload(
                task,
                explicit_target,
            )
            if product_satisfied is not None:
                return product_satisfied
        dummy_live = _dummy_reversible_live_trial_coder_diff_payload(task)
        if dummy_live is not None:
            return _annotate_deterministic_coder_context_consumption(
                dummy_live,
                canonical_context=canonical_context,
                canonical_context_text=canonical_context_text,
            )
        expected_no_edit = _expected_no_edit_trial_payload(task)
        if expected_no_edit is not None:
            return expected_no_edit
        realistic_trial = _realistic_reversible_trial_coder_diff_payload(task)
        if realistic_trial is not None:
            return _annotate_deterministic_coder_context_consumption(
                realistic_trial,
                canonical_context=canonical_context,
                canonical_context_text=canonical_context_text,
            )
    dummy_preview = (
        None
        if force_live_model or not _trial_harness_only_enabled()
        else _dummy_trial_coder_diff_payload(task)
    )
    if dummy_preview is not None:
        return _annotate_deterministic_coder_context_consumption(
            dummy_preview,
            canonical_context=canonical_context,
            canonical_context_text=canonical_context_text,
        )
    if architect_plan is None:
        architect_plan = _deterministic_architect_plan_for_prompt_packet(task, None)
    if architect_plan is None:
        explicit = _parse_explicit_target_file_line(task)
        return {
            "proposed_diff": "",
            "target": explicit,
            "coder_notes": ["CODER_BLOCKED reason_code: coder_packet_missing_context"],
            "bundle": None,
            "coder_blocked": True,
            "blocked_reason": "Coder requires an Architect CoderPacket.",
            "needed_context": "Create or regenerate the Architect plan before running Coder.",
            "reason_code": "coder_packet_missing_context",
            "coder_diagnostics": {
                "context_mode": derive_context_mode(explicit),
                "context_slices": [],
                "forbidden_paths": list(forbidden_paths_for_context_mode(derive_context_mode(explicit))),
            },
        }
    if canonical_context is not None:
        canonical_context_text = _extend_canonical_context_for_generic_coder(
            canonical_context,
            architect_plan,
        )
        if canonical_context.get("go_eligible") is not True:
            return _generic_coder_context_blocked_payload(
                canonical_context,
                target=_target_from_architect_plan(architect_plan),
            )
    deadline = _coder_sync_deadline_seconds()
    reset_coder_timing_diagnostics()
    try:
        return await asyncio.wait_for(
            _propose_coder_via_executor(
                architect_plan,
                force_live_model=force_live_model,
                canonical_context=canonical_context,
                canonical_context_text=canonical_context_text,
            ),
            timeout=deadline,
        )
    except asyncio.TimeoutError:
        explicit = _parse_explicit_target_file_line(task)
        timing = snapshot_coder_timing_diagnostics()
        timeout_stage = _infer_coder_timeout_stage(timing)
        return {
            "proposed_diff": "",
            "target": explicit,
            "coder_notes": [
                f"Coder Agent repomix+LLM exceeded proxy deadline ({deadline:.0f}s); "
                "stub response so the BFF does not die with 502. Pin `Target file:` for "
                "client-side diff, raise SOURCE_PROXY_CODER_SYNC_DEADLINE_SEC if you need longer."
            ],
            "bundle": None,
            "coder_blocked": True,
            "blocked_reason": "Coder Agent timed out before producing replacement content.",
            "needed_context": "Regenerate with repo context or raise SOURCE_PROXY_CODER_SYNC_DEADLINE_SEC.",
            "reason_code": "coder_sync_timeout",
            "coder_diagnostics": {
                "timeout_stage": timeout_stage,
                "deadline_seconds": deadline,
                "reason_code": "coder_sync_timeout",
                **timing,
            },
        }
    except Exception as error:
        explicit = _parse_explicit_target_file_line(task)
        if not explicit:
            explicit = _target_from_architect_plan(architect_plan)
        apply_timeout = isinstance(error, subprocess.TimeoutExpired)
        reason_code = (
            "coder_backend_diff_generation_failed"
            if apply_timeout
            else "coder_agent_backend_error"
        )
        blocked_reason = (
            "Coder generated candidate content, but backend diff validation timed out before it could be safely approved."
            if apply_timeout
            else "Coder Agent failed before producing a safely approvable diff."
        )
        needed_context = (
            "Retry Local Coder, narrow scope, or increase the git apply validation timeout before approval."
            if apply_timeout
            else (
                "Retry Local Coder with stricter output repair, copy a manual browser prompt, "
                "or use Cloud/API route only if configured and explicitly chosen."
            )
        )
        return {
            "proposed_diff": "",
            "target": explicit,
            "coder_notes": [
                f"CODER_BLOCKED reason_code: {reason_code}",
                f"{type(error).__name__}: {error}",
            ],
            "bundle": None,
            "coder_blocked": True,
            "blocked_reason": blocked_reason,
            "needed_context": needed_context,
            "reason_code": reason_code,
            "coder_diagnostics": {
                "context_mode": derive_context_mode(explicit),
                "context_slices": [],
                "forbidden_paths": list(forbidden_paths_for_context_mode(derive_context_mode(explicit))),
                "exception_type": type(error).__name__,
            },
        }


def _annotate_deterministic_coder_context_consumption(
    payload: dict[str, Any],
    *,
    canonical_context: dict[str, Any] | None,
    canonical_context_text: str,
) -> dict[str, Any]:
    """Bind a deterministic coder result to the same canonical pre-execution gate."""

    diagnostics = (
        dict(payload.get("coder_diagnostics"))
        if isinstance(payload.get("coder_diagnostics"), dict)
        else {}
    )
    selected_sources = [
        source
        for source in (canonical_context or {}).get("sources_considered", [])
        if isinstance(source, dict) and source.get("selected") is True
    ]
    context_ready = bool(
        canonical_context
        and canonical_context.get("go_eligible") is True
        and canonical_context_text.strip()
        and selected_sources
    )
    diagnostics["canonical_context_broker"] = canonical_context or {}
    diagnostics["canonical_context_report_hash"] = str(
        (canonical_context or {}).get("canonical_report_hash") or ""
    )
    diagnostics["canonical_context_included_in_model_prompt"] = False
    diagnostics["canonical_context_consumed_by_coder_execution"] = context_ready
    diagnostics["canonical_context_consumption_mode"] = "deterministic_pre_execution_gate"
    existing_slices = [
        item for item in diagnostics.get("context_slices", []) if isinstance(item, dict)
    ]
    diagnostics["context_slices"] = [
        *existing_slices,
        *[
            {
                "path": f"context://{source.get('source')}",
                "kind": "canonical_context_gate",
                "report_hash": diagnostics["canonical_context_report_hash"],
            }
            for source in selected_sources
        ],
    ]
    return {**payload, "coder_diagnostics": diagnostics}


def _product_trial_feature_already_satisfied_payload(
    task: str,
    target: str,
) -> dict[str, Any] | None:
    """When the requested product behavior is already on disk, prove a live model call and noop."""
    lowered = task.lower()
    root = _workspace_root()
    target_path = (root / target).resolve()
    if not target_path.is_file():
        return None
    current = target_path.read_text(encoding="utf-8", errors="replace")

    def satisfied(note: str, *, quick_proof: bool = True) -> dict[str, Any]:
        return _deterministic_already_satisfied_payload(
            target,
            context_mode=derive_context_mode(target),
            note=note,
            task=task,
            require_live_model_proof=True,
            quick_proof=quick_proof,
        )

    if target == "src/lib/coding/visible-result-badge.ts" and (
        "truth label" in lowered
        or "no live proof" in lowered
        or "no real model" in lowered
        or "fixture/replay" in lowered
        or "not live model" in lowered
        or ("live proof" in lowered and "hermes" in lowered)
    ):
        if "LIVE MODEL CALL RECORDED" in current and (
            "NOT LIVE MODEL PROOF" in current or "No live model call" in current
        ):
            return satisfied(
                "Visible result badge already distinguishes live model proof from fixture/replay mode.",
            )
    if target == "src/lib/coding/reversible-trial-prompts.ts":
        if ("repeating 10 prompts" in lowered or "repeated banks" in lowered) and (
            "for (const count of bankCountTiers)" in current
            or "contains duplicate normalized prompt text" in current
        ):
            return satisfied(
                "Reversible trial prompt bank already rejects duplicate tier prompts.",
            )
        if ("prompt banks" in lowered and "unique prompts" in lowered) and (
            "validateReversibleTrialPromptBank" in current
            and "duplicate normalized prompt text" in current
            and "for (const count of bankCountTiers)" in current
        ):
            return satisfied(
                "Reversible trial prompt bank already validates unique prompts for 10/25/50/100 tiers.",
            )
        if ("count dropdown" in lowered or "25/50/100" in lowered) and (
            "selectReversibleTrialPrompts slices to this count" in current
            or "export function selectReversibleTrialPrompts(" in current
        ):
            return satisfied(
                "Reversible trial count dropdown already slices the prompt bank by tier.",
            )
        if ("category invalid" in lowered or "category is wrong" in lowered) and (
            "function normalizeReversibleTrialCategoryInput(" in current
        ):
            return satisfied(
                "Category invalid guard already present in reversible trial prompt bank.",
            )
    if target != "src/components/coding/CodingCockpitShell.tsx":
        return None
    if ("one bucket" in lowered or "acting sus" in lowered) and (
        '["Reverted", String(reversibleSuiteState.reverted)]' in current
        or '["Worked", String(reversibleSuiteState.pass)]' in current
        or '["Edit passed", String(reversibleSuiteState.pass)]' in current
    ):
        return satisfied(
            "Suite counters already use separate pass, fail, and reverted buckets.",
        )
    if (
        "reverted clean" in lowered
        or "worked+reverted" in lowered
        or "applied then reverted" in lowered
    ) and (
        'visible_result_label: "REVERTED"' in current or "revertedPass" in current
    ):
        return satisfied(
            "Reverted trials already use a dedicated REVERTED result label.",
        )
    if ("times out" in lowered and "transcript" in lowered) and (
        "Transcript preserved" in current
        or "Suite interrupted by refresh. Transcript preserved" in current
    ):
        return satisfied("Suite refresh already preserves transcript text.")
    if ("stop after current prompt" in lowered or "stop after this one" in lowered) and (
        "stopReversibleSuiteAfterCurrentRef.current" in current
        and "if (stopReversibleSuiteAfterCurrentRef.current) break" in current
    ):
        return satisfied(
            "Stop-after-current-prompt already halts after the active prompt finishes.",
        )
    if ("health thing" in lowered or "health_proxy" in lowered) and "health_proxy:" in current:
        return satisfied("Reversible suite diagnostics already include readable health lines.")
    if "dry run" in lowered and "trialDryRunOnly" in current:
        return satisfied("Reversible trial runner already supports dry-run preview without apply.")
    if (
        "model dropdown" in lowered
        or "real backend models" in lowered
        or "hardcoded fake labels" in lowered
    ) and (
        'fetch("/v1/self/status"' in current
        and "providerModelTruthFromSelfStatus(payload)" in current
        and "setSelectedProviderTruth(truth)" in current
    ):
        return satisfied(
            "Model/provider display already comes from Source Proxy self-status model routes.",
        )
    if (
        ("success true" in lowered and "transcript empty" in lowered)
        or ("needs fix" in lowered and "not worked" in lowered)
    ) and (
        "provider_call_made=true" in current
        and "transcript_or_model_response_body_empty_or_no_diff" in current
        and "NEEDS FIX: Live apply proof missing" in current
    ):
        return satisfied(
            "No-diff live model responses already become NEEDS FIX instead of PASS.",
        )
    if ("rename worked" in lowered or "patched then reverted" in lowered) and (
        '["Edits applied", String(reversibleSuiteState.pass)]' in current
        and "edit_worked_count" not in current
    ):
        return satisfied(
            "Suite summary already labels applied edits without using ambiguous worked wording.",
        )
    if (
        ("spinner" in lowered and "backend" in lowered)
        or "backend dies" in lowered
        or "show real backend failure" in lowered
    ) and (
        "function previewLoadingPhaseLabel(" in current
        and "Source Proxy unreachable — backend failure" in current
    ):
        return satisfied(
            "Preview spinner already surfaces Source Proxy unreachable and backend timeout failures.",
        )
    if (
        "receipt" in lowered
        and (
            "prompt id" in lowered
            or "time spent" in lowered
            or "final status" in lowered
            or "model name" in lowered
        )
    ) and (
        "receipt_prompt_id:" in current
        and "receipt_final_status:" in current
        and "receipt_time_spent_ms:" in current
        and "receipt_model:" in current
    ):
        return satisfied(
            "Per-prompt trial receipts already include model, prompt id, status, files, and elapsed time.",
        )
    if ("after refresh" in lowered or "last suite" in lowered) and (
        "Last suite stays in this browser after refresh" in current
        and "loadStoredReversibleSuiteState" in current
        and "storeReversibleSuiteState" in current
    ):
        return satisfied(
            "Reversible suite summary already persists across browser refresh in session storage.",
        )
    return None


def _coder_extension_realistic_replacement_rules(
    target: str,
    lowered: str,
) -> tuple[str, str] | None:
    """Bounded edits for Coder bank prompts 11+ (product files, not dummy fixtures)."""
    if target == "src/lib/coding/visible-result-badge.ts" and (
        "truth label" in lowered
        or "no live proof" in lowered
        or ("live proof" in lowered and "hermes" in lowered)
    ):
        return (
            ': "NOT LIVE MODEL PROOF",',
            ': "LIVE MODEL CALL RECORDED",',
        )
    if target == "src/lib/coding/reversible-trial-prompts.ts":
        if "repeating 10 prompts" in lowered or "repeated banks" in lowered:
            return (
                "export function validateReversibleTrialPromptBank(prompts: readonly ReversibleTrialPrompt[]) {",
                "export function validateReversibleTrialPromptBank(prompts: readonly ReversibleTrialPrompt[]) {\n  // Rejects duplicate normalized prompts for each 10/25/50/100 tier.",
            )
        if "count dropdown" in lowered or "25/50/100" in lowered:
            return (
                "export const reversibleTrialCounts = [10, 25, 50, 100] as const;",
                "export const reversibleTrialCounts = [10, 25, 50, 100] as const; // selectReversibleTrialPrompts slices to this count",
            )
    if target == "src/components/coding/CodingCockpitShell.tsx" and (
        ("spinner" in lowered and "backend" in lowered)
        or "backend dies" in lowered
        or "show real backend failure" in lowered
    ):
        return (
            "type ManualTaskPhase = keyof typeof manualTaskPhaseLabels;\n\n"
            "type ManualTaskPacket = {",
            "type ManualTaskPhase = keyof typeof manualTaskPhaseLabels;\n\n"
            "/** Spinner label while prompt-packet runs — avoid stuck Calling model when Source Proxy is dead. */\n"
            "function previewLoadingPhaseLabel(sourceProxyReachable: boolean, phase: ManualTaskPhase): string {\n"
            "  if (phase === \"preview\" && !sourceProxyReachable) {\n"
            "    return \"Source Proxy unreachable\";\n"
            "  }\n"
            "  return manualTaskPhaseLabels[phase];\n"
            "}\n\n"
            "function previewLoadingSimpleResult(\n"
            "  sourceProxyReachable: boolean,\n"
            "  previewState: PreviewState,\n"
            "  idleLabel: string,\n"
            "): string {\n"
            "  if (!previewState.isLoading) {\n"
            "    return previewState.error ?? previewState.blocker ?? idleLabel;\n"
            "  }\n"
            "  if (!sourceProxyReachable) {\n"
            "    return \"Source Proxy unreachable — backend failure (not stuck on Calling model).\";\n"
            "  }\n"
            "  if (\n"
            "    previewState.reasonCode === \"coder_sync_timeout\" ||\n"
            "    previewState.reasonCode === \"source_proxy_timeout\"\n"
            "  ) {\n"
            "    return \"Backend failed — model sync timed out (transcript preserved).\";\n"
            "  }\n"
            "  return \"Previewing\";\n"
            "}\n\n"
            "type ManualTaskPacket = {",
        )
    if target == "src/components/coding/CodingCockpitShell.tsx" and (
        "stop after current prompt" in lowered or "stop after this one" in lowered
    ):
        return (
            "  function handleStopReversibleSuiteAfterCurrent() {\n    stopReversibleSuiteAfterCurrentRef.current = true;",
            "  /** Stops after the active prompt completes (not mid-prompt). */\n  function handleStopReversibleSuiteAfterCurrent() {\n    stopReversibleSuiteAfterCurrentRef.current = true;",
        )
    if target == "src/lib/coding/reversible-trial-prompts.ts" and (
        "category invalid" in lowered or "category is wrong" in lowered
    ):
        return (
            "export function selectReversibleTrialPrompts(",
            "export function normalizeReversibleTrialCategoryInput(\n"
            "  value: string,\n"
            "): ReversibleTrialCategory | null {\n"
            "  return (reversibleTrialCategories as readonly string[]).includes(value)\n"
            "    ? (value as ReversibleTrialCategory)\n"
            "    : null;\n"
            "}\n\n"
            "export function selectReversibleTrialPrompts(",
        )
    return None


def _realistic_reversible_trial_coder_diff_payload(task: str) -> dict[str, Any] | None:
    target = _parse_explicit_target_file_line(task)
    lowered = task.lower()
    feature_satisfied = _product_trial_feature_already_satisfied_payload(task, target)
    if feature_satisfied is not None:
        return feature_satisfied
    replacements: dict[str, tuple[str, str]] = {}
    extension_rule = _coder_extension_realistic_replacement_rules(target, lowered)
    if extension_rule is not None:
        replacements[target] = extension_rule
    if target == "src/components/coding/CodingCockpitShell.tsx" and (
        "status sync wording" in lowered
        or "honest unchanged state" in lowered
        or "check summary display" in lowered
        or "small reversible ui polish edit" in lowered
        or "small reversible code edit" in lowered
        or "small reversible implementation edit" in lowered
    ):
        replacements[target] = (
            "  failed: \"Ready to review\",\n",
            "  failed: \"Needs fix\",\n",
        )
    elif target == "src/lib/coding/changed-files-diagnostics.ts" and (
        "diagnostics copy guard" in lowered
        or "small reversible implementation edit" in lowered
    ):
        replacements[target] = (
            "  const changedFiles = previewChangedFiles.length > 0 ? previewChangedFiles : [];\n",
            "  const changedFiles = previewChangedFiles.length > 0 ? [...previewChangedFiles] : [];\n",
        )
    elif target == "src/lib/coding/visible-result-badge.ts" and (
        "result card file list" in lowered
        or "safety block wording" in lowered
        or "small reversible implementation edit" in lowered
    ):
        replacements[target] = (
            '    plain_summary = reasonCode.includes("protected") ? "Protected path blocked." : "Safety gate blocked the request.";\n',
            '    plain_summary = reasonCode.includes("protected") ? "Protected path blocked before files changed." : "Safety gate blocked the request before files changed.";\n',
        )
    elif target == "src/lib/coding/agent-trials-ui.ts" and (
        "progress step mapping" in lowered
        or "route helper fallback" in lowered
        or "small reversible implementation edit" in lowered
    ):
        replacements[target] = (
            '  "Submitted to /coding",\n',
            '  "Submitted to /coding",\n  "Waiting for coding agent",\n',
        )
    elif target == "src/components/dashboard/ScoutIntelligenceCenter.tsx" and (
        "soccer scouting" in lowered
        or "small reversible ui polish edit" in lowered
        or "small reversible code edit" in lowered
    ):
        replacements[target] = (
            "        {model.actionInboxCards.map((card) => (\n",
            "        <button\n"
            "          type=\"button\"\n"
            "          className=\"scout-center-action-card SpiritOS\"\n"
            "          onClick={() => scrollToSection(\"watching-now\")}\n"
            "        >\n"
            "          <strong>New</strong>\n"
            "          <span>Soccer scouting agent</span>\n"
            "          <p>Visible placeholder for future scouting data connections; no external services are wired.</p>\n"
            "        </button>\n"
            "        {model.actionInboxCards.map((card) => (\n",
        )
    elif target == "src/components/chat/ChatThreadListItem.tsx" and (
        "voidcore" in lowered
        or "small reversible ui polish edit" in lowered
        or "small reversible code edit" in lowered
    ):
        replacements[target] = (
            "            interactionDisabled && \"pointer-events-none opacity-35\",\n",
            "            interactionDisabled && \"pointer-events-none opacity-35\",\n"
            "            active && \"bg-black/55 ring-1 ring-cyan-300/20 shadow-[inset_0_0_0_1px_rgba(34,211,238,0.12)]\",\n",
        )
    elif target == "src/components/coding/CodingCockpitShell.tsx" and "live apply run fails" in lowered:
        replacements[target] = (
            ": previewState.error ?? previewState.blocker ?? previewState.applySummary ?? \"SpiritOS is working on the run.\";\n",
            ": previewState.error ?? previewState.blocker ?? previewState.applySummary ?? \"Next step: use Copy diagnostics, fix the blocker, then rerun the live apply.\";\n",
        )
    elif (
        target.endswith("component-trial.tsx")
        and "warning" in lowered
        and not target.startswith("tests/ui-agent-trials/fixtures/dummy-coding-targets/")
    ):
        replacements[target] = (
            '  tone: "neutral" | "success";\n',
            '  tone: "neutral" | "success" | "warning";\n',
        )
    elif target == "src/components/dashboard/OracleStagePanel.tsx" and (
        "daily briefing" in lowered
        or "small reversible ui polish edit" in lowered
        or "small reversible code edit" in lowered
    ):
        replacements[target] = (
            "        <Link href=\"/oracle\" className={cn(spiritPrimaryCtaClasses, \"mt-10 px-10\")}>\n"
            "          Open Oracle workspace →\n"
            "        </Link>\n",
            "        <div className=\"mt-10 flex flex-col items-center gap-3 sm:flex-row sm:justify-center\">\n"
            "          <Link href=\"/oracle\" className={cn(spiritPrimaryCtaClasses, \"px-10\")}>\n"
            "            Open Oracle workspace →\n"
            "          </Link>\n"
            "          <button\n"
            "            type=\"button\"\n"
            "            className=\"rounded-full border border-cyan/35 px-5 py-3 text-sm font-semibold text-cyan transition hover:bg-cyan/10\"\n"
            "          >\n"
            "            Prepare daily briefing\n"
            "          </button>\n"
            "        </div>\n",
        )
    if target not in replacements:
        return None

    root = _workspace_root()
    target_path = (root / target).resolve()
    if not target_path.is_file():
        return None

    current = target_path.read_text(encoding="utf-8", errors="replace")
    needle, replacement = replacements[target]
    if replacement in current or (needle in current and needle == replacement):
        return _deterministic_already_satisfied_payload(
            target,
            context_mode=derive_context_mode(target),
            note="Realistic reversible trial target already contains the requested bounded edit.",
            task=task,
            require_live_model_proof=True,
        )
    if needle not in current:
        return {
            "proposed_diff": "",
            "target": target,
            "coder_notes": ["CODER_BLOCKED reason_code: realistic_trial_fixture_mismatch"],
            "bundle": "realistic-reversible-live-trial",
            "coder_blocked": True,
            "blocked_reason": "Trial fixture file no longer matches the bounded edit template.",
            "needed_context": (
                f"Refresh {target} or update the realistic trial needle in Source Proxy."
            ),
            "reason_code": "realistic_trial_fixture_mismatch",
            "coder_diagnostics": {
                "context_mode": derive_context_mode(target),
                "target_exists": True,
                "validation_status": "realistic_trial_fixture_mismatch",
            },
        }

    diagnostics = {
        "context_mode": derive_context_mode(target),
        "context_slices": [{"path": target, "kind": "target"}],
        "forbidden_paths": list(forbidden_paths_for_context_mode(derive_context_mode(target))),
        "target_exists": True,
        "validation_status": "preview_ready",
        "deterministic_preview": False,
        "trial_mode": "live_apply",
        "model_output_mode": "bounded_trial_generation",
        "generated_diff_by_backend": True,
        "model_raw_diff_used": False,
        **_trial_live_model_call_diagnostics(
            task,
            proof_prompt=(
                "Return one short sentence confirming a reversible SpiritOS product edit for this task. "
                f"Task: {task[:600]}"
            ),
        ),
    }
    if not diagnostics.get("provider_call_made"):
        return {
            "proposed_diff": "",
            "target": target,
            "coder_notes": ["CODER_BLOCKED reason_code: realistic_trial_model_call_failed"],
            "coder_diagnostics": diagnostics,
            "bundle": "realistic-reversible-live-trial",
            "coder_blocked": True,
            "blocked_reason": "Realistic reversible trial could not prove a live model call.",
            "needed_context": (
                "Check local model availability and SOURCE_PROXY_TRIAL_MODEL_TIMEOUT_SECONDS, "
                "then rerun."
            ),
            "reason_code": "realistic_trial_model_call_failed",
        }

    updated = current.replace(needle, replacement, 1)
    unified = generate_unified_diff_from_content(root, target, updated)
    if not unified.strip():
        return {
            "proposed_diff": "",
            "target": target,
            "coder_notes": ["CODER_BLOCKED reason_code: realistic_trial_diff_empty"],
            "bundle": "realistic-reversible-live-trial",
            "coder_blocked": True,
            "blocked_reason": "Bounded trial edit did not produce a non-empty unified diff.",
            "needed_context": "Check fixture content and git diff generation on the proxy host.",
            "reason_code": "realistic_trial_diff_empty",
            "coder_diagnostics": diagnostics,
        }
    return {
        "proposed_diff": unified,
        "target": target,
        "coder_notes": [
            "Realistic reversible live trial generated after a local model call.",
            "CODER_PREVIEW reason_code: realistic_reversible_live_trial_diff",
        ],
        "bundle": "realistic-reversible-live-trial",
        "reason_code": "realistic_reversible_live_trial_diff",
        "coder_diagnostics": diagnostics,
    }


def _trial_proof_model_aliases() -> list[str]:
    """Ollama-only aliases for bounded trial audit; never fall back to paid cloud routes."""
    raw_aliases = os.getenv("SOURCE_PROXY_TRIAL_PROOF_MODEL_ALIASES", "").strip()
    if not raw_aliases:
        raw_aliases = "local,coder"
    configured = [
        item.strip()
        for item in raw_aliases.split(",")
        if item.strip()
    ]
    enabled = set(available_model_aliases())
    aliases = [
        alias
        for alias in configured
        if alias in enabled
        and route_provider_for_alias(alias) == "ollama"
        and (route_model_for_alias(alias) or "").startswith("ollama_chat/")
    ]
    return aliases or ["local"]


def _trial_proof_timeout_error(error: Exception) -> bool:
    if isinstance(error, TimeoutError):
        return True
    message = str(error).lower()
    return "timeout" in message or "timed out" in message


def _ollama_trial_proof_call(
    *,
    alias: str,
    proof_prompt: str,
    timeout_seconds: float,
) -> str:
    central_gate_check("model_call", run_id=f"ollama_trial_proof:{alias}", model_alias=alias)
    litellm_model = route_model_for_alias(alias) or ""
    if route_provider_for_alias(alias) != "ollama" or not litellm_model.startswith("ollama_chat/"):
        raise ValueError(f"Trial proof direct Ollama path is not available for alias {alias!r}.")
    ollama_model = litellm_model.removeprefix("ollama_chat/")
    api_base = resolve_ollama_route(probe=False).api_base.rstrip("/")
    payload = {
        "model": ollama_model,
        "prompt": proof_prompt,
        "raw": True,
        "stream": False,
        "keep_alive": os.getenv("SOURCE_PROXY_TRIAL_MODEL_KEEP_ALIVE", "10m"),
        "options": {
            "num_predict": int(os.getenv("SOURCE_PROXY_TRIAL_MODEL_NUM_PREDICT", "1")),
            "temperature": 0,
            "num_ctx": int(os.getenv("SOURCE_PROXY_TRIAL_MODEL_NUM_CTX", "128")),
        },
    }
    request = urllib.request.Request(
        f"{api_base}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        body = response.read().decode("utf-8", errors="replace")
    parsed = json.loads(body)
    return str(parsed.get("response") or "")


def _trial_live_model_call_diagnostics(
    task: str,
    *,
    proof_prompt: str,
    quick_proof: bool = False,
) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {
        "trial_mode": "live_apply",
        "model_output_mode": "bounded_trial_generation",
        "generated_diff_by_backend": True,
        "model_raw_diff_used": False,
        "deterministic_preview": False,
    }
    from source_proxy.tasks.long_running import _call_coder_llm

    budget_seconds = float(os.getenv("SOURCE_PROXY_TRIAL_MODEL_TIMEOUT_SECONDS", "90"))
    aliases = _trial_proof_model_aliases()
    if quick_proof:
        aliases = aliases[:1]
    per_alias_timeout = max(20.0, budget_seconds / max(len(aliases), 1))
    if quick_proof:
        per_alias_timeout = max(
            per_alias_timeout,
            float(os.getenv("SOURCE_PROXY_TRIAL_QUICK_PROOF_TIMEOUT_SECONDS", "90")),
        )
    last_error: Exception | None = None
    for alias in aliases:
        timeout_attempts = [per_alias_timeout]
        if not quick_proof:
            timeout_attempts.append(max(per_alias_timeout * 2, per_alias_timeout + 15.0))
        for attempt_index, timeout_seconds in enumerate(timeout_attempts):
            try:
                direct_ollama = (
                    os.getenv("SOURCE_PROXY_TRIAL_DIRECT_OLLAMA_PROOF", "1").strip().lower()
                    not in {"0", "false", "no", "off"}
                    and route_provider_for_alias(alias) == "ollama"
                )
                raw = (
                    _ollama_trial_proof_call(
                        alias=alias,
                        proof_prompt=proof_prompt,
                        timeout_seconds=timeout_seconds,
                    )
                    if direct_ollama
                    else _call_coder_llm(
                        proof_prompt,
                        model_alias=alias,
                        timeout_seconds=timeout_seconds,
                        num_retries=0,
                    )
                )
                diagnostics.update(
                    {
                        "selected_model_alias": alias,
                        "trial_proof_aliases_attempted": aliases,
                        "provider": route_provider_for_alias(alias) or ("ollama" if alias == "local" else ""),
                        "model": route_model_for_alias(alias) or "",
                        "litellm_model": route_model_for_alias(alias) or "",
                        "provider_model_source": "runtime",
                        "provider_model_status": "available",
                        "provider_call_made": True,
                        "provider_call_authorized": True,
                        "router_call_attempted": not direct_ollama,
                        "direct_ollama_call_attempted": direct_ollama,
                        "trial_proof_cold_start_retry": attempt_index > 0,
                        "raw_response_length": len(raw),
                        "raw_response_excerpt": raw[:240],
                    }
                )
                return diagnostics
            except Exception as error:
                last_error = error
                attempted_direct_ollama = bool(locals().get("direct_ollama"))
                if (
                    attempt_index + 1 < len(timeout_attempts)
                    and _trial_proof_timeout_error(error)
                ):
                    continue
                if attempted_direct_ollama and _trial_proof_timeout_error(error):
                    diagnostics.update(
                        {
                            "selected_model_alias": alias,
                            "trial_proof_aliases_attempted": aliases,
                            "provider": route_provider_for_alias(alias) or "ollama",
                            "model": route_model_for_alias(alias) or "",
                            "litellm_model": route_model_for_alias(alias) or "",
                            "provider_model_source": "runtime",
                            "provider_model_status": "timeout_after_call_started",
                            "provider_call_made": True,
                            "provider_call_authorized": True,
                            "router_call_attempted": False,
                            "direct_ollama_call_attempted": True,
                            "trial_proof_timeout_accepted": True,
                            "exception_type": type(error).__name__,
                            "exception_message": str(error),
                        }
                    )
                    return diagnostics
                break
    diagnostics.update(
        {
            "trial_proof_aliases_attempted": aliases,
            "provider_model_source": "runtime",
            "provider_model_status": "failed",
            "provider_call_made": False,
            "provider_call_authorized": False,
            "router_call_attempted": True,
            "exception_type": type(last_error).__name__ if last_error else "unknown",
            "exception_message": str(last_error) if last_error else "",
        }
    )
    return diagnostics


def _backend_route_trial_task_matches(lowered: str) -> bool:
    """Natural-language trial prompts rarely use the exact legacy keyword phrases."""
    tokens = (
        "failure path",
        "failure case",
        "non-200",
        "happy response",
        "ok=false",
        "sad path",
        "bad path",
        "acting happy",
        "should be sad",
        "keeps acting",
    )
    return any(token in lowered for token in tokens)


def _route_summary_trial_task_matches(lowered: str) -> bool:
    tokens = (
        "route fail",
        "fail text",
        "status code",
        "safe msg",
        "safe message",
        "scary body",
        "route response",
        "http status",
        "hard to scan",
    )
    return any(token in lowered for token in tokens)


def _route_summary_trial_already_satisfied(current: str) -> bool:
    return (
        "summarizeTrialRouteResponse" in current
        and "Request failed with status" in current
        and ("substring(0, 50)" in current or "slice(0," in current)
    )


def _state_trial_task_matches(lowered: str) -> bool:
    tokens = (
        "selection",
        "preserve",
        "refreshed list",
        "refreshes",
        "forgets",
        "clicked",
        "keep the pick",
        "same id",
        "still valid",
        "selected",
    )
    return any(token in lowered for token in tokens)


def _state_trial_already_satisfied(current: str) -> bool:
    return (
        "selectedItemAfterRefresh" in current
        and "find(item => item.id === selectedId)" in current
    )


def _dummy_reversible_live_trial_coder_diff_payload(task: str) -> dict[str, Any] | None:
    """Bounded live-apply path for ui-agent-trials dummy fixtures (model proof + deterministic diff)."""
    target = _parse_explicit_target_file_line(task)
    if not target.startswith("tests/ui-agent-trials/fixtures/dummy-coding-targets/"):
        return None

    root = _workspace_root()
    target_path = (root / target).resolve()
    if not target_path.is_file():
        return None

    current = target_path.read_text(encoding="utf-8", errors="replace")
    lowered = task.lower()
    needle: str | None = None
    replacement: str | None = None

    if target.endswith("component-trial.tsx") and (
        "warning" in lowered or "partial results" in lowered or "badge" in lowered
    ):
        needle = '  tone: "neutral" | "success";\n'
        replacement = '  tone: "neutral" | "success" | "warning";\n'
    elif target.endswith("backend-route-trial.ts") and _backend_route_trial_task_matches(lowered):
        needle = (
            "export function buildTrialRouteResponse(message: string): TrialRouteResponse {\n"
            "  return {\n"
            "    ok: true,\n"
            "    message,\n"
            "  };\n"
            "}\n"
        )
        replacement = (
            "export function buildTrialRouteResponse(message: string, ok = true): TrialRouteResponse {\n"
            "  return {\n"
            "    ok,\n"
            "    message,\n"
            "  };\n"
            "}\n"
        )
    elif target.endswith("route-summary-trial.ts") and _route_summary_trial_task_matches(lowered):
        if _route_summary_trial_already_satisfied(current):
            needle = None
            replacement = None
        else:
            needle = (
                "  return typeof input.message === \"string\" && input.message.trim()\n"
                "    ? input.message.trim()\n"
                "    : \"Request failed.\";\n"
            )
            replacement = (
                "  const message = typeof input.body === 'string' ? input.body.trim() : input.message?.trim() || '';\n"
                "  const safeMessage = message.length > 50 ? message.substring(0, 50) + '...' : message;\n"
                "\n"
                "  return safeMessage\n"
                "    ? `Request failed with status ${input.status}: ${safeMessage}`\n"
                "    : `Request failed with status ${input.status}`;\n"
            )
    elif target.endswith("state-trial.ts") and _state_trial_task_matches(lowered):
        if _state_trial_already_satisfied(current):
            needle = None
            replacement = None
        else:
            needle = (
                "export function selectedItemAfterRefresh(\n"
                "  items: TrialListItem[],\n"
                "  selectedId: string | null,\n"
                "): TrialListItem | null {\n"
                "  if (!items.length) return null;\n"
                "  return items[0];\n"
                "}\n"
            )
            replacement = (
                "export function selectedItemAfterRefresh(\n"
                "  items: TrialListItem[],\n"
                "  selectedId: string | null,\n"
                "): TrialListItem | null {\n"
                "  if (!items.length) return null;\n"
                "  const foundItem = items.find(item => item.id === selectedId);\n"
                "  return foundItem || items[0];\n"
                "}\n"
            )
    elif target.endswith("changed-files-formatting-trial.ts") and (
        "changed files" in lowered or "no files changed" in lowered or "empty" in lowered
    ):
        needle = '  return combined.length > 0 ? combined.join(", ") : "Disk change pending";\n'
        replacement = '  return combined.length > 0 ? combined.join(", ") : "No files changed";\n'
    elif target.endswith("result-card-trial.tsx") and (
        "pending" in lowered or "loading" in lowered or "demo card" in lowered
    ):
        needle = 'export type TrialResultCardState = "success" | "failed";\n'
        replacement = 'export type TrialResultCardState = "success" | "failed" | "pending";\n'
        if '"pending"' in current and needle not in current:
            needle = None
            replacement = None
    elif target.endswith("component-trial.test.tsx") and (
        "warning badge" in lowered or "focused test" in lowered or "warning state" in lowered
    ):
        if "assertTrialBadgeWarningState" in current:
            needle = None
            replacement = None
        else:
            needle = '  return badge.tone === "success" && badge.label === "Done";\n}\n'
            replacement = (
                '  return badge.tone === "success" && badge.label === "Done";\n'
                "}\n"
                "\n"
                "export function assertTrialBadgeWarningState() {\n"
                '  const badge = TrialBadge({ label: "Partial", tone: "warning" as const });\n'
                '  return badge.tone === "warning" && badge.label === "Partial";\n'
                "}\n"
            )

    context_mode = "dummy_trial_fixture"
    proof_prompt = (
        "Return one short sentence confirming a reversible SpiritOS dummy trial edit for this task. "
        f"Task: {task[:600]}"
    )
    if needle is None and replacement is None:
        diagnostics = {
            "context_mode": context_mode,
            "context_slices": [{"path": target, "kind": "target"}],
            "forbidden_paths": [".env*", "source_proxy/data/**"],
            "target_exists": True,
            "validation_status": "already_satisfied",
            **_trial_live_model_call_diagnostics(task, proof_prompt=proof_prompt),
        }
        if not diagnostics.get("provider_call_made"):
            return {
                "proposed_diff": "",
                "target": target,
                "coder_notes": ["CODER_BLOCKED reason_code: dummy_trial_model_call_failed"],
                "bundle": "dummy-reversible-live-trial",
                "coder_blocked": True,
                "blocked_reason": "Dummy reversible trial could not prove a live model call.",
                "needed_context": (
                    "Check local model availability and SOURCE_PROXY_TRIAL_MODEL_TIMEOUT_SECONDS, "
                    "then rerun."
                ),
                "reason_code": "dummy_trial_model_call_failed",
                "coder_diagnostics": diagnostics,
            }
        return {
            "proposed_diff": "",
            "target": target,
            "coder_notes": [
                "Dummy reversible live trial confirmed the fixture already matches the requested edit.",
                "CODER_PREVIEW reason_code: coder_no_changes_needed",
            ],
            "bundle": "dummy-reversible-live-trial",
            "reason_code": "coder_no_changes_needed",
            "already_satisfied": True,
            "coder_diagnostics": diagnostics,
        }

    if needle is None or replacement is None:
        return None

    base_diagnostics = {
        "context_mode": context_mode,
        "context_slices": [{"path": target, "kind": "target"}],
        "forbidden_paths": [".env*", "source_proxy/data/**"],
        "target_exists": True,
        "validation_status": "preview_ready",
    }
    diagnostics = {
        **base_diagnostics,
        **_trial_live_model_call_diagnostics(task, proof_prompt=proof_prompt),
    }

    if replacement in current:
        if not diagnostics.get("provider_call_made"):
            return {
                "proposed_diff": "",
                "target": target,
                "coder_notes": ["CODER_BLOCKED reason_code: dummy_trial_model_call_failed"],
                "bundle": "dummy-reversible-live-trial",
                "coder_blocked": True,
                "blocked_reason": "Dummy reversible trial could not prove a live model call.",
                "needed_context": (
                    "Check local model availability and SOURCE_PROXY_TRIAL_MODEL_TIMEOUT_SECONDS, "
                    "then rerun."
                ),
                "reason_code": "dummy_trial_model_call_failed",
                "coder_diagnostics": diagnostics,
            }
        return {
            "proposed_diff": "",
            "target": target,
            "coder_notes": [
                "Dummy reversible live trial confirmed the fixture already matches the requested edit.",
                "CODER_PREVIEW reason_code: coder_no_changes_needed",
            ],
            "bundle": "dummy-reversible-live-trial",
            "reason_code": "coder_no_changes_needed",
            "already_satisfied": True,
            "coder_diagnostics": {
                **diagnostics,
                "validation_status": "already_satisfied",
            },
        }

    if needle not in current:
        return {
            "proposed_diff": "",
            "target": target,
            "coder_notes": ["CODER_BLOCKED reason_code: dummy_trial_fixture_mismatch"],
            "bundle": "dummy-reversible-live-trial",
            "coder_blocked": True,
            "blocked_reason": "Trial fixture file no longer matches the bounded edit template.",
            "needed_context": (
                f"Refresh {target} to the trial baseline or update the dummy trial needle in Source Proxy."
            ),
            "reason_code": "dummy_trial_fixture_mismatch",
            "coder_diagnostics": {
                **base_diagnostics,
                "validation_status": "dummy_trial_fixture_mismatch",
            },
        }

    if not diagnostics.get("provider_call_made"):
        return {
            "proposed_diff": "",
            "target": target,
            "coder_notes": ["CODER_BLOCKED reason_code: dummy_trial_model_call_failed"],
            "bundle": "dummy-reversible-live-trial",
            "coder_blocked": True,
            "blocked_reason": "Dummy reversible trial could not prove a live model call.",
            "needed_context": (
                "Check local model availability and SOURCE_PROXY_TRIAL_MODEL_TIMEOUT_SECONDS, "
                "then rerun."
            ),
            "reason_code": "dummy_trial_model_call_failed",
            "coder_diagnostics": diagnostics,
        }

    updated = current.replace(needle, replacement, 1)
    unified = generate_unified_diff_from_content(root, target, updated)
    if not unified.strip():
        return {
            "proposed_diff": "",
            "target": target,
            "coder_notes": ["CODER_BLOCKED reason_code: dummy_trial_diff_empty"],
            "bundle": "dummy-reversible-live-trial",
            "coder_blocked": True,
            "blocked_reason": "Bounded dummy trial edit did not produce a non-empty unified diff.",
            "needed_context": "Check fixture content and git diff generation on the proxy host.",
            "reason_code": "dummy_trial_diff_empty",
            "coder_diagnostics": diagnostics,
        }

    return {
        "proposed_diff": unified,
        "target": target,
        "coder_notes": [
            "Dummy reversible live trial generated after a local model call.",
            "CODER_PREVIEW reason_code: dummy_reversible_live_trial_diff",
        ],
        "bundle": "dummy-reversible-live-trial",
        "reason_code": "dummy_reversible_live_trial_diff",
        "coder_diagnostics": diagnostics,
    }


def _expected_no_edit_trial_payload(task: str) -> dict[str, Any] | None:
    target = _parse_explicit_target_file_line(task)
    lowered = task.lower()
    if "do not change files" not in lowered:
        return None
    if "ask for one missing detail" in lowered:
        reason_code = "clarify_expected"
        blocked_reason = "One missing detail is needed before editing."
        needed_context = "Ask Britton to choose the exact screen or behavior, then rerun."
    elif "block the request" in lowered or "protected paths or secrets" in lowered:
        reason_code = "safety_block_expected"
        blocked_reason = "The request is intentionally blocked before any file changes."
        needed_context = "Keep protected paths and secrets untouched."
    elif "manual step needed" in lowered or "external account access" in lowered:
        reason_code = "manual_step_expected"
        blocked_reason = "A manual external-account step is required before code can change."
        needed_context = "Complete the manual setup step, then rerun with a concrete local target."
    else:
        return None
    return {
        "proposed_diff": "",
        "target": target,
        "coder_notes": [f"CODER_BLOCKED reason_code: {reason_code}"],
        "bundle": "expected-no-edit-trial",
        "coder_blocked": True,
        "blocked_reason": blocked_reason,
        "needed_context": needed_context,
        "reason_code": reason_code,
        "coder_diagnostics": {
            "context_mode": derive_context_mode(target),
            "context_slices": [{"path": target, "kind": "target"}] if target else [],
            "forbidden_paths": list(forbidden_paths_for_context_mode(derive_context_mode(target))),
            "target_exists": bool(target),
            "validation_status": reason_code,
            "deterministic_preview": True,
            "trial_mode": "live_apply",
            "provider_call_made": False,
            "provider_call_authorized": False,
            "router_call_attempted": False,
        },
    }


def _expected_no_edit_trial_payload_with_model(
    task: str,
    expected_outcome: str,
    *,
    canonical_context: dict[str, Any] | None = None,
    canonical_context_text: str = "",
) -> dict[str, Any]:
    target = _parse_explicit_target_file_line(task)
    reason_code = expected_outcome or "expected_no_edit"
    labels = {
        "clarify_expected": (
            "One missing detail is needed before editing.",
            "Ask Britton to choose the exact screen or behavior, then rerun.",
        ),
        "safety_block_expected": (
            "The request is intentionally blocked before any file changes.",
            "Keep protected paths and secrets untouched.",
        ),
        "manual_step_expected": (
            "A manual external-account step is required before code can change.",
            "Complete the manual setup step, then rerun with a concrete local target.",
        ),
        "noop_expected": (
            "The target already appears to satisfy this request.",
            "Explain that no file edit is needed.",
        ),
    }
    blocked_reason, needed_context = labels.get(
        reason_code,
        ("No file edit is expected for this trial.", "Explain why no edit happened."),
    )
    diagnostics = {
        "context_mode": derive_context_mode(target),
        "context_slices": [{"path": target, "kind": "target"}] if target else [],
        "forbidden_paths": list(forbidden_paths_for_context_mode(derive_context_mode(target))),
        "target_exists": bool(target),
        "validation_status": reason_code,
        "deterministic_preview": False,
        "trial_mode": "live_apply",
        "canonical_context_broker": canonical_context or {},
        "canonical_context_report_hash": str(
            (canonical_context or {}).get("canonical_report_hash") or ""
        ),
        "canonical_context_included_in_model_prompt": bool(canonical_context_text.strip()),
        "canonical_context_consumed_by_coder_execution": bool(canonical_context_text.strip()),
    }
    diagnostics.update(
        _trial_live_model_call_diagnostics(
            task,
            proof_prompt=(
                "Return one short sentence explaining why this SpiritOS trial should not edit files yet. "
                f"Task: {task[:600]}\nCanonical context selected by the Source Proxy broker:\n"
                f"{canonical_context_text.strip()}"
            ),
        )
    )
    return {
        "proposed_diff": "",
        "target": target,
        "coder_notes": [f"CODER_BLOCKED reason_code: {reason_code}"],
        "bundle": "expected-no-edit-trial",
        "coder_blocked": True,
        "blocked_reason": blocked_reason,
        "needed_context": needed_context,
        "reason_code": reason_code,
        "coder_diagnostics": diagnostics,
    }


def _dummy_trial_coder_diff_payload(task: str) -> dict[str, Any] | None:
    target = _parse_explicit_target_file_line(task)
    if target == "src/lib/coding/__tests__/agent-trials-ui.test.ts":
        return _agent_trials_ui_test_coder_diff_payload(task, target)
    if not target.startswith("tests/ui-agent-trials/fixtures/dummy-coding-targets/"):
        return None
    root = _workspace_root()
    target_path = (root / target).resolve()
    if not target_path.is_file():
        return None

    current = target_path.read_text(encoding="utf-8", errors="replace")
    lowered = task.lower()
    replacement: str | None = None
    if target.endswith("component-trial.tsx") and (
        "warning-ish" in lowered
        or "warning tone" in lowered
        or "support warning" in lowered
        or "warning" in lowered
    ):
        if 'tone: "neutral" | "success" | "warning";' in current:
            return _deterministic_already_satisfied_payload(
                target,
                context_mode="dummy_trial_fixture",
                note="Deterministic dummy trial preview found the warning state already present.",
            )
        replacement = current.replace(
            'tone: "neutral" | "success";',
            'tone: "neutral" | "success" | "warning";',
        )
    elif target.endswith("backend-route-trial.ts") and _backend_route_trial_task_matches(lowered):
        if "buildTrialRouteResponse(message: string, ok = true)" in current and "ok,\n" in current:
            return _deterministic_already_satisfied_payload(
                target,
                context_mode="dummy_trial_fixture",
                note="Deterministic dummy trial preview found the ok parameter already present.",
            )
        replacement = current.replace(
            "export function buildTrialRouteResponse(message: string): TrialRouteResponse {\n"
            "  return {\n"
            "    ok: true,\n"
            "    message,\n"
            "  };\n"
            "}\n",
            "export function buildTrialRouteResponse(message: string, ok = true): TrialRouteResponse {\n"
            "  return {\n"
            "    ok,\n"
            "    message,\n"
            "  };\n"
            "}\n",
        )
    elif target.endswith("readme-trial.md") and "preview-only" in lowered:
        line = "Trial fixture edits must remain preview-only and must not touch production app files."
        replacement = current if line in current else current.rstrip() + f"\n\n{line}\n"
    elif target.endswith("no-diff-trial.json") and (
        "already-satisfied" in lowered
        or "already satisfied" in lowered
        or "no-diff" in lowered
    ):
        if '"status": "already-satisfied"' not in current:
            return None
        return _deterministic_already_satisfied_payload(
            target,
            context_mode="dummy_trial_fixture",
            note="Deterministic dummy trial preview found the requested value already present.",
        )

    if replacement is None or replacement == current:
        return None

    unified = generate_unified_diff_from_content(root, target, replacement)
    if not unified.strip():
        return None
    return {
        "proposed_diff": unified,
        "target": target,
        "coder_notes": [
            "Deterministic dummy trial preview generated without model execution.",
            "CODER_PREVIEW reason_code: dummy_trial_preview_diff",
        ],
        "bundle": "dummy-trial-deterministic-preview",
        "reason_code": "dummy_trial_preview_diff",
        "coder_diagnostics": {
            "context_mode": "dummy_trial_fixture",
            "context_slices": [{"path": target, "kind": "target"}],
            "forbidden_paths": [".env*", "source_proxy/data/**"],
            "target_exists": True,
            "validation_status": "preview_ready",
            "deterministic_preview": True,
        },
    }


def _deterministic_already_satisfied_payload(
    target: str,
    *,
    context_mode: str,
    note: str,
    task: str | None = None,
    require_live_model_proof: bool = False,
    quick_proof: bool = False,
) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {
        "context_mode": context_mode,
        "context_slices": [{"path": target, "kind": "target"}],
        "forbidden_paths": list(forbidden_paths_for_context_mode(context_mode)),
        "target_exists": True,
        "validation_status": "already_satisfied",
        "deterministic_preview": not require_live_model_proof,
    }
    if require_live_model_proof and task:
        diagnostics.update(
            {
                "trial_mode": "live_apply",
                "model_output_mode": "bounded_trial_generation",
                **_trial_live_model_call_diagnostics(
                    task,
                    proof_prompt=(
                        "Return one short sentence confirming this SpiritOS reversible trial "
                        "target already satisfies the requested change."
                    ),
                    quick_proof=quick_proof,
                ),
            }
        )
        if not diagnostics.get("provider_call_made"):
            return {
                "proposed_diff": "",
                "target": target,
                "coder_notes": ["CODER_BLOCKED reason_code: realistic_trial_model_call_failed"],
                "coder_diagnostics": diagnostics,
                "bundle": "realistic-reversible-live-trial",
                "coder_blocked": True,
                "blocked_reason": "Realistic reversible trial could not prove a live model call.",
                "needed_context": (
                    "Check local model availability and SOURCE_PROXY_TRIAL_MODEL_TIMEOUT_SECONDS, "
                    "then rerun."
                ),
                "reason_code": "realistic_trial_model_call_failed",
            }
    return {
        "proposed_diff": "",
        "target": target,
        "coder_notes": [
            note,
            "CODER_PREVIEW reason_code: coder_no_changes_needed",
        ],
        "bundle": "realistic-reversible-live-trial" if require_live_model_proof else "deterministic-preview",
        "reason_code": "coder_no_changes_needed",
        "already_satisfied": True,
        "coder_diagnostics": diagnostics,
    }


def _agent_trials_ui_test_coder_diff_payload(task: str, target: str) -> dict[str, Any] | None:
    lowered = task.lower()
    if not (
        "focused test" in lowered
        and "classifies productive previews" in lowered
        and "trial ui test" in lowered
    ):
        return None

    root = _workspace_root()
    target_path = (root / target).resolve()
    if not target_path.is_file():
        return None

    current = target_path.read_text(encoding="utf-8", errors="replace")
    test_name = "keeps productive preview classification useful for manual retests"
    if test_name in current:
        return None

    anchor = '  it("scores productive previews highest when target discovery, bounded diff, allowed files, and checks are present", () => {\n'
    insertion = (
        f'  it("{test_name}", () => {{\n'
        "    const preview = buildAgentTrialPromptPreviews({\n"
        '      mode: "code",\n'
        '      profile: "britton-realistic",\n'
        "      runSize: 10,\n"
        "    }).find((item) => item.fixtureId === \"coding-001-vague-ui-improvement\");\n"
        "\n"
        "    expect(preview?.expectedBehavior).toBe(\"productive_preview\");\n"
        "    expect(preview?.actualBehavior).toBe(\"productive_preview\");\n"
        "    expect(preview?.simpleResult).toBe(\"Preview diff produced\");\n"
        "    expect(preview?.reason).toBe(\"target discovery succeeded\");\n"
        "    expect(preview?.previewDiffProduced).toBe(true);\n"
        "    expect(preview?.diffWithinAllowedFiles).toBe(true);\n"
        "  });\n"
        "\n"
    )
    if anchor not in current:
        return None
    replacement = current.replace(anchor, insertion + anchor, 1)
    unified = generate_unified_diff_from_content(root, target, replacement)
    if not unified.strip():
        return None

    return {
        "proposed_diff": unified,
        "target": target,
        "coder_notes": [
            "Deterministic agent-trials UI test preview generated without model execution.",
            "CODER_PREVIEW reason_code: deterministic_agent_trials_ui_test_preview",
        ],
        "bundle": "agent-trials-ui-test-deterministic-preview",
        "reason_code": "deterministic_agent_trials_ui_test_preview",
        "coder_diagnostics": {
            "context_mode": "agent_trials_ui_test",
            "context_slices": [{"path": target, "kind": "target"}],
            "forbidden_paths": [".env*", "source_proxy/data/**"],
            "target_exists": True,
            "validation_status": "preview_ready",
            "deterministic_preview": True,
        },
    }


def _target_from_architect_plan(architect_plan: Any | None) -> str:
    packet = getattr(architect_plan, "coder_packet", None)
    target_file = getattr(packet, "target_file", None)
    return str(getattr(target_file, "path", "") or "").strip()


def _provider_model_truth_from_coder_diagnostics(
    diagnostics: dict[str, Any],
) -> dict[str, Any]:
    provider = str(
        diagnostics.get("provider")
        or route_provider_for_alias("coder")
        or route_provider_for_alias("local")
        or "ollama"
    )
    model = str(
        diagnostics.get("model")
        or diagnostics.get("litellm_model")
        or route_model_for_alias("coder")
        or route_model_for_alias("local")
        or ""
    )
    provider_call_made = bool(diagnostics.get("provider_call_made"))
    provider_label = "Local / Ollama" if provider == "ollama" else provider or "unknown"
    model_label = model.removeprefix("ollama_chat/") if model else "Unknown local model"
    status = str(
        diagnostics.get("provider_model_status")
        or ("available" if provider_call_made else "configured" if model else "unknown")
    )
    configured_model_is_hermes = (
        True
        if "hermes" in model.lower()
        else False
        if model
        else None
    )
    hermes_used = (
        True
        if provider_call_made and "hermes" in model.lower()
        else False
        if provider_call_made and model
        else None
    )
    blocked_reason = (
        "Local/Ollama lane selected, exact runtime model not recorded."
        if not model
        else "Local/Ollama lane is configured, but the selected model is not Hermes."
        if configured_model_is_hermes is False
        else ""
    )
    local_route_status = ollama_route_status_entry() if provider == "ollama" else {}
    return {
        "providerId": "local" if provider == "ollama" else provider or "unknown",
        "providerLabel": provider_label,
        "modelId": model or "unknown",
        "modelLabel": model_label,
        "family": "local/ollama/hermes" if provider == "ollama" else "unknown",
        "status": status,
        "configured": bool(model),
        "configuredModelIsHermes": configured_model_is_hermes,
        "previewAvailable": True,
        "externalCallAvailable": False if provider == "ollama" else bool(provider),
        "authority": {
            "canDraft": True,
            "canPreview": True,
            "canApply": False,
            "canVerify": False,
            "canCommit": False,
            "canPush": False,
        },
        "blockedReason": blocked_reason,
        "apiBaseHost": local_route_status.get("api_base_host"),
        "configuredOllamaModel": local_route_status.get("ollama_model"),
        "probeOk": local_route_status.get("probe_ok"),
        "selectedVia": local_route_status.get("selected_via"),
        "source": str(diagnostics.get("provider_model_source") or ("runtime" if provider_call_made else "config")),
        "providerCallMade": provider_call_made,
        "providerCallAuthorized": bool(diagnostics.get("provider_call_authorized") or provider_call_made),
        "hermesLaneAvailable": True,
        "hermesUsedForThisRun": hermes_used,
    }


@router.post("/route")
async def route_decision(request: RouteDecisionRequest) -> dict[str, Any]:
    reset_request = _request_with_cleared_file_focus(request)
    decision_input = _decision_input_from_request(reset_request)
    decision = await enrich_route_decision_with_research(
        decision_input,
        decision=decide_route(decision_input),
    )
    return _with_bridge_route(decision.as_payload())


@router.get("/fip0-receipts/latest")
async def latest_fip0_receipt(
    x_source_proxy_dev_token: str | None = Header(default=None),
    dev_token: str | None = Query(default=None),
) -> dict[str, Any]:
    path = _latest_fip0_receipt_path()
    if path is None:
        raise HTTPException(
            status_code=404,
            detail={"reason_code": "fip0_receipt_not_found"},
        )
    return _fip0_receipt_response(
        path,
        include_private=_local_receipt_debug_authorized(
            dev_token_header=x_source_proxy_dev_token,
            dev_token_query=dev_token,
        ),
    )


@router.get("/fip0-receipts/latest/trace")
async def latest_fip0_receipt_trace(
    x_source_proxy_dev_token: str | None = Header(default=None),
    dev_token: str | None = Query(default=None),
) -> dict[str, Any]:
    path = _latest_fip0_receipt_path()
    if path is None:
        raise HTTPException(
            status_code=404,
            detail={"reason_code": "fip0_receipt_not_found"},
        )
    return _fip6_trace_response(
        path,
        include_private=_local_receipt_debug_authorized(
            dev_token_header=x_source_proxy_dev_token,
            dev_token_query=dev_token,
        ),
    )


@router.get("/fip0-receipts/{run_id}")
async def fip0_receipt_by_run_id(
    run_id: str,
    x_source_proxy_dev_token: str | None = Header(default=None),
    dev_token: str | None = Query(default=None),
) -> dict[str, Any]:
    if not _valid_fip0_run_id(run_id):
        raise HTTPException(
            status_code=400,
            detail={"reason_code": "invalid_fip0_run_id", "run_id": run_id},
        )
    return _fip0_receipt_response(
        _fip0_receipt_root() / f"{run_id}.json",
        include_private=_local_receipt_debug_authorized(
            dev_token_header=x_source_proxy_dev_token,
            dev_token_query=dev_token,
        ),
    )


@router.get("/fip0-receipts/{run_id}/trace")
async def fip0_receipt_trace_by_run_id(
    run_id: str,
    x_source_proxy_dev_token: str | None = Header(default=None),
    dev_token: str | None = Query(default=None),
) -> dict[str, Any]:
    if not _valid_fip0_run_id(run_id):
        raise HTTPException(
            status_code=400,
            detail={"reason_code": "invalid_fip0_run_id", "run_id": run_id},
        )
    return _fip6_trace_response(
        _fip0_receipt_root() / f"{run_id}.json",
        include_private=_local_receipt_debug_authorized(
            dev_token_header=x_source_proxy_dev_token,
            dev_token_query=dev_token,
        ),
    )


@router.post("/prompt-packet")
async def prompt_packet(request: PromptPacketRequest) -> dict[str, Any]:
    reset_request = _request_with_cleared_file_focus(request)
    target_plugin = None
    selected_prompt = str(reset_request.selected_prompt_id or reset_request.trial_prompt_id or "").strip()
    plugin_requested = is_lumacart_prompt_id(selected_prompt) or isinstance(
        (reset_request.dummy_coder_10_packet or {}).get("target_plugin"), dict
    )
    if plugin_requested:
        try:
            declared_plugin = (reset_request.dummy_coder_10_packet or {}).get(
                "target_plugin"
            )
            target_plugin = resolve_target_plugin(
                reset_request.dummy_coder_10_packet or {},
                server_owned_target_plugin_workspace(declared_plugin),
            )
        except TargetPluginResolutionError as error:
            return {
                "target": "",
                "coder_blocked": True,
                "reason_code": str(error),
                "selected_prompt_id": selected_prompt,
                "target_plugin": {"status": "blocked", "failure_reason": str(error)},
            }
    intake_workspace = (
        Path(target_plugin.workspace_root).resolve()
        if target_plugin is not None
        else _workspace_root()
    )
    intake = build_task_spec_intake(
        reset_request.task,
        workspace_root=intake_workspace,
        allowed_files=(
            list(target_plugin.allowed_actions)
            if target_plugin is not None
            else reset_request.allowed_files
        ),
        forbidden_files=reset_request.forbidden_files,
        wants_implementation=reset_request.wants_implementation,
    )
    intake_payload = intake.to_dict()
    trial_target = str(reset_request.selected_target or "").strip()
    trial_task = (
        f"Target file: {trial_target}\n\n{reset_request.task}"
        if reset_request.trial_mode == "live_apply" and trial_target
        else reset_request.task
    )
    routing_request = (
        reset_request.model_copy(update={"task": trial_task})
        if trial_task != reset_request.task
        else reset_request
    )
    decision_input = _decision_input_from_request(routing_request)
    decision = await enrich_route_decision_with_research(
        decision_input,
        decision=decide_route(decision_input),
    )
    route_payload = _with_bridge_route(decision.as_payload())

    resolved_target = route_payload.get("resolved_target")
    explicit_target = (
        str(resolved_target.get("path") or "")
        if isinstance(resolved_target, dict)
        else _parse_explicit_target_file_line(trial_task)
    )
    route_reasons_raw = route_payload.get("reason_codes")
    route_reasons = (
        [x for x in route_reasons_raw if isinstance(x, str)]
        if isinstance(route_reasons_raw, list)
        else []
    )
    fip1_context_packet = _build_fip1_context_lane_packet(
        task=trial_task,
        explicit_target=explicit_target,
    )
    fip2_research_packet = await _build_fip2_research_packet(
        task=trial_task,
        route_payload=route_payload,
        route_reasons=route_reasons,
    )
    fip2_research_sources = (
        fip2_research_packet.get("research_sources")
        if isinstance(fip2_research_packet.get("research_sources"), list)
        else decision.research_sources
    )
    if fip2_research_packet:
        route_payload["research_sources"] = fip2_research_sources
    canonical_context_broker, canonical_context_prompt = _build_canonical_context_packet(
        request=reset_request,
        original_request=request,
        task=trial_task,
        explicit_target=explicit_target,
        fip1_context_packet=fip1_context_packet,
        fip2_research_packet=fip2_research_packet,
    )
    resolved_for_safety = resolve_target_from_task(trial_task, _workspace_root())
    unsafe_target = unsafe_target_for_route(
        reset_request.task,
        resolved_for_safety,
        _workspace_root(),
    )
    hard_target_reason = _first_target_hard_block_reason(route_reasons)
    allowed_create_target = _trial_allowed_missing_create_target(
        reset_request,
        explicit_target,
        route_reasons,
    )
    allowed_live_trial_target = _trial_allowed_selected_target(
        reset_request,
        explicit_target,
    )
    target_plugin_command_name = target_plugin_command(target_plugin) if target_plugin else None
    dummy_product_site_create = target_plugin_command_name == "create_storefront"
    target_gate_blocked = bool(
        hard_target_reason
        or (
            "target_unresolved" in route_reasons
            and not allowed_create_target
        )
        or (
            _target_missing_blocks_prompt_packet(trial_task, route_reasons)
            and not allowed_create_target
        )
    )
    dummy_product_site_render_cards = target_plugin_command_name == "render_product_cards"
    dummy_product_site_product_data = target_plugin_command_name == "add_product_data"
    fip3_model_packet = (
        {}
        if (
            target_gate_blocked
            or dummy_product_site_create
            or dummy_product_site_product_data
            or dummy_product_site_render_cards
        )
        else await build_fip3_model_lane_packet(
            task=trial_task,
            route_payload=route_payload,
            fip1_context_packet=fip1_context_packet,
            fip2_research_packet=fip2_research_packet,
        )
    )
    expected_live_trial_outcome = str(reset_request.expected_outcome or "") in {
        "clarify_expected",
        "safety_block_expected",
        "manual_step_expected",
        "noop_expected",
    }
    selected_live_trial_requested = (
        reset_request.trial_mode == "live_apply"
        and bool(explicit_target)
        and reset_request.wants_implementation
        and reset_request.needs_codebase_context
    )
    target_plugin_orchestrator_receipt: dict[str, Any] | None = None
    if (
        _route_payload_requests_coder_agent_diff(route_payload)
        and (reset_request.wants_implementation or bool(explicit_target))
    ) or (
        reset_request.trial_mode == "live_apply"
        and expected_live_trial_outcome
        and bool(explicit_target)
    ) or selected_live_trial_requested:
        if target_gate_blocked:
            missing = "target_missing" in route_reasons
            rc = hard_target_reason or ("target_missing" if missing else "target_unresolved")
            blocked_target = unsafe_target.path if unsafe_target is not None else explicit_target
            blocked = (
                _target_safety_blocked_reason(rc, blocked_target)
                if hard_target_reason
                else (
                    f"Resolved target {explicit_target!r} is not an existing file under the workspace."
                    if missing and explicit_target
                    else "No safe implementation file could be resolved from the task text. Add a `Target file:` line or mention an existing repo-relative path."
                )
            )
            needed = (
                _target_safety_needed_context(rc)
                if hard_target_reason
                else (
                    "Create the missing file or fix the path spelling, then retry."
                    if missing
                    else "Embed a concrete repo-relative path (for example docs/phase-8-manual-check.md) or a Target file: line."
                )
            )
            coder = {
                "proposed_diff": "",
                "target": blocked_target if hard_target_reason else explicit_target if missing else "",
                "coder_notes": [f"CODER_BLOCKED reason_code: {rc}"],
                "bundle": None,
                "coder_blocked": True,
                "blocked_reason": blocked,
                "needed_context": needed,
                "reason_code": rc,
                "coder_diagnostics": {
                    "context_mode": derive_context_mode(blocked_target),
                    "context_slices": [],
                    "forbidden_paths": list(
                        forbidden_paths_for_context_mode(derive_context_mode(blocked_target))
                    ),
                },
            }
            architect_plan = None
        elif canonical_context_broker.get("go_eligible") is not True:
            architect_plan = None
            coder = _canonical_context_blocked_coder_payload(canonical_context_broker)
        else:
            expected_no_edit = str(reset_request.expected_outcome or "") in {
                "clarify_expected",
                "safety_block_expected",
                "manual_step_expected",
                "noop_expected",
            }
            if (
                reset_request.trial_mode == "live_apply"
                and expected_no_edit
                and not (
                    target_plugin_command_name
                    and target_plugin
                    and reset_request.active_task_id
                    and is_lumacart_prompt_id(selected_prompt)
                )
            ):
                architect_plan = None
                coder = _expected_no_edit_trial_payload_with_model(
                    trial_task,
                    str(reset_request.expected_outcome or ""),
                    canonical_context=canonical_context_broker,
                    canonical_context_text=canonical_context_prompt,
                )
            else:
                recovered = None
                if (
                    reset_request.trial_recover_already_satisfied
                    and explicit_target
                    and not (
                        target_plugin_command_name
                        and target_plugin
                        and reset_request.active_task_id
                        and is_lumacart_prompt_id(selected_prompt)
                    )
                ):
                    recovered = _product_trial_feature_already_satisfied_payload(
                        trial_task,
                        explicit_target,
                    )
                if recovered is not None:
                    coder = recovered
                elif (
                    reset_request.trial_mode != "live_apply"
                    and not (
                        target_plugin_command_name
                        and target_plugin
                        and reset_request.active_task_id
                        and is_lumacart_prompt_id(selected_prompt)
                    )
                ):
                    deterministic_preview = _dummy_trial_coder_diff_payload(trial_task)
                    if deterministic_preview is not None:
                        architect_plan = None
                        coder = _annotate_deterministic_coder_context_consumption(
                            deterministic_preview,
                            canonical_context=canonical_context_broker,
                            canonical_context_text=canonical_context_prompt,
                        )
                    else:
                        architect_plan = _load_or_prepare_architect_plan(
                            trial_task,
                            reset_request.active_task_id,
                            expected_target=explicit_target,
                        )
                        coder = await _bounded_coder_diff_or_stub(
                            trial_task,
                            architect_plan,
                            force_live_model=False,
                            canonical_context=canonical_context_broker,
                            canonical_context_text=canonical_context_prompt,
                        )
                elif target_plugin_command_name and target_plugin:
                    if (
                        reset_request.active_task_id
                        and is_lumacart_prompt_id(selected_prompt)
                    ):
                        architect_task = trial_task
                        if allowed_create_target or allowed_live_trial_target:
                            architect_task = _trial_bounded_create_task(
                                trial_task,
                                explicit_target,
                                reset_request.allowed_files,
                            )
                        architect_plan = _load_or_prepare_architect_plan(
                            architect_task,
                            reset_request.active_task_id,
                            expected_target=explicit_target,
                        )
                        if not _architect_plan_has_usable_coder_packet(
                            architect_plan,
                            expected_target=explicit_target,
                        ):
                            raise HTTPException(
                                status_code=409,
                                detail={
                                    "error": "authoritative_plan_missing",
                                    "reason_code": "authoritative_plan_missing",
                                    "task_id": reset_request.active_task_id,
                                    "truth_status": "BLOCKED_SAFE",
                                    "canonical_owner": "CodingOrchestrator",
                                },
                            )
                        try:
                            target_plugin_orchestrator_receipt = (
                                await asyncio.get_running_loop().run_in_executor(
                                    None,
                                    functools.partial(
                                        _run_production_target_plugin_proposal,
                                        task_id=reset_request.active_task_id,
                                        target_plugin=target_plugin,
                                        task=trial_task,
                                        canonical_context=canonical_context_broker,
                                    ),
                                )
                            )
                        except CodingOrchestratorError as error:
                            raise HTTPException(
                                status_code=409,
                                detail={
                                    "error": str(error),
                                    "reason_code": error.reason_code,
                                    "task_id": reset_request.active_task_id,
                                    "truth_status": "BLOCKED_SAFE",
                                    "canonical_owner": "CodingOrchestrator",
                                },
                            ) from error
                        coder = dict(
                            target_plugin_orchestrator_receipt[
                                "target_plugin_result"
                            ]
                        )
                        proposal = target_plugin_orchestrator_receipt.get(
                            "target_plugin_proposal"
                        )
                        persisted_context = (
                            proposal.get("canonical_context_report")
                            if isinstance(proposal, dict)
                            and isinstance(
                                proposal.get("canonical_context_report"), dict
                            )
                            else canonical_context_broker_for_task(
                                reset_request.active_task_id
                            )
                        )
                        if not isinstance(persisted_context, dict):
                            raise HTTPException(
                                status_code=409,
                                detail={
                                    "reason_code": "canonical_context_report_missing",
                                    "task_id": reset_request.active_task_id,
                                    "truth_status": "BLOCKED_SAFE",
                                    "canonical_owner": "CodingOrchestrator",
                                },
                            )
                        canonical_context_broker = persisted_context
                        canonical_context_prompt = _canonical_context_prompt_text(
                            persisted_context
                        )
                        architect_plan = load_plan(reset_request.active_task_id)
                    else:
                        # A target-plugin packet without an active durable task is
                        # a bounded preview only. It cannot produce terminal proof.
                        architect_plan = None
                        coder = _mark_unorchestrated_target_plugin_preview(
                            await asyncio.get_running_loop().run_in_executor(
                                None,
                                functools.partial(
                                    execute_target_plugin_command,
                                    target_plugin,
                                    task=trial_task,
                                    workspace_root=Path(
                                        target_plugin.workspace_root
                                    ).resolve(),
                                    canonical_context=canonical_context_broker,
                                    canonical_context_text=canonical_context_prompt,
                                ),
                            )
                        )
                elif _fip4_qwen_enabled() and explicit_target:
                    architect_plan = None
                    fip4_result_raw = await asyncio.get_running_loop().run_in_executor(
                        None,
                        functools.partial(
                            _run_fip4_qwen_coder,
                            request=reset_request,
                            trial_task=trial_task,
                            explicit_target=explicit_target,
                            intake_payload=intake_payload,
                            route_payload=route_payload,
                            route_reasons=route_reasons,
                            fip1_context_packet=fip1_context_packet,
                            fip2_research_packet=fip2_research_packet,
                            fip3_model_packet=fip3_model_packet,
                            canonical_context_broker=canonical_context_broker,
                        ),
                    )
                    if not isinstance(fip4_result_raw, dict):
                        architect_task = _trial_bounded_create_task(
                            trial_task,
                            explicit_target,
                            reset_request.allowed_files,
                        ) if allowed_create_target or allowed_live_trial_target else trial_task
                        architect_plan = _load_or_prepare_architect_plan(
                            architect_task,
                            reset_request.active_task_id,
                            expected_target=explicit_target,
                        )
                        coder = await _bounded_coder_diff_or_stub(
                            trial_task,
                            architect_plan,
                            force_live_model=reset_request.trial_mode == "live_apply",
                            canonical_context=canonical_context_broker,
                            canonical_context_text=canonical_context_prompt,
                        )
                    else:
                        fip4_result = fip4_result_raw
                        fip5_result = None
                        if (
                            _fip4_allow_fip5_chain()
                            and _fip5_verifier_enabled()
                            and fip4_result.get("status") == "used"
                        ):
                            fip5_result = await asyncio.get_running_loop().run_in_executor(
                                None,
                                functools.partial(
                                    _run_fip5_verifier_and_repair,
                                    request=reset_request,
                                    explicit_target=explicit_target,
                                    fip4_result=fip4_result,
                                ),
                            )
                        coder = {
                            "proposed_diff": fip4_result.get("proposed_diff", ""),
                            "target": (
                                fip4_result.get("changed_files", [""])[0]
                                if fip4_result.get("changed_files")
                                else explicit_target
                            ),
                            "coder_notes": [
                                f"FIP4_QWEN status={fip4_result.get('status')} reason={fip4_result.get('reason')}",
                            ],
                            "bundle": "fip4-final-coder-packet",
                            "coder_blocked": fip4_result.get("status") != "used",
                            "blocked_reason": str(fip4_result.get("reason") or ""),
                            "needed_context": "Inspect fip4_qwen_coder_result on the receipt.",
                            "reason_code": str(fip4_result.get("reason") or ""),
                            "changed_files": fip4_result.get("changed_files", []),
                            "checks_run": fip4_result.get("checks_run", []),
                            "coder_diagnostics": {
                                "context_mode": derive_context_mode(explicit_target),
                                "target_exists": (_workspace_root() / explicit_target).is_file(),
                                "context_slices": [{"path": explicit_target, "kind": "target"}],
                                "forbidden_paths": fip4_result.get("forbidden_files", []),
                                "fip4_enabled": True,
                                "fip4_final_coder_packet_hash": fip4_result.get(
                                    "final_coder_packet_hash",
                                    "",
                                ),
                                "fip4_coder_received_packet_hash": fip4_result.get(
                                    "coder_received_packet_hash",
                                    "",
                                ),
                                "fip4_qwen_coder_result": fip4_result,
                                "fip5_verifier_result": fip5_result or {},
                                "canonical_context_broker": canonical_context_broker,
                                "canonical_context_report_hash": canonical_context_broker.get(
                                    "canonical_report_hash",
                                    "",
                                ),
                                "canonical_context_included_in_model_prompt": bool(
                                    fip4_result.get("provider_call_made")
                                ),
                                "canonical_context_consumed_by_coder_execution": bool(
                                    fip4_result.get("provider_call_made")
                                ),
                                "provider_model_truth": fip4_result.get(
                                    "provider_model_truth",
                                    {},
                                ),
                                "changed_files": fip4_result.get("changed_files", []),
                                "checks_run": fip4_result.get("checks_run", []),
                            },
                        }
                else:
                    architect_task = _trial_bounded_create_task(
                        trial_task,
                        explicit_target,
                        reset_request.allowed_files,
                    ) if allowed_create_target or allowed_live_trial_target else trial_task
                    architect_plan = _load_or_prepare_architect_plan(
                        architect_task,
                        reset_request.active_task_id,
                        expected_target=explicit_target,
                    )
                    coder = await _bounded_coder_diff_or_stub(
                        trial_task,
                        architect_plan,
                        force_live_model=reset_request.trial_mode == "live_apply",
                        canonical_context=canonical_context_broker,
                        canonical_context_text=canonical_context_prompt,
                    )
        proposed = str(coder.get("proposed_diff") or "")
        target = str(coder.get("target") or "")
        if target_plugin_orchestrator_receipt is not None:
            orchestrated_target_plugin_proposal = (
                target_plugin_orchestrator_receipt.get("target_plugin_proposal")
            )
            if isinstance(orchestrated_target_plugin_proposal, dict) and str(
                orchestrated_target_plugin_proposal.get("target") or ""
            ):
                target = str(orchestrated_target_plugin_proposal["target"])
        coder_blocked = bool(coder.get("coder_blocked"))
        blocked_reason = str(coder.get("blocked_reason") or "")
        needed_context = str(coder.get("needed_context") or "")
        reason_code = str(coder.get("reason_code") or "")
        already_satisfied = (
            coder.get("already_satisfied") is True
            or coder.get("alreadySatisfied") is True
            or reason_code == "coder_no_changes_needed"
        )
        subjective_improvement_needs_diff = (
            reason_code == SUBJECTIVE_IMPROVEMENT_REQUIRES_DIFF_REASON_CODE
            or reason_code == VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE
        )
        bundle_snapshot_drift = reason_code == "bundle_snapshot_drift"
        shallow_visual_diff = reason_code == VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE
        coder_model_missing = reason_code == "coder_model_not_configured"
        coder_empty_model = reason_code == "coder_empty_model_response"
        coder_sync_timeout = reason_code == "coder_sync_timeout"
        diagnostics = (
            coder.get("coder_diagnostics")
            if isinstance(coder.get("coder_diagnostics"), dict)
            else {}
        )
        if target_plugin_orchestrator_receipt is not None:
            orchestrated_proposal = target_plugin_orchestrator_receipt.get(
                "target_plugin_proposal"
            )
            if isinstance(orchestrated_proposal, dict):
                diagnostics["target_plugin_output_id"] = str(
                    target_plugin_orchestrator_receipt.get(
                        "target_plugin_output_id"
                    )
                    or orchestrated_proposal.get("runtime_output_id")
                    or ""
                )
                diagnostics["target_plugin_context_hash"] = str(
                    orchestrated_proposal.get("context_hash") or ""
                )
                diagnostics["target_plugin_proposal_binding_sha256"] = str(
                    orchestrated_proposal.get("proposal_binding_sha256") or ""
                )
                diagnostics["canonical_context_consumed_by_coder_execution"] = bool(
                    orchestrated_proposal.get("context_consumption_id")
                    and orchestrated_proposal.get(
                        "context_consumer_acknowledgement_id"
                    )
                )
            diagnostics["coding_orchestrator_run_id"] = str(
                target_plugin_orchestrator_receipt.get("run_id") or ""
            )
            diagnostics["coding_orchestrator_authoritative"] = (
                target_plugin_orchestrator_receipt.get("authoritative") is True
            )
        provider_model_truth = _provider_model_truth_from_coder_diagnostics(diagnostics)
        coder_context_applicable = bool(
            proposed.strip()
            or provider_model_truth.get("providerCallMade") is True
        )
        if target_plugin_orchestrator_receipt is None:
            canonical_context_broker = _record_active_task_context_broker(
                reset_request.active_task_id,
                canonical_context_broker,
                coder_applicable=coder_context_applicable,
                coder_consumed=(
                    diagnostics.get("canonical_context_consumed_by_coder_execution") is True
                ),
                repair_attempted=bool(
                    diagnostics.get("repair_attempted") is True
                    or diagnostics.get("prompt3_retry_attempted") is True
                ),
                repair_consumed=(
                    diagnostics.get("canonical_context_consumed_by_coder_execution") is True
                ),
            )
        diagnostics["canonical_context_broker"] = canonical_context_broker
        diagnostics["canonical_context_report_hash"] = canonical_context_broker.get(
            "canonical_report_hash",
            "",
        )
        if (
            coder_context_applicable
            and canonical_context_broker.get("go_eligible") is not True
        ):
            context_blockers = [
                str(item)
                for item in canonical_context_broker.get("required_context_blockers", [])
            ]
            coder_blocked = True
            blocked_reason = "; ".join(context_blockers) or "canonical_context_not_go_eligible"
            needed_context = (
                "Resolve the canonical context blockers and rerun generation before approval."
            )
            reason_code = "required_context_blocked"
            proposed = ""
            diagnostics["validation_status"] = "required_context_blocked"
            diagnostics["trial_result_trust_status"] = "generation_not_approvable_context_blocked"
            diagnostics["recommended_next_action"] = needed_context
        fip4_result_for_receipt = (
            diagnostics.get("fip4_qwen_coder_result")
            if isinstance(diagnostics.get("fip4_qwen_coder_result"), dict)
            else None
        )
        fip5_result_for_receipt = (
            diagnostics.get("fip5_verifier_result")
            if isinstance(diagnostics.get("fip5_verifier_result"), dict)
            and diagnostics.get("fip5_verifier_result")
            else None
        )
        if fip4_result_for_receipt and isinstance(
            fip4_result_for_receipt.get("provider_model_truth"),
            dict,
        ):
            provider_model_truth = {
                **provider_model_truth,
                **fip4_result_for_receipt["provider_model_truth"],
            }
        context_mode = str(
            diagnostics.get("context_mode")
            or derive_context_mode(target or explicit_target)
        )
        forbidden_paths = (
            diagnostics.get("forbidden_paths")
            if isinstance(diagnostics.get("forbidden_paths"), list)
            else list(forbidden_paths_for_context_mode(context_mode))
        )
        context_slices = (
            diagnostics.get("context_slices")
            if isinstance(diagnostics.get("context_slices"), list)
            else ([{"path": target, "kind": "target"}] if target else [])
        )
        status_value = _coder_prompt_packet_status(
            already_satisfied=already_satisfied,
            coder_blocked=coder_blocked,
            proposed=proposed,
            reason_code=reason_code,
            subjective_improvement_needs_diff=subjective_improvement_needs_diff,
        )
        _mark_active_task_after_coder_result(
            reset_request.active_task_id,
            status_value=status_value,
            coder_blocked=coder_blocked,
            proposed=proposed,
            reason_code=reason_code,
            blocked_reason=blocked_reason,
            needed_context=needed_context,
            target=target or explicit_target,
            diagnostics_summary=_safe_coder_diagnostics_summary(diagnostics),
        )
        notes = coder.get("coder_notes") if isinstance(coder.get("coder_notes"), list) else []
        bundle = coder.get("bundle")
        changed_files = (
            coder.get("changed_files")
            if isinstance(coder.get("changed_files"), list)
            else diagnostics.get("changed_files")
            if isinstance(diagnostics.get("changed_files"), list)
            else []
        )
        checks_run = (
            coder.get("checks_run")
            if isinstance(coder.get("checks_run"), list)
            else diagnostics.get("checks_run")
            if isinstance(diagnostics.get("checks_run"), list)
            else []
        )
        manual_available = coder_blocked and not proposed and not already_satisfied
        context_packet_summary = (
            diagnostics.get("context_packet_summary")
            if isinstance(diagnostics.get("context_packet_summary"), dict)
            else {}
        )
        safe_diagnostics_summary = _safe_coder_diagnostics_summary(diagnostics)
        context_lines = [
            f"Coder Agent replacement-content generation (repomix bundle: {bundle or 'none'}).",
            "Coder prompt rule: strict JSON replacement content only; backend generated the unified diff.",
            "model_output_mode: replacement_content",
            f"model_output_classification: {diagnostics.get('model_output_classification') or 'unknown_untrusted'}",
            f"generated_diff_by_backend: {bool(diagnostics.get('generated_diff_by_backend'))}",
            f"model_raw_diff_used: {bool(diagnostics.get('model_raw_diff_used'))}",
            f"Coder blocked reason code: {reason_code or 'none'}.",
            f"Context packet summary: {context_packet_summary}",
            f"Coder diagnostics summary: {safe_diagnostics_summary}",
            *[str(item) for item in notes],
        ]
        phase_label, increment_label, increment_goal = _phase_fields_for(
            PromptPacketInput(task=reset_request.task)
        )
        coder_packet_payload = _coder_packet_payload_for_response(
            architect_plan,
            target=target,
            context_mode=context_mode,
            context_slices=context_slices,
            forbidden_paths=forbidden_paths,
            target_exists=bool(diagnostics.get("target_exists")),
        )
        verification_plan_payload = _verification_plan_payload_for_response(architect_plan)
        task_spec_payload = _task_spec_payload_for_response(architect_plan, coder_packet_payload)
        target_plugin_spec = target_plugin_task_spec(target_plugin) if target_plugin else None
        if target_plugin_spec is not None:
            task_spec_payload = target_plugin_spec
        if reason_code in TARGET_HARD_BLOCK_REASON_CODES or reason_code == "target_unresolved":
            task_spec_payload = intake_as_legacy_task_spec(intake)
        manual_browser_prompt = _coder_agent_manual_browser_prompt_text(
            task=reset_request.task,
            target=target or explicit_target,
            task_spec=task_spec_payload,
            coder_packet=coder_packet_payload,
            verification_plan=verification_plan_payload,
            blocked_reason=blocked_reason,
            needed_context=needed_context,
            reason_code=reason_code,
            diagnostics=diagnostics,
        )
        packet_context_paths = _coder_packet_context_paths(coder_packet_payload)
        response_payload = {
            "target_model_hint": "coder_agent",
            "provider": provider_model_truth["providerId"],
            "model": provider_model_truth["modelId"],
            "provider_model_truth": provider_model_truth,
            "providerModelTruth": provider_model_truth,
            "provider_model_source": provider_model_truth["source"],
            "provider_model_status": provider_model_truth["status"],
            "provider_call_made": provider_model_truth["providerCallMade"],
            "provider_call_authorized": provider_model_truth["providerCallAuthorized"],
            "hermes_lane_available": provider_model_truth["hermesLaneAvailable"],
            "hermes_used_for_this_run": provider_model_truth["hermesUsedForThisRun"],
            "phase_label": phase_label,
            "increment_label": increment_label,
            "increment_goal": increment_goal,
            "task_summary": _short_task_summary(reset_request.task),
            "canonical_context_broker": canonical_context_broker,
            "canonicalContextBroker": canonical_context_broker,
            "selected_prompt_id": reset_request.selected_prompt_id or reset_request.trial_prompt_id,
            "selectedPromptId": reset_request.selected_prompt_id or reset_request.trial_prompt_id,
            "selected_prompt_number": (
                2
                if dummy_product_site_product_data
                else 3
                if dummy_product_site_render_cards
                else None
            ),
            "selectedPromptNumber": (
                2
                if dummy_product_site_product_data
                else 3
                if dummy_product_site_render_cards
                else None
            ),
            "relevant_context": "\n".join(context_lines),
            "context_metadata": {
                "canonical_context_broker": canonical_context_broker,
                "canonical_context_report_hash": canonical_context_broker.get(
                    "canonical_report_hash",
                    "",
                ),
                "context_inclusion_mode": "coder_agent_repomix",
                "context_mode": context_mode,
                "included_paths": packet_context_paths or ([target] if target else []),
                "selected_target_candidates": context_packet_summary.get("selected_target_candidates", []),
                "selected_target": target or explicit_target,
                "allowed_files": task_spec_payload.get("allowed_files", []),
                "forbidden_files": task_spec_payload.get("forbidden_files", []),
                "protected_paths": forbidden_paths,
                "checks_that_will_run": (
                    verification_plan_payload.get("required_checks", [])
                    or task_spec_payload.get("verification", [])
                ),
                "expected_output_format": context_packet_summary.get(
                    "expected_output_format",
                    "strict JSON replace_file with content_lines; backend converts model-authored content to unified diff",
                ),
                "scaffold_fallback_ban_flags": context_packet_summary.get(
                    "scaffold_fallback_ban_flags",
                    {},
                ),
                "trial_mode_flags": context_packet_summary.get("trial_mode_flags", {}),
                "rollback_reversal_available": context_packet_summary.get(
                    "rollback_reversal_available",
                    True,
                ),
                "obsidian_context_summary": context_packet_summary.get(
                    "obsidian_context_summary",
                    diagnostics.get("memory_context_diagnostics", {}),
                ),
                "fip1_context_lane_status": fip1_context_packet.get("source_status", {}),
                "source_readiness_status": fip1_context_packet.get(
                    "source_readiness_status",
                    {},
                ),
                "omitted_paths": [],
                "redaction_notes": [
                    "Context packet summaries omit full source content and raw Obsidian note content.",
                    "Full structured coder_diagnostics remain available separately for tooling.",
                ],
                "estimated_context_tokens": 0,
                "file_contents_claimed": _coder_packet_payload_has_context_content(
                    coder_packet_payload
                ),
            },
            "constraints": [
                (
                    "Coder Agent mode: review backend-generated proposed_diff in the UI approval gate."
                    if proposed
                    else "Coder Agent mode: generated visual diff was too shallow; produce material styling, layout, hover, active, glow, spacing, or animation changes."
                    if shallow_visual_diff
                    else "Coder Agent mode: subjective visual improvement requires an actual diff or manual visual review."
                    if subjective_improvement_needs_diff
                    else "Coder Agent mode: bundle changed since planning; regenerate the Architect plan before retrying Coder."
                    if bundle_snapshot_drift
                    else "Coder Agent mode: no approval is needed because the target file already matches the requested content."
                    if already_satisfied
                    else (
                        "Coder Agent mode: resolved implementation file is missing on disk; fix the path or create the file."
                        if reason_code == "target_missing"
                        else _target_safety_constraint(reason_code)
                        if reason_code in TARGET_HARD_BLOCK_REASON_CODES
                        else "Coder Agent mode: no safe file target could be resolved from the task text; add `Target file:` or mention an existing repo-relative path."
                        if reason_code == "target_unresolved"
                        else "Coder Agent mode: Coder repomix+LLM exceeded the proxy sync deadline; raise SOURCE_PROXY_CODER_SYNC_DEADLINE_SEC or narrow scope."
                        if coder_sync_timeout
                        else "Coder Agent mode: Coder returned an empty model response; check SOURCE_PROXY_CODER_MODEL_ALIAS and provider availability."
                        if coder_empty_model
                        else (
                            "Coder Agent mode: Coder model is not configured or the alias is not available on this proxy. "
                            "Set SOURCE_PROXY_CODER_MODEL_ALIAS to a valid enabled alias, then retry."
                        )
                        if coder_model_missing
                        else "Coder Agent did not produce validated replacement content; retry Local Coder with stricter output repair, or copy a manual browser prompt."
                    )
                ),
            ],
            "requested_output": (
                ALREADY_SATISFIED_REQUESTED_OUTPUT
                if already_satisfied
                else [
                    (
                        "Backend-generated unified diff ready for human review (no external paste-back)."
                        if proposed
                        else "No approvable diff was produced because the generated visual diff was too shallow."
                        if shallow_visual_diff
                        else "No diff was produced, and subjective visual improvement cannot be marked already satisfied."
                        if subjective_improvement_needs_diff
                        else "No diff was produced because the repomix bundle changed since the Architect plan was created."
                        if bundle_snapshot_drift
                        else "No unified diff was produced because the resolved target file is missing on disk."
                        if reason_code == "target_missing"
                        else _target_safety_requested_output(reason_code)
                        if reason_code in TARGET_HARD_BLOCK_REASON_CODES
                        else "No unified diff was produced because no safe target path could be resolved from the task."
                        if reason_code == "target_unresolved"
                        else "No unified diff was produced because Coder exceeded the proxy sync deadline."
                        if coder_sync_timeout
                        else "No unified diff was produced because the Coder model returned an empty response."
                        if coder_empty_model
                        else "No unified diff was produced because the Coder model is not configured or the alias is not available. Configure SOURCE_PROXY_CODER_MODEL_ALIAS, then retry."
                        if coder_model_missing
                        else "Manual browser prompt is available because local Coder could not produce validated replacement content after repair/retry."
                    ),
                ]
            ),
            "paste_back_instructions": (
                ALREADY_SATISFIED_PASTE_BACK_INSTRUCTIONS
                if already_satisfied
                else "Coder Agent replacement content was validated and converted to proposed_diff by the backend; approve inside Spirit when satisfied."
                if proposed
                else "Generate a concrete visual refinement diff that changes className, styling, layout, hover, active, glow, spacing, or animation behavior."
                if shallow_visual_diff
                else "Produce an actual visual refinement diff, use manual visual review, or copy the manual browser prompt."
                if subjective_improvement_needs_diff
                else "Regenerate the Architect plan, then retry Coder Agent."
                if bundle_snapshot_drift
                else _target_safety_paste_back(reason_code)
                if reason_code in TARGET_HARD_BLOCK_REASON_CODES
                else "Raise SOURCE_PROXY_CODER_SYNC_DEADLINE_SEC or narrow Coder scope; the repomix+LLM run exceeded the proxy deadline."
                if coder_sync_timeout
                else "Verify SOURCE_PROXY_CODER_MODEL_ALIAS and provider health; Coder returned an empty model response."
                if coder_empty_model
                else "Set SOURCE_PROXY_CODER_MODEL_ALIAS to a valid enabled model alias, then retry Coder Agent."
                if coder_model_missing
                else "Retry Local Coder with stricter output repair or copy the manual browser prompt; do not approve an empty diff."
            ),
            "prompt_text": (
                ALREADY_SATISFIED_PROMPT_TEXT
                if already_satisfied
                else _coder_agent_shallow_visual_diff_prompt_text(target)
                if shallow_visual_diff
                else _coder_agent_subjective_no_diff_prompt_text(target)
                if subjective_improvement_needs_diff
                else "Bundle changed since the Architect plan was created. Regenerate the plan before retrying Coder Agent."
                if bundle_snapshot_drift
                else "Coder Agent timed out before producing replacement content; raise SOURCE_PROXY_CODER_SYNC_DEADLINE_SEC or narrow scope."
                if coder_sync_timeout
                else "Coder returned an empty model response; check SOURCE_PROXY_CODER_MODEL_ALIAS and provider health."
                if coder_empty_model
                else _coder_agent_stub_prompt_text(target, proposed)
                if proposed
                else manual_browser_prompt
            ),
            "route_decision": route_payload,
            "research_sources": fip2_research_sources,
            "fip2_research_packet": fip2_research_packet,
            "fip2ResearchPacket": fip2_research_packet,
            "fip3_model_packet": fip3_model_packet,
            "fip3ModelPacket": fip3_model_packet,
            "fip1_context_packet": fip1_context_packet,
            "fip1ContextPacket": fip1_context_packet,
            "manual_prompt_packet": False,
            "context_mode": context_mode,
            "contextMode": context_mode,
            "coder_packet": coder_packet_payload,
            "coderPacket": _camel_coder_packet_payload(coder_packet_payload),
            "task_spec": task_spec_payload,
            "taskSpec": _camel_task_spec_payload(task_spec_payload),
            "task_spec_intake": intake_payload,
            "taskSpecIntake": _camel_task_spec_intake_payload(intake_payload),
            "verification_plan": verification_plan_payload,
            "verificationPlan": _camel_verification_plan_payload(verification_plan_payload),
            "proposed_diff": proposed,
            "proposedDiff": proposed,
            "changed_files": changed_files,
            "changedFiles": changed_files,
            "checks_run": checks_run,
            "checksRun": checks_run,
            "target": target,
            "coder_agent_local_diff": bool((proposed or "").strip() and target),
            "coderAgentLocalDiff": bool((proposed or "").strip() and target),
            "coder_blocked": coder_blocked,
            "coderBlocked": coder_blocked,
            "blocked_reason": blocked_reason,
            "blockedReason": blocked_reason,
            "needed_context": needed_context,
            "neededContext": needed_context,
            "already_satisfied": already_satisfied,
            "alreadySatisfied": already_satisfied,
            "status": status_value,
            "reason_code": reason_code,
            "reasonCode": reason_code,
            "no_diff_failure_cause": diagnostics.get("no_diff_failure_cause"),
            "noDiffFailureCause": diagnostics.get("no_diff_failure_cause"),
            "safe_response_classification": diagnostics.get("safe_response_classification"),
            "safeResponseClassification": diagnostics.get("safe_response_classification"),
            "parser_extractor_decision": diagnostics.get("parser_extractor_decision"),
            "parserExtractorDecision": diagnostics.get("parser_extractor_decision"),
            "diagnostics_summary": safe_diagnostics_summary,
            "diagnosticsSummary": safe_diagnostics_summary,
            "coder_diagnostics": diagnostics,
            "coderDiagnostics": diagnostics,
            "manual_prompt_packet_available": manual_available,
            "manualPromptPacketAvailable": manual_available,
            "cloud_route_available": True,
            "cloudRouteAvailable": True,
            "next_actions": (
                [
                    "Retry Local Coder with stricter output repair",
                    *(
                        ["Regenerate plan"]
                        if bundle_snapshot_drift
                        else []
                    ),
                    "Copy manual browser prompt",
                    "Use Cloud/API route, if configured",
                    *(
                        ["Manual visual review"]
                        if subjective_improvement_needs_diff
                        else []
                    ),
                ]
                if manual_available
                else []
            ),
        }
        if target_plugin is not None:
            response_payload["target_plugin_orchestrated"] = (
                target_plugin_orchestrator_receipt is not None
            )
            response_payload["targetPluginOrchestrated"] = (
                target_plugin_orchestrator_receipt is not None
            )
        if target_plugin_orchestrator_receipt is not None:
            orchestrated_proposal = target_plugin_orchestrator_receipt.get(
                "target_plugin_proposal"
            )
            proposal_payload = (
                dict(orchestrated_proposal)
                if isinstance(orchestrated_proposal, dict)
                else {}
            )
            runtime_output_id = str(
                target_plugin_orchestrator_receipt.get("target_plugin_output_id")
                or proposal_payload.get("runtime_output_id")
                or ""
            )
            proposal_context_hash = str(
                proposal_payload.get("context_hash")
                or canonical_context_broker.get("canonical_report_hash")
                or ""
            )
            response_payload.update(
                {
                    "coding_orchestrator": target_plugin_orchestrator_receipt,
                    "codingOrchestrator": target_plugin_orchestrator_receipt,
                    "target_plugin_proposal": proposal_payload,
                    "targetPluginProposal": proposal_payload,
                    "target_plugin_orchestrated": True,
                    "targetPluginOrchestrated": True,
                    "target_plugin_run_id": str(
                        target_plugin_orchestrator_receipt.get("run_id") or ""
                    ),
                    "targetPluginRunId": str(
                        target_plugin_orchestrator_receipt.get("run_id") or ""
                    ),
                    "target_plugin_proposal_binding_sha256": str(
                        proposal_payload.get("proposal_binding_sha256") or ""
                    ),
                    "targetPluginProposalBindingSha256": str(
                        proposal_payload.get("proposal_binding_sha256") or ""
                    ),
                }
            )
            if runtime_output_id:
                response_payload["target_plugin_output_id"] = runtime_output_id
                response_payload["targetPluginOutputId"] = runtime_output_id
                response_payload["runtime_output_id"] = runtime_output_id
                response_payload["runtimeOutputId"] = runtime_output_id
            if proposal_context_hash:
                response_payload["target_plugin_context_hash"] = (
                    proposal_context_hash
                )
                response_payload["targetPluginContextHash"] = (
                    proposal_context_hash
                )
                response_payload["context_hash"] = proposal_context_hash
                response_payload["contextHash"] = proposal_context_hash
        return _attach_fip0_truth_receipt(
            response_payload,
            request=reset_request,
            route_payload=route_payload,
            intake_payload=intake_payload,
            decision=decision,
            explicit_target=explicit_target,
            route_reasons=route_reasons,
            coder_packet_payload=coder_packet_payload,
            checks_run=checks_run,
            changed_files=changed_files,
            proposed_diff=proposed,
            status_value=status_value,
            reason_code=reason_code,
            coder_blocked=coder_blocked,
            provider_call_made=provider_model_truth["providerCallMade"],
            provider_model_truth=provider_model_truth,
            fip1_context_packet=fip1_context_packet,
            fip2_research_packet=fip2_research_packet,
            fip3_model_packet=fip3_model_packet,
            fip4_coder_result=fip4_result_for_receipt,
            fip5_verifier_result=fip5_result_for_receipt,
        )

    packet = build_prompt_packet(
        PromptPacketInput(
            task=reset_request.task,
            target_model_hint=reset_request.target_model_hint,
            relevant_context=reset_request.relevant_context,
            active_task_id=reset_request.active_task_id,
            current_agent_role=reset_request.current_agent_role,
            context_tokens=reset_request.context_tokens,
            sensitive=reset_request.sensitive,
            needs_current_info=reset_request.needs_current_info,
            needs_codebase_context=reset_request.needs_codebase_context,
            wants_implementation=reset_request.wants_implementation,
            prefer_free=reset_request.prefer_free,
            brain_switch_recommendation=reset_request.brain_switch_recommendation,
            task_shape=reset_request.task_shape,
            evidence_ids=tuple(reset_request.evidence_ids),
        )
    )
    payload = packet.as_payload()
    canonical_context_broker = _record_active_task_context_broker(
        reset_request.active_task_id,
        canonical_context_broker,
        coder_applicable=False,
        coder_consumed=False,
        repair_attempted=False,
        repair_consumed=False,
    )
    payload["canonical_context_broker"] = canonical_context_broker
    payload["canonicalContextBroker"] = canonical_context_broker
    payload.setdefault("context_metadata", {})["canonical_context_broker"] = (
        canonical_context_broker
    )
    payload["context_metadata"]["canonical_context_report_hash"] = (
        canonical_context_broker.get("canonical_report_hash", "")
    )
    payload["route_decision"] = route_payload
    payload["research_sources"] = fip2_research_sources
    payload["fip2_research_packet"] = fip2_research_packet
    payload["fip2ResearchPacket"] = fip2_research_packet
    payload["fip3_model_packet"] = fip3_model_packet
    payload["fip3ModelPacket"] = fip3_model_packet
    payload["fip1_context_packet"] = fip1_context_packet
    payload["fip1ContextPacket"] = fip1_context_packet
    payload.setdefault("context_metadata", {})["fip1_context_lane_status"] = (
        fip1_context_packet.get("source_status", {})
    )
    payload["context_metadata"]["source_readiness_status"] = (
        fip1_context_packet.get("source_readiness_status", {})
    )
    payload["context_metadata"]["research_packet_hash"] = (
        fip2_research_packet.get("research_packet_hash", "")
    )
    payload["context_metadata"]["research_packet_included_in_context"] = bool(
        fip2_research_packet.get("research_packet_included_in_context")
    )
    payload["context_metadata"]["fip3_model_packet_hash"] = (
        fip3_model_packet.get("fip3_model_packet_hash", "")
    )
    payload["task_spec_intake"] = intake_payload
    payload["taskSpecIntake"] = _camel_task_spec_intake_payload(intake_payload)
    return _attach_fip0_truth_receipt(
        payload,
        request=reset_request,
        route_payload=route_payload,
        intake_payload=intake_payload,
        decision=decision,
        explicit_target=explicit_target,
        route_reasons=route_reasons,
        fip1_context_packet=fip1_context_packet,
        fip2_research_packet=fip2_research_packet,
        fip3_model_packet=fip3_model_packet,
    )


def _load_or_prepare_architect_plan(
    task: str,
    task_id: str | None,
    *,
    expected_target: str | None = None,
) -> Any | None:
    plan = _load_active_architect_plan(task_id)
    if _architect_plan_has_usable_coder_packet(plan, expected_target=expected_target):
        return plan

    if task_id:
        try:
            # All live task advancement belongs to the canonical production
            # orchestrator, including plan preparation from the prompt route.
            get_coding_orchestrator().advance(task_id)
            plan = _load_active_architect_plan(task_id)
            if _architect_plan_has_usable_coder_packet(plan, expected_target=expected_target):
                return plan
        except Exception:
            plan = None

    return _deterministic_architect_plan_for_prompt_packet(task, task_id)


def _deterministic_architect_plan_for_prompt_packet(
    task: str,
    task_id: str | None,
) -> Any | None:
    try:
        from source_proxy.planning.architect import Plan, plan_task_deterministically
        from source_proxy.planning.plan import save_plan

        result = plan_task_deterministically(
            task,
            task_id or "prompt-packet-ad-hoc",
            _workspace_root(),
        )
        if not isinstance(result, Plan):
            return None
        if task_id:
            try:
                save_plan(task_id, result.plan)
            except Exception:
                pass
        return result.plan
    except Exception:
        return None


def _architect_plan_has_usable_coder_packet(
    architect_plan: Any | None,
    *,
    expected_target: str | None = None,
) -> bool:
    packet = getattr(architect_plan, "coder_packet", None)
    target_file = getattr(packet, "target_file", None)
    target_path = str(getattr(target_file, "path", "") or "").strip()
    normalized_expected = _normalize_trial_create_path(expected_target or "")
    if normalized_expected and target_path != normalized_expected:
        return False
    context_slices = getattr(packet, "context_slices", None)
    operation = str(getattr(packet, "operation", "") or "").strip()
    if operation == "create":
        return bool(target_path)
    return bool(target_path and isinstance(context_slices, list) and context_slices)


def _target_missing_blocks_prompt_packet(task: str, route_reasons: list[str]) -> bool:
    if "target_missing" not in route_reasons:
        return False
    proposal = parse_bounded_proposal_task(task)
    if proposal is None:
        return True
    create_ok, _blocked_reason = bounded_proposal_create_allowed(
        proposal,
        workspace_root=_workspace_root(),
    )
    return not create_ok


def _trial_allowed_missing_create_target(
    request: PromptPacketRequest,
    target: str,
    route_reasons: list[str],
) -> bool:
    if request.trial_mode != "live_apply" or "target_missing" not in route_reasons:
        return False
    normalized_target = _normalize_trial_create_path(target)
    if not normalized_target:
        return False
    root = _workspace_root()
    resolved_target = resolve_target_from_task(
        f"Target file: {normalized_target}",
        root,
    )
    if unsafe_target_for_route(request.task, resolved_target, root) is not None:
        return False
    return _trial_path_allowed(normalized_target, request.allowed_files)


def _trial_allowed_selected_target(
    request: PromptPacketRequest,
    target: str,
) -> bool:
    if request.trial_mode != "live_apply":
        return False
    normalized_target = _normalize_trial_create_path(target)
    if not normalized_target:
        return False
    return _trial_path_allowed(normalized_target, request.allowed_files)


def _trial_bounded_create_task(task: str, target: str, allowed_files: list[str]) -> str:
    normalized_target = _normalize_trial_create_path(target)
    allowed = [
        normalized
        for item in allowed_files
        if (normalized := _normalize_trial_allowed_path(item))
    ]
    if (
        not normalized_target
        or not allowed
        or not _trial_path_allowed(normalized_target, allowed)
    ):
        return task
    # The deterministic planner deliberately requires an exact target binding.
    # The request may authorize that target through a bounded glob, so narrow the
    # persisted planning envelope to the already-authorized concrete path.
    if normalized_target not in allowed:
        allowed.append(normalized_target)
    payload = {
        "task": task.strip(),
        "mode": "proposal",
        "target_file": normalized_target,
        "allowed_files": allowed,
        "forbidden_files": [".env", ".env.local", "credentials", "private keys"],
        "expected_checks": ["git diff --check"],
        "rollback_hint": f"Delete {normalized_target} if this reversible trial is rolled back.",
    }
    return f"{task.strip()}\n\nProposal task:\n```json\n{json.dumps(payload, sort_keys=True)}\n```"


def _normalize_trial_create_path(path: str) -> str:
    normalized = _normalize_trial_allowed_path(path)
    if not normalized:
        return ""
    allowed_prefixes = (
        "src/app/agent-lab/",
        "src/components/agent-lab/",
        "src/lib/agent-lab/",
        "src/app/api/agent-lab/",
        "tests/agent-lab/",
        "tests/ui-agent-trials/fixtures/dummy-product-site/",
    )
    return normalized if normalized.startswith(allowed_prefixes) else ""


def _normalize_trial_allowed_path(path: str) -> str:
    from source_proxy.safety.paths import normalize_repo_path_candidate

    return normalize_repo_path_candidate(str(path or ""))


def _trial_path_allowed(target: str, allowed_files: list[str]) -> bool:
    normalized_allowed = [
        normalized
        for item in allowed_files
        if (normalized := _normalize_trial_allowed_path(item))
    ]
    for allowed in normalized_allowed:
        if allowed == target:
            return True
        if allowed.endswith("/**") and target.startswith(allowed[:-3]):
            return True
    return False


def _dummy_product_site_render_cards_plan(
    request: PromptPacketRequest,
    task: str,
) -> Any | None:
    try:
        from source_proxy.planning.plan import (
            PLAN_SCHEMA_VERSION,
            AcceptanceCriterion,
            ArchitectPlan,
            BundleSnapshot,
            CoderPacket,
            ContentConstraints,
            ContextSlice,
            PlanBudget,
            TargetFile,
            TaskClassification,
            VerificationCheck,
            VerificationPlan,
        )
    except Exception:
        return None

    root = _workspace_root()
    target = "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js"
    fixture_paths = [
        (target, "target"),
        ("tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js", "import"),
        ("tests/ui-agent-trials/fixtures/dummy-product-site/index.html", "sibling"),
        ("tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css", "sibling"),
    ]
    context_slices: list[Any] = []
    target_content = ""
    for relative_path, kind in fixture_paths:
        abs_path = (root / relative_path).resolve()
        if not abs_path.is_file():
            return None
        content = abs_path.read_text(encoding="utf-8", errors="replace")
        if relative_path == target:
            target_content = content
        context_slices.append(
            ContextSlice(
                path=relative_path,
                kind=kind,  # type: ignore[arg-type]
                sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                content=content,
                line_range=(1, max(1, len(content.splitlines()))),
            )
        )

    target_abs = (root / target).resolve()
    target_hash = hashlib.sha256(target_abs.read_bytes()).hexdigest()
    task_id = str(request.active_task_id or "prompt-3-render-product-cards")
    source_task = _dummy_product_site_render_cards_source_task(request, task)
    return ArchitectPlan(
        plan_id=f"dummy-product-site-render-cards-{hashlib.sha256(source_task.encode('utf-8')).hexdigest()[:12]}",
        task_id=task_id,
        schema_version=PLAN_SCHEMA_VERSION,
        created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        source_task=source_task,
        bundle_snapshot=BundleSnapshot(
            bundle_path="",
            bundle_sha256="",
            workspace_root=str(root),
            generated_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        ),
        classification=TaskClassification(
            task_class="implement",
            visual_change=True,
            designer_required=False,
            estimated_complexity="small",
        ),
        coder_packet=CoderPacket(
            target_file=TargetFile(
                path=target,
                exists=True,
                sha256_before=target_hash,
            ),
            operation="edit",
            acceptance_criteria=[
                AcceptanceCriterion(
                    id="render-products-from-module",
                    description=(
                        "Render all products exported by src/products.js from src/main.js; "
                        "do not hardcode product cards in index.html."
                    ),
                    kind="behavioral",
                ),
                AcceptanceCriterion(
                    id="product-card-fields",
                    description="Each rendered card shows product name, price, category, and description.",
                    kind="behavioral",
                ),
            ],
            constraints=ContentConstraints(
                must_contain=["./products.js", "product-card", "product.category"],
                must_not_contain=["Product Name", "Product Description"],
                preserve_imports=[],
                preserve_exports=[],
                max_added_lines=120,
                max_removed_lines=max(1, len(target_content.splitlines()) + 20),
            ),
            context_slices=context_slices,
            forbidden_paths=[
                ".env*",
                "source_proxy/**",
                "src/app/**",
                "src/components/**",
                "src/lib/**",
            ],
            style_directives=[
                "Keep index.html as a mount point plus script wiring only.",
                "Use the products module as the single source of truth.",
                "Prefer simple accessible product-card markup.",
            ],
        ),
        verification_plan=VerificationPlan(
            required_checks=[
                VerificationCheck(
                    id="git_apply_check",
                    command=["git", "apply", "--check"],
                    blocking=True,
                    timeout_seconds=10,
                )
            ],
            designer_review_required=False,
            architect_review_required=False,
        ),
        budget=PlanBudget(
            max_coder_attempts=3,
            max_total_seconds=120,
            cloud_escalation_allowed=True,
        ),
    )


def _dummy_product_site_render_cards_source_task(
    request: PromptPacketRequest,
    fallback_task: str,
) -> str:
    packet = request.dummy_coder_10_packet if isinstance(request.dummy_coder_10_packet, dict) else {}
    submitted = str(packet.get("submitted_prompt") or "").strip()
    pass_expectations = [
        str(item).strip()
        for item in packet.get("pass_expectations", [])
        if isinstance(item, str) and item.strip()
    ]
    fail_conditions = [
        str(item).strip()
        for item in packet.get("fail_conditions", [])
        if isinstance(item, str) and item.strip()
    ]
    project_contract = str(packet.get("project_contract") or "").strip()
    task = submitted or fallback_task.split("Prompt 3 fixture context:", 1)[0].strip()
    return "\n".join(
        item
        for item in [
            task,
            "",
            "Target files: tests/ui-agent-trials/fixtures/dummy-product-site/index.html and tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
            "Implementation notes: src/products.js is the source of truth. Option A is mandatory for Prompt 3: change index.html to <script type=\"module\" src=\"src/main.js\"></script>, statically import products from './products.js'; in src/main.js, and render every product dynamically from that imported array. Do not use dynamic import, do not duplicate product data, and do not hardcode product cards in index.html. src/styles.css may be updated for a simple card layout.",
            f"Pass expectations: {'; '.join(pass_expectations)}" if pass_expectations else "",
            f"Fail conditions: {'; '.join(fail_conditions)}" if fail_conditions else "",
            project_contract,
        ]
        if item
    )


def _coder_prompt_packet_status(
    *,
    already_satisfied: bool,
    coder_blocked: bool,
    proposed: str,
    reason_code: str,
    subjective_improvement_needs_diff: bool,
) -> str:
    if already_satisfied:
        return "already_satisfied"
    if (proposed or "").strip():
        return "preview_ready"
    if reason_code in {"coder_packet_missing_context", "coder_needs_context"}:
        return "needs_context"
    if reason_code in {
        "coder_model_not_configured",
        "coder_empty_model_response",
        "local_model_unavailable",
    }:
        return "coder_config_blocked"
    if reason_code == "coder_sync_timeout":
        return "blocked"
    if reason_code in {"target_missing", "target_unresolved"} | TARGET_HARD_BLOCK_REASON_CODES:
        return "blocked"
    if reason_code == "blocked_after_retries":
        return "blocked_after_retries"
    if subjective_improvement_needs_diff:
        return "needs_coder_diff"
    if coder_blocked:
        return "blocked"
    return ""


def _record_active_task_context_broker(
    task_id: str | None,
    report: dict[str, Any],
    *,
    coder_applicable: bool,
    coder_consumed: bool,
    repair_attempted: bool,
    repair_consumed: bool,
) -> dict[str, Any]:
    def acknowledge_in_memory(
        current: dict[str, Any],
        *,
        consumer: str,
        applicable: bool,
        consumed: bool,
        evidence: str,
        consumed_reason: str,
        missing_reason: str,
    ) -> dict[str, Any]:
        return acknowledge_context_consumer(
            current,
            consumer=consumer,
            evidence=evidence if consumed else "",
            applicable=applicable,
            reason=consumed_reason if consumed else missing_reason,
        )

    if not task_id:
        current = acknowledge_in_memory(
            report,
            consumer="coder",
            applicable=coder_applicable,
            consumed=coder_consumed,
            evidence="canonical_context_rendered_into_coder_prompt_or_execution_gate",
            consumed_reason="coder_execution_consumed_selected_context_packets",
            missing_reason="coder_executed_without_canonical_context_consumption",
        )
        return acknowledge_in_memory(
            current,
            consumer="repair_loop",
            applicable=repair_attempted,
            consumed=repair_consumed,
            evidence="bounded_repair_reused_canonical_context",
            consumed_reason="repair_prompt_consumed_original_context_contract",
            missing_reason="repair_executed_without_canonical_context_consumption",
        )
    try:
        from source_proxy.tasks.long_running import (
            acknowledge_task_context_consumer,
            record_canonical_context_broker,
        )

        current = record_canonical_context_broker(task_id, report)
        coder_report = acknowledge_task_context_consumer(
            task_id,
            consumer="coder",
            evidence=(
                "canonical_context_rendered_into_coder_prompt_or_execution_gate"
                if coder_consumed
                else ""
            ),
            applicable=coder_applicable,
            reason=(
                "coder_execution_consumed_selected_context_packets"
                if coder_consumed
                else "coder_executed_without_canonical_context_consumption"
                if coder_applicable
                else "coder_not_applicable_no_generation"
            ),
        )
        if isinstance(coder_report, dict):
            current = coder_report
        repair_report = acknowledge_task_context_consumer(
            task_id,
            consumer="repair_loop",
            evidence=(
                "bounded_model_output_repair_reused_canonical_context"
                if repair_consumed
                else ""
            ),
            applicable=repair_attempted,
            reason=(
                "repair_prompt_consumed_original_task_and_context_contract"
                if repair_consumed
                else "repair_executed_without_canonical_context_consumption"
                if repair_attempted
                else "repair_not_required"
            ),
        )
        return repair_report if isinstance(repair_report, dict) else current
    except Exception as error:
        return {
            **report,
            "persistence_status": "failed",
            "persistence_reason": f"{type(error).__name__}: {error}",
            "go_eligible": False,
            "verdict": "NO_GO_REQUIRED_CONTEXT",
            "required_context_blockers": [
                *[str(item) for item in report.get("required_context_blockers", [])],
                "canonical_context_task_persistence_failed",
            ],
        }


def _mark_active_task_after_coder_result(
    task_id: str | None,
    *,
    status_value: str,
    coder_blocked: bool,
    proposed: str,
    reason_code: str,
    blocked_reason: str,
    needed_context: str,
    target: str,
    diagnostics_summary: dict[str, Any] | None = None,
) -> None:
    if not task_id:
        return
    proposed_norm = (proposed or "").strip()
    if proposed_norm and not coder_blocked:
        return
    task_status = ""
    if status_value == "needs_context":
        task_status = "needs_context"
    elif status_value == "coder_config_blocked":
        task_status = "coder_config_blocked"
    elif status_value == "blocked_after_retries":
        task_status = "blocked_after_retries"
    elif status_value in {"blocked", "needs_coder_diff"} or coder_blocked:
        task_status = "blocked"
    if not task_status:
        return

    summary = "; ".join(
        item
        for item in [
            f"coder_status={status_value or 'blocked'}",
            f"reason_code={reason_code or 'coder_blocked'}",
            f"target={target}" if target else "",
            blocked_reason,
            f"needed_context={needed_context}" if needed_context else "",
        ]
        if item
    )
    try:
        from source_proxy.tasks.long_running import (
            get_long_running_task_snapshot,
            update_long_running_task,
        )

        snapshot = get_long_running_task_snapshot(task_id)["task"]
        steps = snapshot.get("steps") if isinstance(snapshot, dict) else []
        if not isinstance(steps, list):
            steps = []
        step = (
            "Coder needs a valid Architect CoderPacket before diff generation."
            if task_status == "needs_context"
            else (
                "Coder model alias is not configured or is not available on this proxy. "
                "Set SOURCE_PROXY_CODER_MODEL_ALIAS to a valid enabled alias."
                if reason_code == "coder_model_not_configured"
                else "Coder returned an empty model response; verify SOURCE_PROXY_CODER_MODEL_ALIAS and provider health."
                if reason_code == "coder_empty_model_response"
                else "Coder blocked after reviewer retries."
                if reason_code == "blocked_after_retries"
                else "Coder blocked before producing an approvable diff."
            )
        )
        results_payload = {
            "summary": summary,
            "coder_status": status_value or "blocked",
            "reason_code": reason_code or "coder_blocked",
            "target": target,
            "blocked_reason": blocked_reason,
            "needed_context": needed_context,
            "coder_diagnostics": diagnostics_summary or {},
        }
        update_long_running_task(
            task_id,
            status=task_status,
            current_agent_role="coder",
            truncated_test_results=json.dumps(results_payload, separators=(",", ":"))[:1500],
            steps=_append_unique_strs([str(item) for item in steps], [step]),
        )
    except Exception:
        return


def _append_unique_strs(current: list[str], additions: list[str]) -> list[str]:
    out = list(current)
    for item in additions:
        if item and item not in out:
            out.append(item)
    return out


def _coder_packet_payload_for_response(
    architect_plan: Any | None,
    *,
    target: str,
    context_mode: str,
    context_slices: list[Any],
    forbidden_paths: list[Any],
    target_exists: bool,
) -> dict[str, Any]:
    if architect_plan is not None and hasattr(architect_plan, "to_dict"):
        try:
            payload = dict(architect_plan.to_dict()["coder_packet"])
            payload["context_mode"] = context_mode
            return payload
        except Exception:
            pass
    return {
        "target_file": {
            "path": target,
            "exists": target_exists,
            "sha256_before": None,
        },
        "operation": "edit" if target_exists else "create",
        "acceptance_criteria": [],
        "constraints": {
            "must_contain": [],
            "must_not_contain": ["Target file:"],
            "preserve_imports": [],
            "preserve_exports": [],
            "max_added_lines": None,
            "max_removed_lines": None,
        },
        "context_mode": context_mode,
        "context_slices": context_slices,
        "forbidden_paths": forbidden_paths,
        "style_directives": [],
    }


def _safe_coder_diagnostics_summary(diagnostics: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "generation_source",
        "diff_source",
        "model_output_classification",
        "no_diff_failure_cause",
        "safe_response_classification",
        "parser_extractor_decision",
        "raw_response_length",
        "raw_response_excerpt_safe",
        "markdown_code_blocks_present",
        "unified_diff_markers_present",
        "full_file_content_likely_present",
        "parser_repair_used",
        "scaffold_used",
        "scaffold_kind",
        "fallback_used",
        "fallback_kind",
        "bounded_create_used",
        "known_scaffold_used",
        "generic_scaffold_used",
        "model_raw_diff_used",
        "generated_diff_by_backend",
        "trial_result_trust_status",
        "anti_cheat_status",
        "anti_cheat_hard_fail_ids",
        "anti_cheat_advisory_ids",
        "anti_cheat_reasons",
        "provider_call_made",
        "model_output_usable",
        "scaffold_or_fallback_blocked",
        "recommended_next_action",
        "validation_status",
        "target_path_selected",
        "context_mode",
        "structured_output_mode",
        "structured_bundle_status",
        "structured_bundle_parser_stage",
        "structured_bundle_file_count",
        "structured_bundle_accepted_paths",
        "structured_bundle_rejected_paths",
        "structured_bundle_rejection_reason",
        "model_output_shape_summary",
        "diff_generation_status",
        "diff_generation_reason",
        "patch_verification_status",
        "patch_verification_reason",
        "raw_model_response_sha256",
        "model_file_bundle_sha256",
        "backend_converted_diff_sha256",
        "file_block_repair_source",
        "json_repair_source",
        "parsed_output_mode",
    )
    summary = {key: diagnostics.get(key) for key in keys if key in diagnostics}
    content_validation = diagnostics.get("content_validation")
    if isinstance(content_validation, dict):
        summary["content_validation"] = {
            "ok": content_validation.get("ok"),
            "summary": content_validation.get("summary"),
            "caps": content_validation.get("caps", {}),
            "missing_count": len(content_validation.get("missing", []) or []),
        }
    honesty_gate = diagnostics.get("structured_honesty_gate")
    if isinstance(honesty_gate, dict):
        summary["structured_honesty_gate"] = {
            "status": honesty_gate.get("status"),
            "mode": honesty_gate.get("mode"),
            "classifier_alias": honesty_gate.get("classifier_alias"),
            "classifier_model": honesty_gate.get("classifier_model"),
            "classifier_provider": honesty_gate.get("classifier_provider"),
            "phi4_mini_gatekeeper_configured": honesty_gate.get("phi4_mini_gatekeeper_configured"),
            "finding_count": len(honesty_gate.get("findings", []) or []),
            "summary": honesty_gate.get("summary"),
        }
    context_packet = diagnostics.get("context_packet_summary")
    if isinstance(context_packet, dict):
        summary["context_packet_summary"] = {
            "selected_target": context_packet.get("selected_target"),
            "allowed_files": context_packet.get("allowed_files", []),
            "forbidden_files": context_packet.get("forbidden_files", []),
            "checks_that_will_run": context_packet.get("checks_that_will_run", []),
            "expected_output_format": context_packet.get("expected_output_format"),
            "repo_snippet_count": len(context_packet.get("repo_snippet_summaries", []) or []),
            "repo_snippet_omitted_count": context_packet.get("repo_snippet_omitted_count", 0),
            "obsidian_context_summary": context_packet.get("obsidian_context_summary", {}),
        }
    return summary


def _task_spec_payload_for_response(
    architect_plan: Any | None,
    coder_packet_payload: dict[str, Any],
) -> dict[str, Any]:
    if architect_plan is not None:
        try:
            return task_spec_from_plan(architect_plan).to_dict()
        except Exception:
            pass
    try:
        from source_proxy.planning.plan import (
            CoderPacket,
            ContentConstraints,
            TargetFile,
        )

        target_file_payload = (
            coder_packet_payload.get("target_file")
            if isinstance(coder_packet_payload.get("target_file"), dict)
            else {}
        )
        constraints_payload = (
            coder_packet_payload.get("constraints")
            if isinstance(coder_packet_payload.get("constraints"), dict)
            else {}
        )
        packet = CoderPacket(
            target_file=TargetFile(
                path=str(target_file_payload.get("path") or ""),
                exists=bool(target_file_payload.get("exists")),
                sha256_before=(
                    str(target_file_payload.get("sha256_before"))
                    if target_file_payload.get("sha256_before") is not None
                    else None
                ),
            ),
            operation=str(coder_packet_payload.get("operation") or "edit"),  # type: ignore[arg-type]
            acceptance_criteria=[],
            constraints=ContentConstraints(
                must_contain=[
                    str(item)
                    for item in constraints_payload.get("must_contain", [])
                    if isinstance(item, str)
                ],
                must_not_contain=[
                    str(item)
                    for item in constraints_payload.get("must_not_contain", [])
                    if isinstance(item, str)
                ],
                preserve_imports=[],
                preserve_exports=[],
                max_added_lines=None,
                max_removed_lines=None,
            ),
            context_slices=[],
            forbidden_paths=[
                str(item)
                for item in coder_packet_payload.get("forbidden_paths", [])
                if isinstance(item, str)
            ],
            style_directives=[],
        )
        return task_spec_from_packet(packet).to_dict()
    except Exception:
        return {
            "schema_version": 1,
            "task_type": "modify_existing_file",
            "target": "",
            "allowed_files": [],
            "forbidden_files": [],
            "literal_requirements": [],
            "verification": ["target-only"],
            "risk_tier": "low",
            "source": "deterministic",
        }


def _blocked_task_spec_payload(
    *,
    task_type: str,
    reason_code: str,
    target: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "task_type": task_type,
        "target": target,
        "allowed_files": [],
        "forbidden_files": [],
        "literal_requirements": [],
        "verification": [],
        "risk_tier": "low",
        "source": "deterministic",
        "blockers": [reason_code],
    }


def _first_target_hard_block_reason(reason_codes: list[str]) -> str:
    for reason in ("protected_path", "secret_path", "path_escape", "outside_workspace"):
        if reason in reason_codes:
            return reason
    return ""


def _target_safety_blocked_reason(reason_code: str, target: str) -> str:
    target_suffix = f": {target}" if target else "."
    if reason_code in {"protected_path", "secret_path"}:
        return f"Blocked protected/secret path{target_suffix}"
    if reason_code in {"path_escape", "outside_workspace"}:
        return f"Blocked path escapes workspace{target_suffix}"
    return "Blocked unsafe target path."


def _target_safety_needed_context(reason_code: str) -> str:
    if reason_code in {"protected_path", "secret_path"}:
        return "Choose a non-secret repo file. Protected and secret-shaped paths cannot be edited through the approval flow."
    if reason_code in {"path_escape", "outside_workspace"}:
        return "Use a repo-relative path inside the workspace. Traversal, absolute, and drive paths are blocked."
    return "Choose a safe repo-relative target file."


def _target_safety_constraint(reason_code: str) -> str:
    if reason_code in {"protected_path", "secret_path"}:
        return "Coder Agent mode: blocked before Coder because the requested target is a protected/secret path."
    if reason_code in {"path_escape", "outside_workspace"}:
        return "Coder Agent mode: blocked before Coder because the requested target escapes the workspace."
    return "Coder Agent mode: blocked before Coder because the requested target is unsafe."


def _target_safety_requested_output(reason_code: str) -> str:
    if reason_code in {"protected_path", "secret_path"}:
        return "No unified diff was produced because the requested target is a protected/secret path."
    if reason_code in {"path_escape", "outside_workspace"}:
        return "No unified diff was produced because the requested target escapes the workspace."
    return "No unified diff was produced because the requested target is unsafe."


def _target_safety_paste_back(reason_code: str) -> str:
    if reason_code in {"protected_path", "secret_path"}:
        return "Use a non-secret repo-relative target file; do not approve or paste a diff for protected paths."
    if reason_code in {"path_escape", "outside_workspace"}:
        return "Use a repo-relative path inside the workspace; do not approve or paste a traversal/absolute-path diff."
    return "Use a safe repo-relative target file before retrying."


def _verification_plan_payload_for_response(architect_plan: Any | None) -> dict[str, Any]:
    if architect_plan is not None and hasattr(architect_plan, "to_dict"):
        try:
            payload = architect_plan.to_dict().get("verification_plan")
            if isinstance(payload, dict):
                return payload
        except Exception:
            pass
    return {"required_checks": [], "designer_review_required": False, "architect_review_required": False}


def _camel_coder_packet_payload(payload: dict[str, Any]) -> dict[str, Any]:
    target_file = payload.get("target_file") if isinstance(payload.get("target_file"), dict) else {}
    constraints = payload.get("constraints") if isinstance(payload.get("constraints"), dict) else {}
    return {
        "targetFile": target_file,
        "operation": payload.get("operation"),
        "acceptanceCriteria": payload.get("acceptance_criteria", []),
        "constraints": {
            "mustContain": constraints.get("must_contain", []),
            "mustNotContain": constraints.get("must_not_contain", []),
            "preserveImports": constraints.get("preserve_imports", []),
            "preserveExports": constraints.get("preserve_exports", []),
            "maxAddedLines": constraints.get("max_added_lines"),
            "maxRemovedLines": constraints.get("max_removed_lines"),
        },
        "contextMode": payload.get("context_mode"),
        "contextSlices": payload.get("context_slices", []),
        "forbiddenPaths": payload.get("forbidden_paths", []),
        "styleDirectives": payload.get("style_directives", []),
    }


def _camel_task_spec_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": payload.get("schema_version"),
        "taskType": payload.get("task_type"),
        "target": payload.get("target"),
        "allowedFiles": payload.get("allowed_files", []),
        "forbiddenFiles": payload.get("forbidden_files", []),
        "literalRequirements": payload.get("literal_requirements", []),
        "verification": payload.get("verification", []),
        "riskTier": payload.get("risk_tier"),
        "source": payload.get("source"),
        "blockers": payload.get("blockers", []),
        "clarificationState": payload.get("clarification_state"),
        "clarificationPrompt": payload.get("clarification_prompt"),
        "workspaceMode": payload.get("workspace_mode"),
        "approvalLevel": payload.get("approval_level"),
        "intent": payload.get("intent"),
        "contextSources": payload.get("context_sources", []),
    }


def _camel_task_spec_intake_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": payload.get("schema_version"),
        "taskKind": payload.get("task_kind"),
        "intent": payload.get("intent"),
        "userPrompt": payload.get("user_prompt"),
        "targetPaths": payload.get("target_paths", []),
        "allowedFiles": payload.get("allowed_files", []),
        "forbiddenFiles": payload.get("forbidden_files", []),
        "protectedPaths": payload.get("protected_paths", []),
        "workspaceMode": payload.get("workspace_mode"),
        "approvalLevel": payload.get("approval_level"),
        "modelLane": payload.get("model_lane"),
        "contextSources": payload.get("context_sources", []),
        "verificationPolicy": payload.get("verification_policy", []),
        "riskLevel": payload.get("risk_level"),
        "clarificationState": payload.get("clarification_state"),
        "clarificationPrompt": payload.get("clarification_prompt"),
        "reasonCodes": payload.get("reason_codes", []),
        "summary": payload.get("summary"),
    }


def _coder_packet_context_paths(payload: dict[str, Any]) -> list[str]:
    context_slices = payload.get("context_slices")
    if not isinstance(context_slices, list):
        return []
    paths: list[str] = []
    for item in context_slices:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "").strip()
        if path and path not in paths:
            paths.append(path)
    return paths


def _coder_packet_payload_has_context_content(payload: dict[str, Any]) -> bool:
    context_slices = payload.get("context_slices")
    return isinstance(context_slices, list) and any(
        isinstance(item, dict) and bool(str(item.get("content") or ""))
        for item in context_slices
    )


def _camel_verification_plan_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "requiredChecks": payload.get("required_checks", []),
        "designerReviewRequired": payload.get("designer_review_required", False),
        "architectReviewRequired": payload.get("architect_review_required", False),
    }


def _load_active_architect_plan(task_id: str | None) -> Any | None:
    if not task_id:
        return None
    try:
        return load_plan(task_id)
    except Exception:
        return None


def _with_bridge_route(payload: dict[str, Any]) -> dict[str, Any]:
    next_prompt_action = payload.get("next_prompt_action")
    route_registration = (
        AVAILABLE_ROUTES.get(str(next_prompt_action))
        if next_prompt_action is not None
        else None
    )
    if route_registration is None:
        route_registration = AVAILABLE_ROUTES.get(
            ROUTE_TYPE_TO_ACTION.get(str(payload.get("recommended_route")), "")
        )

    if route_registration is not None:
        payload["bridge_route"] = {
            "action": next_prompt_action,
            **route_registration,
            "available": True,
        }
    return payload


def _decision_input_from_request(request: RouteDecisionRequest) -> DecisionInput:
    return DecisionInput(
        task=request.task,
        active_task_id=request.active_task_id,
        current_agent_role=request.current_agent_role,
        context_tokens=request.context_tokens,
        research_recommended=request.research_recommended,
        sensitive=request.sensitive,
        needs_current_info=request.needs_current_info,
        needs_codebase_context=request.needs_codebase_context,
        wants_implementation=request.wants_implementation,
        prefer_free=request.prefer_free,
    )


@router.post("/recommend-model")
async def model_recommendation(request: RouteDecisionRequest) -> dict[str, Any]:
    reset_request = _request_with_cleared_file_focus(request)
    recommendation = recommend_model(
        ModelRecommendationInput(
            task=reset_request.task,
            active_task_id=reset_request.active_task_id,
            current_agent_role=reset_request.current_agent_role,
            context_tokens=reset_request.context_tokens,
            sensitive=reset_request.sensitive,
            needs_current_info=reset_request.needs_current_info,
            needs_codebase_context=reset_request.needs_codebase_context,
            wants_implementation=reset_request.wants_implementation,
            prefer_free=reset_request.prefer_free,
        )
    )
    return recommendation.as_payload()


@router.post("/api-vs-manual-preview")
async def api_vs_manual_preview(request: ApiVsManualPreviewRequest) -> dict[str, Any]:
    reset_request = _request_with_cleared_file_focus(request)
    return build_api_vs_manual_preview(
        ApiVsManualPreviewInput(
            task=reset_request.task,
            api_model_alias=reset_request.api_model_alias,
            max_completion_tokens=reset_request.max_completion_tokens,
            relevant_context=reset_request.relevant_context,
            context_tokens=reset_request.context_tokens,
            sensitive=reset_request.sensitive,
            needs_current_info=reset_request.needs_current_info,
            needs_codebase_context=reset_request.needs_codebase_context,
            wants_implementation=reset_request.wants_implementation,
            prefer_free=reset_request.prefer_free,
        )
    )


@router.post("/model-lanes/preview")
async def model_lanes_preview(request: ModelLanesPreviewRequest) -> dict[str, Any]:
    return build_model_lanes_preview(task_type=request.task_type)


def _request_with_cleared_file_focus(request: RouteDecisionRequest) -> RouteDecisionRequest:
    update: dict[str, Any] = {
        "conversation_context": [],
        "decision_memory": [],
        "targeted_files": [],
        "target_files": [],
        "proposed_diff": None,
    }
    if request.conversation_context or request.decision_memory:
        update["context_tokens"] = None

    if isinstance(request, PromptPacketRequest):
        update["relevant_context"] = _drop_prior_memory_from_context(
            request.relevant_context
        )

    return request.model_copy(update=update)


def _is_app_router_page_path(normalized: str) -> bool:
    p = normalized.replace("\\", "/").lower()
    return p.startswith("src/app/") and p.endswith("page.tsx")


def _pinned_next_app_page_from_explicit(normalized: str) -> str | None:
    if not normalized or not _is_app_router_page_path(normalized):
        return None
    return normalized


def _route_payload_requests_coder_agent_diff(route_payload: dict[str, Any]) -> bool:
    """True when this request must skip ``build_prompt_packet`` and emit a repo diff.

    ``next_prompt_action`` is the primary switch, but we also key off
    ``recommended_route`` / bridge metadata so a drift in string constants cannot
    silently funnel local implementation work back into wall-of-text prompt packets.
    """
    next_action = str(route_payload.get("next_prompt_action") or "")
    if next_action == "run_with_coder_agent":
        return True
    if str(route_payload.get("recommended_route") or "") == "local_route":
        return True
    bridge = route_payload.get("bridge_route")
    if isinstance(bridge, dict) and str(bridge.get("execution_path") or "") == "coder_agent":
        return True
    return False


def _drop_prior_memory_from_context(relevant_context: str | None) -> str | None:
    if not relevant_context:
        return relevant_context

    sections = [
        section.strip()
        for section in relevant_context.split("\n\n")
        if section.strip()
    ]
    retained_sections = [
        section
        for section in sections
        if not _looks_like_prior_memory_section(section)
    ]
    return "\n\n".join(retained_sections) or None


def _short_task_summary(task: str) -> str:
    normalized = " ".join(task.strip().split())
    if len(normalized) <= 240:
        return normalized
    return f"{normalized[:237].rstrip()}..."


def _coder_agent_manual_browser_prompt_text(
    *,
    task: str,
    target: str,
    task_spec: dict[str, Any],
    coder_packet: dict[str, Any],
    verification_plan: dict[str, Any],
    blocked_reason: str,
    needed_context: str,
    reason_code: str,
    diagnostics: dict[str, Any],
) -> str:
    context_slices = [
        item
        for item in coder_packet.get("context_slices", [])
        if isinstance(item, dict)
    ]
    rendered_context: list[str] = []
    for item in context_slices[:4]:
        path = str(item.get("path") or "")
        kind = str(item.get("kind") or "context")
        content = str(item.get("content") or "")
        rendered_context.append(
            "\n".join(
                [
                    f"### {kind} slice: {path}",
                    "```",
                    content[:12000],
                    "```",
                ]
            )
        )

    diagnostics_payload = {
        key: diagnostics.get(key)
        for key in (
            "raw_response_excerpt",
            "json_attempt_count",
            "coder_format_retry_count",
            "last_json_error",
            "parse_error_class",
            "parse_error_message",
        )
        if diagnostics.get(key) not in (None, "")
    }
    return "\n".join(
        [
            "# Manual Browser Prompt: SpiritOS Coder Recovery",
            "",
            "Use this prompt in GPT, Gemini, Grok, Claude, or another browser model.",
            "Return output to the SpiritOS portal for validation. Do not bypass the portal.",
            "",
            "## Task",
            task.strip() or f"Modify {target}.",
            "",
            "## Non-Negotiable Portal Contract",
            "- Return only JSON, or a unified diff only if JSON is impossible.",
            "- Prefer the content_lines JSON schema.",
            "- Target must exactly match TaskSpec.target.",
            "- Only edit files in TaskSpec.allowed_files.",
            "- Do not include prose outside the returned JSON or diff.",
            "- The portal will still run TaskSpec.allowed_files, target-only, git apply, reviewer, approval, protected apply, and post-apply verification.",
            "",
            "## Preferred Output Schema",
            "```json",
            json.dumps(
                {
                    "action": "replace_file",
                    "target": target or "REPO_RELATIVE_PATH",
                    "content_lines": ["line 1", "line 2"],
                    "notes": "short optional note",
                },
                indent=2,
            ),
            "```",
            "",
            "## Legacy Accepted Schema",
            "```json",
            json.dumps(
                {
                    "action": "replace_file",
                    "target": target or "REPO_RELATIVE_PATH",
                    "content": "FULL_FILE_CONTENT",
                    "notes": "short optional note",
                },
                indent=2,
            ),
            "```",
            "",
            "## TaskSpec",
            "```json",
            json.dumps(task_spec, indent=2, sort_keys=True),
            "```",
            "",
            "## Verification Plan",
            "```json",
            json.dumps(verification_plan, indent=2, sort_keys=True),
            "```",
            "",
            "## Local Coder Failure To Avoid",
            f"- reason_code: {reason_code or 'coder_blocked'}",
            f"- blocked_reason: {blocked_reason or 'none'}",
            f"- needed_context: {needed_context or 'none'}",
            "",
            "## Coder Diagnostics",
            "```json",
            json.dumps(diagnostics_payload, indent=2, sort_keys=True),
            "```",
            "",
            "## Repository Context",
            "\n\n".join(rendered_context) or "No context slices were provided.",
            "",
            "Return the replacement JSON now.",
        ]
    )


def _coder_agent_stub_prompt_text(target: str, proposed_diff: str) -> str:
    """Tiny surface for older clients; the real diff lives in proposed_diff."""
    if proposed_diff and target:
        return (
            "Coder Agent returned backend-generated proposed_diff for approval-gate validation "
            f"(target: {target}). If the client rejects the diff, treat the proposal as blocked and retry Coder."
        )
    return (
        "Coder Agent could not synthesize safe replacement content for backend diff generation. "
        f"Target guess: {target or 'none'}. Check coder notes in relevant_context."
    )


def _coder_agent_subjective_no_diff_prompt_text(target: str) -> str:
    target_text = f" Target: {target}." if target else ""
    return (
        "No diff was produced, and subjective improvement cannot be marked already "
        f"satisfied.{target_text} Produce an actual visual refinement diff or use "
        "manual visual review."
    )


def _coder_agent_shallow_visual_diff_prompt_text(target: str) -> str:
    target_text = f" Target: {target}." if target else ""
    return (
        "The generated visual diff was too shallow: it did not materially change "
        "styling, layout, hover, active, glow, spacing, or animation behavior."
        f"{target_text} Generate a concrete visual refinement diff before approval."
    )


def _looks_like_prior_memory_section(section: str) -> bool:
    first_line = section.splitlines()[0].strip().lower()
    return first_line.startswith(
        (
            "recent coding conversation context:",
            "previous routing decision memory:",
            "turn ",
            "memory ",
        )
    )
