#!/usr/bin/env python3
"""Focused regression tests for the Campaign 3 completion evaluator."""
from __future__ import annotations

import copy

from campaign_3_control_plane import HISTORICAL_C3, completion_failures, repo_root, terminal_fixture


ROOT = repo_root()


def assert_fails(name: str, fixture: dict, expected_fragment: str) -> None:
    failures = completion_failures(ROOT, fixture)
    if not any(expected_fragment in failure for failure in failures):
        raise AssertionError(f"{name} did not fail with {expected_fragment}; got {failures}")


def main() -> int:
    current_failures = completion_failures(ROOT)
    if not current_failures or "go_not_true" not in current_failures:
        raise AssertionError(f"current incomplete state did not fail closed: {current_failures}")

    base = terminal_fixture(ROOT)
    terminal_failures = completion_failures(ROOT, base)
    if terminal_failures:
        raise AssertionError(f"correct terminal fixture failed: {terminal_failures}")

    malformed = copy.deepcopy(base)
    malformed["schema"] = "wrong"
    assert_fails("malformed state", malformed, "unsupported_state_schema")

    missing_gate = copy.deepcopy(base)
    missing_gate["completed_gate_ids"] = missing_gate["completed_gate_ids"][:-1]
    assert_fails("missing mandatory gate", missing_gate, "mandatory_gates_missing")

    missing_proving = copy.deepcopy(base)
    missing_proving["proving_task"]["real_lane_invocation"] = False
    assert_fails("missing proving-task proof", missing_proving, "proving_task_missing:real_lane_invocation")

    missing_failure = copy.deepcopy(base)
    missing_failure["controlled_failure_requirements"]["proven_failures"] = []
    assert_fails("missing controlled-failure proof", missing_failure, "controlled_failures_missing")

    missing_external = copy.deepcopy(base)
    missing_external["controlled_failure_requirements"]["proven_failures"] = [
        {"lane_id": "extended.scout-research", "recovered": True, "external_host_failure": False},
        {"lane_id": "extended.obsidian-knowledge", "recovered": True, "external_host_failure": False},
    ]
    assert_fails("missing external-host failure", missing_external, "external_host_failure_missing")

    missing_immutable = copy.deepcopy(base)
    missing_immutable["immutable_evidence_requirements"]["current_terminal_evidence_complete"] = False
    assert_fails("missing immutable-evidence proof", missing_immutable, "immutable_evidence_incomplete")

    missing_consumption = copy.deepcopy(base)
    missing_consumption["lane_consumption_requirements"]["all_retained_mandatory_outputs_consumed"] = False
    assert_fails("missing lane-consumption proof", missing_consumption, "lane_consumption_missing")

    stale_ledger = copy.deepcopy(base)
    stale_ledger["next_gate_id"] = "gate_3_9_genuine_all_lane_proving_task"
    assert_fails("stale ledger/state disagreement", stale_ledger, "next_gate_not_terminal")

    design_c3 = copy.deepcopy(base)
    design_c3["base"]["accepted_closeout_commit"] = HISTORICAL_C3
    assert_fails("historical design C3", design_c3, "historical_design_c3_cannot_satisfy_corrected_c3")

    print("CAMPAIGN_3_COMPLETION_REGRESSION_TESTS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

