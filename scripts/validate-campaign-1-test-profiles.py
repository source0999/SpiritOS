#!/usr/bin/env python3
"""Reject an incomplete or ambiguous Campaign 1 product-test registry."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
payload = json.loads((root / "docs/architecture/campaign-1-test-profiles.json").read_text())
profiles = payload.get("profiles") if isinstance(payload, dict) else None
required = {"continuity", "authority", "source-proxy-authority", "coding-backend", "coding-frontend", "prompt1-browser", "canonical-shell", "cartographer-api", "design-route", "spiritflix-operator", "build"}
seen = {entry.get("id") for entry in profiles if isinstance(entry, dict)} if isinstance(profiles, list) else set()
bad = [entry.get("id", "<unknown>") for entry in profiles or [] if not isinstance(entry, dict) or not all(isinstance(entry.get(key), str) and entry[key].strip() for key in ("id", "product", "command", "claim_ceiling"))]
missing = sorted(required - seen)
if payload.get("schema") != "spiritos-campaign-1-test-profiles/v1" or missing or bad:
    raise SystemExit("CAMPAIGN_1_TEST_PROFILES_INVALID " + json.dumps({"missing": missing, "invalid": bad}))
print("CAMPAIGN_1_TEST_PROFILES_VALID")
