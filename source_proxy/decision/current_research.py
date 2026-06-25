from __future__ import annotations

import asyncio
import hashlib
import json
import os
from typing import Any

from source_proxy.decision.research import run_searxng_research_diagnostics
from source_proxy.decision.scout_research import run_scout_research_diagnostics
from source_proxy.tasks.long_running import record_subsystem_integration_result


CURRENT_RESEARCH_HANDLER_VERSION = "source-proxy-plan2-current-research-v1"
DEFAULT_CURRENT_RESEARCH_MAX_RETRIES = 2
DEFAULT_CURRENT_RESEARCH_RETRY_BACKOFF_SECONDS = 0.25


def _json_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _sources_from_diagnostics(scout: dict[str, Any], searxng: dict[str, Any]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for item in scout.get("scout_sources") or []:
        if isinstance(item, dict):
            sources.append(
                {
                    **item,
                    "provider": "scout",
                    "untrusted": False,
                    "provenance_required": True,
                }
            )
    for item in searxng.get("searxng_sources") or []:
        if isinstance(item, dict):
            sources.append(
                {
                    **item,
                    "provider": "searxng",
                    "untrusted": True,
                    "provenance_required": True,
                }
            )
    return sources


def _bounded_int_env(name: str, default: int, *, minimum: int, maximum: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError:
        return default
    return min(max(value, minimum), maximum)


def _bounded_float_env(name: str, default: float, *, minimum: float, maximum: float) -> float:
    try:
        value = float(os.environ.get(name, str(default)))
    except ValueError:
        return default
    return min(max(value, minimum), maximum)


def _provider_attempt_summary(index: int, query: str, scout: dict[str, Any], searxng: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "attempt": index,
        "query": query,
        "source_count": len(sources),
        "providers": {
            "scout": scout.get("status"),
            "scout_reason": scout.get("reason"),
            "scout_result_count": scout.get("scout_result_count", 0),
            "scout_provider_errors": scout.get("provider_errors", []),
            "searxng": searxng.get("status"),
            "searxng_reason": searxng.get("reason"),
            "searxng_result_count": searxng.get("searxng_result_count", 0),
            "searxng_provider_errors": searxng.get("provider_errors", []),
            "searxng_provider_url_used": searxng.get("provider_url_used") or "",
            "searxng_latency_ms": searxng.get("searxng_latency_ms"),
        },
    }


def _research_provider_failure_classification(attempts: list[dict[str, Any]]) -> str:
    if not attempts:
        return "UNKNOWN_NEEDS_HUMAN"
    if any(int(attempt.get("source_count") or 0) > 0 for attempt in attempts):
        return "SOURCES_AVAILABLE"
    serialized_errors = json.dumps(attempts, sort_keys=True, default=str).lower()
    if "timeout" in serialized_errors:
        return "PROVIDER_TIMEOUT"
    if "http " in serialized_errors or "http_status" in serialized_errors:
        return "PROVIDER_HTTP_ERROR"
    if "invalid_json" in serialized_errors or "json_results_missing" in serialized_errors:
        return "PROVIDER_PARSE_ERROR"
    if "returned_no_usable_results" in serialized_errors or "no_allowed_packets" in serialized_errors:
        return "PROVIDER_ZERO_RESULTS"
    return "PROVIDER_ZERO_RESULTS"


async def run_current_research_for_task(
    task_id: str,
    *,
    query: str,
    upstream_state: dict[str, Any],
    max_results: int = 6,
) -> dict[str, Any]:
    """Run current research through Scout/SearXNG only and consume it into task state."""
    normalized_query = " ".join(str(query or "").split())
    upstream = {
        **dict(upstream_state),
        "query": normalized_query,
        "handler_version": CURRENT_RESEARCH_HANDLER_VERSION,
    }
    max_retries = _bounded_int_env(
        "SOURCE_PROXY_CURRENT_RESEARCH_MAX_RETRIES",
        DEFAULT_CURRENT_RESEARCH_MAX_RETRIES,
        minimum=0,
        maximum=3,
    )
    retry_backoff_seconds = _bounded_float_env(
        "SOURCE_PROXY_CURRENT_RESEARCH_RETRY_BACKOFF_SECONDS",
        DEFAULT_CURRENT_RESEARCH_RETRY_BACKOFF_SECONDS,
        minimum=0.0,
        maximum=2.0,
    )
    attempts: list[dict[str, Any]] = []
    scout: dict[str, Any] = {}
    searxng: dict[str, Any] = {}
    sources: list[dict[str, Any]] = []
    for attempt_index in range(1, max_retries + 2):
        scout = await run_scout_research_diagnostics(normalized_query, max_results=max_results)
        searxng = await run_searxng_research_diagnostics(normalized_query, max_results=max_results)
        sources = _sources_from_diagnostics(scout, searxng)
        attempts.append(_provider_attempt_summary(attempt_index, normalized_query, scout, searxng, sources))
        if sources:
            break
        if attempt_index <= max_retries and retry_backoff_seconds:
            await asyncio.sleep(retry_backoff_seconds)
    provider_status = {
        "scout": scout.get("status"),
        "scout_reason": scout.get("reason"),
        "searxng": searxng.get("status"),
        "searxng_reason": searxng.get("reason"),
    }
    failure_classification = _research_provider_failure_classification(attempts)
    if sources:
        status = "INTEGRATED_LIVE"
        reason = "current_research_sources_consumed"
        downstream_decision = "research_sources_available"
    else:
        status = "BLOCKED_ENV"
        reason = "no_current_research_provider_returned_sources"
        downstream_decision = "research_required_but_unavailable"

    packet = {
        "handler_version": CURRENT_RESEARCH_HANDLER_VERSION,
        "summary": reason,
        "query": normalized_query,
        "status": status,
        "reason": reason,
        "providers": provider_status,
        "provider_url_used": searxng.get("provider_url_used") or "",
        "sources": sources,
        "source_count": len(sources),
        "research_provider_attempts": attempts,
        "research_provider_attempt_count": len(attempts),
        "research_provider_retry_count": max(0, len(attempts) - 1),
        "research_provider_max_retries": max_retries,
        "research_provider_retry_backoff_seconds": retry_backoff_seconds,
        "research_provider_failure_classification": failure_classification,
        "research_provider_result_counts": [attempt.get("source_count", 0) for attempt in attempts],
        "retrieved_at": searxng.get("retrieved_at") or "",
        "untrusted_content_marked": all(item.get("untrusted") is not None for item in sources),
        "provenance_required": True,
        "generic_local_file_fallback_used": False,
        "local_fallback_used": False,
        "downstream_state_changed": bool(sources),
        "downstream_decision": downstream_decision,
    }
    packet["research_packet_hash"] = _json_hash(packet)
    payload = record_subsystem_integration_result(
        task_id,
        subsystem="current_research",
        consumer_subsystem="cartographer_current_research_consumer",
        upstream_state=upstream,
        output=packet,
        status=status,
        changed_state_fields=["ast_snapshot.plan_2_research"],
        failure_reason=None if sources else reason,
    )
    return {
        "status": status,
        "reason": reason,
        "research_packet": packet,
        "task": payload["task"],
    }
