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
