#!/usr/bin/env python3
"""Scope-aware, read-only validation for the Campaign 3.5 planning transaction."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = "74ac367faf9a72c652061a5482c0180bb0b0c844"
REQUIRED = {"check_id", "status", "severity", "scope", "applies_to_current_transaction", "blocks_current_transaction", "blocks_campaign_execution", "affected_component", "affected_campaigns", "reason", "evidence", "remediation_plan", "operator_acknowledgement_required"}
SCOPES = {"TRANSACTION", "EXTERNAL_DEPENDENCY_HEALTH", "CAMPAIGN_EXECUTION_GATE"}


def check(check_id: str, status: str, scope: str, reason: str, evidence: str, *, applies: bool = True, blocks_execution: bool = False, component: str = "Campaign 3.5", campaigns: list[str] | None = None, remediation: str | None = None) -> dict:
    return {"check_id": check_id, "status": status, "severity": "ERROR" if status == "FAIL" else "INFO", "scope": scope, "applies_to_current_transaction": applies, "blocks_current_transaction": status == "FAIL" and scope == "TRANSACTION", "blocks_campaign_execution": blocks_execution, "affected_component": component, "affected_campaigns": campaigns or ["campaign-3.5"], "reason": reason, "evidence": evidence, "remediation_plan": remediation, "operator_acknowledgement_required": status == "FAIL"}


def evaluate_checks(checks: list[dict]) -> dict:
    normalized: list[dict] = []
    transaction_blockers: list[str] = []
    external_failures: list[str] = []
    for item in checks:
        missing = REQUIRED - set(item)
        unknown = item.get("scope") not in SCOPES
        if missing or unknown:
            item = check(item.get("check_id", "unclassified"), "FAIL", "TRANSACTION", "missing or unknown scope metadata defaults conservatively to blocking", item.get("evidence", "none"))
            item["blocks_current_transaction"] = True
        if item["status"] == "FAIL" and item["scope"] == "TRANSACTION":
            transaction_blockers.append(item["check_id"])
        if item["status"] == "FAIL" and item["scope"] == "EXTERNAL_DEPENDENCY_HEALTH":
            external_failures.append(item["check_id"])
        normalized.append(item)
    return {"transaction_checks_pass": not transaction_blockers, "external_dependency_checks_pass": not external_failures, "planning_commit_allowed": not transaction_blockers, "spiritflix_dependent_execution_allowed": not any(item["status"] == "FAIL" and item["affected_component"] == "SpiritFlix" for item in normalized), "checks": normalized, "transaction_blockers": transaction_blockers, "external_dependency_failures": external_failures}


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(ROOT), *args], text=True, capture_output=True, check=False)


def main() -> int:
    checks: list[dict] = []
    base_type = git("cat-file", "-t", BASE)
    base_relation = git("merge-base", "--is-ancestor", BASE, "HEAD")
    checks.append(check("corrected_campaign_3_base", "PASS" if base_type.stdout.strip() == "commit" and base_relation.returncode == 0 else "FAIL", "TRANSACTION", "corrected Campaign 3 base must be a readable ancestor", BASE))
    fsck = git("fsck", "--no-reflogs", "--full", "--strict")
    checks.append(check("planning_repository_integrity", "PASS" if fsck.returncode == 0 else "FAIL", "TRANSACTION", "strict planning-repository integrity", "git fsck --no-reflogs --full --strict"))
    try:
        plan = json.loads((ROOT / "docs/architecture/campaign-3.5/plan.json").read_text())
        pause = json.loads((ROOT / "docs/architecture/campaign-4-state.json").read_text())
        valid = plan["status"] == "PLANNED_AWAITING_OPERATOR_AUTHORIZATION" and pause["status"] == "PAUSED_FOR_CAMPAIGN_3_5_BACKEND_PROOF"
    except (OSError, KeyError, json.JSONDecodeError):
        valid = False
    checks.append(check("campaign_plan_and_pause_state", "PASS" if valid else "FAIL", "TRANSACTION", "Campaign 3.5 must be planned and Campaign 4 paused", "docs/architecture/campaign-3.5/plan.json; docs/architecture/campaign-4-state.json"))
    benchmark = subprocess.run([sys.executable, str(ROOT / "scripts/validate-campaign-3-5-benchmark.py")], text=True, capture_output=True, check=False)
    checks.append(check("benchmark_static_validation", "PASS" if benchmark.returncode == 0 else "FAIL", "TRANSACTION", "immutable operator benchmark must pass static validation", "scripts/validate-campaign-3-5-benchmark.py"))
    drift = json.loads((ROOT / "docs/architecture/campaign-1-2-continuity-drift-20260719.json").read_text())
    checks.append(check("spiritflix_campaign_1_2_continuity", "FAIL", "EXTERNAL_DEPENDENCY_HEALTH", drift["actual_relation"] + "; " + drift["strict_fsck"], "docs/architecture/campaign-1-2-continuity-drift-20260719.json", applies=False, blocks_execution=True, component="SpiritFlix", campaigns=["campaign-1", "campaign-2", "campaign-3.5", "campaign-4"], remediation="docs/architecture/spiritflix-continuity-repair-plan-20260719.md"))
    result = evaluate_checks(checks)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["planning_commit_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
