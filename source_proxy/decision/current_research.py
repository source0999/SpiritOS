from __future__ import annotations

import hashlib
import json
from typing import Any

from source_proxy.decision.research import run_searxng_research_diagnostics
from source_proxy.decision.scout_research import run_scout_research_diagnostics
from source_proxy.tasks.long_running import record_subsystem_integration_result


CURRENT_RESEARCH_HANDLER_VERSION = "source-proxy-plan2-current-research-v1"


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
    scout = await run_scout_research_diagnostics(normalized_query, max_results=max_results)
    searxng = await run_searxng_research_diagnostics(normalized_query, max_results=max_results)
    sources = _sources_from_diagnostics(scout, searxng)
    provider_status = {
        "scout": scout.get("status"),
        "scout_reason": scout.get("reason"),
        "searxng": searxng.get("status"),
        "searxng_reason": searxng.get("reason"),
    }
    if sources:
        status = "INTEGRATED"
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
        "sources": sources,
        "source_count": len(sources),
        "untrusted_content_marked": all(item.get("untrusted") is not None for item in sources),
        "provenance_required": True,
        "generic_local_file_fallback_used": False,
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
