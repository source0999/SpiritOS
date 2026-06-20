from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


HARDLINE_STATUS_VERSION = "source-proxy-plan2-hardline-status-v1"

HardlineIntegrationStatus = Literal[
    "INTEGRATED_LIVE",
    "NOT_INTEGRATED_PREVIEW_ONLY",
    "NOT_INTEGRATED_ADVISORY_ONLY",
    "NOT_INTEGRATED_STATUS_ONLY",
    "NOT_INTEGRATED_READ_ONLY_FOR_ACTION",
    "NOT_INTEGRATED_UNCONSUMED_OUTPUT",
    "NOT_INTEGRATED_MOCK_ONLY",
    "NOT_INTEGRATED_FIXTURE_ONLY",
    "BLOCKED_ENV",
    "BLOCKED_HUMAN",
    "NEEDS_FIX",
]

NON_GO_STATUSES = {
    "NOT_INTEGRATED_PREVIEW_ONLY",
    "NOT_INTEGRATED_ADVISORY_ONLY",
    "NOT_INTEGRATED_STATUS_ONLY",
    "NOT_INTEGRATED_READ_ONLY_FOR_ACTION",
    "NOT_INTEGRATED_UNCONSUMED_OUTPUT",
    "NOT_INTEGRATED_MOCK_ONLY",
    "NOT_INTEGRATED_FIXTURE_ONLY",
    "BLOCKED_ENV",
    "BLOCKED_HUMAN",
    "NEEDS_FIX",
}

GO_LIKE_WORDS = {"GO", "productive_go", "integrated", "ready"}


@dataclass(frozen=True)
class HardlineProofInput:
    invoked_by_canonical_workflow: bool
    real_upstream_state: bool
    live_function_performed: bool
    output_consumed_downstream: bool
    failure_changes_outcome: bool
    causal_trace_recorded: bool
    focused_tests: bool
    live_proof: bool
    active_surface_visible: bool
    preview_only: bool = False
    advisory_only: bool = False
    status_only: bool = False
    read_only_for_action_subsystem: bool = False
    mock_only: bool = False
    fixture_only: bool = False
    blocked_env: bool = False
    blocked_human: bool = False
    needs_fix: bool = False


def classify_hardline_integration(proof: HardlineProofInput) -> HardlineIntegrationStatus:
    if proof.blocked_human:
        return "BLOCKED_HUMAN"
    if proof.blocked_env:
        return "BLOCKED_ENV"
    if proof.needs_fix:
        return "NEEDS_FIX"
    if proof.preview_only:
        return "NOT_INTEGRATED_PREVIEW_ONLY"
    if proof.advisory_only:
        return "NOT_INTEGRATED_ADVISORY_ONLY"
    if proof.status_only:
        return "NOT_INTEGRATED_STATUS_ONLY"
    if proof.read_only_for_action_subsystem:
        return "NOT_INTEGRATED_READ_ONLY_FOR_ACTION"
    if proof.mock_only:
        return "NOT_INTEGRATED_MOCK_ONLY"
    if proof.fixture_only:
        return "NOT_INTEGRATED_FIXTURE_ONLY"
    if not proof.output_consumed_downstream:
        return "NOT_INTEGRATED_UNCONSUMED_OUTPUT"
    required = (
        proof.invoked_by_canonical_workflow,
        proof.real_upstream_state,
        proof.live_function_performed,
        proof.output_consumed_downstream,
        proof.failure_changes_outcome,
        proof.causal_trace_recorded,
        proof.focused_tests,
        proof.live_proof,
        proof.active_surface_visible,
    )
    if all(required):
        return "INTEGRATED_LIVE"
    return "NEEDS_FIX"


def hardline_status_allows_go(status: str) -> bool:
    return status == "INTEGRATED_LIVE"


def reject_go_like_label(status: str, proposed_label: str) -> bool:
    return status in NON_GO_STATUSES and proposed_label in GO_LIKE_WORDS


def plan2_final_go_allowed(
    *,
    mac_write_integration: str,
    mac_search_check_integration: str,
    research_integration: str,
    specialist_lane_integration: str,
    task_a: str,
    task_b: str,
    task_c: str,
    operator_check: str,
    focused_tests: str,
    preview_go_detected: bool,
    advisory_go_detected: bool,
    status_only_go_detected: bool,
    read_only_action_go_detected: bool,
    mock_go_detected: bool,
    fixture_only_go_detected: bool,
    plan_3_started: bool,
) -> bool:
    return (
        mac_write_integration == "INTEGRATED_LIVE"
        and mac_search_check_integration == "INTEGRATED_LIVE"
        and research_integration == "INTEGRATED_LIVE"
        and specialist_lane_integration == "INTEGRATED_LIVE"
        and task_a == "PASS"
        and task_b == "PASS"
        and task_c == "PASS"
        and operator_check == "PASS"
        and focused_tests == "PASS"
        and not preview_go_detected
        and not advisory_go_detected
        and not status_only_go_detected
        and not read_only_action_go_detected
        and not mock_go_detected
        and not fixture_only_go_detected
        and not plan_3_started
    )
