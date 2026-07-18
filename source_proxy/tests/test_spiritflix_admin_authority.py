from __future__ import annotations

import pytest

from source_proxy.approval.campaign_authority import CampaignApprovalError
from source_proxy.approval.campaign_authority import _call
from source_proxy.approval.spiritflix_admin_authority import compensate_spiritflix_admin_execution, consume_spiritflix_admin_approval, finalize_spiritflix_admin_execution, issue_spiritflix_admin_approval, persist_spiritflix_admin_preview


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


def test_spiritflix_admin_compensation_is_exact_and_idempotent() -> None:
    preview = persist_spiritflix_admin_preview(
        action="metadata.write", target="item:fixture-compensate", configured_root="fixture-root",
        plan={"value": "fixture"},
    )
    issued = issue_spiritflix_admin_approval(
        preview_id=preview["preview_id"], expected_generation=preview["generation"],
    )
    consumed = consume_spiritflix_admin_approval(
        approval_id=issued["approval_id"], action="metadata.write",
        target="item:fixture-compensate", configured_root="fixture-root", plan={"value": "fixture"},
    )
    result_hash = "a" * 64
    first = compensate_spiritflix_admin_execution(consumed, result_hash=result_hash)
    repeated = compensate_spiritflix_admin_execution(consumed, result_hash=result_hash)
    assert first["state"] == "invalidated"
    assert first["idempotent"] is False
    assert repeated["state"] == "invalidated"
    assert repeated["idempotent"] is True

    changed_result = dict(consumed["binding"])
    changed_result.update({
        "result_hash": "b" * 64,
        "evidence": '{"redacted":true}',
    })
    with pytest.raises(CampaignApprovalError) as mismatch:
        _call("compensate", changed_result)
    assert mismatch.value.reason_code == "approval_compensation_mismatch"

    changed_binding = dict(consumed["binding"])
    changed_binding.update({
        "target": "item:forged-target",
        "result_hash": result_hash,
        "evidence": '{"redacted":true}',
    })
    with pytest.raises(CampaignApprovalError) as binding_mismatch:
        _call("compensate", changed_binding)
    assert binding_mismatch.value.reason_code == "approval_target_mismatch"


def test_spiritflix_admin_compensation_rejects_unauthorized_consumer() -> None:
    preview = persist_spiritflix_admin_preview(
        action="metadata.write", target="item:fixture-forbidden", configured_root="fixture-root",
        plan={"value": "fixture"},
    )
    issued = issue_spiritflix_admin_approval(
        preview_id=preview["preview_id"], expected_generation=preview["generation"],
    )
    consumed = consume_spiritflix_admin_approval(
        approval_id=issued["approval_id"], action="metadata.write",
        target="item:fixture-forbidden", configured_root="fixture-root", plan={"value": "fixture"},
    )
    forged = dict(consumed["binding"])
    forged.update({
        "consumer": "coding-executor:coder",
        "operation": "coding_execution",
        "result_hash": "b" * 64,
        "evidence": '{"redacted":true}',
    })
    with pytest.raises(CampaignApprovalError) as forbidden:
        _call("compensate", forged)
    assert forbidden.value.reason_code == "approval_compensation_not_permitted"
