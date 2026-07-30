"""Strict NDJSON evidence mapping for the disabled JCode qualification lane."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from source_proxy.jcode.adapter import JCODE_EXECUTION_RESULT_FIELDS
from source_proxy.jcode.event_schema import EventBinding, parse_strict_event_stream


def map_strict_jcode_event_evidence(raw: bytes, binding: EventBinding) -> dict[str, Any]:
    """Gate 2-J.9D strict bridge; fixture claims never become terminal truth."""
    return parse_strict_event_stream(raw, binding)


def seal_strict_event_evidence(result: dict[str, Any], destination: Path) -> dict[str, Any]:
    """Persist strict evidence atomically enough for no-model fixture receipts."""
    updated = dict(result)
    try:
        destination.write_text(
            json.dumps(updated, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    except OSError:
        updated["status"] = "EVIDENCE_INCOMPLETE"
        updated["evidence_sealed"] = False
        updated.setdefault("blocked_reasons", []).append("event_evidence_write_failed")
        return updated
    updated["evidence_sealed"] = True
    return updated


def map_jcode_ndjson_evidence(raw: bytes) -> dict[str, Any]:
    """Map only a complete, ordered event stream into non-authoritative evidence."""
    reasons: list[str] = []
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            reasons.append(f"ndjson_blank_line:{line_number}")
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            reasons.append(f"ndjson_invalid_json:{line_number}")
            continue
        if not isinstance(event, dict):
            reasons.append(f"ndjson_event_not_object:{line_number}")
            continue
        events.append(event)
    if not events:
        reasons.append("ndjson_events_missing")
    for expected, event in enumerate(events, start=1):
        if event.get("sequence") != expected:
            reasons.append(f"ndjson_sequence_invalid:{expected}")
        if not isinstance(event.get("type"), str):
            reasons.append(f"ndjson_type_missing:{expected}")
    terminal = events[-1] if events else {}
    if terminal.get("type") != "run.completed":
        reasons.append("ndjson_terminal_sentinel_missing")
    result = terminal.get("result") if isinstance(terminal.get("result"), dict) else {}
    missing_fields = [field for field in JCODE_EXECUTION_RESULT_FIELDS if field not in result]
    reasons.extend(f"jcode_result_field_missing:{field}" for field in missing_fields)
    return {
        "status": "evidence_ready" if not reasons else "EVIDENCE_INCOMPLETE",
        "raw_ndjson_sha256": hashlib.sha256(raw).hexdigest(),
        "event_count": len(events),
        "events": events,
        "result": result if not reasons else None,
        "blocked_reasons": reasons,
        "executor_claim_is_terminal_truth": False,
        "proxy_independent_determination_required": [
            "git_diff",
            "protected_path_policy",
            "tests",
            "reviewer",
            "verifier",
            "anti_cheat",
            "terminal_truth",
        ],
    }
