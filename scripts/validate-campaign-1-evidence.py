#!/usr/bin/env python3
"""Fail closed when Campaign 1's redacted final evidence references disagree."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = json.loads((ROOT / "docs/architecture/campaign-1-state.json").read_text(encoding="utf-8"))
INDEX = (ROOT / "docs/architecture/campaign-1-evidence-index.md").read_text(encoding="utf-8")
LEDGER = (ROOT / "docs/architecture/campaign-1-ledger.md").read_text(encoding="utf-8")
RECEIPT = ROOT / "docs/evidence/e2e-loop/2026-07-15T23-36-28-866Z/result.json"

failures: list[str] = []
if not RECEIPT.is_file():
    failures.append("receipt_missing")
else:
    payload = json.loads(RECEIPT.read_text(encoding="utf-8"))
    truth = payload.get("authoritative_final_truth")
    if not isinstance(truth, dict) or truth.get("truth_status") != "GO" or truth.get("commit_safe") is not True:
        failures.append("receipt_not_go_commit_safe")
    required = truth.get("required_stages", {}) if isinstance(truth, dict) else {}
    if not isinstance(required, dict) or not required or any(not isinstance(stage, dict) or stage.get("evidence_complete") is not True for stage in required.values()):
        failures.append("receipt_required_stages_incomplete")
for text_name, text in (("index", INDEX), ("ledger", LEDGER)):
    if "GO_CAMPAIGN_1_COMPLETE" not in text or "docs/evidence/e2e-loop/2026-07-15T23-36-28-866Z/result.json" not in text:
        failures.append(f"{text_name}_final_reference_missing")
if STATE.get("go_eligible") is not True or STATE.get("closeout", {}).get("commit_safe") is not True:
    failures.append("state_not_final")
if failures:
    raise SystemExit("CAMPAIGN_1_EVIDENCE_INVALID " + ",".join(failures))
print("CAMPAIGN_1_EVIDENCE_VALID")
