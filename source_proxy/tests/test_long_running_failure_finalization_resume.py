from __future__ import annotations

from typing import Any

import pytest

import source_proxy.approval.campaign_authority as campaign_authority
import source_proxy.tasks.long_running as long_running
from source_proxy.approval.campaign_authority import CampaignApprovalError
from source_proxy.tasks.long_running import LongRunningTask, LongRunningTaskError


def _approval(*, state: str = "consuming") -> dict[str, Any]:
    approval_id = "apr_failure_resume"
    generation = 7
    return {
        "approval_id": approval_id,
        "generation": generation,
        "state": state,
        "target_plugin_identity": {},
        "binding": {
            "approval_id": approval_id,
            "generation": str(generation),
            "consumer": "coding-executor:coder",
            "lane_id": "coder",
            "operation": "coding_execution",
            "repository": "SpiritOS",
            "worktree": "/srv/spiritos",
            "root": "/srv/spiritos",
            "target": "src/example.py",
            "plugin": "coding-shell",
            "preview": "prv_failure_resume",
            "content_hash": "a" * 64,
            "context": "b" * 64,
            "source_head": "c" * 40,
        },
    }


def _task(*, approval_state: str = "consuming") -> LongRunningTask:
    task = LongRunningTask(
        id="task_failure_resume",
        description="exercise durable failure finalization recovery",
        status="verification_passed_pending_participants",
    )
    task.ast_snapshot = {
        "campaign_2_approval": _approval(state=approval_state),
        "coding_artifact": {
            "run_id": "run_failure_resume",
            "artifact_sha256": "d" * 64,
        },
    }
    return task


def _authority_record(approval: dict[str, Any], *, state: str) -> dict[str, Any]:
    binding = approval["binding"]
    return {
        "id": approval["approval_id"],
        "generation": approval["generation"],
        "state": state,
        **{
            field: binding[field]
            for field in (
                "consumer",
                "operation",
                "repository",
                "worktree",
                "root",
                "target",
                "plugin",
                "preview",
                "content_hash",
                "context",
                "source_head",
            )
        },
    }


def _install_task_boundary(
    monkeypatch: pytest.MonkeyPatch,
    task: LongRunningTask,
) -> None:
    monkeypatch.setattr(long_running, "_lookup_task", lambda task_id: task)
    monkeypatch.setattr(long_running, "_save_task", lambda value: None)
    monkeypatch.setattr(
        long_running,
        "_append_causal_event",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        long_running,
        "_task_envelope",
        lambda value: {
            "task": {
                "status": value.status,
                "ast_snapshot": value.ast_snapshot,
            }
        },
    )


def _failure_receipt(
    approval: dict[str, Any],
    *,
    result_id: str,
    idempotent: bool,
) -> dict[str, Any]:
    return {
        "approval_id": approval["approval_id"],
        "generation": approval["generation"],
        "state": "invalidated",
        "result_id": result_id,
        "idempotent": idempotent,
    }


def test_transient_failure_finalization_is_retried_on_resume(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task()
    _install_task_boundary(monkeypatch, task)
    approval = task.ast_snapshot["campaign_2_approval"]
    records = [{"invocation_id": "verifier-failed"}]
    calls = 0

    monkeypatch.setattr(
        long_running,
        "lookup_coding_execution_approval",
        lambda value: _authority_record(approval, state="consuming"),
    )

    def finalize(
        value: dict[str, Any],
        *,
        result_id: str,
        evidence: dict[str, Any],
        status: str,
    ) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise CampaignApprovalError("approval_issuer_unavailable")
        assert status == "failed"
        assert evidence["reason_code"] == "repair_attempt_superseded:test_failure"
        return _failure_receipt(value, result_id=result_id, idempotent=False)

    monkeypatch.setattr(long_running, "finalize_coding_execution_approval", finalize)

    long_running.fail_orchestrated_coding_execution(
        task.id,
        reason_code="repair_attempt_superseded:test_failure",
        participant_records=records,
    )
    local = task.ast_snapshot["campaign_2_approval"]
    assert local["state"] == "failure_finalization_failed"
    assert local["finalization_error"] == "approval_issuer_unavailable"

    resumed = long_running.fail_orchestrated_coding_execution(
        task.id,
        reason_code="repair_attempt_superseded:test_failure",
        participant_records=records,
    )
    local = resumed["task"]["ast_snapshot"]["campaign_2_approval"]
    assert calls == 2
    assert local["state"] == "invalidated"
    assert "finalization_error" not in local
    assert local["failure_finalization_receipt"]["idempotent"] is False
    assert (
        local["failure_finalization_receipt"][
            "authority_state_before_finalization"
        ]
        == "consuming"
    )


def test_crash_after_authority_finalization_accepts_only_exact_idempotent_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task(approval_state="consuming")
    _install_task_boundary(monkeypatch, task)
    approval = task.ast_snapshot["campaign_2_approval"]
    records = [{"invocation_id": "reviewer-failed"}]
    monkeypatch.setattr(
        long_running,
        "lookup_coding_execution_approval",
        lambda value: _authority_record(approval, state="invalidated"),
    )
    monkeypatch.setattr(
        long_running,
        "finalize_coding_execution_approval",
        lambda value, *, result_id, evidence, status: _failure_receipt(
            value,
            result_id=result_id,
            idempotent=True,
        ),
    )

    result = long_running.fail_orchestrated_coding_execution(
        task.id,
        reason_code="repair_attempt_superseded:reviewer_rejection",
        participant_records=records,
    )

    local = result["task"]["ast_snapshot"]["campaign_2_approval"]
    assert local["state"] == "invalidated"
    assert local["failure_finalization_receipt"]["idempotent"] is True
    assert (
        local["failure_finalization_receipt"][
            "authority_state_before_finalization"
        ]
        == "invalidated"
    )


def test_mismatched_authority_record_fails_closed_without_finalizing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task()
    _install_task_boundary(monkeypatch, task)
    records = [{"invocation_id": "verifier-failed"}]
    finalized = False

    def reject_mismatch(value: dict[str, Any]) -> dict[str, Any]:
        raise CampaignApprovalError("approval_content_hash_mismatch")

    def forbidden_finalize(*args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal finalized
        finalized = True
        raise AssertionError("a mismatched authority record must not be finalized")

    monkeypatch.setattr(
        long_running,
        "lookup_coding_execution_approval",
        reject_mismatch,
    )
    monkeypatch.setattr(
        long_running,
        "finalize_coding_execution_approval",
        forbidden_finalize,
    )

    result = long_running.fail_orchestrated_coding_execution(
        task.id,
        reason_code="repair_attempt_superseded:verifier_rejection",
        participant_records=records,
    )

    local = result["task"]["ast_snapshot"]["campaign_2_approval"]
    assert finalized is False
    assert local["state"] == "failure_finalization_failed"
    assert local["finalization_error"] == "approval_content_hash_mismatch"
    assert "failure_finalization_receipt" not in local


def test_authority_finalizer_rejects_tampered_terminal_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    approval = _approval()
    monkeypatch.setattr(campaign_authority, "current_head", lambda: "c" * 40)
    monkeypatch.setattr(
        campaign_authority,
        "_call",
        lambda command, payload: {
            "approval_id": approval["approval_id"],
            "generation": approval["generation"],
            "state": "invalidated",
            "result_id": "tampered-result",
            "idempotent": True,
        },
    )

    with pytest.raises(
        CampaignApprovalError,
        match="approval_finalization_receipt_mismatch",
    ):
        campaign_authority.finalize_coding_execution_approval(
            approval,
            result_id="coding-execution-task_failure_resume-failed",
            evidence={"schema_version": "failure/v1"},
            status="failed",
        )


def test_failure_finalization_resume_rejects_changed_failure_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task(approval_state="failure_finalization_failed")
    task.ast_snapshot["campaign_2_approval"].update(
        {
            "failure_reason": "repair_attempt_superseded:original",
            "participant_records": [{"invocation_id": "original"}],
            "finalization_error": "approval_issuer_unavailable",
        }
    )
    _install_task_boundary(monkeypatch, task)

    with pytest.raises(
        LongRunningTaskError,
        match="Failure-finalization recovery did not match",
    ) as caught:
        long_running.fail_orchestrated_coding_execution(
            task.id,
            reason_code="repair_attempt_superseded:tampered",
            participant_records=[{"invocation_id": "tampered"}],
        )

    assert caught.value.reason_code == "approval_failure_resume_payload_mismatch"
    assert task.ast_snapshot["campaign_2_approval"]["state"] == (
        "failure_finalization_failed"
    )
