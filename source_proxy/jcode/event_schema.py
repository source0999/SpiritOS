"""Strict, tamper-evident no-model event ingestion for Gate 2-J.9D."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any


EVENT_SCHEMA_VERSION = "source-proxy.jcode-event/v1"
EVENT_TYPES = frozenset({
    "process.started", "environment.attested", "binary.attested", "provider.configured",
    "model_request.started", "model_request.completed", "model_request.failed",
    "tool.proposed", "tool.allowed", "tool.denied", "tool.completed",
    "command.started", "command.completed", "command.denied", "file.read",
    "file.created", "file.modified", "file.deleted", "retry", "budget.warning",
    "timeout", "cancellation.requested", "cancellation.completed", "process.exited",
    "evidence.sealed", "executor.claimed_result", "run.completed",
})
REQUIRED_EVENT_FIELDS = (
    "schema_version", "event_id", "sequence", "timestamp", "task_id", "run_id",
    "correlation_id", "gate_id", "type", "source", "payload", "prev_event_hash", "event_hash",
)


@dataclass(frozen=True)
class EventBinding:
    task_id: str
    run_id: str
    correlation_id: str
    gate_id: str = "2-J.9D"
    max_line_bytes: int = 262_144
    max_events: int = 50_000
    max_total_bytes: int = 104_857_600


def canonical_event_hash(event: dict[str, Any]) -> str:
    """Hash the canonical event body, excluding its self-referential field."""
    body = dict(event)
    body.pop("event_hash", None)
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def parse_strict_event_stream(raw: bytes, binding: EventBinding) -> dict[str, Any]:
    """Parse only complete, bound, hash-chained NDJSON; never infer success."""
    reasons: list[str] = []
    if not raw:
        return _result([], ["ndjson_events_missing"], raw)
    if len(raw) > binding.max_total_bytes:
        reasons.append("ndjson_total_bytes_exceeded")
    if raw.startswith(b"\xef\xbb\xbf"):
        reasons.append("ndjson_bom_forbidden")
    if not raw.endswith(b"\n"):
        reasons.append("ndjson_partial_final_line")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return _result([], [*reasons, "ndjson_invalid_utf8"], raw)
    events: list[dict[str, Any]] = []
    previous_hash = ""
    seen_ids: set[str] = set()
    terminal_seen = False
    for number, line in enumerate(text.splitlines(), start=1):
        encoded = line.encode("utf-8")
        if not line:
            reasons.append(f"ndjson_blank_line:{number}")
            continue
        if len(encoded) > binding.max_line_bytes:
            reasons.append(f"ndjson_oversized_line:{number}")
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            reasons.append(f"ndjson_invalid_json:{number}")
            continue
        if not isinstance(event, dict):
            reasons.append(f"ndjson_event_not_object:{number}")
            continue
        events.append(event)
        _validate_event(event, number, binding, previous_hash, seen_ids, reasons)
        current_hash = event.get("event_hash")
        if isinstance(current_hash, str):
            previous_hash = current_hash
        if terminal_seen:
            reasons.append(f"ndjson_event_after_terminal:{number}")
        if event.get("type") == "run.completed":
            terminal_seen = True
        if len(events) > binding.max_events:
            reasons.append("ndjson_event_count_exceeded")
            break
    if not events:
        reasons.append("ndjson_events_missing")
    if not terminal_seen:
        reasons.append("ndjson_terminal_sentinel_missing")
    return _result(events, reasons, raw)


def event_inactivity_status(elapsed_seconds: float, timeout_seconds: float) -> str | None:
    """Expose the fail-closed event-stream silence decision to supervision."""
    if timeout_seconds <= 0:
        raise ValueError("event_inactivity_timeout_invalid")
    return "event_inactivity_timeout" if elapsed_seconds >= timeout_seconds else None


def _validate_event(
    event: dict[str, Any],
    number: int,
    binding: EventBinding,
    previous_hash: str,
    seen_ids: set[str],
    reasons: list[str],
) -> None:
    for field in REQUIRED_EVENT_FIELDS:
        if field not in event:
            reasons.append(f"event_field_missing:{number}:{field}")
    if event.get("schema_version") != EVENT_SCHEMA_VERSION:
        reasons.append(f"event_schema_unknown:{number}")
    if not isinstance(event.get("sequence"), int) or event.get("sequence") != number:
        reasons.append(f"event_sequence_invalid:{number}")
    event_id = event.get("event_id")
    if not isinstance(event_id, str) or not event_id:
        reasons.append(f"event_id_invalid:{number}")
    elif event_id in seen_ids:
        reasons.append(f"event_id_duplicate:{number}")
    else:
        seen_ids.add(event_id)
    if event.get("type") not in EVENT_TYPES:
        reasons.append(f"event_type_unknown:{number}")
    if event.get("source") not in {"proxy", "fixture", "jcode"}:
        reasons.append(f"event_source_invalid:{number}")
    if not isinstance(event.get("payload"), dict):
        reasons.append(f"event_payload_invalid:{number}")
    for name, expected in (("task_id", binding.task_id), ("run_id", binding.run_id), ("correlation_id", binding.correlation_id), ("gate_id", binding.gate_id)):
        if event.get(name) != expected:
            reasons.append(f"event_binding_mismatch:{number}:{name}")
    if event.get("prev_event_hash") != previous_hash:
        reasons.append(f"event_prev_hash_invalid:{number}")
    if event.get("event_hash") != canonical_event_hash(event):
        reasons.append(f"event_hash_invalid:{number}")
    timestamp = event.get("timestamp")
    try:
        parsed = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError
    except ValueError:
        reasons.append(f"event_timestamp_invalid:{number}")


def _result(events: list[dict[str, Any]], reasons: list[str], raw: bytes) -> dict[str, Any]:
    return {
        "status": "evidence_ready" if not reasons else "EVIDENCE_INCOMPLETE",
        "events": events,
        "event_count": len(events),
        "raw_ndjson_sha256": hashlib.sha256(raw).hexdigest(),
        "blocked_reasons": sorted(set(reasons)),
        "executor_claim_is_terminal_truth": False,
    }
