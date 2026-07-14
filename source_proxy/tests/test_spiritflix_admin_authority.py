from __future__ import annotations

import pytest

from source_proxy.approval.campaign_authority import CampaignApprovalError
from source_proxy.approval.spiritflix_admin_authority import consume_spiritflix_admin_approval, finalize_spiritflix_admin_execution, issue_spiritflix_admin_approval, persist_spiritflix_admin_preview


def test_spiritflix_admin_preview_issue_consume_and_finalize() -> None:
    preview = persist_spiritflix_admin_preview(action="metadata.write", target="item:fixture-1", configured_root="fixture-root", plan={"value": "fixture"})
    issued = issue_spiritflix_admin_approval(preview_id=preview["preview_id"], expected_generation=preview["generation"])
    consumed = consume_spiritflix_admin_approval(approval_id=issued["approval_id"], action="metadata.write", target="item:fixture-1", configured_root="fixture-root", plan={"value": "fixture"})
    assert finalize_spiritflix_admin_execution(consumed, result_id="result:fixture-1")["state"] == "consumed"


def test_spiritflix_admin_rejects_changed_target_and_single_use() -> None:
    preview = persist_spiritflix_admin_preview(action="metadata.write", target="item:fixture-2", configured_root="fixture-root", plan={"value": "fixture"})
    issued = issue_spiritflix_admin_approval(preview_id=preview["preview_id"], expected_generation=preview["generation"])
    with pytest.raises(CampaignApprovalError) as mismatch:
        consume_spiritflix_admin_approval(approval_id=issued["approval_id"], action="metadata.write", target="item:wrong", configured_root="fixture-root", plan={"value": "fixture"})
    assert mismatch.value.reason_code == "approval_target_mismatch"
    consumed = consume_spiritflix_admin_approval(approval_id=issued["approval_id"], action="metadata.write", target="item:fixture-2", configured_root="fixture-root", plan={"value": "fixture"})
    finalize_spiritflix_admin_execution(consumed, result_id="result:fixture-2")
    with pytest.raises(CampaignApprovalError) as reused:
        consume_spiritflix_admin_approval(approval_id=issued["approval_id"], action="metadata.write", target="item:fixture-2", configured_root="fixture-root", plan={"value": "fixture"})
    assert reused.value.reason_code == "approval_already_consumed"
