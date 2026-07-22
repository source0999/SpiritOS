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
from source_proxy.approval.campaign_evidence import (
    REQUIRED_CONSUMERS,
    CampaignApprovalEvidenceError,
    validate_coding_approval_evidence,
)
from source_proxy.approval.campaign_authority import (
    CampaignApprovalError,
    consume_coding_execution_approval,
    finalize_coding_execution_approval,
    persist_coding_execution_preview,
)
from source_proxy.cartographer import cartographer_selection_authority as cartographer_selection
from source_proxy.cartographer.proposal_transfer import CartographerProposalTransferError, transfer_proposal


def issue(preview_id: str, *, consumer: str = "coding-executor:coder", operation: str = "coding_execution") -> str:
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


def test_coding_approval_rejects_lane_mismatched_approval() -> None:
    preview = coding_preview(task_id="campaign2-lane-mismatch")
    approval_id = issue(str(preview["preview_id"]), consumer="coding-executor:coder")
    with pytest.raises(CampaignApprovalError, match="approval_lane_not_permitted"):
        consume_coding_execution_approval(
            approval_id=approval_id, task_id="campaign2-lane-mismatch", action="test action",
            approved_diff="diff --git a/a b/a\n", target="src/app/coding/a.ts",
            selected_prompt_id="legacy-test", context_hash="test-context", lane_id="reviewer",
        )


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


def test_coding_approval_finalization_is_idempotent_only_for_the_exact_result() -> None:
    task_id = "campaign1-test-idempotent-finalization"
    preview = coding_preview(task_id=task_id)
    consumed = consume(issue(str(preview["preview_id"])), task_id=task_id)
    evidence = {"schema_version": "test/v1", "artifact_sha256": "sha256:" + "a" * 64}

    first = finalize_coding_execution_approval(
        consumed,
        result_id=task_id,
        evidence=evidence,
        status="succeeded",
    )
    replay = finalize_coding_execution_approval(
        consumed,
        result_id=task_id,
        evidence=evidence,
        status="succeeded",
    )

    assert first["state"] == replay["state"] == "consumed"
    assert first["idempotent"] is False
    assert replay["idempotent"] is True
    with pytest.raises(CampaignApprovalError, match="approval_already_consumed"):
        finalize_coding_execution_approval(
            consumed,
            result_id=f"{task_id}-different",
            evidence=evidence,
            status="succeeded",
        )
    with pytest.raises(CampaignApprovalError, match="approval_already_consumed"):
        finalize_coding_execution_approval(
            consumed,
            result_id=task_id,
            evidence={"schema_version": "test/v1", "artifact_sha256": "sha256:" + "b" * 64},
            status="succeeded",
        )


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


def test_cartographer_selection_binds_the_registered_runtime_repository(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Proposal:
        proposal_id = "runtime-identity-selection"
        approved_diff = ""
        diff_preview = ""
        proposed_files = ["tests/ui-agent-trials/fixtures/dummy-product-site/README.md"]
        fingerprint = "runtime-identity-fingerprint"
        persisted = True
        status = "pending_review"
        warnings: list[str] = []

    captured: dict[str, object] = {}
    monkeypatch.setattr(cartographer_selection, "list_proposals", lambda: [Proposal()])
    monkeypatch.setattr(
        cartographer_selection,
        "_call",
        lambda command, payload: captured.update(command=command, payload=payload)
        or {"preview_id": "prv_runtime", "generation": 1},
    )

    cartographer_selection.persist_cartographer_selection(
        proposal_id=Proposal.proposal_id,
        consumer="coding-executor:coder",
        target=Proposal.proposed_files[0],
    )

    assert captured["command"] == "persist-preview"
    assert captured["payload"]["repository"] == authority.REPOSITORY
    assert captured["payload"]["worktree"] == authority.ROOT


def test_coding_evidence_requires_identical_approval_generation_for_all_consumers() -> None:
    artifact_sha256 = "sha256:" + "a" * 64
    acknowledgements = {
        name: {
            "approval_id": "apr_campaign1",
            "generation": 2,
            "artifact_sha256": artifact_sha256,
            "invocation_id": f"invocation-{index}",
            "output_id": f"output-{index}",
            "acknowledgement_id": f"acknowledgement-{index}",
        }
        for index, name in enumerate(REQUIRED_CONSUMERS)
    }
    receipt = {
        "approval_id": "apr_campaign1",
        "generation": 2,
        "artifact_sha256": artifact_sha256,
        "acknowledgements": acknowledgements,
        "participant_records": [
            {
                "role": name,
                "consumer_acknowledgement_id": acknowledgement["acknowledgement_id"],
                "consumer_acknowledgement": acknowledgement,
            }
            for name, acknowledgement in acknowledgements.items()
        ],
    }
    validate_coding_approval_evidence(receipt)
    receipt["acknowledgements"]["coding-verifier"]["generation"] = 3
    with pytest.raises(CampaignApprovalEvidenceError) as caught:
        validate_coding_approval_evidence(receipt)
    assert caught.value.reason_code == "approval_acknowledgement_mismatch:coding-verifier"


def test_coding_evidence_rejects_acknowledgement_not_owned_by_the_participant() -> None:
    identity = {"plugin_id": "lumacart", "selected_prompt_id": "coder-001-init-dummy-product-site"}
    artifact_sha256 = "sha256:" + "b" * 64
    acknowledgements = {
        name: {
            "approval_id": "apr_campaign1",
            "generation": 2,
            "artifact_sha256": artifact_sha256,
            "invocation_id": f"invocation-{index}",
            "output_id": f"output-{index}",
            "acknowledgement_id": f"acknowledgement-{index}",
        }
        for index, name in enumerate(REQUIRED_CONSUMERS)
    }
    receipt = {
        "approval_id": "apr_campaign1",
        "generation": 2,
        "target_plugin_identity": identity,
        "artifact_sha256": artifact_sha256,
        "acknowledgements": acknowledgements,
        "participant_records": [
            {
                "role": name,
                "consumer_acknowledgement_id": acknowledgement["acknowledgement_id"],
                "consumer_acknowledgement": dict(acknowledgement),
            }
            for name, acknowledgement in acknowledgements.items()
        ],
    }
    receipt["participant_records"][-1]["consumer_acknowledgement"]["output_id"] = "forged-output"
    with pytest.raises(CampaignApprovalEvidenceError) as caught:
        validate_coding_approval_evidence(receipt)
    assert caught.value.reason_code == "approval_acknowledgement_not_participant_owned:evidence-recorder"


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
    assert plugin.value.reason_code == "target_plugin_identity_mismatch"

    monkeypatch.undo()
    worktree_preview = coding_preview(task_id="campaign1-test-worktree")
    worktree_id = issue(str(worktree_preview["preview_id"]))
    original_root = authority.ROOT
    monkeypatch.setattr(authority, "ROOT", "/tmp/fabricated-worktree")
    monkeypatch.setattr(authority, "current_head", lambda: authority._call("lookup", {"approval_id": worktree_id})["source_head"])
    with pytest.raises(CampaignApprovalError) as worktree:
        consume(worktree_id, task_id="campaign1-test-worktree")
    assert worktree.value.reason_code == "approval_root_unavailable"
    monkeypatch.setattr(authority, "ROOT", original_root)

    content_preview = coding_preview(task_id="campaign1-test-content")
    content_id = issue(str(content_preview["preview_id"]))
    with pytest.raises(CampaignApprovalError) as content:
        consume(content_id, task_id="campaign1-test-content", approved_diff="diff --git a/a b/a\n+stale\n")
    assert content.value.reason_code == "approval_content_hash_mismatch"


def test_generic_target_plugin_binds_fixture_head_and_every_changed_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "fixture"
    (root / "src").mkdir(parents=True)
    (root / "src" / "value.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "outside.py").write_text("OUTSIDE = 0\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "fixture@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Fixture"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "src/value.py", "outside.py"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "baseline"], check=True)
    fixture_head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    fixture_tree = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD^{tree}"],
        text=True,
    ).strip()
    from source_proxy.benchmarks.campaign_3_5_fixture_authority import (
        ENV_MANIFEST,
        MANIFEST_SCHEMA_V2,
    )
    from source_proxy.target_plugins.adapter import (
        GENERIC_WORKSPACE_CONTEXT_ID,
        GENERIC_WORKSPACE_PLUGIN_ID,
        GENERIC_WORKSPACE_PROFILE,
        GENERIC_WORKSPACE_PROMPT_ID,
        TARGET_PLUGIN_SCHEMA_VERSION,
        resolve_target_plugin,
    )

    manifest = tmp_path / "fixture-authority.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": MANIFEST_SCHEMA_V2,
                "fixture_id": "approval-authority-fixture",
                "workspace_root": str(root.resolve()),
                "baseline_commit": fixture_head,
                "baseline_tree": fixture_tree,
                "readable_paths": ["src/"],
                "writable_paths": ["src/"],
                "execution_profile": GENERIC_WORKSPACE_PROFILE,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    manifest.chmod(0o600)
    monkeypatch.setenv(ENV_MANIFEST, str(manifest.resolve()))
    packet = {
        "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID,
        "target_plugin": {
            "schema_version": TARGET_PLUGIN_SCHEMA_VERSION,
            "id": GENERIC_WORKSPACE_PLUGIN_ID,
            "fixture_root": ".",
            "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID,
            "selected_context_id": GENERIC_WORKSPACE_CONTEXT_ID,
            "execution_profile": GENERIC_WORKSPACE_PROFILE,
        },
    }
    identity = resolve_target_plugin(packet, root).evidence_identity()
    plugin, bound = authority._target_plugin_binding(
        target="src/value.py",
        selected_prompt_id=GENERIC_WORKSPACE_PROMPT_ID,
        identity=identity,
    )
    assert plugin == "generic-workspace"
    assert bound == identity

    fabricated = dict(identity)
    fabricated["workspace_root"] = str(tmp_path.resolve())
    with pytest.raises(CampaignApprovalError, match="workspace_authority_mismatch"):
        authority._target_plugin_binding(
            target="src/value.py",
            selected_prompt_id=GENERIC_WORKSPACE_PROMPT_ID,
            identity=fabricated,
        )

    widened = dict(identity)
    widened["allowed_actions"] = ["src/", "outside.py"]
    with pytest.raises(CampaignApprovalError, match="identity_authority_mismatch"):
        authority._target_plugin_binding(
            target="src/value.py",
            selected_prompt_id=GENERIC_WORKSPACE_PROMPT_ID,
            identity=widened,
        )

    valid_diff = """diff --git a/src/value.py b/src/value.py
--- a/src/value.py
+++ b/src/value.py
@@ -1 +1 @@
-VALUE = 1
+VALUE = 2
"""
    authority._validate_target_plugin_diff_scope(
        valid_diff,
        plugin=plugin,
        identity=identity,
    )

    outside_diff = """diff --git a/outside.py b/outside.py
--- a/outside.py
+++ b/outside.py
@@ -1 +1 @@
-OUTSIDE = 0
+OUTSIDE = 1
"""
    with pytest.raises(CampaignApprovalError, match="target_plugin_diff_scope_violation"):
        authority._validate_target_plugin_diff_scope(
            outside_diff,
            plugin=plugin,
            identity=identity,
        )

    (root / "src" / "value.py").write_text("VALUE = 9\n", encoding="utf-8")
    with pytest.raises(CampaignApprovalError, match="target_plugin_workspace_state_mismatch"):
        authority._target_plugin_binding(
            target="src/value.py",
            selected_prompt_id=GENERIC_WORKSPACE_PROMPT_ID,
            identity=identity,
        )
    (root / "src" / "value.py").write_text("VALUE = 1\n", encoding="utf-8")

    stale = dict(identity)
    stale["target_source_head"] = "0" * 40
    with pytest.raises(CampaignApprovalError, match="target_plugin_target_source_head_mismatch"):
        authority._target_plugin_binding(
            target="src/value.py",
            selected_prompt_id=GENERIC_WORKSPACE_PROMPT_ID,
            identity=stale,
        )


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
        proposed_files = ["design:dashboard"]
        fingerprint = "proposal-fingerprint"
        persisted = True
        status = "pending_review"
        warnings = []

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
    transfer = {
        "schema_version": "cartographer.coding-transfer/v1",
        "proposal_id": Proposal.proposal_id,
        "selection_id": approval_id,
        "selection_approval_id": approval_id,
        "selection_generation": 1,
        "consumer": "design-writeback",
        "target": "design:dashboard",
        "task_id": "design-task-1",
        "run_id": "design-run-1",
        "transfer_event_id": "cartographer-transfer-event-1",
        "downstream_consumer_invocation_id": "design-consumer-invocation-1",
        "provenance": {
            "content_hash": consumed["binding"]["content_hash"],
            "context": consumed["binding"]["context"],
            "preview_id": consumed["binding"]["preview"],
            "source_head": consumed["binding"]["source_head"],
        },
    }
    acknowledgement = {
        "schema_version": "cartographer.downstream-acknowledgement/v2",
        "acknowledgement_id": "design-consumer-ack-1",
        "transfer_event_id": transfer["transfer_event_id"],
        "consumer_invocation_id": transfer["downstream_consumer_invocation_id"],
        "consumer_output_id": "design-consumer-output-1",
        "consumer_output_sha256": "b" * 64,
        "consumer_artifact_sha256": "c" * 64,
        "consumer_completed_at": "2026-07-17T12:00:00+00:00",
        "consumer_passed": True,
        "proposal_id": Proposal.proposal_id,
        "selection_id": approval_id,
        "task_id": transfer["task_id"],
        "run_id": transfer["run_id"],
        "consumed": True,
    }
    finalized = cartographer_selection.finalize_cartographer_selection(
        consumed=consumed, proposal_id=Proposal.proposal_id,
        consumer="design-writeback", target="design:dashboard",
        transfer=transfer,
        downstream_acknowledgement=acknowledgement,
    )
    assert finalized["receipt"]["state"] == "consumed"
    assert finalized["transfer"] == transfer
    assert finalized["downstream_acknowledgement"] == acknowledgement

    with pytest.raises(CampaignApprovalError) as replay:
        cartographer_selection.consume_cartographer_selection(
            approval_id=approval_id, proposal_id=Proposal.proposal_id,
            consumer="design-writeback", target="design:dashboard",
        )
    assert replay.value.reason_code == "approval_already_consumed"


def test_cartographer_selection_rejects_changed_proposal_fingerprint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Proposal:
        proposal_id = "bp-campaign1-selection-fingerprint"
        approved_diff = "diff --git a/blueprint b/blueprint\n+"
        diff_preview = ""
        proposed_files = ["src/app/page.tsx"]
        fingerprint = "a" * 16
        persisted = True
        status = "pending_review"
        warnings = []

    proposal = Proposal()
    monkeypatch.setattr(cartographer_selection, "list_proposals", lambda: [proposal])
    preview = cartographer_selection.persist_cartographer_selection(
        proposal_id=proposal.proposal_id,
        consumer="coding-executor:coder",
        target=proposal.proposed_files[0],
    )
    approval_id = issue(
        str(preview["preview_id"]),
        consumer="cartographer-transfer-consumer",
        operation="cartographer_selection_transfer",
    )

    proposal.fingerprint = "b" * 16
    with pytest.raises(CampaignApprovalError) as changed:
        cartographer_selection.consume_cartographer_selection(
            approval_id=approval_id,
            proposal_id=proposal.proposal_id,
            consumer="coding-executor:coder",
            target=proposal.proposed_files[0],
        )
    assert changed.value.reason_code == "approval_content_hash_mismatch"


def test_cartographer_durable_selection_rejects_wrong_consumer_and_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Proposal:
        proposal_id = "bp-campaign1-selection-reject"
        approved_diff = "diff --git a/blueprint b/blueprint\n+"
        diff_preview = ""
        proposed_files = ["src/app/page.tsx"]
        fingerprint = "proposal-fingerprint"
        persisted = True
        status = "pending_review"
        warnings = []

    monkeypatch.setattr(cartographer_selection, "list_proposals", lambda: [Proposal()])
    preview = cartographer_selection.persist_cartographer_selection(
        proposal_id=Proposal.proposal_id, consumer="coding-executor:coder", target="src/app/page.tsx",
    )
    approval_id = issue(
        str(preview["preview_id"]), consumer="cartographer-transfer-consumer",
        operation="cartographer_selection_transfer",
    )
    with pytest.raises(CampaignApprovalError) as wrong_target:
        cartographer_selection.consume_cartographer_selection(
            approval_id=approval_id, proposal_id=Proposal.proposal_id,
                consumer="coding-executor:coder", target="src/app/other.tsx",
        )
    assert (
        wrong_target.value.reason_code
        == "cartographer_selection_target_not_proposed"
    )
    with pytest.raises(CampaignApprovalError) as wrong_consumer:
        cartographer_selection.persist_cartographer_selection(
            proposal_id=Proposal.proposal_id, consumer="unregistered-writer", target="src/app/page.tsx",
        )
    assert wrong_consumer.value.reason_code == "cartographer_selection_consumer_mismatch"


def test_cartographer_selection_rejects_unpersisted_or_unproposed_targets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Proposal:
        proposal_id = "bp-campaign1-selection-source-bound"
        approved_diff = None
        diff_preview = ""
        proposed_files = ["tests/ui-agent-trials/fixtures/dummy-product-site/README.md"]
        fingerprint = "proposal-fingerprint"
        persisted = False
        status = "pending_review"
        warnings = []

    monkeypatch.setattr(cartographer_selection, "list_proposals", lambda: [Proposal()])
    with pytest.raises(cartographer_selection.CartographerSelectionError) as unpersisted:
        cartographer_selection.persist_cartographer_selection(
            proposal_id=Proposal.proposal_id,
            consumer="coding-executor:coder",
            target=Proposal.proposed_files[0],
        )
    assert (
        unpersisted.value.reason_code
        == "cartographer_selection_proposal_not_persisted"
    )

    Proposal.persisted = True
    with pytest.raises(cartographer_selection.CartographerSelectionError) as unrelated_target:
        cartographer_selection.persist_cartographer_selection(
            proposal_id=Proposal.proposal_id,
            consumer="coding-executor:coder",
            target="src/app/page.tsx",
        )
    assert (
        unrelated_target.value.reason_code
        == "cartographer_selection_target_not_proposed"
    )
