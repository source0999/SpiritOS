from __future__ import annotations

import json
import logging
import os
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


async def run_scout_research_preview(
    query: str,
    max_results: int = 6,
) -> list[dict[str, Any]]:
    """Return Scout packets as research sources.

    Any failure returns an empty list. Default filtering only admits surface and
    promote packets. The admin override only adds stored packets.
    """
    if os.environ.get("SOURCE_PROXY_SCOUT_RESEARCH_ENABLED", "0") != "1":
        return []

    base = os.environ.get("SOURCE_PROXY_SCOUT_RESEARCH_URL", "http://localhost:8077")
    timeout_ms = int(
        os.environ.get("SOURCE_PROXY_SCOUT_RESEARCH_TIMEOUT_MS", DEFAULT_TIMEOUT_MS)
    )
    admin = os.environ.get("SOURCE_PROXY_SCOUT_ADMIN_INCLUDE_STORED", "0") == "1"
    allowed = SAFE_DECISIONS_ADMIN if admin else SAFE_DECISIONS_DEFAULT

    try:
        async with httpx.AsyncClient(timeout=timeout_ms / 1000.0) as client:
            response = await client.get(
                f"{base.rstrip('/')}/v1/scout/packets/search",
                params={
                    "q": query,
                    "limit": max_results,
                    "with_verdict": "true",
                },
            )
            if response.status_code != 200:
                return []
            payload = response.json()

        results: list[dict[str, Any]] = []
        for raw in payload.get("packets", []):
            packet = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(packet, dict):
                continue
            verdict = packet.get("_verdict") or {}
            decision = verdict.get("decision")
            if decision not in allowed:
                continue
            summary = _clean_text(packet.get("summary"))[:120]
            impact = _clean_text(packet.get("impact_analysis"))[:400]
            results.append(
                {
                    "title": summary,
                    "url": packet.get("source_uri", ""),
                    "snippet": impact,
                    "source": "scout",
                    "scout_decision": decision,
                    "scout_packet_id": packet.get("packet_id"),
                    "authority": SCOUT_AUTHORITY,
                    "can_apply": False,
                    "can_approve": False,
                    "can_mutate_proxy_memory": False,
                    "evidence": {
                        "source": packet.get("source_uri", ""),
                        "freshness": _packet_freshness(packet),
                        "trust_status": _trust_status(packet, verdict),
                        "review_status": decision,
                        "packet_summary": summary,
                        "why_relevant": _why_relevant(packet, verdict),
                    },
                }
            )
        return results
    except Exception as exc:
        if structlog:
            logger.warning("scout_research_failed", error=str(exc))
        else:
            logger.warning("scout_research_failed: %s", exc)
        return []


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
