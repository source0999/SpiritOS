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
            results.append(
                {
                    "title": packet.get("summary", "")[:120],
                    "url": packet.get("source_uri", ""),
                    "snippet": packet.get("impact_analysis", "")[:400],
                    "source": "scout",
                    "scout_decision": decision,
                    "scout_packet_id": packet.get("packet_id"),
                }
            )
        return results
    except Exception as exc:
        if structlog:
            logger.warning("scout_research_failed", error=str(exc))
        else:
            logger.warning("scout_research_failed: %s", exc)
        return []
