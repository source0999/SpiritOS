#!/usr/bin/env python3
"""Reject an incomplete or unaccepted Campaign 2 test-profile registry."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/architecture/campaign-2-test-profiles.json"
REQUIRED = {"continuity", "authority", "lane-contracts", "orchestrator", "authority-evidence", "cartographer-handoff", "lane-recovery", "shell-observability", "proving-task"}


def main() -> int:
    try:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"CAMPAIGN_2_TEST_PROFILES_INVALID registry_unreadable:{error}")
        return 1
    profiles = payload.get("profiles") if isinstance(payload, dict) else None
    seen = {entry.get("id") for entry in profiles if isinstance(entry, dict)} if isinstance(profiles, list) else set()
    invalid: list[str] = []
    for entry in profiles or []:
        if not isinstance(entry, dict) or not all(isinstance(entry.get(field), str) and entry[field].strip() for field in ("id", "product", "command", "claim_ceiling")):
            invalid.append(entry.get("id", "<unknown>") if isinstance(entry, dict) else "<unknown>")
            continue
        receipt = entry.get("latest_accepted")
        if not isinstance(entry.get("mandatory"), bool) or not isinstance(receipt, dict) or not all(isinstance(receipt.get(field), str) and receipt[field].strip() for field in ("status", "receipt_path", "freshness")):
            invalid.append(entry["id"])
        elif entry["mandatory"] and receipt["status"] != "passed":
            invalid.append(entry["id"])
    missing = sorted(REQUIRED - seen)
    if payload.get("schema") != "spiritos-campaign-2-test-profiles/v1" or missing or invalid:
        print("CAMPAIGN_2_TEST_PROFILES_INVALID " + json.dumps({"missing": missing, "invalid": invalid}))
        return 1
    print("CAMPAIGN_2_TEST_PROFILES_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
