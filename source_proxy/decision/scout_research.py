from __future__ import annotations

import json
import logging
import os
import hashlib
from datetime import UTC, datetime
from typing import Any

import httpx

try:
    import structlog
except ModuleNotFoundError:
    structlog = None

logger = structlog.get_logger() if structlog else logging.getLogger(__name__)

DEFAULT_TIMEOUT_MS = 500
SAFE_DECISIONS_DEFAULT = ("surface", "promote")
SAFE_DECISIONS_ADMIN = ("surface", "promote", "stored")
SCOUT_AUTHORITY = "evidence_only"
SCOUT_SEARCH_QUERY_MAX_CHARS = 200


def _scout_search_query(query: str) -> tuple[str, bool]:
    compact = " ".join(str(query or "").split())
    if len(compact) <= SCOUT_SEARCH_QUERY_MAX_CHARS:
        return compact, False
    return compact[:SCOUT_SEARCH_QUERY_MAX_CHARS], True


async def run_scout_research_preview(
    query: str,
    max_results: int = 6,
) -> list[dict[str, Any]]:
    """Return Scout packets as research sources.

    Any failure returns an empty list. Default filtering only admits surface and
    promote packets. The admin override only adds stored packets.
    """
    diagnostics = await run_scout_research_diagnostics(query, max_results=max_results)
    sources = diagnostics.get("scout_sources")
    return sources if isinstance(sources, list) else []


async def run_scout_research_diagnostics(
    query: str,
    max_results: int = 6,
) -> dict[str, Any]:
    enabled = os.environ.get("SOURCE_PROXY_SCOUT_RESEARCH_ENABLED", "0") == "1"
    base = os.environ.get("SOURCE_PROXY_SCOUT_RESEARCH_URL", "http://localhost:8077")
    endpoint = f"{base.rstrip('/')}/v1/scout/packets/search"
    scout_query, query_truncated = _scout_search_query(query)
    request_params = {
        "q": scout_query,
        "limit": max_results,
        "with_verdict": "true",
    }
    request_shape = {
        "method": "GET",
        "endpoint": endpoint,
        "params": request_params,
        "param_keys": sorted(request_params.keys()),
        "query_length": len(query or ""),
        "submitted_query_length": len(scout_query),
        "query_truncated": query_truncated,
    }
    packet: dict[str, Any] = {
        "status": "skipped",
        "reason": "scout_research_disabled",
        "scout_enabled": enabled,
        "scout_url": base,
        "scout_request": request_shape,
        "scout_result_count": 0,
        "scout_sources": [],
        "raw_packet_count": 0,
        "filtered_packet_count": 0,
        "allowed_decisions": [],
        "allowed_packet_filter_reason": "",
        "provider_errors": [],
        "fix_command": "Set SOURCE_PROXY_SCOUT_RESEARCH_ENABLED=1 and SOURCE_PROXY_SCOUT_RESEARCH_URL to a reachable Scout API if Scout research is required.",
        "config_target": "SOURCE_PROXY_SCOUT_RESEARCH_URL",
        "authority": SCOUT_AUTHORITY,
    }
    if not enabled:
        return packet

    timeout_ms = int(
        os.environ.get("SOURCE_PROXY_SCOUT_RESEARCH_TIMEOUT_MS", DEFAULT_TIMEOUT_MS)
    )
    admin = os.environ.get("SOURCE_PROXY_SCOUT_ADMIN_INCLUDE_STORED", "0") == "1"
    allowed = SAFE_DECISIONS_ADMIN if admin else SAFE_DECISIONS_DEFAULT
    packet["allowed_decisions"] = list(allowed)

    try:
        async with httpx.AsyncClient(timeout=timeout_ms / 1000.0) as client:
            response = await client.get(
                endpoint,
                params=request_params,
            )
            if response.status_code != 200:
                response_body = str(getattr(response, "text", "") or "")[:1000]
                return {
                    **packet,
                    "status": "failed",
                    "reason": "scout_http_status_error",
                    "http_status": response.status_code,
                    "response_body_excerpt": response_body,
                    "provider_errors": [
                        f"HTTP {response.status_code}: {response_body}"
                        if response_body
                        else f"HTTP {response.status_code}"
                    ],
                    "fix_command": "Verify the Scout API is healthy at SOURCE_PROXY_SCOUT_RESEARCH_URL and that /v1/scout/packets/search is available.",
                }
            payload = response.json()
    except Exception as exc:
        return {
            **packet,
            "status": "blocked",
            "reason": "scout_dependency_unreachable",
            "provider_errors": [f"{type(exc).__name__}: {exc}"],
            "fix_command": "Start or repair the Scout API dependency, verify SOURCE_PROXY_SCOUT_RESEARCH_URL, then restart npm run proxy:https:lan.",
        }

    results: list[dict[str, Any]] = []
    raw_packets = payload.get("packets", []) if isinstance(payload, dict) else []
    if not isinstance(raw_packets, list):
        raw_packets = []
    filtered_count = 0
    for raw in raw_packets:
        packet_data = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(packet_data, dict):
            continue
        verdict = packet_data.get("_verdict") or {}
        decision = verdict.get("decision")
        if decision not in allowed:
            filtered_count += 1
            continue
        summary = _clean_text(packet_data.get("summary"))[:120]
        impact = _clean_text(packet_data.get("impact_analysis"))[:400]
        results.append(
            {
                "title": summary,
                "url": packet_data.get("source_uri", ""),
                "snippet": impact,
                "source": "scout",
                "scout_decision": decision,
                "scout_packet_id": packet_data.get("packet_id"),
                "authority": SCOUT_AUTHORITY,
                "can_apply": False,
                "can_approve": False,
                "can_mutate_proxy_memory": False,
                "evidence": {
                    "source": packet_data.get("source_uri", ""),
                    "freshness": _packet_freshness(packet_data),
                    "trust_status": _trust_status(packet_data, verdict),
                    "review_status": decision,
                    "packet_summary": summary,
                    "why_relevant": _why_relevant(packet_data, verdict),
                },
            }
        )

    return {
        **packet,
        "status": "used" if results else "skipped",
        "reason": "scout_research_sources_selected"
        if results
        else "scout_returned_no_allowed_packets",
        "scout_result_count": len(results),
        "scout_sources": results,
        "raw_packet_count": len(raw_packets),
        "filtered_packet_count": filtered_count,
        "allowed_decisions": list(allowed),
        "allowed_packet_filter_reason": ""
        if results
        else "no_packets_with_allowed_scout_decisions",
        "provider_errors": [],
        "fix_command": "" if results else "Add or promote Scout packets for this query, or leave Scout skipped.",
    }


async def run_canonical_coding_research(
    *,
    task_id: str,
    query: str,
    max_results: int = 6,
) -> dict[str, Any]:
    """Run the only selectable coding-research lane.

    Scout owns provider invocation and selection.  SearXNG and fetch are
    recorded as providers, never promoted to independently selectable lanes.
    Empty, unavailable, or untrusted provider results remain explicit failures
    or degradations; this function never manufactures a citation.
    """
    from source_proxy.decision.research import run_searxng_research_diagnostics

    normalized_task = str(task_id or "").strip()
    normalized_query, query_truncated = _scout_search_query(query)
    request_hash = hashlib.sha256(
        json.dumps({"task_id": normalized_task, "query": normalized_query}, sort_keys=True).encode("utf-8")
    ).hexdigest()
    base = {
        "schema_version": "campaign-3/scout-research-receipt/v1",
        "task_id": normalized_task,
        "research_id": f"scout-research-{request_hash[:16]}",
        "request_hash": f"sha256:{request_hash}",
        "query": normalized_query,
        "query_truncated": query_truncated,
        "requested_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "authority": SCOUT_AUTHORITY,
        "mutation_authority": False,
        "provider_chain": ["scout", "searxng", "bounded-fetch"],
        "sources": [],
        "citations": [],
        "consumption_required": True,
    }
    if not normalized_task:
        return {**base, "status": "blocked", "reason": "task_id_missing", "claim_ceiling": "no_research_claim"}
    if not normalized_query:
        return {**base, "status": "blocked", "reason": "research_query_missing", "claim_ceiling": "no_research_claim"}

    scout = await run_scout_research_diagnostics(normalized_query, max_results=max_results)
    searxng = await run_searxng_research_diagnostics(normalized_query, max_results=max_results)
    selected = _select_current_primary_sources(
        [
            *(scout.get("scout_sources") if isinstance(scout.get("scout_sources"), list) else []),
            *(searxng.get("searxng_sources") if isinstance(searxng.get("searxng_sources"), list) else []),
        ],
        max_results=max_results,
    )
    fetches = await _bounded_fetch_sources(selected)
    sources: list[dict[str, Any]] = []
    for source in selected:
        url = str(source.get("url") or "")
        fetch = fetches.get(url, {})
        source_copy = dict(source)
        evidence = dict(source.get("evidence") or {})
        evidence.update({
            "query": normalized_query,
            "primary_source_preferred": _is_primary_source(url),
            "fetched_at": fetch.get("fetched_at"),
            "fetch_status": fetch.get("status", "not_requested"),
            "content_sha256": fetch.get("content_sha256"),
        })
        source_copy["evidence"] = evidence
        source_copy["source"] = "scout"
        source_copy["authority"] = SCOUT_AUTHORITY
        source_copy["can_apply"] = False
        source_copy["can_approve"] = False
        source_copy["can_mutate_proxy_memory"] = False
        sources.append(source_copy)
    statuses = {str(scout.get("status") or "unknown"), str(searxng.get("status") or "unknown")}
    if sources:
        status, reason, ceiling = "used", "canonical_scout_sources_selected", "research_provenance_bound"
    elif "blocked" in statuses or "failed" in statuses:
        status, reason, ceiling = "blocked", "scout_or_provider_unavailable", "research_required_but_unavailable"
    else:
        status, reason, ceiling = "skipped", "no_current_research_sources", "no_external_research_claim"
    return {
        **base,
        "status": status,
        "reason": reason,
        "claim_ceiling": ceiling,
        "sources": sources,
        "citations": [
            {"url": str(source.get("url") or ""), "freshness": str((source.get("evidence") or {}).get("freshness") or "unknown")}
            for source in sources
        ],
        "providers": {"scout": scout, "searxng": searxng, "fetch": fetches},
    }


def _select_current_primary_sources(raw_sources: list[dict[str, Any]], *, max_results: int) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for raw in raw_sources:
        if not isinstance(raw, dict):
            continue
        url = str(raw.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            continue
        evidence = raw.get("evidence") if isinstance(raw.get("evidence"), dict) else {}
        if str(evidence.get("freshness") or "unknown") == "unknown" and raw.get("source") == "scout":
            continue
        unique.setdefault(url, dict(raw))
    return sorted(unique.values(), key=lambda item: (not _is_primary_source(str(item.get("url") or "")), str(item.get("url") or "")))[: max(1, min(int(max_results), 12))]


async def _bounded_fetch_sources(sources: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    timeout_seconds = max(0.1, min(int(os.environ.get("SOURCE_PROXY_SCOUT_FETCH_TIMEOUT_MS", "5000")) / 1000, 15.0))
    results: dict[str, dict[str, Any]] = {}
    async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
        for source in sources:
            url = str(source.get("url") or "")
            if not url:
                continue
            try:
                response = await client.get(url, headers={"User-Agent": "SpiritOSScoutResearch/1.0"})
                body = response.content[:200_000]
                results[url] = {
                    "status": "fetched" if response.status_code < 400 else f"http_{response.status_code}",
                    "fetched_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    "content_sha256": "sha256:" + hashlib.sha256(body).hexdigest(),
                }
            except httpx.HTTPError as error:
                results[url] = {"status": f"fetch_error:{type(error).__name__}", "fetched_at": datetime.now(UTC).isoformat().replace("+00:00", "Z")}
    return results


def _is_primary_source(url: str) -> bool:
    host = url.split("/", 3)[2].lower() if "://" in url and len(url.split("/", 3)) > 2 else ""
    return host.endswith((".gov", ".edu", ".org")) or host in {"developer.mozilla.org", "docs.python.org", "www.rfc-editor.org", "openai.com"}

def _clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())


def _packet_freshness(packet: dict[str, Any]) -> str:
    timestamp = _clean_text(packet.get("timestamp"))
    if timestamp:
        return timestamp
    provenance = packet.get("provenance")
    if isinstance(provenance, dict):
        return _clean_text(provenance.get("synthesized_at")) or "unknown"
    return "unknown"


def _trust_status(packet: dict[str, Any], verdict: dict[str, Any]) -> str:
    trust = packet.get("trust_status") or packet.get("trust_label")
    if isinstance(trust, str) and trust.strip():
        return _clean_text(trust)
    score = verdict.get("source_quality_score")
    if isinstance(score, int | float):
        if score >= 0.75:
            return "high"
        if score >= 0.5:
            return "medium"
        return "low"
    return "reviewed"


def _why_relevant(packet: dict[str, Any], verdict: dict[str, Any]) -> str:
    decision = _clean_text(verdict.get("decision"))
    tags = packet.get("entity_tags")
    tag_text = ""
    if isinstance(tags, list):
        visible_tags = [str(tag).strip() for tag in tags if str(tag).strip()][:4]
        if visible_tags:
            tag_text = f" Tags: {', '.join(visible_tags)}."
    if decision:
        return f"Scout debugger reviewed this packet with decision '{decision}'.{tag_text}"
    return f"Scout packet matched the research query.{tag_text}"
