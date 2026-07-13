from __future__ import annotations

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest

import source_proxy.approval.campaign_authority as authority
from source_proxy.approval.campaign_evidence import CampaignApprovalEvidenceError, validate_coding_approval_evidence
from source_proxy.approval.campaign_authority import (
    CampaignApprovalError,
    consume_coding_execution_approval,
    finalize_coding_execution_approval,
    persist_coding_execution_preview,
)


def issue(preview_id: str) -> str:
    result = subprocess.run(
        ["python3", "scripts/approval-authority.py", "issue"],
        input=json.dumps({
            "preview_id": preview_id,
            "consumer": "coding-executor",
            "operation": "coding_execution",
            "expires_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
        }),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)["approval_id"]


def transition(approval_id: str, state: str) -> None:
    subprocess.run(
        ["python3", "scripts/approval-authority.py", "transition"],
        input=json.dumps({"approval_id": approval_id, "state": state}),
        text=True,
        capture_output=True,
        check=True,
    )


def coding_preview(*, task_id: str, target: str = "src/app/coding/a.ts", approved_diff: str = "diff --git a/a b/a\n") -> dict[str, object]:
    return persist_coding_execution_preview(
        task_id=task_id,
        action="test action",
        approved_diff=approved_diff,
        target=target,
        selected_prompt_id="prompt-1",
        context_hash="context-1",
    )


def consume(approval_id: str, *, task_id: str, target: str = "src/app/coding/a.ts", approved_diff: str = "diff --git a/a b/a\n") -> dict[str, object]:
    return consume_coding_execution_approval(
        approval_id=approval_id,
        task_id=task_id,
        action="test action",
        approved_diff=approved_diff,
        target=target,
        selected_prompt_id="prompt-1",
        context_hash="context-1",
    )


def test_coding_approval_rejects_changed_target_after_persisted_preview() -> None:
    preview = persist_coding_execution_preview(
        task_id="campaign1-test-target",
        action="test action",
        approved_diff="diff --git a/a b/a\n",
        target="src/app/coding/a.ts",
        selected_prompt_id="prompt-1",
        context_hash="context-1",
    )
    with pytest.raises(CampaignApprovalError) as caught:
        consume_coding_execution_approval(
            approval_id=issue(preview["preview_id"]),
            task_id="campaign1-test-target",
            action="test action",
            approved_diff="diff --git a/a b/a\n",
            target="src/app/coding/b.ts",
            selected_prompt_id="prompt-1",
            context_hash="context-1",
        )
    assert caught.value.reason_code == "approval_target_mismatch"


def test_coding_approval_rejects_changed_context_and_single_use() -> None:
    preview = persist_coding_execution_preview(
        task_id="campaign1-test-context",
        action="test action",
        approved_diff="diff --git a/a b/a\n",
        target="src/app/coding/a.ts",
        selected_prompt_id="prompt-1",
        context_hash="context-1",
    )
    approval_id = issue(preview["preview_id"])
    with pytest.raises(CampaignApprovalError) as caught:
        consume_coding_execution_approval(
            approval_id=approval_id, task_id="campaign1-test-context", action="test action",
            approved_diff="diff --git a/a b/a\n", target="src/app/coding/a.ts",
            selected_prompt_id="prompt-1", context_hash="context-2",
        )
    assert caught.value.reason_code == "approval_context_mismatch"

    consumed = consume_coding_execution_approval(
        approval_id=approval_id, task_id="campaign1-test-context", action="test action",
        approved_diff="diff --git a/a b/a\n", target="src/app/coding/a.ts",
        selected_prompt_id="prompt-1", context_hash="context-1",
    )
    finalize_coding_execution_approval(consumed, result_id="campaign1-test-context", evidence={"redacted": True}, status="succeeded")
    with pytest.raises(CampaignApprovalError) as consumed_again:
        consume_coding_execution_approval(
            approval_id=approval_id, task_id="campaign1-test-context", action="test action",
            approved_diff="diff --git a/a b/a\n", target="src/app/coding/a.ts",
            selected_prompt_id="prompt-1", context_hash="context-1",
        )
    assert consumed_again.value.reason_code == "approval_already_consumed"


def test_coding_approval_rejects_changed_source_head(monkeypatch: pytest.MonkeyPatch) -> None:
    preview = persist_coding_execution_preview(
        task_id="campaign1-test-source",
        action="test action",
        approved_diff="diff --git a/a b/a\n",
        target="src/app/coding/a.ts",
        selected_prompt_id="prompt-1",
        context_hash="context-1",
    )
    monkeypatch.setattr(authority, "current_head", lambda: "0" * 40)
    with pytest.raises(CampaignApprovalError) as caught:
        consume_coding_execution_approval(
            approval_id=issue(preview["preview_id"]), task_id="campaign1-test-source",
            action="test action", approved_diff="diff --git a/a b/a\n",
            target="src/app/coding/a.ts", selected_prompt_id="prompt-1", context_hash="context-1",
        )
    assert caught.value.reason_code == "approval_source_mismatch"


def test_coding_evidence_requires_identical_approval_generation_for_all_consumers() -> None:
    receipt = {
        "approval_id": "apr_campaign1", "generation": 2,
        "acknowledgements": {
            name: {"approval_id": "apr_campaign1", "generation": 2}
            for name in ("coding-executor", "coding-reviewer", "coding-verifier", "evidence-recorder")
        },
    }
    validate_coding_approval_evidence(receipt)
    receipt["acknowledgements"]["coding-verifier"]["generation"] = 3
    with pytest.raises(CampaignApprovalEvidenceError) as caught:
        validate_coding_approval_evidence(receipt)
    assert caught.value.reason_code == "approval_acknowledgement_mismatch:coding-verifier"


def test_coding_approval_rejects_fabricated_and_cancelled_ids() -> None:
    with pytest.raises(CampaignApprovalError) as fabricated:
        consume("apr_fabricated", task_id="campaign1-test-fabricated")
    assert fabricated.value.reason_code == "approval_not_found"

    preview = coding_preview(task_id="campaign1-test-cancelled")
    approval_id = issue(str(preview["preview_id"]))
    transition(approval_id, "cancelled")
    with pytest.raises(CampaignApprovalError) as cancelled:
        consume(approval_id, task_id="campaign1-test-cancelled")
    assert cancelled.value.reason_code == "approval_cancelled"


def test_coding_approval_rejects_wrong_plugin_worktree_and_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plugin_preview = coding_preview(task_id="campaign1-test-plugin")
    plugin_id = issue(str(plugin_preview["preview_id"]))
    monkeypatch.setattr(authority, "coding_target_plugin", lambda _target: "dummy-product-site")
    with pytest.raises(CampaignApprovalError) as plugin:
        consume(plugin_id, task_id="campaign1-test-plugin")
    assert plugin.value.reason_code == "approval_plugin_mismatch"

    monkeypatch.undo()
    worktree_preview = coding_preview(task_id="campaign1-test-worktree")
    worktree_id = issue(str(worktree_preview["preview_id"]))
    original_root = authority.ROOT
    monkeypatch.setattr(authority, "ROOT", "/tmp/fabricated-worktree")
    monkeypatch.setattr(authority, "current_head", lambda: authority._call("lookup", {"approval_id": worktree_id})["source_head"])
    with pytest.raises(CampaignApprovalError) as worktree:
        consume(worktree_id, task_id="campaign1-test-worktree")
    assert worktree.value.reason_code == "approval_worktree_mismatch"
    monkeypatch.setattr(authority, "ROOT", original_root)

    content_preview = coding_preview(task_id="campaign1-test-content")
    content_id = issue(str(content_preview["preview_id"]))
    with pytest.raises(CampaignApprovalError) as content:
        consume(content_id, task_id="campaign1-test-content", approved_diff="diff --git a/a b/a\n+stale\n")
    assert content.value.reason_code == "approval_content_hash_mismatch"


def test_coding_approval_consumption_is_transactionally_single_winner() -> None:
    preview = coding_preview(task_id="campaign1-test-concurrent")
    approval_id = issue(str(preview["preview_id"]))

    def attempt() -> tuple[str, object]:
        try:
            return "consumed", consume(approval_id, task_id="campaign1-test-concurrent")
        except CampaignApprovalError as error:
            return "blocked", error.reason_code

    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(lambda _index: attempt(), range(2)))

    winners = [value for state, value in results if state == "consumed"]
    blocked = [value for state, value in results if state == "blocked"]
    assert len(winners) == 1
    assert blocked in (["approval_concurrent_consumption"], ["approval_already_consumed"])
    finalize_coding_execution_approval(
        winners[0], result_id="campaign1-test-concurrent", evidence={"redacted": True}, status="succeeded"
    )
