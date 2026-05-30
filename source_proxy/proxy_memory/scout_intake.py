from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import os


class ScoutIntakeConfigError(RuntimeError):
    pass


def write(packet: Any, verdict: Any, *, promotion_id: str, approved_by: str) -> dict[str, Any]:
    """Persist a Scout promotion into the proxy's v0.1 append-only intake log."""
    configured_path = os.environ.get("SOURCE_PROXY_SCOUT_INTAKE_LOG", "").strip()
    if not configured_path:
        raise ScoutIntakeConfigError("SOURCE_PROXY_SCOUT_INTAKE_LOG is required")
    path = Path(configured_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "event": "scout_promotion_intake",
        "promotion_id": promotion_id,
        "packet_id": packet.packet_id,
        "approved_by": approved_by,
        "packet": packet.model_dump(mode="json"),
        "verdict": verdict.model_dump(mode="json"),
        "written_at": datetime.now(timezone.utc).isoformat(),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return {
        "written": True,
        "path": str(path),
        "packet_id": packet.packet_id,
        "promotion_id": promotion_id,
        "authority": "append_only_evidence",
        "applied": False,
        "approved_proxy_action": False,
    }


def write_design_inspiration(
    *,
    title: str,
    note: str,
    source_url: str | None = None,
    tags: list[str] | None = None,
    log_path: str | Path | None = None,
) -> dict[str, Any]:
    """Store design inspiration notes without crawl, promotion, or proxy-memory authority."""
    path_value = log_path or os.environ.get("SOURCE_PROXY_SCOUT_DESIGN_INTAKE_LOG", "").strip()
    if not path_value:
        raise ScoutIntakeConfigError("SOURCE_PROXY_SCOUT_DESIGN_INTAKE_LOG or log_path is required")
    if not title.strip():
        raise ValueError("title is required")
    if not note.strip():
        raise ValueError("note is required")

    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "event": "scout_design_inspiration_stored_only",
        "title": title.strip(),
        "note": note.strip(),
        "source_url": source_url.strip() if source_url else None,
        "tags": sorted({tag.strip() for tag in tags or [] if tag.strip()}),
        "stored_at": datetime.now(timezone.utc).isoformat(),
        "authority": "stored_only_design_inspiration",
        "crawl_requested": False,
        "crawler_started": False,
        "scheduler_started": False,
        "worker_started": False,
        "proxy_memory_written": False,
        "proxy_memory_promoted": False,
        "coding_context_injected": False,
        "approved_proxy_action": False,
        "applied": False,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return {
        "written": True,
        "path": str(path),
        "authority": record["authority"],
        "crawl_requested": False,
        "crawler_started": False,
        "scheduler_started": False,
        "worker_started": False,
        "proxy_memory_written": False,
        "proxy_memory_promoted": False,
        "coding_context_injected": False,
    }
