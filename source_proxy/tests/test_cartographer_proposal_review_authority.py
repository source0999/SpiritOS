from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.cartographer import router as cartographer_router
from source_proxy.approval.campaign_authority import CampaignApprovalError
from source_proxy.cartographer.proposal_review_authority import (
    CartographerProposalReviewError,
    SERVER_ACTOR,
)


class FakeApprovalAuthority:
    def __init__(self, *, fail_success_finalize: bool = False):
        self.previews: dict[str, dict[str, Any]] = {}
        self.approvals: dict[str, dict[str, Any]] = {}
        self.events: list[str] = []
        self.fail_success_finalize = fail_success_finalize

    def __call__(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.events.append(command)
        if command == "persist-preview":
            preview_id = f"prv_review_{len(self.previews) + 1}"
            preview = {
                "id": preview_id,
                "generation": 1,
                "state": "previewed",
                "repository": payload["repository"],
                "worktree": payload["worktree"],
                "root": payload["root"],
                "target": payload["target"],
                "plugin": payload["plugin"],
                "content_hash": payload["content_hash"],
                "context_hash": payload["context"],
                "source_head": payload["source_head"],
            }
            self.previews[preview_id] = preview
            return {"preview_id": preview_id, "generation": 1, "state": "previewed"}
        if command == "lookup-preview":
            return dict(self.previews[payload["preview_id"]])
        if command == "issue":
            preview = self.previews[payload["preview_id"]]
            assert preview["state"] == "previewed"
            assert int(payload["expected_generation"]) == preview["generation"]
            preview["state"] = "approved"
            approval_id = f"apr_review_{len(self.approvals) + 1}"
            approval = {
                "approval_id": approval_id,
                "generation": preview["generation"],
                "state": "approved",
            }
            self.approvals[approval_id] = approval
            return dict(approval)
        if command == "consume":
            approval = self.approvals[payload["approval_id"]]
            assert approval["state"] == "approved"
            plan = json.loads(payload["context"])
            source = Path(plan["source"])
            target = Path(plan["target"])
            assert source.is_file()
            assert target == source or not target.exists()
            approval["state"] = "consuming"
            approval["binding"] = dict(payload)
            return {
                "approval_id": payload["approval_id"],
                "generation": approval["generation"],
                "state": "consuming",
            }
        if command == "finalize":
            approval = self.approvals[payload["approval_id"]]
            assert approval["state"] == "consuming"
            if payload["status"] == "succeeded" and self.fail_success_finalize:
                raise CampaignApprovalError("injected_review_finalization_failure")
            approval["state"] = "consumed" if payload["status"] == "succeeded" else "invalidated"
            return {
                "approval_id": payload["approval_id"],
                "generation": approval["generation"],
                "state": approval["state"],
                "result_id": payload["result_id"],
            }
        raise AssertionError(f"unexpected authority command: {command}")


def _app() -> FastAPI:
    app = FastAPI()
    app.include_router(cartographer_router)
    return app


def _write_proposal(root: Path, proposal_id: str) -> tuple[Path, Path]:
    blueprint = root / "_blueprints" / "current" / "dashboard_state.md"
    blueprint.parent.mkdir(parents=True, exist_ok=True)
    blueprint.write_text("# Dashboard state\n", encoding="utf-8")
    proposal = root / "_blueprints" / "proposals" / "pending_review" / f"{proposal_id}.json"
    proposal.parent.mkdir(parents=True, exist_ok=True)
    proposal.write_text(
        json.dumps(
            {
                "proposal_id": proposal_id,
                "status": "pending_review",
                "type": "blueprint_update",
                "component": "dashboard",
                "affected_blueprints": ["dashboard-state"],
                "changed_files": ["src/components/dashboard/Widget.tsx"],
                "proposed_files": ["_blueprints/current/dashboard_state.md"],
                "diff_preview": "diff --git a/_blueprints/current/dashboard_state.md b/_blueprints/current/dashboard_state.md\n",
                "transitions": [
                    {
                        "status": "pending_review",
                        "timestamp": "2026-07-17T10:00:00Z",
                        "actor": "cartographer",
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return proposal, blueprint


def _preview(
    client: TestClient,
    proposal_id: str,
    *,
    decision: str = "approve",
    reason: str | None = None,
) -> dict[str, Any]:
    response = client.post(
        f"/v1/cartographer/proposals/{proposal_id}/review-preview",
        json={"decision": decision, **({} if reason is None else {"reason": reason})},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _assertion(
    proposal_id: str,
    preview: dict[str, Any],
    *,
    action: str,
) -> dict[str, object]:
    return {
        "task_id": proposal_id,
        "preview_id": preview["preview"]["preview_id"],
        "generation": preview["preview"]["generation"],
        "action": action,
        "operator": SERVER_ACTOR,
    }


def test_authenticated_review_consumes_before_transaction_and_records_independent_proof() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        proposal_id = "bp-r1-review-success"
        source, blueprint = _write_proposal(root, proposal_id)
        blueprint_before = blueprint.read_bytes()
        authority = FakeApprovalAuthority()
        client = TestClient(_app())
        with (
            patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False),
            patch("source_proxy.cartographer.proposal_review_authority._call", side_effect=authority),
        ):
            preview = _preview(client, proposal_id)
            with patch(
                "source_proxy.api.cartographer.verify_operator_approval_assertion",
                return_value=_assertion(proposal_id, preview, action="approve"),
            ):
                response = client.post(
                    f"/v1/cartographer/proposals/{proposal_id}/review",
                    headers={"x-spiritos-operator-assertion": "signed"},
                    json={
                        "decision": "approve",
                        "generation": preview["preview"]["generation"],
                        "preview_id": preview["preview"]["preview_id"],
                    },
                )
            approved = root / "_blueprints" / "proposals" / "approved" / f"{proposal_id}.json"
            approved_payload = json.loads(approved.read_text(encoding="utf-8"))

        assert response.status_code == 200, response.text
        body = response.json()
        assert authority.events == ["persist-preview", "lookup-preview", "issue", "consume", "finalize"]
        assert not source.exists()
        assert approved.is_file()
        assert blueprint.read_bytes() == blueprint_before
        assert body["status"] == "review_recorded"
        assert body["max_authority"] == "proposal_review_record_only"
        assert body["actions_taken"] is False
        assert body["apply_ran"] is False
        assert approved_payload["status"] == "approved"
        assert approved_payload["transitions"][-1]["actor"] == SERVER_ACTOR
        assert approved_payload["proposal_review_authority"]["generation"] == 1
        assert approved_payload["proposal_review_authority"]["result_hash"] == body["result_hash"]
        assert "invocations" not in approved_payload["proposal_review_authority"]
        requirements = approved_payload["proposal_review_authority"][
            "participant_requirements"
        ]
        assert len(requirements) == 3
        assert all(
            "invocation_id" not in item
            and "output_id" not in item
            and "consumer_acknowledgement_id" not in item
            and "status" not in item
            for item in requirements
        )
        persisted_preview_plan = json.loads(
            authority.previews[preview["preview"]["preview_id"]]["context_hash"]
        )
        assert "invocation_records" not in persisted_preview_plan
        assert all(
            "invocation_id" not in item
            for item in persisted_preview_plan["participant_requirements"]
        )
        invocation_ids = {item["invocation_id"] for item in body["invocations"]}
        output_ids = {item["output_id"] for item in body["invocations"]}
        acknowledgement_ids = {
            item["consumer_acknowledgement_id"] for item in body["invocations"]
        }
        artifact_hashes = {item["artifact_hash"] for item in body["invocations"]}
        assert len(invocation_ids) == 3
        assert len(output_ids) == 3
        assert len(acknowledgement_ids) == 3
        assert artifact_hashes == {body["review_artifact_hash"]}
        assert {item["artifact_sha256"] for item in body["invocations"]} == {
            body["review_artifact_hash"]
        }
        assert {item["role"] for item in body["invocations"]} == {
            "cartographer-reviewer",
            "cartographer-verifier",
            "evidence-recorder",
        }
        assert {item["kind"] for item in body["invocations"]} == {
            "independent_review",
            "independent_verification",
            "evidence_recording",
        }
        assert all(
            item["schema_version"] == "cartographer.participant-invocation/v2"
            and item["status"] == "succeeded"
            and item["output_sha256"]
            and item["started_at"]
            and item["completed_at"]
            and item["consumer_acknowledgement"]["consumed"] is True
            and item["consumer_acknowledgement"]["output_id"] == item["output_id"]
            and item["consumer_acknowledgement"]["output_sha256"]
            == item["output_sha256"]
            for item in body["invocations"]
        )


def test_review_rejects_caller_authored_authority_fields_and_missing_assertion() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        proposal_id = "bp-r1-review-auth"
        source, _blueprint = _write_proposal(root, proposal_id)
        source_before = source.read_bytes()
        authority = FakeApprovalAuthority()
        client = TestClient(_app())
        with (
            patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False),
            patch("source_proxy.cartographer.proposal_review_authority._call", side_effect=authority),
        ):
            preview = _preview(client, proposal_id, decision="reject", reason="Too broad.")
            forbidden = client.post(
                f"/v1/cartographer/proposals/{proposal_id}/review",
                headers={"x-spiritos-operator-assertion": "signed"},
                json={
                    "decision": "reject",
                    "reason": "Too broad.",
                    "generation": 1,
                    "preview_id": preview["preview"]["preview_id"],
                    "actor": "caller",
                    "proposal": {"status": "approved"},
                    "target": "/tmp/caller-path",
                    "write_authority": True,
                },
            )
            missing_assertion = client.post(
                f"/v1/cartographer/proposals/{proposal_id}/review",
                json={
                    "decision": "reject",
                    "reason": "Too broad.",
                    "generation": 1,
                    "preview_id": preview["preview"]["preview_id"],
                },
            )

        assert forbidden.status_code == 422
        assert missing_assertion.status_code == 403
        assert source.read_bytes() == source_before
        assert authority.events == ["persist-preview"]


def test_snapshot_drift_cannot_consume_preview() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        proposal_id = "bp-r1-review-drift"
        source, _blueprint = _write_proposal(root, proposal_id)
        authority = FakeApprovalAuthority()
        client = TestClient(_app())
        with (
            patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False),
            patch("source_proxy.cartographer.proposal_review_authority._call", side_effect=authority),
        ):
            preview = _preview(client, proposal_id, decision="reject", reason="Too broad.")
            payload = json.loads(source.read_text(encoding="utf-8"))
            payload["component"] = "caller-drift"
            source.write_text(json.dumps(payload), encoding="utf-8")
            with patch(
                "source_proxy.api.cartographer.verify_operator_approval_assertion",
                return_value=_assertion(proposal_id, preview, action="reject"),
            ):
                response = client.post(
                    f"/v1/cartographer/proposals/{proposal_id}/review",
                    headers={"x-spiritos-operator-assertion": "signed"},
                    json={
                        "decision": "reject",
                        "reason": "Too broad.",
                        "generation": 1,
                        "preview_id": preview["preview"]["preview_id"],
                    },
                )

        assert response.status_code == 422
        assert response.json()["detail"]["reason_code"] == "proposal_review_snapshot_drift"
        assert authority.events == ["persist-preview", "lookup-preview"]
        assert source.is_file()


def test_decision_and_reason_are_bound_to_the_server_preview() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        proposal_id = "bp-r1-review-decision-binding"
        source, _blueprint = _write_proposal(root, proposal_id)
        source_before = source.read_bytes()
        authority = FakeApprovalAuthority()
        client = TestClient(_app())
        with (
            patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False),
            patch("source_proxy.cartographer.proposal_review_authority._call", side_effect=authority),
        ):
            preview = _preview(client, proposal_id, decision="reject", reason="Exact reason.")
            with patch(
                "source_proxy.api.cartographer.verify_operator_approval_assertion",
                return_value=_assertion(proposal_id, preview, action="reject"),
            ):
                response = client.post(
                    f"/v1/cartographer/proposals/{proposal_id}/review",
                    headers={"x-spiritos-operator-assertion": "signed"},
                    json={
                        "decision": "reject",
                        "reason": "Changed reason.",
                        "generation": 1,
                        "preview_id": preview["preview"]["preview_id"],
                    },
                )

        assert response.status_code == 422
        assert response.json()["detail"]["reason_code"] == "proposal_review_reason_mismatch"
        assert authority.events == ["persist-preview", "lookup-preview"]
        assert source.read_bytes() == source_before


def test_verification_failure_rolls_back_and_invalidates_consuming_approval() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        proposal_id = "bp-r1-review-verify-fail"
        source, _blueprint = _write_proposal(root, proposal_id)
        source_before = source.read_bytes()
        authority = FakeApprovalAuthority()
        client = TestClient(_app())
        with (
            patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False),
            patch("source_proxy.cartographer.proposal_review_authority._call", side_effect=authority),
        ):
            preview = _preview(client, proposal_id)
            with (
                patch(
                    "source_proxy.api.cartographer.verify_operator_approval_assertion",
                    return_value=_assertion(proposal_id, preview, action="approve"),
                ),
                patch(
                    "source_proxy.cartographer.proposal_review_authority._invoke_independent_verification",
                    side_effect=CartographerProposalReviewError(
                        "injected verification failure",
                        "proposal_review_verification_failed",
                    ),
                ),
            ):
                response = client.post(
                    f"/v1/cartographer/proposals/{proposal_id}/review",
                    headers={"x-spiritos-operator-assertion": "signed"},
                    json={
                        "decision": "approve",
                        "generation": 1,
                        "preview_id": preview["preview"]["preview_id"],
                    },
                )
            approved = root / "_blueprints" / "proposals" / "approved" / f"{proposal_id}.json"

        assert response.status_code == 422
        assert response.json()["detail"]["reason_code"] == "proposal_review_verification_failed"
        assert source.read_bytes() == source_before
        assert not approved.exists()
        assert next(iter(authority.approvals.values()))["state"] == "invalidated"
        assert authority.events[-1] == "finalize"


def test_finalization_failure_rolls_back_and_leaves_explicit_non_success() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        proposal_id = "bp-r1-review-finalize-fail"
        source, _blueprint = _write_proposal(root, proposal_id)
        source_before = source.read_bytes()
        authority = FakeApprovalAuthority(fail_success_finalize=True)
        client = TestClient(_app())
        with (
            patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False),
            patch("source_proxy.cartographer.proposal_review_authority._call", side_effect=authority),
        ):
            preview = _preview(client, proposal_id)
            with patch(
                "source_proxy.api.cartographer.verify_operator_approval_assertion",
                return_value=_assertion(proposal_id, preview, action="approve"),
            ):
                response = client.post(
                    f"/v1/cartographer/proposals/{proposal_id}/review",
                    headers={"x-spiritos-operator-assertion": "signed"},
                    json={
                        "decision": "approve",
                        "generation": 1,
                        "preview_id": preview["preview"]["preview_id"],
                    },
                )
            approved = root / "_blueprints" / "proposals" / "approved" / f"{proposal_id}.json"

        assert response.status_code == 422
        assert response.json()["detail"]["reason_code"] == "injected_review_finalization_failure"
        assert source.read_bytes() == source_before
        assert not approved.exists()
        assert next(iter(authority.approvals.values()))["state"] == "invalidated"
        assert authority.events[-2:] == ["finalize", "finalize"]


def test_preview_requires_a_persisted_proposal_and_rejects_caller_snapshot() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        (root / "_blueprints" / "proposals").mkdir(parents=True)
        authority = FakeApprovalAuthority()
        client = TestClient(_app())
        with (
            patch.dict(os.environ, {"SPIRIT_PROJECT_PATH": str(root)}, clear=False),
            patch("source_proxy.cartographer.proposal_review_authority._call", side_effect=authority),
        ):
            response = client.post(
                "/v1/cartographer/proposals/bp-generated/review-preview",
                json={
                    "decision": "reject",
                    "proposal": {"proposal_id": "bp-generated", "status": "pending_review"},
                },
            )
            no_snapshot = client.post(
                "/v1/cartographer/proposals/bp-generated/review-preview",
                json={"decision": "reject"},
            )

        assert response.status_code == 422
        assert no_snapshot.status_code == 422
        assert no_snapshot.json()["detail"]["reason_code"] == "persisted_proposal_not_found"
        assert authority.events == []
