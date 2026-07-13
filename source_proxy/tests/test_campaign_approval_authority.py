from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime, timedelta

import pytest

from source_proxy.approval.campaign_authority import (
    CampaignApprovalError,
    consume_coding_execution_approval,
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
