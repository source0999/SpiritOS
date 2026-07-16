#!/usr/bin/env python3
"""Reject an incomplete or ambiguous Campaign 1 product-test registry."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
payload = json.loads((root / "docs/architecture/campaign-1-test-profiles.json").read_text())
profiles = payload.get("profiles") if isinstance(payload, dict) else None
required = {"continuity", "authority", "source-proxy-authority", "coding-backend", "coding-frontend", "prompt1-browser", "canonical-shell", "cartographer-api", "design-route", "spiritflix-operator", "build", "test-profile-registry", "target-adapter", "evidence-validator", "secret-scan", "anti-cheat", "undo-reset-rerun"}
seen = {entry.get("id") for entry in profiles if isinstance(entry, dict)} if isinstance(profiles, list) else set()
bad = []
for entry in profiles or []:
    if not isinstance(entry, dict) or not all(isinstance(entry.get(key), str) and entry[key].strip() for key in ("id", "product", "command", "claim_ceiling")):
        bad.append(entry.get("id", "<unknown>") if isinstance(entry, dict) else "<unknown>")
        continue
    if not isinstance(entry.get("mandatory"), bool):
        bad.append(entry["id"])
        continue
    receipt = entry.get("latest_accepted")
    if not isinstance(receipt, dict) or not isinstance(receipt.get("status"), str) or not receipt["status"].strip() or not isinstance(receipt.get("receipt_path"), str) or not receipt["receipt_path"].strip() or not isinstance(receipt.get("freshness"), str) or not receipt["freshness"].strip():
        bad.append(entry["id"])
        continue
    if entry["mandatory"] and receipt["status"] != "passed":
        bad.append(entry["id"])
missing = sorted(required - seen)
mandatory_missing = sorted(entry["id"] for entry in profiles or [] if isinstance(entry, dict) and entry.get("id") in required and entry.get("mandatory") is not True)
if payload.get("schema") != "spiritos-campaign-1-test-profiles/v1" or missing or bad or mandatory_missing:
    raise SystemExit("CAMPAIGN_1_TEST_PROFILES_INVALID " + json.dumps({"missing": missing, "invalid": bad, "mandatory_missing": mandatory_missing}))
print("CAMPAIGN_1_TEST_PROFILES_VALID")
