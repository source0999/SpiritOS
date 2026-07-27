from __future__ import annotations

import json

from source_proxy.jcode.adapter import JCODE_EXECUTION_RESULT_FIELDS
from source_proxy.jcode.evidence import map_jcode_ndjson_evidence


def _complete_stream() -> bytes:
    result = {field: [] for field in JCODE_EXECUTION_RESULT_FIELDS}
    result.update({"task_id": "task-1", "correlation_id": "corr-1", "actual_model": "qwen2.5-coder:7b"})
    return b"\n".join(
        [
            json.dumps({"sequence": 1, "type": "run.started"}).encode(),
            json.dumps({"sequence": 2, "type": "tool.completed"}).encode(),
            json.dumps({"sequence": 3, "type": "run.completed", "result": result}).encode(),
        ]
    )


def test_complete_ndjson_maps_evidence_without_terminal_authority() -> None:
    mapped = map_jcode_ndjson_evidence(_complete_stream())

    assert mapped["status"] == "evidence_ready"
    assert mapped["event_count"] == 3
    assert mapped["executor_claim_is_terminal_truth"] is False
    assert "terminal_truth" in mapped["proxy_independent_determination_required"]


def test_gap_missing_terminal_and_missing_field_fail_closed() -> None:
    raw = b'{"sequence":2,"type":"run.started"}\n{"sequence":3,"type":"run.completed","result":{}}'
    mapped = map_jcode_ndjson_evidence(raw)

    assert mapped["status"] == "EVIDENCE_INCOMPLETE"
    assert "ndjson_sequence_invalid:1" in mapped["blocked_reasons"]
    assert "jcode_result_field_missing:actual_model" in mapped["blocked_reasons"]


def test_invalid_json_and_terminal_absence_fail_closed() -> None:
    mapped = map_jcode_ndjson_evidence(b'{bad}\n{"sequence":1,"type":"run.started"}')

    assert mapped["status"] == "EVIDENCE_INCOMPLETE"
    assert "ndjson_invalid_json:1" in mapped["blocked_reasons"]
    assert "ndjson_terminal_sentinel_missing" in mapped["blocked_reasons"]
