from __future__ import annotations

from unittest.mock import patch

from source_proxy.decision.mac_integration import run_bound_mac_verification


def test_mac_result_is_not_counted_without_exact_source_binding() -> None:
    with patch("source_proxy.decision.mac_integration._run_mac_worker_job", return_value={"success": True, "result": {"head": "b" * 40}}):
        receipt = run_bound_mac_verification("task-1", source_commit="a" * 40, source_worktree="/repo")
    assert receipt["source_bound"] is False
    assert receipt["verdict_effect"] == "mac_verification_unavailable_or_source_mismatch"


def test_mac_timeout_is_truthful_and_never_grants_write_authority() -> None:
    with patch("source_proxy.decision.mac_integration._run_mac_worker_job", return_value={"success": False, "error": "mac_worker_timeout"}):
        receipt = run_bound_mac_verification("task-1", source_commit="a" * 40, source_worktree="/repo")
    assert receipt["source_bound"] is False
    assert receipt["write_authority"] is False
