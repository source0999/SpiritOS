"""Gate 2-J.9D strict NDJSON bridge proofs using deterministic event fixtures."""
from __future__ import annotations

import copy
import json

import pytest

from source_proxy.jcode.evidence import seal_strict_event_evidence
from source_proxy.jcode.event_schema import (
    EventBinding,
    canonical_event_hash,
    event_inactivity_status,
    parse_strict_event_stream,
)


def _binding(**kwargs) -> EventBinding:
    return EventBinding(task_id="task-1", run_id="run-1", correlation_id="corr-1", **kwargs)


def _event(sequence: int, event_type: str, previous: str = "") -> dict:
    event = {
        "schema_version": "source-proxy.jcode-event/v1", "event_id": f"event-{sequence}",
        "sequence": sequence, "timestamp": "2026-07-29T22:00:00Z", "task_id": "task-1",
        "run_id": "run-1", "correlation_id": "corr-1", "gate_id": "2-J.9D",
        "type": event_type, "source": "fixture", "payload": {"n": sequence},
        "prev_event_hash": previous,
    }
    event["event_hash"] = canonical_event_hash(event)
    return event


def _valid() -> bytes:
    first = _event(1, "process.started")
    second = _event(2, "evidence.sealed", first["event_hash"])
    final = _event(3, "run.completed", second["event_hash"])
    return b"".join(json.dumps(item, sort_keys=True, separators=(",", ":")).encode() + b"\n" for item in (first, second, final))


def test_valid_stream_is_reproducible_and_never_terminal_truth() -> None:
    raw = _valid()
    result = parse_strict_event_stream(raw, _binding())
    assert result["status"] == "evidence_ready"
    assert result["event_count"] == 3
    assert result["executor_claim_is_terminal_truth"] is False
    assert result == parse_strict_event_stream(raw, _binding())


@pytest.mark.parametrize(
    "mutate, reason",
    [
        (lambda raw: b"not-json\n", "ndjson_invalid_json:1"),
        (lambda raw: raw[:-1], "ndjson_partial_final_line"),
        (lambda raw: b"\xff\n", "ndjson_invalid_utf8"),
        (lambda raw: raw.replace(b'"event-2"', b'"event-1"'), "event_id_duplicate:2"),
        (lambda raw: raw.replace(b'"sequence":2', b'"sequence":1'), "event_sequence_invalid:2"),
        (lambda raw: raw.replace(b'"evidence.sealed"', b'"unknown.event"'), "event_type_unknown:2"),
        (lambda raw: raw.replace(b'"source-proxy.jcode-event/v1"', b'"unknown/v1"', 1), "event_schema_unknown:1"),
        (lambda raw: raw.replace(b'"task-1"', b'"wrong-task"', 1), "event_binding_mismatch:1:task_id"),
        (lambda raw: raw.replace(b'"prev_event_hash":"', b'"prev_event_hash":"bad', 1), "event_hash_invalid:1"),
        (lambda raw: raw.replace(b'"event_hash":"', b'"event_hash":"bad', 1), "event_hash_invalid:1"),
        (lambda raw: raw.rsplit(b"\n", 2)[0] + b"\n", "ndjson_terminal_sentinel_missing"),
        (lambda raw: raw + _valid().splitlines()[0] + b"\n", "ndjson_event_after_terminal:4"),
        (lambda raw: b"x" * 300_000 + b"\n", "ndjson_oversized_line:1"),
    ],
)
def test_controlled_invalid_streams_fail_closed(mutate, reason: str) -> None:
    binding = _binding()
    result = parse_strict_event_stream(mutate(_valid()), binding)
    assert result["status"] == "EVIDENCE_INCOMPLETE"
    assert reason in result["blocked_reasons"]


def test_missing_field_count_limit_and_total_limit_fail_closed() -> None:
    event = _event(1, "run.completed")
    del event["payload"]
    event["event_hash"] = canonical_event_hash(event)
    missing = parse_strict_event_stream(json.dumps(event).encode() + b"\n", _binding())
    assert "event_field_missing:1:payload" in missing["blocked_reasons"]
    count = parse_strict_event_stream(_valid(), _binding(max_events=2))
    assert "ndjson_event_count_exceeded" in count["blocked_reasons"]
    total = parse_strict_event_stream(_valid(), _binding(max_total_bytes=8))
    assert "ndjson_total_bytes_exceeded" in total["blocked_reasons"]


def test_payload_tamper_and_stdout_contamination_do_not_pass() -> None:
    raw = _valid()
    tampered = raw.replace(b'"n":2', b'"n":99')
    result = parse_strict_event_stream(tampered, _binding())
    assert "event_hash_invalid:2" in result["blocked_reasons"]
    contaminated = parse_strict_event_stream(b"stdout text\n" + raw, _binding())
    assert "ndjson_invalid_json:1" in contaminated["blocked_reasons"]


def test_event_inactivity_and_evidence_write_failure_fail_closed(tmp_path) -> None:
    assert event_inactivity_status(2, 1) == "event_inactivity_timeout"
    valid = parse_strict_event_stream(_valid(), _binding())
    failed = seal_strict_event_evidence(valid, tmp_path / "missing" / "event.json")
    assert failed["evidence_sealed"] is False
    assert "event_evidence_write_failed" in failed["blocked_reasons"]
