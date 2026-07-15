from __future__ import annotations

import json
import subprocess
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi import FastAPI
from fastapi.testclient import TestClient

import source_proxy.approval.campaign_authority as authority
from source_proxy.api.cartographer import cartographer_docs_autopilot_apply, router as cartographer_router
from source_proxy.approval.campaign_evidence import CampaignApprovalEvidenceError, validate_coding_approval_evidence
from source_proxy.approval.campaign_authority import (
    CampaignApprovalError,
    consume_coding_execution_approval,
    finalize_coding_execution_approval,
    persist_coding_execution_preview,
)
from source_proxy.cartographer import cartographer_selection_authority as cartographer_selection
from source_proxy.cartographer.proposal_transfer import CartographerProposalTransferError, transfer_proposal


def issue(preview_id: str, *, consumer: str = "coding-executor", operation: str = "coding_execution") -> str:
    result = subprocess.run(
        ["python3", "scripts/approval-authority.py", "issue"],
        input=json.dumps({
            "preview_id": preview_id,
            "expected_generation": "1",
            "consumer": consumer,
            "operation": operation,
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


def test_coding_approval_persists_the_server_resolved_lumacart_plugin() -> None:
    identity = {
        "plugin_id": "lumacart",
        "selected_prompt_id": "coder-001-init-dummy-product-site",
        "fixture_root": "tests/ui-agent-trials/fixtures/dummy-product-site/",
        "source_head": authority.current_head(),
    }
    preview = persist_coding_execution_preview(
        task_id="campaign1-test-lumacart-plugin",
        action="test LumaCart plugin binding",
        approved_diff="diff --git a/a b/a\n",
        target="tests/ui-agent-trials/fixtures/dummy-product-site/",
        selected_prompt_id="coder-001-init-dummy-product-site",
        context_hash="context-lumacart",
        target_plugin_identity=identity,
    )
    assert str(preview["preview_id"]).startswith("prv_")


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


def test_coding_evidence_requires_identical_target_plugin_identity_for_all_consumers() -> None:
    identity = {"plugin_id": "lumacart", "selected_prompt_id": "coder-001-init-dummy-product-site"}
    receipt = {
        "approval_id": "apr_campaign1", "generation": 2, "target_plugin_identity": identity,
        "acknowledgements": {
            name: {"approval_id": "apr_campaign1", "generation": 2, "target_plugin_identity": dict(identity)}
            for name in ("coding-executor", "coding-reviewer", "coding-verifier", "evidence-recorder")
        },
    }
    receipt["acknowledgements"]["evidence-recorder"]["target_plugin_identity"] = {"plugin_id": "other"}
    with pytest.raises(CampaignApprovalEvidenceError) as caught:
        validate_coding_approval_evidence(receipt)
    assert caught.value.reason_code == "approval_target_plugin_acknowledgement_mismatch:evidence-recorder"


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
    with pytest.raises(CampaignApprovalError) as plugin:
        consume_coding_execution_approval(
            approval_id=plugin_id,
            task_id="campaign1-test-plugin",
            action="test action",
            approved_diff="diff --git a/a b/a\n",
            target="src/app/coding/a.ts",
            selected_prompt_id="prompt-1",
            context_hash="context-1",
            target_plugin_identity={
                "plugin_id": "lumacart",
                "selected_prompt_id": "prompt-1",
                "source_head": authority.current_head(),
            },
        )
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


def test_cartographer_router_has_no_execution_authority_or_duplicate_registration() -> None:
    registrations = [
        (method.upper(), route.path)
        for route in cartographer_router.routes
        for method in route.methods or set()
        if method not in {"HEAD", "OPTIONS"}
    ]

    assert len(registrations) == len(set(registrations))
    assert ("POST", "/v1/cartographer/safe-write") not in registrations
    assert ("POST", "/v1/cartographer/verification/run") not in registrations
    assert ("POST", "/v1/cartographer/proposals/{proposal_id}/transfer") in registrations

    source = (Path(__file__).parents[1] / "api" / "cartographer.py").read_text(encoding="utf-8")
    for forbidden in (
        "source_proxy.cartographer.safe_write",
        "source_proxy.cartographer.verification_runner",
        "approve_git_queue_item",
        "apply_cartographer_clutter_proposal",
        "run_cartographer_docs_autopilot_apply",
        "run_cartographer_level_2_docs_apply",
        "write_cartographer_starter_blueprints",
    ):
        assert forbidden not in source


def test_cartographer_legacy_mutation_compatibility_route_fails_closed() -> None:
    with pytest.raises(HTTPException) as blocked:
        asyncio.run(cartographer_docs_autopilot_apply())
    assert blocked.value.status_code == 410
    assert blocked.value.detail["reason_code"] == "forbidden_cartographer_mutation"


def test_cartographer_direct_transfer_route_and_helper_fail_closed() -> None:
    app = FastAPI()
    app.include_router(cartographer_router)
    response = TestClient(app).post(
        "/v1/cartographer/proposals/bp-any/transfer",
        json={"consumer": "coding-executor", "target": "src/app/page.tsx"},
    )
    assert response.status_code == 410
    assert response.json()["detail"]["reason_code"] == "cartographer_direct_transfer_forbidden"
    with pytest.raises(CartographerProposalTransferError) as direct:
        transfer_proposal(proposal_id="bp-any", consumer="coding-executor", target="src/app/page.tsx")
    assert direct.value.reason_code == "cartographer_direct_transfer_forbidden"


def test_cartographer_durable_selection_binds_consumer_target_and_acknowledgements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Proposal:
        proposal_id = "bp-campaign1-selection"
        approved_diff = "diff --git a/blueprint b/blueprint\n+"
        diff_preview = ""
        proposed_files = ["_blueprints/current/dashboard.md"]
        fingerprint = "proposal-fingerprint"

    monkeypatch.setattr(cartographer_selection, "list_proposals", lambda: [Proposal()])
    preview = cartographer_selection.persist_cartographer_selection(
        proposal_id=Proposal.proposal_id, consumer="design-writeback", target="design:dashboard",
    )
    approval_id = issue(
        str(preview["preview_id"]), consumer="cartographer-transfer-consumer",
        operation="cartographer_selection_transfer",
    )
    consumed = cartographer_selection.consume_cartographer_selection(
        approval_id=approval_id, proposal_id=Proposal.proposal_id,
        consumer="design-writeback", target="design:dashboard",
    )
    finalized = cartographer_selection.finalize_cartographer_selection(
        consumed=consumed, proposal_id=Proposal.proposal_id,
        consumer="design-writeback", target="design:dashboard",
    )
    assert finalized["receipt"]["state"] == "consumed"
    assert set(finalized["acknowledgements"]) == {
        "cartographer-transfer-consumer", "cartographer-reviewer", "cartographer-verifier", "evidence-recorder",
    }
    assert all(value == {"approval_id": approval_id, "generation": 1} for value in finalized["acknowledgements"].values())

    with pytest.raises(CampaignApprovalError) as replay:
        cartographer_selection.consume_cartographer_selection(
            approval_id=approval_id, proposal_id=Proposal.proposal_id,
            consumer="design-writeback", target="design:dashboard",
        )
    assert replay.value.reason_code == "approval_already_consumed"


def test_cartographer_durable_selection_rejects_wrong_consumer_and_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Proposal:
        proposal_id = "bp-campaign1-selection-reject"
        approved_diff = "diff --git a/blueprint b/blueprint\n+"
        diff_preview = ""
        proposed_files = ["_blueprints/current/dashboard.md"]
        fingerprint = "proposal-fingerprint"

    monkeypatch.setattr(cartographer_selection, "list_proposals", lambda: [Proposal()])
    preview = cartographer_selection.persist_cartographer_selection(
        proposal_id=Proposal.proposal_id, consumer="coding-executor", target="src/app/page.tsx",
    )
    approval_id = issue(
        str(preview["preview_id"]), consumer="cartographer-transfer-consumer",
        operation="cartographer_selection_transfer",
    )
    with pytest.raises(CampaignApprovalError) as wrong_target:
        cartographer_selection.consume_cartographer_selection(
            approval_id=approval_id, proposal_id=Proposal.proposal_id,
            consumer="coding-executor", target="src/app/other.tsx",
        )
    assert wrong_target.value.reason_code == "approval_target_mismatch"
    with pytest.raises(CampaignApprovalError) as wrong_consumer:
        cartographer_selection.persist_cartographer_selection(
            proposal_id=Proposal.proposal_id, consumer="unregistered-writer", target="src/app/page.tsx",
        )
    assert wrong_consumer.value.reason_code == "cartographer_selection_consumer_mismatch"
