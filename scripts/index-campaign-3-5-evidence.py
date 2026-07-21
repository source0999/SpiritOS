#!/usr/bin/env python3
"""Index Campaign 3.5 receipts without reading or exposing private model text."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


RECEIPT_SCHEMA = "campaign-3.5-run-receipt/v1"
INDEX_SCHEMA = "campaign-3.5-forensic-index/v1"


def _classification(receipt: dict[str, Any]) -> str:
    reason = str(receipt.get("runner_reason") or "")
    response_format = str(receipt.get("adapter", {}).get("model_response_format") or "")
    if receipt.get("benchmark_passed") is True:
        return "BENCHMARK_PASSED"
    if "Timeout" in reason:
        return "PROVIDER_TIMEOUT"
    if "ExternalGate" in reason:
        return "MODEL_AUTHORITY_OR_GATE_FAILURE"
    if "diff_check_failed" in reason:
        return "ADAPTER_PATCH_VALIDATION_FAILED"
    if response_format == "structured_edits_python_syntax_invalid":
        return "MODEL_STRUCTURED_EDIT_SYNTAX_INVALID"
    if "model_diff_invalid" in reason:
        return "MODEL_RESPONSE_NOT_APPLICABLE"
    if response_format:
        return "MODEL_OR_ADAPTER_FAILURE_UNSPECIFIED"
    return "EXECUTION_FAILURE_UNSPECIFIED"


def _raw_available(receipt: dict[str, Any]) -> bool:
    raw = receipt.get("raw_model_output")
    return isinstance(raw, dict) and raw.get("captured_privately") is True


def _receipt_records(roots: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for root in roots:
        for path in sorted(root.rglob("*.json")):
            try:
                raw = path.read_bytes()
                receipt = json.loads(raw)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            if not isinstance(receipt, dict) or receipt.get("schema_version") != RECEIPT_SCHEMA:
                continue
            adapter = receipt.get("adapter") if isinstance(receipt.get("adapter"), dict) else {}
            records.append(
                {
                    "receipt_sha256": hashlib.sha256(raw).hexdigest(),
                    "receipt_name": path.name,
                    "recorded_at": receipt.get("recorded_at"),
                    "task_id": receipt.get("task_id"),
                    "model_alias": receipt.get("model_alias"),
                    "provider": adapter.get("provider"),
                    "model": adapter.get("model"),
                    "transport_kind": adapter.get("transport_kind"),
                    "call_count": adapter.get("call_count"),
                    "model_response_format": adapter.get("model_response_format"),
                    "runner_reason": receipt.get("runner_reason"),
                    "final_disposition": receipt.get("final_disposition"),
                    "benchmark_passed": receipt.get("benchmark_passed"),
                    "raw_output_available": _raw_available(receipt),
                    "failure_classification": _classification(receipt),
                }
            )
    return sorted(records, key=lambda record: (str(record["recorded_at"]), record["receipt_name"]))


def _write_private_safe(path: Path, value: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write(value)
        os.chmod(temporary_name, 0o600)
        os.replace(temporary_name, path)
        os.chmod(path, 0o600)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def _markdown(index: dict[str, Any]) -> str:
    counts = index["summary"]["failure_classifications"]
    lines = [
        "# Campaign 3.5 provider forensic index",
        "",
        "This index is receipt-derived. It does not reconstruct or infer missing raw model output.",
        "",
        f"Receipts indexed: {index['summary']['receipt_count']}; raw outputs available: {index['summary']['raw_output_available_count']}.",
        "",
        "| Task | Alias | Resolved model | Calls | Response format | Classification | Raw output |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for record in index["records"]:
        lines.append(
            "| {task_id} | {model_alias} | {model} | {call_count} | {model_response_format} | {failure_classification} | {raw} |".format(
                **record,
                raw="private capture available" if record["raw_output_available"] else "not retained",
            )
        )
    lines.extend(["", "## Classification counts", ""])
    lines.extend(f"- {name}: {count}" for name, count in sorted(counts.items()))
    lines.extend(
        [
            "",
            "Historical receipts without private capture remain a forensic evidence gap. They support only the recorded adapter/runner outcome and response-format field; no claim about the omitted model text is made.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", action="append", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    records = _receipt_records(args.evidence_root)
    classifications = Counter(str(record["failure_classification"]) for record in records)
    index = {
        "schema_version": INDEX_SCHEMA,
        "evidence_roots": [str(root) for root in args.evidence_root],
        "summary": {
            "receipt_count": len(records),
            "raw_output_available_count": sum(bool(record["raw_output_available"]) for record in records),
            "failure_classifications": dict(sorted(classifications.items())),
            "historical_raw_output_limit": "Raw text is unavailable unless a receipt explicitly records private capture.",
        },
        "records": records,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(args.output_dir, 0o700)
    _write_private_safe(args.output_dir / "campaign-3-5-forensic-index-v1.json", json.dumps(index, indent=2, sort_keys=True) + "\n")
    _write_private_safe(args.output_dir / "campaign-3-5-forensic-index-v1.md", _markdown(index))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
