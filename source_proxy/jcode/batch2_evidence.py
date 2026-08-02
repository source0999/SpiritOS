"""Fail-closed per-run evidence contract for the Batch 2 remediation."""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any, Mapping
from source_proxy.jcode.canonical_io import canonical_bytes, sha256_bytes

EVIDENCE_COMPLETE = "EVIDENCE_COMPLETE"
EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
RUN_REJECTED = "RUN_REJECTED"
REQUIRED_JSON = ("authorization.json", "task_manifest.json", "model_binding.json", "packet.json", "request.json", "raw_response.json", "tool_schema.json", "tool_parse_receipt.json", "tool_ledger.json", "observation_ledger.json", "model_request_receipt.json", "evaluation_receipt.json", "diff_receipt.json")
HASHED_PAYLOADS = ("packet", "request", "raw_response")
REQUIRED_RECEIPT_FIELDS = ("run_id", "task_id", "gate", "harness", "model_registry_id", "full_digest", "provider_reported_identity", "packet_sha256", "request_sha256", "request_started_at", "request_ended_at", "turn_count", "tool_calls", "observations_reinjected", "final_output", "timeout_or_cancellation", "diff", "evaluator_outcome", "request_budget_counter", "evidence_completeness")
class EvidenceContractError(ValueError): pass
def _write_json(path: Path, value: Any) -> bytes:
    raw = canonical_bytes(value); path.write_bytes(raw); return raw
def seal_run(root: Path, run_id: str, records: Mapping[str, Any]) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,79}", run_id): raise EvidenceContractError("invalid_run_id")
    missing = [n for n in REQUIRED_JSON if n.removesuffix(".json") not in records]
    if missing: raise EvidenceContractError("missing_required_artifacts:" + ",".join(missing))
    receipt = records.get("run_receipt")
    if not isinstance(receipt, Mapping): raise EvidenceContractError("run_receipt_missing")
    absent = [n for n in REQUIRED_RECEIPT_FIELDS if n not in receipt]
    if absent: raise EvidenceContractError("run_receipt_fields_missing:" + ",".join(absent))
    if receipt["run_id"] != run_id or receipt["evidence_completeness"] != EVIDENCE_COMPLETE: raise EvidenceContractError("run_receipt_identity_or_status_invalid")
    path = root / run_id
    if path.exists(): raise EvidenceContractError("duplicate_run_id")
    path.mkdir(parents=True)
    hashes = {}
    for filename in REQUIRED_JSON:
        key = filename.removesuffix(".json"); raw = _write_json(path / filename, records[key])
        if key in HASHED_PAYLOADS:
            hashes[key] = sha256_bytes(raw); (path / f"{key}.sha256").write_text(hashes[key] + "\n", encoding="ascii")
    if receipt["packet_sha256"] != hashes["packet"] or receipt["request_sha256"] != hashes["request"]: raise EvidenceContractError("receipt_payload_hash_mismatch")
    _write_json(path / "run_receipt.json", dict(receipt))
    if verify_run(path)["status"] != EVIDENCE_COMPLETE: raise EvidenceContractError("self_verification_failed")
    return path
def verify_run(path: Path) -> dict[str, Any]:
    required = (*REQUIRED_JSON, "run_receipt.json", *(f"{n}.sha256" for n in HASHED_PAYLOADS))
    missing = [n for n in required if not (path / n).is_file()]
    if missing: return {"status": EVIDENCE_INCOMPLETE, "reasons": ["missing:" + ",".join(sorted(missing))]}
    try: receipt = json.loads((path / "run_receipt.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError: return {"status": RUN_REJECTED, "reasons": ["run_receipt_invalid_json"]}
    absent = [n for n in REQUIRED_RECEIPT_FIELDS if n not in receipt]
    if absent: return {"status": EVIDENCE_INCOMPLETE, "reasons": ["receipt_fields_missing:" + ",".join(absent)]}
    reasons = []
    for name in HASHED_PAYLOADS:
        actual = sha256_bytes((path / f"{name}.json").read_bytes())
        if (path / f"{name}.sha256").read_text(encoding="ascii").strip() != actual: reasons.append(f"{name}_hash_mismatch")
        if name != "raw_response" and receipt[f"{name}_sha256"] != actual: reasons.append(f"{name}_receipt_hash_mismatch")
    binding = json.loads((path / "model_binding.json").read_text(encoding="utf-8"))
    if binding.get("digest") != receipt["full_digest"]: reasons.append("digest_mismatch")
    if binding.get("model") != receipt["model_registry_id"]: reasons.append("model_mismatch")
    if not isinstance(receipt["request_budget_counter"], int) or receipt["request_budget_counter"] < 1: reasons.append("request_count_mismatch")
    if receipt["evidence_completeness"] != EVIDENCE_COMPLETE: reasons.append("receipt_not_complete")
    return {"status": EVIDENCE_COMPLETE if not reasons else EVIDENCE_INCOMPLETE, "reasons": reasons}