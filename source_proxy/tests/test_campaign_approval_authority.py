from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime, timedelta

import pytest

import source_proxy.approval.campaign_authority as authority
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
