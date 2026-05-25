from __future__ import annotations

from pathlib import Path
from typing import Any

from source_proxy.cartographer.live_state import build_cartographer_truth_packet
from source_proxy.cartographer.proxy_consultation import (
    FALSE_CONSULTATION_AUTHORITY,
    consult_cartographer_for_proxy_action,
)


REQUIRED_PROXY_QUESTIONS = [
    "Lane Status",
    "Dirty Tree Risk",
    "Protected Path Conflicts",
    "Approval Requirements",
    "Verification Requirements",
    "Active Lane Ownership",
    "Safe Next Action",
]

REQUIRED_RESPONSE_OUTCOMES = [
    "`go`",
    "`no_go`",
    "`needs_approval`",
    "`needs_verification`",
    "`dirty_tree_blocked`",
    "`ownership_conflict`",
    "`cartographer_unavailable`",
]


def test_consultation_contract_documents_required_questions_and_outcomes() -> None:
    contract = Path("docs/cartographer-proxy-consultation-contract-v0.1.md").read_text(
        encoding="utf-8",
    )

    for question in REQUIRED_PROXY_QUESTIONS:
        assert question in contract
    for outcome in REQUIRED_RESPONSE_OUTCOMES:
        assert outcome in contract
    assert "`cartographer_unavailable`" in contract
    assert "Cartographer unavailable; default NO-GO." in contract
    assert "`apply`: false" in contract
    assert "`commit`: false" in contract
    assert "`push`: false" in contract
    assert "`queue`: false" in contract
    assert "`worker`: false" in contract


def test_proxy_consultation_contract_fails_closed_when_cartographer_is_unavailable() -> None:
    response = _future_proxy_consultation_response(None)

    assert response["outcome"] == "cartographer_unavailable"
    assert response["go"] is False
    assert response["summary"] == "Cartographer unavailable; default NO-GO."
    assert response["safe_next_action"] == "Stop and inspect Cartographer status manually."
    assert response["authority"] == FALSE_CONSULTATION_AUTHORITY
    assert "cartographer_unavailable" in response["reason_codes"]


def test_proxy_consultation_contract_keeps_malformed_packets_blocked() -> None:
    response = _future_proxy_consultation_response({"status": "clear"})

    assert response["outcome"] == "cartographer_unavailable"
    assert response["go"] is False
    assert response["authority"] == FALSE_CONSULTATION_AUTHORITY
    assert "truth_packet_malformed" in response["reason_codes"]


def test_proxy_consultation_contract_keeps_no_go_truth_packet_blocked() -> None:
    packet = build_cartographer_truth_packet(
        {
            "current_branch": None,
            "current_head": None,
            "tracked_dirty_files": [],
            "untracked_files": [],
            "protected_lane_matches": [],
            "coding_files_dirty": False,
            "map_files_dirty": False,
            "package_config_env_files_dirty": False,
            "source_proxy_runtime_files_dirty": False,
            "unknown_unclassified_dirty_files": [],
            "recommended_safety_state": "blocked",
            "blocker_reasons": ["git command failed closed: git status"],
            "collected_at": "2026-05-24T00:00:00Z",
            "no_mutation_guarantee": {"mutates_files": False},
            "git_available": False,
            "git_errors": [{"command": ["git", "status"], "returncode": 2}],
        },
    )
    response = _future_proxy_consultation_response(packet)

    assert packet["status"] == "no_go"
    assert response["outcome"] == "cartographer_unavailable"
    assert response["go"] is False
    assert response["authority"] == FALSE_CONSULTATION_AUTHORITY
    assert "cartographer_status_no_go" in response["reason_codes"]


def test_proxy_consultation_contract_blocks_dirty_protected_lane_packets() -> None:
    packet = build_cartographer_truth_packet(
        {
            "current_branch": "main",
            "current_head": "abc123",
            "tracked_dirty_files": ["src/app/coding/page.tsx"],
            "untracked_files": [],
            "protected_lane_matches": [
                {"path": "src/app/coding/page.tsx", "lane": "coding"},
            ],
            "coding_files_dirty": True,
            "map_files_dirty": False,
            "package_config_env_files_dirty": False,
            "source_proxy_runtime_files_dirty": False,
            "unknown_unclassified_dirty_files": [],
            "recommended_safety_state": "blocked",
            "blocker_reasons": ["/coding files are dirty"],
            "collected_at": "2026-05-24T00:00:00Z",
            "no_mutation_guarantee": {"mutates_files": False},
            "git_available": True,
            "git_errors": [],
        },
    )
    packet["protected_lane_matches"] = [
        {"path": "src/app/coding/page.tsx", "lane": "coding"},
    ]

    response = _future_proxy_consultation_response(packet)

    assert packet["status"] == "blocked"
    assert response["outcome"] == "dirty_tree_blocked"
    assert response["go"] is False
    assert response["blocked_paths"] == ["src/app/coding/page.tsx"]
    assert response["authority"] == FALSE_CONSULTATION_AUTHORITY
    assert "protected_path_conflict" in response["reason_codes"]


def test_proxy_consultation_contract_treats_clear_packet_as_advisory_only() -> None:
    packet = build_cartographer_truth_packet(
        {
            "current_branch": "main",
            "current_head": "abc123",
            "tracked_dirty_files": [],
            "untracked_files": [],
            "protected_lane_matches": [],
            "coding_files_dirty": False,
            "map_files_dirty": False,
            "package_config_env_files_dirty": False,
            "source_proxy_runtime_files_dirty": False,
            "unknown_unclassified_dirty_files": [],
            "recommended_safety_state": "clear",
            "blocker_reasons": [],
            "collected_at": "2026-05-24T00:00:00Z",
            "no_mutation_guarantee": {"mutates_files": False},
            "git_available": True,
            "git_errors": [],
        },
    )

    response = _future_proxy_consultation_response(packet)

    assert packet["status"] == "clear"
    assert response["outcome"] == "go"
    assert response["go"] is False
    assert response["summary"] == "Clear for read-only planning only."
    assert response["authority"] == FALSE_CONSULTATION_AUTHORITY
    assert response["reason_codes"] == ["advisory_read_only"]


def test_proxy_consultation_adapter_blocks_apply_capable_work_without_approval() -> None:
    packet = build_cartographer_truth_packet(
        {
            "current_branch": "main",
            "current_head": "abc123",
            "tracked_dirty_files": [],
            "untracked_files": [],
            "protected_lane_matches": [],
            "coding_files_dirty": False,
            "map_files_dirty": False,
            "package_config_env_files_dirty": False,
            "source_proxy_runtime_files_dirty": False,
            "unknown_unclassified_dirty_files": [],
            "recommended_safety_state": "clear",
            "blocker_reasons": [],
            "collected_at": "2026-05-24T00:00:00Z",
            "no_mutation_guarantee": {"mutates_files": False},
            "git_available": True,
            "git_errors": [],
        },
    )

    response = _future_proxy_consultation_response(packet, proposed_action="apply")

    assert response["outcome"] == "needs_approval"
    assert response["go"] is False
    assert response["action_allowed"] is False
    assert response["runtime_action_available"] is False
    assert response["authority"] == FALSE_CONSULTATION_AUTHORITY
    assert response["approval_requirements"]["approval_state"] == "required_for_future_action"
    assert response["verification_requirements"]["verification_state"] == "needs_focused_tests"
    assert response["verification_requirements"]["closeout_blocked_without_proof"] is True
    assert "git diff --check" in response["verification_requirements"]["required_checks"]
    assert (
        "focused tests covering: docs/example.md"
        in response["verification_requirements"]["required_checks"]
    )
    assert (
        "confirm changed files match allowed_paths exactly"
        in response["verification_requirements"]["manual_checks"]
    )
    assert "human approval token" in response["missing_proof"]
    assert "proxy_action_requires_future_approval" in response["reason_codes"]


def _future_proxy_consultation_response(
    truth_packet: dict[str, Any] | None,
    *,
    proposed_action: str = "review",
) -> dict[str, Any]:
    return consult_cartographer_for_proxy_action(
        truth_packet,
        proposed_action=proposed_action,
        target_paths=("docs/example.md",),
        allowed_paths=("docs/example.md",),
    )
