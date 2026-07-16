#!/usr/bin/env python3
"""Fail closed when Campaign 1's redacted final evidence references disagree."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = json.loads((ROOT / "docs/architecture/campaign-1-state.json").read_text(encoding="utf-8"))
TEXT_ARTIFACTS = {
    "plan": ROOT / "docs/architecture/campaign-1-plan.md",
    "ledger": ROOT / "docs/architecture/campaign-1-ledger.md",
    "evidence_index": ROOT / "docs/architecture/campaign-1-evidence-index.md",
    "profiles": ROOT / "docs/architecture/campaign-1-test-profiles.md",
    "authority_inventory": ROOT / "docs/architecture/campaign-1-authority-inventory.md",
    "glm_handoff": ROOT / "docs/architecture/campaign-1-glm-handoff.md",
    "recovery_record": ROOT / "docs/architecture/campaign-1-recovery-record.md",
}
TEXT = {name: path.read_text(encoding="utf-8") for name, path in TEXT_ARTIFACTS.items()}
PROFILES = json.loads((ROOT / "docs/architecture/campaign-1-test-profiles.json").read_text(encoding="utf-8"))
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
for text_name, text in TEXT.items():
    if "GO_CAMPAIGN_1_COMPLETE" not in text:
        failures.append(f"{text_name}_final_verdict_missing")
for text_name in ("ledger", "evidence_index", "profiles", "authority_inventory", "glm_handoff"):
    if "Campaign 2" not in TEXT[text_name] or "not started" not in TEXT[text_name]:
        failures.append(f"{text_name}_campaign2_guard_missing")
if "docs/evidence/e2e-loop/2026-07-15T23-36-28-866Z/result.json" not in TEXT["ledger"] or "docs/evidence/e2e-loop/2026-07-15T23-36-28-866Z/result.json" not in TEXT["evidence_index"]:
    failures.append("final_receipt_reference_missing")
if "## Current checkpoint" in TEXT["ledger"] or "GO eligibility: `false`" in TEXT["ledger"] or "Phase: **Phase 3**" in TEXT["ledger"]:
    failures.append("ledger_stale_current_claim")
closeout = STATE.get("closeout", {})
if STATE.get("go_eligible") is not True or closeout.get("commit_safe") is not True or closeout.get("critical_blocker") is not None or closeout.get("campaign2_started") is not False:
    failures.append("state_not_final")
if PROFILES.get("schema") != "spiritos-campaign-1-test-profiles/v1" or not isinstance(PROFILES.get("profiles"), list):
    failures.append("profile_registry_invalid")
else:
    profile_ids = {profile.get("id") for profile in PROFILES["profiles"] if isinstance(profile, dict)}
    required_ids = {"continuity", "authority", "source-proxy-authority", "coding-backend", "coding-frontend", "canonical-shell", "cartographer-api", "design-route", "spiritflix-operator", "build", "test-profile-registry", "target-adapter", "evidence-validator", "secret-scan", "prompt1-browser", "anti-cheat", "undo-reset-rerun"}
    if not required_ids.issubset(profile_ids):
        failures.append("profile_registry_missing_final_ids")
if failures:
    raise SystemExit("CAMPAIGN_1_EVIDENCE_INVALID " + ",".join(failures))
print("CAMPAIGN_1_EVIDENCE_VALID")
