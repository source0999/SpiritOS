#!/usr/bin/env python3
"""Focused regression tests for scope-aware planning validation."""
import importlib.util
from pathlib import Path


path = Path(__file__).with_name("validate-campaign-3-5-planning-transaction.py")
spec = importlib.util.spec_from_file_location("scope_validator", path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def result(*items):
    return module.evaluate_checks(list(items))


def transaction_failure(name):
    return module.check(name, "FAIL", "TRANSACTION", name, "test")


external = module.check("spiritflix", "FAIL", "EXTERNAL_DEPENDENCY_HEALTH", "protected ref mismatch", "test", applies=False, blocks_execution=True, component="SpiritFlix")
assert not result(transaction_failure("invalid_planning_json"))["planning_commit_allowed"]
assert not result(transaction_failure("benchmark_hash_mismatch"))["planning_commit_allowed"]
assert not result(transaction_failure("wrong_campaign_3_base"))["planning_commit_allowed"]
assert result(external)["planning_commit_allowed"]
assert not result(external)["spiritflix_dependent_execution_allowed"]
assert not result(external, transaction_failure("campaign_4_execution_gate"))["planning_commit_allowed"]
assert not result(external, transaction_failure("spiritflix_task_preflight"))["planning_commit_allowed"]
assert not result({"check_id": "missing_scope"})["planning_commit_allowed"]
assert not result({**external, "scope": "UNKNOWN"})["planning_commit_allowed"]
assert "spiritflix" in result(external)["external_dependency_failures"]
print("VALIDATION_SCOPE_POLICY_TESTS_PASS")
