"""Durable production owner for the core SpiritOS coding lifecycle."""
from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import os
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from source_proxy.cartographer.cartographer_selection_authority import (
    CartographerSelectionError,
    consume_cartographer_selection,
    finalize_cartographer_selection,
)
from source_proxy.cartographer.lane_registry import (
    CORE_CODING_LANE_IDS,
    build_canonical_coding_lane_registry,
    validate_lane_registry_record,
)
from source_proxy.coding.participants import (
    acknowledge_coding_participant_output,
    build_applied_artifact,
    run_coding_anti_cheat,
    run_coding_evidence_recorder,
    run_coding_reviewer,
    run_coding_verifier,
    validate_coding_participant_record,
)
from source_proxy.coding.runtime_lane_boundary import RuntimeLaneBoundary
from source_proxy.coding.recovery import (
    RECOVERY_PARTICIPANT_SCHEMA,
    ControlledRecoveryLineage,
    RecoveryPolicy,
    build_failed_participant_event,
)
from source_proxy.context.canonical_broker import build_context_broker_report
from source_proxy.contracts.coding_lane_contracts import canonical_coding_lane_contracts
from source_proxy.approval.campaign_authority import (
    CampaignApprovalError,
    current_head,
    finalize_coding_execution_approval,
)
from source_proxy.planning.plan import load_plan
from source_proxy.routing.litellm_router import route_model_for_alias, route_provider_for_alias
from source_proxy.target_plugins.adapter import (
    ResolvedTargetPlugin,
    execute_target_plugin_command,
)
from source_proxy.target_plugins.lumacart import is_lumacart_prompt_id
from source_proxy.tasks.long_running import (
    acknowledge_task_context_consumer,
    advance_long_running_task,
    canonical_context_broker_for_task,
    coding_orchestrator_state_for_task,
    execute_approved_long_running_task,
    fail_orchestrated_coding_execution,
    finalize_orchestrated_coding_execution,
    prepare_orchestrated_coding_finalization,
    record_canonical_context_broker_for_task,
    record_coding_orchestrator_state,
    record_post_apply_verification,
    LongRunningTaskError,
)


ORCHESTRATOR_SCHEMA = "coding-orchestrator/v2"
ORCHESTRATOR_CONSUMER_VERSION = "coding-orchestrator/v1"
LANE_SEQUENCE = CORE_CODING_LANE_IDS
REQUIRED_PARTICIPANT_ROLES = (
    "coding-executor",
    "coding-reviewer",
    "coding-verifier",
    "coding-anti-cheat",
    "evidence-recorder",
)
LANE_TO_CONTEXT_CONSUMER = {
    "planner": "planner",
    "coder": "coder",
    "reviewer": "reviewer",
    "verifier": "verifier",
    "anti-cheat": "verifier",
    "repair": "repair_loop",
    "evidence-recorder": "final_receipt_builder",
}
LANE_STATES = {
    "pending",
    "running",
    "completed",
    "failed",
    "blocked",
    "skipped",
    "recovering",
}
ALLOWED_LANE_TRANSITIONS = {
    "pending": {"running", "blocked", "skipped"},
    "running": {"completed", "failed", "blocked"},
    "failed": {"recovering", "blocked"},
    "recovering": {"running", "completed", "failed", "blocked"},
    "completed": set(),
    "blocked": set(),
    "skipped": set(),
}


class CodingOrchestratorError(ValueError):
    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclasses.dataclass
class CodingLaneStateMachine:
    task_id: str
    run_id: str
    attempt_id: str = dataclasses.field(default_factory=lambda: f"coding-attempt-{uuid4().hex}")
    parent_attempt_id: str | None = None
    lane_states: dict[str, str] = dataclasses.field(
        default_factory=lambda: {lane_id: "pending" for lane_id in LANE_SEQUENCE}
    )
    lane_reasons: dict[str, str] = dataclasses.field(default_factory=dict)
    causal_events: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    runtime_outputs: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    runtime_acknowledgements: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    runtime_consumptions: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    required_output_ids: list[str] = dataclasses.field(default_factory=list)
    participant_records: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    immutable_artifact: dict[str, Any] | None = None
    target_plugin_proposal: dict[str, Any] | None = None
    cartographer_selection_consumption: dict[str, Any] | None = None
    cartographer_transfer: dict[str, Any] | None = None
    cartographer_finalization: dict[str, Any] | None = None
    authority_finalization: dict[str, Any] | None = None
    recovery_lineage: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    model_invocations: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    created_at: str = dataclasses.field(default_factory=lambda: _utc_now())
    updated_at: str = dataclasses.field(default_factory=lambda: _utc_now())

    def transition(self, lane_id: str, next_state: str, *, reason: str = "") -> None:
        if lane_id not in LANE_SEQUENCE:
            raise CodingOrchestratorError("unknown_coding_lane")
        if next_state not in LANE_STATES:
            raise CodingOrchestratorError("unknown_coding_lane_state")
        current = self.lane_states[lane_id]
        if next_state not in ALLOWED_LANE_TRANSITIONS[current]:
            raise CodingOrchestratorError(
                f"invalid_coding_lane_transition:{lane_id}:{current}:{next_state}"
            )
        self.lane_states[lane_id] = next_state
        if reason:
            self.lane_reasons[lane_id] = reason
        self.record_event(
            event_type="lane_transition",
            lane_id=lane_id,
            status_before=current,
            status_after=next_state,
            detail={"reason": reason},
        )

    def record_event(
        self,
        *,
        event_type: str,
        lane_id: str | None = None,
        status_before: str | None = None,
        status_after: str | None = None,
        detail: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        parent_event_id = self.causal_events[-1]["event_id"] if self.causal_events else None
        event = {
            "schema_version": "coding.orchestrator-event/v1",
            "event_id": f"coding-event-{uuid4().hex}",
            "parent_event_id": parent_event_id,
            "run_id": self.run_id,
            "attempt_id": self.attempt_id,
            "task_id": self.task_id,
            "event_type": event_type,
            "lane_id": lane_id,
            "status_before": status_before,
            "status_after": status_after,
            "detail": json.loads(json.dumps(dict(detail or {}), sort_keys=True, default=str)),
            "recorded_at": _utc_now(),
        }
        self.causal_events.append(event)
        self.updated_at = event["recorded_at"]
        return event

    def receipt(self, *, summary: str) -> dict[str, Any]:
        return {
            "schema_version": ORCHESTRATOR_SCHEMA,
            "run_id": self.run_id,
            "attempt_id": self.attempt_id,
            "parent_attempt_id": self.parent_attempt_id,
            "task_id": self.task_id,
            "lane_sequence": list(LANE_SEQUENCE),
            "lane_states": dict(self.lane_states),
            "lane_reasons": dict(self.lane_reasons),
            "causal_events": list(self.causal_events),
            "runtime_outputs": list(self.runtime_outputs),
            "runtime_acknowledgements": list(self.runtime_acknowledgements),
            "runtime_consumptions": list(self.runtime_consumptions),
            "required_output_ids": list(self.required_output_ids),
            "participant_records": list(self.participant_records),
            "immutable_artifact": dict(self.immutable_artifact) if self.immutable_artifact else None,
            "target_plugin_proposal": (
                dict(self.target_plugin_proposal) if self.target_plugin_proposal else None
            ),
            "cartographer_selection_consumption": (
                dict(self.cartographer_selection_consumption)
                if self.cartographer_selection_consumption
                else None
            ),
            "cartographer_transfer": dict(self.cartographer_transfer) if self.cartographer_transfer else None,
            "cartographer_finalization": (
                dict(self.cartographer_finalization) if self.cartographer_finalization else None
            ),
            "authority_finalization": (
                dict(self.authority_finalization) if self.authority_finalization else None
            ),
            "recovery_lineage": list(self.recovery_lineage),
            "model_invocations": list(self.model_invocations),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "summary": summary,
            "authoritative": True,
        }


class CodingOrchestrator:
    """Own task creation, execution, verification, recovery, and final result."""

    def __init__(
        self,
        *,
        executor: Callable[..., dict[str, Any]] = execute_approved_long_running_task,
        planner_loader: Callable[[str], Any] = load_plan,
        post_apply_verifier: Callable[..., dict[str, Any]] = record_post_apply_verification,
        state_loader: Callable[[str], dict[str, Any] | None] = coding_orchestrator_state_for_task,
        reviewer: Callable[[Mapping[str, Any]], dict[str, Any]] = run_coding_reviewer,
        verifier: Callable[[Mapping[str, Any], Mapping[str, Any]], dict[str, Any]] = run_coding_verifier,
        anti_cheat: Callable[..., dict[str, Any]] = run_coding_anti_cheat,
        evidence_recorder: Callable[..., dict[str, Any]] = run_coding_evidence_recorder,
    ) -> None:
        self._executor = executor
        self._planner_loader = planner_loader
        self._post_apply_verifier = post_apply_verifier
        self._state_loader = state_loader
        self._reviewer = reviewer
        self._verifier = verifier
        self._anti_cheat = anti_cheat
        self._evidence_recorder = evidence_recorder

    def start(self, task_id: str, *, sources: list[dict[str, Any]]) -> dict[str, Any]:
        if not task_id.strip():
            raise CodingOrchestratorError("coding_task_id_missing")
        try:
            existing = self._state_loader(task_id)
        except LongRunningTaskError as error:
            if error.reason_code != "not_found":
                raise
            existing = None
        if isinstance(existing, Mapping):
            restored = self._restore(task_id)
            if restored.task_id == task_id:
                return restored.receipt(summary="coding run already initialized")
        registry = build_canonical_coding_lane_registry()
        if tuple(record.lane_id for record in registry) != LANE_SEQUENCE:
            raise CodingOrchestratorError("canonical_coding_lane_registry_mismatch")
        for record in registry:
            if not validate_lane_registry_record(record).accepted:
                raise CodingOrchestratorError(
                    f"canonical_coding_lane_registry_invalid:{record.lane_id}"
                )

        run = CodingLaneStateMachine(
            task_id=task_id,
            run_id=f"coding-run-{uuid4().hex}",
        )
        run.record_event(
            event_type="run_requested",
            detail={"requested_lane": "core-coding", "source_count": len(sources)},
        )
        report = build_context_broker_report(sources, applicable_consumers=("planner",))
        record_canonical_context_broker_for_task(
            task_id,
            report=report,
            orchestrator_run_id=run.run_id,
        )
        run.transition("context-broker", "running", reason="canonical_context_report_persisted")
        self._enforce_runtime_contract_output(
            run,
            lane_id="context-broker",
            producer_invocation_id=f"context-broker-invocation-{uuid4().hex}",
            payload={
                "context_hash": str(report.get("canonical_report_hash") or ""),
                "verdict": str(report.get("verdict") or "UNKNOWN"),
            },
        )
        return self._persist(
            run,
            "coding run initialized; planner must consume canonical context",
        )

    def start_from_cartographer_selection(
        self,
        task_id: str,
        *,
        selection_approval_id: str,
        proposal_id: str,
        target: str,
        sources: list[dict[str, Any]],
    ) -> dict[str, Any]:
        selection = consume_cartographer_selection(
            approval_id=selection_approval_id,
            proposal_id=proposal_id,
            consumer="coding-executor:coder",
            target=target,
        )
        receipt = self.start(task_id, sources=sources)
        if not str(receipt.get("run_id") or ""):
            raise CodingOrchestratorError(
                "cartographer_run_persistence_missing_after_selection_consumption"
            )
        run = self._restore(task_id)
        transfer_event = run.record_event(
            event_type="cartographer_transfer_pending_downstream_consumption",
            detail={"proposal_id": proposal_id, "selection_approval_id": selection_approval_id},
        )
        transfer = {
            "schema_version": "cartographer.coding-transfer/v1",
            "proposal_id": proposal_id,
            "selection_id": selection_approval_id,
            "selection_approval_id": selection_approval_id,
            "selection_generation": int(selection["generation"]),
            "consumer": "coding-executor:coder",
            "target": target,
            "task_id": task_id,
            "run_id": run.run_id,
            "transfer_event_id": transfer_event["event_id"],
            "downstream_consumer_invocation_id": None,
            "provenance": {
                "content_hash": selection["binding"].get("content_hash"),
                "context": selection["binding"].get("context"),
                "preview_id": selection["binding"].get("preview"),
                "source_head": selection["binding"].get("source_head"),
            },
        }
        transfer_event["detail"] = dict(transfer)
        run.cartographer_selection_consumption = dict(selection)
        run.cartographer_transfer = transfer
        receipt = self._persist(
            run,
            "coding run initialized with Cartographer transfer pending a real downstream invocation",
        )
        receipt["cartographer_selection"] = transfer
        return receipt

    def _finalize_cartographer_transfer_after_invocation(
        self,
        run: CodingLaneStateMachine,
        *,
        participant: Mapping[str, Any],
        target: str,
    ) -> None:
        """Finalize a pending transfer only after a real downstream output exists."""

        transfer = run.cartographer_transfer
        if not isinstance(transfer, dict):
            return
        consumer_invocation_id = str(participant.get("invocation_id") or "")
        finalization = run.cartographer_finalization
        if isinstance(finalization, Mapping) and finalization.get("state") == "consumed":
            acknowledgement = finalization.get("downstream_acknowledgement")
            if not isinstance(acknowledgement, Mapping) or (
                acknowledgement.get("consumer_invocation_id") != consumer_invocation_id
            ):
                raise CodingOrchestratorError(
                    "cartographer_transfer_consumer_invocation_mismatch"
                )
            return
        selection = run.cartographer_selection_consumption
        if not isinstance(selection, dict):
            raise CodingOrchestratorError("cartographer_selection_consumption_missing")
        if str(transfer.get("target") or "") != target:
            raise CodingOrchestratorError("cartographer_transfer_target_mismatch")
        provenance = transfer.get("provenance")
        if not isinstance(provenance, Mapping) or provenance.get("source_head") != current_head():
            raise CodingOrchestratorError("cartographer_transfer_source_head_mismatch")
        required_participant_fields = (
            "invocation_id",
            "output_id",
            "output_sha256",
            "artifact_sha256",
            "completed_at",
        )
        if participant.get("passed") is not True or any(
            not str(participant.get(field) or "").strip()
            for field in required_participant_fields
        ):
            raise CodingOrchestratorError(
                "cartographer_downstream_completed_output_missing"
            )

        transfer = dict(transfer)
        transfer["downstream_consumer_invocation_id"] = consumer_invocation_id
        acknowledgement = {
            "schema_version": "cartographer.downstream-acknowledgement/v2",
            "acknowledgement_id": f"cartographer-ack-{uuid4().hex}",
            "transfer_event_id": transfer["transfer_event_id"],
            "consumer_invocation_id": consumer_invocation_id,
            "consumer_output_id": str(participant["output_id"]),
            "consumer_output_sha256": str(participant["output_sha256"]),
            "consumer_artifact_sha256": str(participant["artifact_sha256"]),
            "consumer_completed_at": str(participant["completed_at"]),
            "consumer_passed": True,
            "proposal_id": transfer["proposal_id"],
            "selection_id": transfer["selection_id"],
            "task_id": run.task_id,
            "run_id": run.run_id,
            "consumed": True,
        }
        run.cartographer_transfer = transfer
        run.cartographer_finalization = {
            "state": "pending_authority_finalization",
            "downstream_acknowledgement": acknowledgement,
        }
        run.record_event(
            event_type="cartographer_transfer_consumed_by_downstream_output",
            lane_id="coder",
            detail={
                "transfer_event_id": transfer["transfer_event_id"],
                "consumer_invocation_id": consumer_invocation_id,
                "consumer_output_id": str(participant["output_id"]),
                "consumer_artifact_sha256": str(participant["artifact_sha256"]),
                "acknowledgement_id": acknowledgement["acknowledgement_id"],
            },
        )
        self._persist(
            run,
            "persisted completed Cartographer downstream output before authority finalization",
        )
        try:
            finalized = finalize_cartographer_selection(
                consumed=selection,
                proposal_id=str(transfer["proposal_id"]),
                consumer=str(transfer["consumer"]),
                target=target,
                transfer=transfer,
                downstream_acknowledgement=acknowledgement,
            )
        except CartographerSelectionError as error:
            run.cartographer_finalization = {
                "state": "failed",
                "reason_code": error.reason_code,
                "downstream_acknowledgement": acknowledgement,
            }
            self._persist(run, "Cartographer transfer authority finalization failed closed")
            raise CodingOrchestratorError(error.reason_code) from error
        authority_receipt = {
            "approval_id": finalized["receipt"].get("approval_id"),
            "generation": finalized["receipt"].get("generation"),
            "state": finalized["receipt"].get("state"),
            "result_id": finalized["receipt"].get("result_id"),
        }
        if authority_receipt["state"] != "consumed":
            raise CodingOrchestratorError("cartographer_transfer_finalization_not_consumed")
        run.cartographer_finalization = {
            "state": "consumed",
            "authority_receipt": authority_receipt,
            "downstream_acknowledgement": acknowledgement,
        }
        run.record_event(
            event_type="cartographer_transfer_finalized",
            lane_id="coder",
            detail={
                "transfer_event_id": transfer["transfer_event_id"],
                "consumer_invocation_id": consumer_invocation_id,
                "acknowledgement_id": acknowledgement["acknowledgement_id"],
                "authority_state": "consumed",
            },
        )
        self._persist(run, "Cartographer transfer finalized for real downstream invocation")

    def acknowledge_planner(self, task_id: str) -> dict[str, Any]:
        run = self._restore(task_id)
        if run.lane_states["planner"] == "completed":
            return run.receipt(summary="planner already completed")
        plan = self._planner_loader(task_id)
        if plan is None:
            run.transition("planner", "blocked", reason="authoritative_plan_missing")
            self._persist(run, "planner blocked: authoritative plan missing")
            raise CodingOrchestratorError("authoritative_plan_missing")
        report = self._acknowledge_persisted_context(
            task_id,
            consumer="planner",
            evidence="authoritative_plan_loaded_for_canonical_coding_run",
            reason="planner_consumed_canonical_context",
        )
        if report.get("go_eligible") is not True:
            run.transition(
                "planner", "blocked", reason="planner_context_acknowledgement_blocked"
            )
            self._persist(run, "planner blocked by canonical context")
            raise CodingOrchestratorError("planner_context_acknowledgement_blocked")
        context_output = self._issue_refreshed_context_output(
            run,
            report=report,
            refresh_reason="planner_acknowledgement_persisted_before_planner_invocation",
        )
        self._persist(run, "refreshed canonical context persisted before planner invocation")

        planner_invocation_id = f"planner-invocation-{uuid4().hex}"
        run.transition("planner", "running", reason="loading_authoritative_plan")
        self._consume_output(
            run,
            output_id=context_output["output_id"],
            consumer_invocation_id=planner_invocation_id,
            payload={
                "consumer": "planner",
                "context_hash": str(report["canonical_report_hash"]),
            },
        )
        plan_payload = plan.to_dict() if hasattr(plan, "to_dict") else dict(plan)
        self._enforce_runtime_contract_output(
            run,
            lane_id="planner",
            producer_invocation_id=planner_invocation_id,
            payload={
                "plan_id": str(plan_payload.get("task_id") or task_id),
                "task_spec": plan_payload,
            },
        )
        run.transition("planner", "completed", reason="authoritative_plan_loaded")
        run.transition("context-broker", "completed", reason="planner_context_consumed")
        return self._persist(run, "planner completed with consumed canonical context")

    def advance(
        self,
        task_id: str,
        *,
        proposed_diff: str | None = None,
        sandbox_result: dict[str, Any] | None = None,
        test_command: list[str] | None = None,
    ) -> dict[str, Any]:
        """Own the legacy architect/coder/debugger advance behind durable events."""

        run = self._restore(task_id)
        requested = run.record_event(
            event_type="task_advance_requested",
            detail={
                "has_proposed_diff": bool(str(proposed_diff or "").strip()),
                "has_sandbox_result": isinstance(sandbox_result, dict),
                "test_command_count": len(test_command or []),
            },
        )
        self._persist(run, "task advance entered canonical orchestrator")
        try:
            advanced = advance_long_running_task(
                task_id,
                proposed_diff=proposed_diff,
                sandbox_result=sandbox_result,
                test_command=test_command,
            )
        except Exception as error:
            run = self._restore(task_id)
            run.record_event(
                event_type="task_advance_failed",
                detail={
                    "request_event_id": requested["event_id"],
                    "error": type(error).__name__,
                    "message": str(error)[:500],
                },
            )
            self._persist(run, "task advance failed inside canonical orchestrator")
            raise
        run = self._restore(task_id)
        run.record_event(
            event_type="task_advance_completed",
            detail={
                "request_event_id": requested["event_id"],
                "task_status": str(advanced.get("task", {}).get("status") or "unknown"),
            },
        )
        receipt = self._persist(run, "task advance completed inside canonical orchestrator")
        response = dict(advanced)
        response["coding_orchestrator"] = receipt
        return response

    def propose_target_plugin(
        self,
        task_id: str,
        *,
        plugin: ResolvedTargetPlugin,
        task: str,
    ) -> dict[str, Any]:
        """Run a real target-owned model proposal and persist any controlled fallback."""

        run = self._restore(task_id)
        if run.lane_states["planner"] != "completed":
            self.acknowledge_planner(task_id)
            run = self._restore(task_id)
        if str(plugin.source_head or "") != current_head():
            raise CodingOrchestratorError("target_plugin_source_head_mismatch")
        primary_invocation_id = f"target-plugin-model-invocation-{uuid4().hex}"
        context = self._acknowledge_persisted_context(
            task_id,
            consumer="coder",
            evidence="target_plugin_command_consumed_canonical_context",
            reason="coder_consumed_context_before_target_plugin_command",
        )
        if context.get("go_eligible") is not True:
            raise CodingOrchestratorError("target_plugin_canonical_context_blocked")
        primary_context_binding = self._bind_context_to_invocation(
            run,
            report=context,
            consumer_invocation_id=primary_invocation_id,
            refresh_reason="coder_acknowledgement_persisted_before_target_plugin_invocation",
        )
        invocation_event = run.record_event(
            event_type="target_plugin_model_invocation",
            lane_id="coder",
            detail={
                "invocation_id": primary_invocation_id,
                "plugin_id": plugin.plugin_id,
                "selected_prompt_id": plugin.selected_prompt_id,
                "target_plugin_identity": plugin.evidence_identity(),
                "canonical_context_report_hash": context["canonical_report_hash"],
                "context_runtime_output_id": primary_context_binding["output_id"],
                "context_consumer_acknowledgement_id": primary_context_binding[
                    "acknowledgement_id"
                ],
                "context_consumption_id": primary_context_binding["consumption_id"],
            },
        )
        self._persist(run, "target-plugin model invocation started")

        input_sha256 = _sha256_json(
            {
                "task": task,
                "target_plugin_identity": plugin.evidence_identity(),
                "canonical_context_report_hash": context.get("canonical_report_hash"),
                "canonical_context_report": context,
            }
        )
        primary_alias = os.getenv("SPIRITOS_CODING_PRIMARY_MODEL_ALIAS", "").strip() or None
        primary_started_at = _utc_now()
        primary_result = execute_target_plugin_command(
            plugin,
            task=task,
            workspace_root=Path(plugin.workspace_root),
            canonical_context=context,
            canonical_context_text=json.dumps(context, sort_keys=True),
            model_alias=primary_alias,
        )
        primary_completed_at = _utc_now()
        if _is_truthful_non_mutating_target_result(primary_result):
            outcome = {
                "schema_version": "coding.target-plugin-outcome/v1",
                "task_id": task_id,
                "run_id": run.run_id,
                "target_plugin_identity": plugin.evidence_identity(),
                "selected_prompt_id": plugin.selected_prompt_id,
                "selected_context_id": plugin.selected_context_id,
                "context_hash": str(context.get("canonical_report_hash") or ""),
                "source_head": current_head(),
                "invocation_id": primary_invocation_id,
                "outcome": (
                    "noop"
                    if bool(
                        primary_result.get("already_satisfied")
                        or primary_result.get("alreadySatisfied")
                    )
                    else "blocked"
                ),
                "reason_code": str(
                    primary_result.get("reason_code")
                    or primary_result.get("reasonCode")
                    or "target_plugin_non_mutating_result"
                ),
                "target_adapter_provenance": dict(
                    primary_result.get("target_adapter_provenance") or {}
                ),
                "terminal_proof_eligible": False,
                "claim_ceiling": "truthful_non_mutating_target_outcome_only",
                "status": "non_mutating_terminal",
            }
            outcome["proposal_binding_sha256"] = _sha256_json(outcome)
            run.target_plugin_proposal = outcome
            run.record_event(
                event_type="target_plugin_non_mutating_result",
                lane_id="coder",
                detail={
                    "selected_prompt_id": plugin.selected_prompt_id,
                    "invocation_id": primary_invocation_id,
                    "outcome": outcome["outcome"],
                    "reason_code": outcome["reason_code"],
                },
            )
            receipt = self._persist(run, "target-plugin returned a truthful non-mutating result")
            receipt["target_plugin_result"] = primary_result
            return receipt
        primary_participant = _target_plugin_model_participant(
            run=run,
            task_id=task_id,
            attempt_id=run.attempt_id,
            input_sha256=input_sha256,
            result=primary_result,
            configured_alias=primary_alias,
            invocation_id=primary_invocation_id,
            started_at=primary_started_at,
            completed_at=primary_completed_at,
        )
        run.model_invocations.append(primary_participant)
        selected_result = primary_result
        selected_participant = primary_participant

        if primary_participant["passed"] is not True:
            fallback_alias = os.getenv("SPIRITOS_CODING_FALLBACK_MODEL_ALIAS", "").strip()
            if not fallback_alias:
                run.record_event(
                    event_type="target_plugin_model_failed",
                    lane_id="coder",
                    detail={
                        "invocation_id": primary_participant["invocation_id"],
                        "error_code": primary_participant["error_code"],
                        "recovery_available": False,
                    },
                )
                self._persist(run, "target-plugin model failed without proof-eligible recovery")
                raise CodingOrchestratorError(str(primary_participant["error_code"]))

            failure_event = build_failed_participant_event(
                primary_participant,
                parent_event_id=invocation_event["event_id"],
                recorded_at=primary_completed_at,
            )
            replacement_attempt_id = f"coding-attempt-{uuid4().hex}"
            replacement_provider = route_provider_for_alias(fallback_alias) or "model-router"
            replacement_model = route_model_for_alias(fallback_alias) or fallback_alias
            fallback_started_at = _utc_now()
            authorization = ControlledRecoveryLineage.authorize(
                failed_event=failure_event,
                failed_participant=primary_participant,
                policy=RecoveryPolicy(
                    allow_fallback=True,
                    allowed_replacement_routes=((replacement_provider, replacement_model),),
                ),
                decision="fallback",
                replacement_attempt_id=replacement_attempt_id,
                replacement_provider=replacement_provider,
                replacement_model=replacement_model,
                recorded_at=fallback_started_at,
            )
            self._upsert_controlled_recovery(run, authorization)
            self._persist(
                run,
                "primary model failure and authorized fallback persisted before replacement call",
            )
            fallback_invocation_id = f"target-plugin-model-invocation-{uuid4().hex}"
            fallback_context_binding = self._bind_context_to_invocation(
                run,
                report=context,
                consumer_invocation_id=fallback_invocation_id,
                refresh_reason="canonical_context_reissued_for_authorized_fallback",
            )
            run.record_event(
                event_type="target_plugin_model_invocation",
                lane_id="coder",
                detail={
                    "invocation_id": fallback_invocation_id,
                    "plugin_id": plugin.plugin_id,
                    "selected_prompt_id": plugin.selected_prompt_id,
                    "target_plugin_identity": plugin.evidence_identity(),
                    "canonical_context_report_hash": context["canonical_report_hash"],
                    "context_runtime_output_id": fallback_context_binding["output_id"],
                    "context_consumer_acknowledgement_id": fallback_context_binding[
                        "acknowledgement_id"
                    ],
                    "context_consumption_id": fallback_context_binding["consumption_id"],
                    "recovery_id": authorization.to_payload()["recovery_id"],
                },
            )
            self._persist(run, "fallback context consumption persisted before replacement call")
            fallback_result = execute_target_plugin_command(
                plugin,
                task=task,
                workspace_root=Path(plugin.workspace_root),
                canonical_context=context,
                canonical_context_text=json.dumps(context, sort_keys=True),
                model_alias=fallback_alias,
            )
            fallback_completed_at = _utc_now()
            fallback_participant = _target_plugin_model_participant(
                run=run,
                task_id=task_id,
                attempt_id=replacement_attempt_id,
                input_sha256=input_sha256,
                result=fallback_result,
                configured_alias=fallback_alias,
                invocation_id=fallback_invocation_id,
                started_at=fallback_started_at,
                completed_at=fallback_completed_at,
            )
            completed_recovery = authorization.complete(
                replacement_participant=fallback_participant,
                recorded_at=_utc_now(),
            )
            run.model_invocations.append(fallback_participant)
            self._upsert_controlled_recovery(run, completed_recovery)
            selected_result = fallback_result
            selected_participant = fallback_participant
            selected_context_binding = fallback_context_binding
            if completed_recovery.proof_eligible is not True:
                self._persist(run, "target-plugin fallback failed in the same run lineage")
                raise CodingOrchestratorError(str(fallback_participant["error_code"]))
        else:
            selected_context_binding = primary_context_binding

        proposed_diff = str(selected_result.get("proposed_diff") or "")
        diagnostics = _coder_diagnostics(selected_result)
        changed_files = [str(value) for value in diagnostics.get("changed_files", [])]
        if not proposed_diff.strip():
            run.record_event(
                event_type="target_plugin_non_mutating_result",
                lane_id="coder",
                detail={
                    "selected_prompt_id": plugin.selected_prompt_id,
                    "reason_code": str(selected_result.get("reason_code") or "target_plugin_no_diff"),
                },
            )
            receipt = self._persist(run, "target-plugin returned a truthful non-mutating result")
            receipt["target_plugin_result"] = selected_result
            return receipt

        if isinstance(run.cartographer_transfer, Mapping) and str(
            run.cartographer_transfer.get("target") or ""
        ) not in changed_files:
            raise CodingOrchestratorError("cartographer_transfer_proposal_target_mismatch")
        if not changed_files:
            raise CodingOrchestratorError("target_plugin_changed_files_missing")
        if isinstance(run.cartographer_transfer, dict):
            transfer_target = str(run.cartographer_transfer.get("target") or "")
            if not transfer_target.startswith(str(plugin.fixture_root or "")):
                raise CodingOrchestratorError("cartographer_target_plugin_scope_mismatch")
            self._finalize_cartographer_transfer_after_invocation(
                run,
                participant=selected_participant,
                target=transfer_target,
            )
        proposal_target = (
            str(run.cartographer_transfer.get("target"))
            if isinstance(run.cartographer_transfer, Mapping)
            else (changed_files[0] if changed_files else "")
        )
        output = self._enforce_runtime_contract_output(
            run,
            lane_id="coder",
            producer_invocation_id=str(selected_participant["invocation_id"]),
            payload={"approved_diff": proposed_diff, "changed_files": changed_files},
        )
        proposal_body = {
            "schema_version": "coding.target-plugin-proposal/v1",
            "task_id": task_id,
            "run_id": run.run_id,
            "runtime_output_id": output["output_id"],
            "runtime_output_artifact_sha256": output["artifact_hash"],
            "producer_model_invocation_id": selected_participant["invocation_id"],
            "producer_model_output_sha256": selected_participant["output_sha256"],
            "producer_model_artifact_sha256": selected_participant["artifact_sha256"],
            "model_output_provenance": _target_plugin_model_output_provenance(
                selected_result
            ),
            "target_adapter_provenance": dict(
                selected_result.get("target_adapter_provenance") or {}
            ),
            "target_plugin_identity": plugin.evidence_identity(),
            "selected_prompt_id": plugin.selected_prompt_id,
            "selected_context_id": plugin.selected_context_id,
            "context_hash": str(context.get("canonical_report_hash") or ""),
            "canonical_context_report": context,
            "canonical_context_report_sha256": _sha256_json(context),
            "context_runtime_output_id": selected_context_binding["output_id"],
            "context_runtime_artifact_sha256": selected_context_binding["artifact_hash"],
            "context_consumer_acknowledgement_id": selected_context_binding[
                "acknowledgement_id"
            ],
            "context_consumption_id": selected_context_binding["consumption_id"],
            "source_head": current_head(),
            "target": proposal_target,
            "approved_diff_sha256": hashlib.sha256(proposed_diff.encode("utf-8")).hexdigest(),
            "changed_files": changed_files,
            "status": "ready_for_approval_preview",
        }
        proposal_body["proposal_binding_sha256"] = _sha256_json(proposal_body)
        run.target_plugin_proposal = proposal_body
        run.record_event(
            event_type="target_plugin_proposal_ready",
            lane_id="coder",
            detail={
                "output_id": output["output_id"],
                "selected_prompt_id": plugin.selected_prompt_id,
                "target_plugin_identity": plugin.evidence_identity(),
                "model_invocation_id": selected_participant["invocation_id"],
                "proposal_binding_sha256": proposal_body["proposal_binding_sha256"],
            },
        )
        receipt = self._persist(run, "model-authored target-plugin proposal persisted")
        receipt["target_plugin_result"] = selected_result
        receipt["target_plugin_output_id"] = output["output_id"]
        return receipt

    def target_plugin_approval_material(
        self,
        task_id: str,
        *,
        runtime_output_id: str,
        selected_prompt_id: str,
    ) -> dict[str, Any]:
        """Return server-owned approval material for one persisted model proposal."""

        run = self._restore(task_id)
        proposal, output = self._require_target_plugin_proposal(
            run,
            runtime_output_id=runtime_output_id,
            selected_prompt_id=selected_prompt_id,
        )
        payload = output.get("payload")
        if not isinstance(payload, Mapping):
            raise CodingOrchestratorError("target_plugin_proposal_output_invalid")
        approved_diff = str(payload.get("approved_diff") or "")
        return {
            "approved_diff": approved_diff,
            "target": proposal["target"],
            "selected_prompt_id": proposal["selected_prompt_id"],
            "context_hash": proposal["context_hash"],
            "target_plugin_identity": dict(proposal["target_plugin_identity"]),
            "proposal_binding": dict(proposal),
        }

    def execute_approved(
        self,
        task_id: str,
        *,
        approved_diff: str,
        action: str,
        approval_id: str,
        selected_prompt_id: str,
        context_hash: str,
        runtime_output_id: str | None = None,
        target: str | None = None,
        approved_by: str = "human",
        test_command: list[str] | None = None,
    ) -> dict[str, Any]:
        run = self._restore(task_id)
        if run.lane_states["planner"] != "completed":
            self.acknowledge_planner(task_id)
            run = self._restore(task_id)
        proposal: dict[str, Any] | None = None
        if is_lumacart_prompt_id(selected_prompt_id):
            if not runtime_output_id:
                raise CodingOrchestratorError("target_plugin_runtime_output_id_missing")
            proposal, _ = self._require_target_plugin_proposal(
                run,
                runtime_output_id=runtime_output_id,
                selected_prompt_id=selected_prompt_id,
                approved_diff=approved_diff,
                target=target,
                context_hash=context_hash,
            )
        run.transition("coder", "running", reason="dispatching_canonical_executor")
        coder_invocation_id = f"coding-executor-invocation-{uuid4().hex}"
        planner_output = self._latest_output(run, "planner")
        if not self._output_consumed(run, planner_output["output_id"]):
            self._consume_output(
                run,
                output_id=planner_output["output_id"],
                consumer_invocation_id=coder_invocation_id,
                payload={"context_hash": context_hash},
            )
        coder_context = acknowledge_task_context_consumer(
            task_id,
            consumer="coder",
            evidence="canonical_executor_dispatch_started",
            applicable=True,
            reason="coder_consumed_context_before_approved_execution",
        )
        if not isinstance(coder_context, dict) or coder_context.get("go_eligible") is not True:
            run.transition("coder", "blocked", reason="coder_context_acknowledgement_blocked")
            self._persist(run, "coder blocked by canonical context")
            raise CodingOrchestratorError("coder_context_acknowledgement_blocked")
        try:
            execution = self._call_executor(
                task_id,
                approved_diff=approved_diff,
                action=action,
                approval_id=approval_id,
                selected_prompt_id=selected_prompt_id,
                context_hash=context_hash,
                runtime_output_id=runtime_output_id,
                proposal_binding=proposal,
                artifact_provenance=_artifact_provenance_for_run(run),
                target=target,
                approved_by=approved_by,
                test_command=test_command,
                orchestrator_run_id=run.run_id,
                orchestrator_attempt_id=run.attempt_id,
            )
        except Exception as error:
            run.transition("coder", "failed", reason="canonical_executor_failed")
            run.record_event(
                event_type="participant_failure",
                lane_id="coder",
                detail={"error": type(error).__name__, "message": str(error)[:500]},
            )
            self._persist(run, "canonical executor failed")
            raise
        execution_payload = execution.get("execution") if isinstance(execution, Mapping) else None
        if not isinstance(execution_payload, Mapping):
            raise CodingOrchestratorError("canonical_executor_receipt_missing")
        artifact = execution_payload.get("artifact")
        if not isinstance(artifact, Mapping):
            artifact = build_applied_artifact(
                task_id=task_id,
                run_id=run.run_id,
                approval_id=approval_id,
                generation=int(execution_payload.get("generation") or 1),
                approved_diff=approved_diff,
                execution=execution_payload,
            )
        run.immutable_artifact = dict(artifact)
        executor_record = execution_payload.get("executor_participant")
        if not isinstance(executor_record, Mapping):
            raise CodingOrchestratorError("coding_executor_participant_record_missing")
        self._append_participant(run, executor_record)
        if isinstance(run.cartographer_transfer, dict) and not isinstance(
            run.cartographer_finalization, dict
        ):
            self._finalize_cartographer_transfer_after_invocation(
                run,
                participant=executor_record,
                target=str(run.cartographer_transfer.get("target") or ""),
            )
        coder_output = self._matching_unconsumed_coder_output(run, approved_diff)
        if coder_output is None:
            if is_lumacart_prompt_id(selected_prompt_id):
                raise CodingOrchestratorError("target_plugin_model_output_missing_before_apply")
            coder_output = self._enforce_runtime_contract_output(
                run,
                lane_id="coder",
                producer_invocation_id=str(executor_record["invocation_id"]),
                payload={
                    "approved_diff": approved_diff,
                    "changed_files": list(execution_payload.get("changed_files") or []),
                },
            )
            output_consumer_invocation_id = f"orchestrator-coder-consumer-{uuid4().hex}"
        else:
            output_consumer_invocation_id = str(executor_record["invocation_id"])
        self._consume_output(
            run,
            output_id=coder_output["output_id"],
            consumer_invocation_id=output_consumer_invocation_id,
            payload={
                "approval_id": approval_id,
                "generation": int(run.immutable_artifact.get("generation") or 0),
            },
        )
        run.transition("coder", "completed", reason="canonical_executor_applied_approved_diff")

        run.transition("reviewer", "running", reason="independent_artifact_review_started")
        reviewer_record = self._reviewer(run.immutable_artifact)
        self._append_participant(run, reviewer_record)
        reviewer_output = self._enforce_runtime_contract_output(
            run,
            lane_id="reviewer",
            producer_invocation_id=str(reviewer_record["invocation_id"]),
            payload={
                "passed": bool(reviewer_record["passed"]),
                "findings": list(reviewer_record.get("result", {}).get("findings") or []),
            },
        )
        self._consume_output(
            run,
            output_id=reviewer_output["output_id"],
            consumer_invocation_id=f"orchestrator-review-consumer-{uuid4().hex}",
            payload={
                "approval_id": approval_id,
                "generation": int(run.immutable_artifact.get("generation") or 0),
            },
        )
        if reviewer_record.get("passed") is not True:
            run.transition("reviewer", "failed", reason="independent_review_failed")
            fail_orchestrated_coding_execution(
                task_id,
                reason_code="independent_review_failed",
                participant_records=run.participant_records,
            )
            self._persist(run, "independent reviewer failed")
            raise CodingOrchestratorError("independent_review_failed")
        run.transition("reviewer", "completed", reason="independent_review_passed")
        receipt = self._persist(run, "approved execution and independent review completed")
        receipt["artifact"] = dict(run.immutable_artifact)
        response = dict(execution)
        response["coding_orchestrator"] = receipt
        return response

    def complete_post_apply(self, task_id: str, **verification_kwargs: Any) -> dict[str, Any]:
        run = self._restore(task_id)
        if isinstance(run.authority_finalization, Mapping):
            return self._resume_authority_finalization(run)
        if run.lane_states["coder"] != "completed" or run.lane_states["reviewer"] != "completed":
            raise CodingOrchestratorError("coder_and_reviewer_must_complete_before_verification")
        if not isinstance(run.immutable_artifact, dict):
            raise CodingOrchestratorError("coding_artifact_missing")
        request_event = run.record_event(
            event_type="post_apply_verification_requested",
            lane_id="verifier",
            detail={"verification_fields": sorted(verification_kwargs)},
        )
        self._persist(run, "post-apply verification request persisted before invocation")
        try:
            result = self._post_apply_verifier(task_id, **verification_kwargs)
        except Exception as error:
            run = self._restore(task_id)
            run.record_event(
                event_type="post_apply_verification_rejected",
                lane_id="verifier",
                detail={
                    "request_event_id": request_event["event_id"],
                    "reason_code": str(getattr(error, "reason_code", type(error).__name__)),
                },
            )
            self._persist(run, "post-apply verification request rejected without lane completion")
            raise
        run = self._restore(task_id)
        run.transition("verifier", "running", reason="server_post_apply_verification_started")
        task_payload = result.get("task") if isinstance(result, Mapping) else None
        snapshot = task_payload.get("ast_snapshot") if isinstance(task_payload, Mapping) else None
        verification = snapshot.get("post_apply_verification") if isinstance(snapshot, Mapping) else None
        if not isinstance(verification, Mapping):
            raise CodingOrchestratorError("post_apply_verification_receipt_missing")
        verifier_context = acknowledge_task_context_consumer(
            task_id,
            consumer="verifier",
            evidence="independent_verifier_consumed_bound_post_apply_evidence",
            applicable=True,
            reason="verifier_consumed_canonical_context_before_independent_verification",
        )
        if not isinstance(verifier_context, dict) or verifier_context.get("go_eligible") is not True:
            run.transition("verifier", "failed", reason="verifier_context_acknowledgement_blocked")
            self._persist(run, "independent verifier blocked by canonical context")
            raise CodingOrchestratorError("verifier_context_acknowledgement_blocked")
        verifier_record = self._verifier(run.immutable_artifact, verification)
        self._append_participant(run, verifier_record)
        verifier_output = self._enforce_runtime_contract_output(
            run,
            lane_id="verifier",
            producer_invocation_id=str(verifier_record["invocation_id"]),
            payload={
                "verdict": str(verifier_record.get("result", {}).get("verdict") or "FAIL"),
                "checks": list(verifier_record.get("result", {}).get("checks") or []),
            },
        )
        approval_id, generation = self._approval_identity(run)
        self._consume_output(
            run,
            output_id=verifier_output["output_id"],
            consumer_invocation_id=f"orchestrator-verifier-consumer-{uuid4().hex}",
            payload={"approval_id": approval_id, "generation": generation},
        )
        if verifier_record.get("passed") is not True:
            run.transition("verifier", "failed", reason="independent_verification_failed")
            fail_orchestrated_coding_execution(
                task_id,
                reason_code="independent_verification_failed",
                participant_records=run.participant_records,
            )
            receipt = self._persist(run, "independent verifier failed")
            response = dict(result)
            response["coding_orchestrator"] = receipt
            return response
        run.transition("verifier", "completed", reason="independent_verification_passed")

        run.transition("anti-cheat", "running", reason="independent_anti_cheat_started")
        model_evidence = _model_evidence_for_run(run)
        anti_cheat_record = self._anti_cheat(
            run.immutable_artifact,
            model_evidence=model_evidence,
        )
        self._append_participant(run, anti_cheat_record)
        anti_cheat_output = self._enforce_runtime_contract_output(
            run,
            lane_id="anti-cheat",
            producer_invocation_id=str(anti_cheat_record["invocation_id"]),
            payload={
                "passed": bool(anti_cheat_record["passed"]),
                "detector_ids": list(anti_cheat_record.get("result", {}).get("detector_ids") or []),
                "violations": list(anti_cheat_record.get("result", {}).get("violations") or []),
            },
        )
        self._consume_output(
            run,
            output_id=anti_cheat_output["output_id"],
            consumer_invocation_id=f"orchestrator-anti-cheat-consumer-{uuid4().hex}",
            payload={"approval_id": approval_id, "generation": generation},
        )
        if anti_cheat_record.get("passed") is not True:
            run.transition("anti-cheat", "failed", reason="independent_anti_cheat_failed")
            fail_orchestrated_coding_execution(
                task_id,
                reason_code="independent_anti_cheat_failed",
                participant_records=run.participant_records,
            )
            self._persist(run, "independent anti-cheat failed")
            raise CodingOrchestratorError("independent_anti_cheat_failed")
        run.transition("anti-cheat", "completed", reason="independent_anti_cheat_passed")
        run.transition("repair", "skipped", reason="verification_passed_no_repair_needed")

        run.transition("evidence-recorder", "running", reason="independent_evidence_recording_started")
        evidence_context = acknowledge_task_context_consumer(
            task_id,
            consumer="final_receipt_builder",
            evidence="evidence_recorder_consumed_canonical_context_verdict",
            applicable=True,
            reason="evidence_recorder_gated_final_receipt_on_canonical_context",
        )
        if not isinstance(evidence_context, dict) or evidence_context.get("go_eligible") is not True:
            run.transition(
                "evidence-recorder",
                "failed",
                reason="evidence_context_acknowledgement_blocked",
            )
            self._persist(run, "evidence recorder blocked by canonical context")
            raise CodingOrchestratorError("evidence_context_acknowledgement_blocked")
        evidence_record = self._evidence_recorder(
            run.immutable_artifact,
            participant_records=list(run.participant_records),
        )
        self._append_participant(run, evidence_record)
        evidence_output = self._enforce_runtime_contract_output(
            run,
            lane_id="evidence-recorder",
            producer_invocation_id=str(evidence_record["invocation_id"]),
            payload={
                "receipt_id": str(evidence_record.get("result", {}).get("receipt_id") or ""),
                "truth_status": str(evidence_record.get("result", {}).get("truth_status") or "FAIL"),
            },
        )
        self._consume_output(
            run,
            output_id=evidence_output["output_id"],
            consumer_invocation_id=f"orchestrator-evidence-consumer-{uuid4().hex}",
            payload={"approval_id": approval_id, "generation": generation},
        )
        if evidence_record.get("passed") is not True:
            run.transition("evidence-recorder", "failed", reason="independent_evidence_failed")
            fail_orchestrated_coding_execution(
                task_id,
                reason_code="independent_evidence_failed",
                participant_records=run.participant_records,
            )
            self._persist(run, "independent evidence recorder failed")
            raise CodingOrchestratorError("independent_evidence_failed")

        boundary = self._boundary(run)
        boundary.require_outputs_consumed(run.required_output_ids)
        if {str(record.get("role") or "") for record in run.participant_records} != set(
            REQUIRED_PARTICIPANT_ROLES
        ):
            raise CodingOrchestratorError("coding_participant_set_invalid")
        pre_finalization_state = self._persist(
            run,
            "all participant outputs consumed; canonical state frozen for authority finalization",
        )
        orchestrator_state_sha256 = _sha256_json(pre_finalization_state)
        authority_request = prepare_orchestrated_coding_finalization(
            task_id,
            participant_records=run.participant_records,
            runtime_outputs=run.runtime_outputs,
            runtime_acknowledgements=run.runtime_acknowledgements,
            runtime_consumptions=run.runtime_consumptions,
            orchestrator_state_sha256=orchestrator_state_sha256,
        )
        run.authority_finalization = {
            "schema_version": "coding.authority-finalization-outbox/v1",
            "state": "pending_authority_commit",
            "approval": dict(authority_request["approval"]),
            "result_id": str(authority_request["result_id"]),
            "evidence": dict(authority_request["evidence"]),
            "evidence_sha256": _sha256_json(authority_request["evidence"]),
            "orchestrator_state_sha256": orchestrator_state_sha256,
            "status": "succeeded",
        }
        self._persist(
            run,
            "all participant outputs consumed; canonical state frozen for authority finalization",
        )
        return self._resume_authority_finalization(run)

    def _resume_authority_finalization(
        self,
        run: CodingLaneStateMachine,
    ) -> dict[str, Any]:
        """Reconcile a durable approval outbox without repeating participant work."""

        intent = run.authority_finalization
        if not isinstance(intent, dict):
            raise CodingOrchestratorError("coding_authority_finalization_intent_missing")
        approval = intent.get("approval")
        evidence = intent.get("evidence")
        state_sha256 = str(intent.get("orchestrator_state_sha256") or "")
        result_id = str(intent.get("result_id") or "")
        if (
            intent.get("schema_version") != "coding.authority-finalization-outbox/v1"
            or intent.get("status") != "succeeded"
            or intent.get("state")
            not in {
                "pending_authority_commit",
                "authority_committed_local_pending",
                "locally_committed",
            }
            or not isinstance(approval, Mapping)
            or not isinstance(evidence, Mapping)
            or not result_id
            or not state_sha256.startswith("sha256:")
            or intent.get("evidence_sha256") != _sha256_json(evidence)
        ):
            raise CodingOrchestratorError("coding_authority_finalization_intent_invalid")

        authority_finalization = intent.get("authority_receipt")
        if intent["state"] == "pending_authority_commit":
            try:
                authority_finalization = finalize_coding_execution_approval(
                    dict(approval),
                    result_id=result_id,
                    evidence=dict(evidence),
                    status="succeeded",
                )
            except CampaignApprovalError as error:
                # A response can be lost after the authority commits. Preserve
                # the exact request so retry can reconcile it idempotently.
                intent["last_error"] = error.reason_code
                self._persist(
                    run,
                    "all participant outputs consumed; canonical state frozen for authority finalization",
                )
                raise CodingOrchestratorError(error.reason_code) from error
            if (
                not isinstance(authority_finalization, Mapping)
                or authority_finalization.get("state") != "consumed"
                or str(authority_finalization.get("approval_id") or "")
                != str(approval.get("approval_id") or "")
                or int(authority_finalization.get("generation") or -1)
                != int(approval.get("generation") or -2)
                or str(authority_finalization.get("result_id") or "") != result_id
            ):
                raise CodingOrchestratorError(
                    "coding_authority_finalization_binding_invalid"
                )
            intent.pop("last_error", None)
            intent["state"] = "authority_committed_local_pending"
            intent["authority_receipt"] = dict(authority_finalization)
            intent["authority_committed_at"] = _utc_now()
            self._persist(
                run,
                "all participant outputs consumed; canonical state frozen for authority finalization",
            )
        elif not isinstance(authority_finalization, Mapping):
            raise CodingOrchestratorError("coding_authority_finalization_receipt_missing")

        finalized = finalize_orchestrated_coding_execution(
            run.task_id,
            authority_finalization=dict(authority_finalization),
            participant_records=run.participant_records,
            runtime_outputs=run.runtime_outputs,
            runtime_acknowledgements=run.runtime_acknowledgements,
            runtime_consumptions=run.runtime_consumptions,
            orchestrator_state_sha256=state_sha256,
        )
        if run.lane_states["evidence-recorder"] == "running":
            run.transition(
                "evidence-recorder",
                "completed",
                reason="evidence_persisted_before_finalization",
            )
            run.record_event(
                event_type="final_result",
                status_after="completed",
                detail={
                    "artifact_sha256": run.immutable_artifact["artifact_sha256"]
                    if isinstance(run.immutable_artifact, Mapping)
                    else "",
                    "participant_invocation_ids": [
                        record["invocation_id"] for record in run.participant_records
                    ],
                },
            )
        elif run.lane_states["evidence-recorder"] != "completed":
            raise CodingOrchestratorError("coding_evidence_recorder_state_invalid")
        intent["state"] = "locally_committed"
        intent["local_committed_at"] = _utc_now()
        receipt = self._persist(
            run,
            "canonical coding run completed after all required participants",
        )
        response = dict(finalized)
        response["coding_orchestrator"] = receipt
        return response

    def recover_interrupted_lane(
        self,
        task_id: str,
        *,
        lane_id: str,
        recovery: Callable[[], bool] | None = None,
    ) -> dict[str, Any]:
        """Legacy operator recovery; explicitly ineligible as production proof."""

        run = self._restore(task_id)
        if lane_id not in LANE_SEQUENCE:
            raise CodingOrchestratorError("unknown_coding_lane")
        current = run.lane_states[lane_id]
        failure_event = run.record_event(
            event_type="interrupted_lane_detected",
            lane_id=lane_id,
            detail={"prior_state": current},
        )
        if current == "running":
            run.transition(lane_id, "failed", reason="interrupted_before_lane_completion")
        elif current != "failed":
            raise CodingOrchestratorError(f"lane_not_recoverable:{lane_id}:{current}")
        run.transition(lane_id, "recovering", reason="durable_lane_recovery_started")
        recovery_record = {
            "schema_version": "coding.recovery-lineage/v1",
            "recovery_id": f"coding-recovery-{uuid4().hex}",
            "run_id": run.run_id,
            "attempt_id": run.attempt_id,
            "failed_event_id": failure_event["event_id"],
            "failed_participant": lane_id,
            "failure": "interrupted_before_lane_completion",
            "decision": "operator_callback_legacy",
            "replacement_provider": None,
            "replacement_model": None,
            "claim_ceiling_impact": "not_eligible_for_production_recovery_proof",
            "proof_eligible": False,
        }
        if recovery is None:
            run.transition(lane_id, "blocked", reason="recovery_action_required")
            recovery_record.update({"outcome": "degraded", "recovered": False})
        else:
            try:
                recovered = recovery() is True
            except Exception:
                recovered = False
            if recovered:
                run.transition(lane_id, "completed", reason="explicit_lane_recovery_completed")
                recovery_record.update({"outcome": "recovered", "recovered": True})
            else:
                run.transition(lane_id, "blocked", reason="explicit_lane_recovery_failed")
                recovery_record.update({"outcome": "degraded", "recovered": False})
        run.recovery_lineage.append(recovery_record)
        receipt = self._persist(run, "legacy interrupted-lane recovery recorded with claim ceiling")
        receipt["recovery"] = {
            "lane_id": lane_id,
            "outcome": recovery_record["outcome"],
            "recovered": recovery_record["recovered"],
        }
        return receipt

    def _restore(self, task_id: str) -> CodingLaneStateMachine:
        state = self._state_loader(task_id)
        if not isinstance(state, Mapping) or state.get("schema_version") not in {
            ORCHESTRATOR_SCHEMA,
            "coding-orchestrator/v1",
        }:
            raise CodingOrchestratorError("coding_orchestrator_state_missing")
        lane_states = state.get("lane_states")
        lane_reasons = state.get("lane_reasons")
        if not isinstance(lane_states, Mapping) or set(lane_states) != set(LANE_SEQUENCE):
            raise CodingOrchestratorError("coding_orchestrator_state_invalid")
        if any(value not in LANE_STATES for value in lane_states.values()):
            raise CodingOrchestratorError("coding_orchestrator_state_invalid")
        run = CodingLaneStateMachine(
            task_id=task_id,
            run_id=str(state.get("run_id") or ""),
            attempt_id=str(state.get("attempt_id") or f"coding-attempt-{uuid4().hex}"),
            parent_attempt_id=(
                str(state.get("parent_attempt_id")) if state.get("parent_attempt_id") else None
            ),
            lane_states={lane_id: str(lane_states[lane_id]) for lane_id in LANE_SEQUENCE},
            lane_reasons=dict(lane_reasons) if isinstance(lane_reasons, Mapping) else {},
            causal_events=_mapping_list(state.get("causal_events")),
            runtime_outputs=_mapping_list(state.get("runtime_outputs")),
            runtime_acknowledgements=_mapping_list(state.get("runtime_acknowledgements")),
            runtime_consumptions=_mapping_list(state.get("runtime_consumptions")),
            required_output_ids=[str(item) for item in state.get("required_output_ids", [])],
            participant_records=_mapping_list(state.get("participant_records")),
            immutable_artifact=(
                dict(state["immutable_artifact"])
                if isinstance(state.get("immutable_artifact"), Mapping)
                else None
            ),
            target_plugin_proposal=(
                dict(state["target_plugin_proposal"])
                if isinstance(state.get("target_plugin_proposal"), Mapping)
                else None
            ),
            cartographer_selection_consumption=(
                dict(state["cartographer_selection_consumption"])
                if isinstance(state.get("cartographer_selection_consumption"), Mapping)
                else None
            ),
            cartographer_transfer=(
                dict(state["cartographer_transfer"])
                if isinstance(state.get("cartographer_transfer"), Mapping)
                else None
            ),
            cartographer_finalization=(
                dict(state["cartographer_finalization"])
                if isinstance(state.get("cartographer_finalization"), Mapping)
                else None
            ),
            authority_finalization=(
                dict(state["authority_finalization"])
                if isinstance(state.get("authority_finalization"), Mapping)
                else None
            ),
            recovery_lineage=_mapping_list(state.get("recovery_lineage")),
            model_invocations=_mapping_list(state.get("model_invocations")),
            created_at=str(state.get("created_at") or _utc_now()),
            updated_at=str(state.get("updated_at") or _utc_now()),
        )
        if not run.run_id:
            raise CodingOrchestratorError("coding_orchestrator_state_invalid")
        self._boundary(run)
        return run

    def _call_executor(self, task_id: str, **kwargs: Any) -> dict[str, Any]:
        signature = inspect.signature(self._executor)
        accepts_extra = any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in signature.parameters.values()
        )
        filtered = {
            key: value
            for key, value in kwargs.items()
            if accepts_extra or key in signature.parameters
        }
        return self._executor(task_id, **filtered)

    @staticmethod
    def _acknowledge_persisted_context(
        task_id: str,
        *,
        consumer: str,
        evidence: str,
        reason: str,
    ) -> dict[str, Any]:
        """Acknowledge one exact broker report and prove that it became durable."""

        report = acknowledge_task_context_consumer(
            task_id,
            consumer=consumer,
            evidence=evidence,
            applicable=True,
            reason=reason,
        )
        if (
            not isinstance(report, Mapping)
            or report.get("canonical") is not True
            or not str(report.get("canonical_report_hash") or "")
        ):
            raise CodingOrchestratorError("canonical_context_acknowledgement_invalid")
        persisted = canonical_context_broker_for_task(task_id)
        if not isinstance(persisted, Mapping) or dict(persisted) != dict(report):
            raise CodingOrchestratorError("canonical_context_acknowledgement_not_persisted")
        if persisted.get("canonical_report_hash") != report.get("canonical_report_hash"):
            raise CodingOrchestratorError("canonical_context_acknowledgement_hash_mismatch")
        return json.loads(json.dumps(dict(report), sort_keys=True, default=str))

    def _issue_refreshed_context_output(
        self,
        run: CodingLaneStateMachine,
        *,
        report: Mapping[str, Any],
        refresh_reason: str,
    ) -> dict[str, Any]:
        """Supersede the latest broker output with the exact persisted report hash."""

        report_hash = str(report.get("canonical_report_hash") or "")
        if not report_hash:
            raise CodingOrchestratorError("canonical_context_report_hash_missing")
        predecessor = self._latest_output(run, "context-broker")
        predecessor_hash = str(
            predecessor.get("payload", {}).get("context_hash")
            if isinstance(predecessor.get("payload"), Mapping)
            else ""
        )
        if (
            predecessor_hash == report_hash
            and not self._output_consumed(run, str(predecessor.get("output_id") or ""))
            and any(
                event.get("event_type") == "context_report_refreshed"
                and event.get("detail", {}).get("refreshed_output_id")
                == predecessor.get("output_id")
                for event in run.causal_events
            )
        ):
            return predecessor

        refresh_invocation_id = f"context-broker-refresh-invocation-{uuid4().hex}"
        predecessor_consumption: dict[str, Any] | None = next(
            (
                item
                for item in run.runtime_consumptions
                if item.get("output_id") == predecessor.get("output_id")
            ),
            None,
        )
        if predecessor_consumption is None:
            predecessor_consumption = self._consume_output(
                run,
                output_id=str(predecessor["output_id"]),
                consumer_invocation_id=refresh_invocation_id,
                payload={
                    "consumer": "context-broker-refresh",
                    "context_hash": predecessor_hash,
                },
            )
        refreshed = self._enforce_runtime_contract_output(
            run,
            lane_id="context-broker",
            producer_invocation_id=refresh_invocation_id,
            payload={
                "context_hash": report_hash,
                "verdict": str(report.get("verdict") or "UNKNOWN"),
            },
        )
        run.record_event(
            event_type="context_report_refreshed",
            lane_id="context-broker",
            detail={
                "reason": refresh_reason,
                "predecessor_output_id": predecessor["output_id"],
                "predecessor_context_hash": predecessor_hash,
                "predecessor_artifact_sha256": predecessor["artifact_hash"],
                "predecessor_consumption_id": predecessor_consumption["consumption_id"],
                "refreshed_output_id": refreshed["output_id"],
                "refreshed_context_hash": report_hash,
                "refreshed_artifact_sha256": refreshed["artifact_hash"],
            },
        )
        return refreshed

    def _bind_context_to_invocation(
        self,
        run: CodingLaneStateMachine,
        *,
        report: Mapping[str, Any],
        consumer_invocation_id: str,
        refresh_reason: str,
    ) -> dict[str, str]:
        output = self._issue_refreshed_context_output(
            run,
            report=report,
            refresh_reason=refresh_reason,
        )
        consumption = self._consume_output(
            run,
            output_id=str(output["output_id"]),
            consumer_invocation_id=consumer_invocation_id,
            payload={
                "consumer": "coder",
                "context_hash": str(report["canonical_report_hash"]),
            },
        )
        return {
            "output_id": str(output["output_id"]),
            "artifact_hash": str(output["artifact_hash"]),
            "acknowledgement_id": str(consumption["acknowledgement_id"]),
            "consumption_id": str(consumption["consumption_id"]),
        }

    def _enforce_runtime_contract_output(
        self,
        run: CodingLaneStateMachine,
        *,
        lane_id: str,
        producer_invocation_id: str,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        boundary = self._boundary(run)
        contract_version = canonical_coding_lane_contracts()[lane_id]["contract_version"]
        output = boundary.issue_output(
            lane_id=lane_id,
            contract_version=contract_version,
            producer_invocation_id=producer_invocation_id,
            payload=payload,
        ).to_payload()
        run.runtime_outputs.append(output)
        run.required_output_ids.append(output["output_id"])
        run.record_event(
            event_type="output",
            lane_id=lane_id,
            detail={
                "output_id": output["output_id"],
                "contract_version": output["contract_version"],
                "producer_invocation_id": producer_invocation_id,
                "artifact_sha256": output["artifact_hash"],
            },
        )
        return output

    def _consume_output(
        self,
        run: CodingLaneStateMachine,
        *,
        output_id: str,
        consumer_invocation_id: str,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        boundary = self._boundary(run)
        acknowledgement = boundary.record_consumer_acknowledgement(
            output_id=output_id,
            consumer_version=ORCHESTRATOR_CONSUMER_VERSION,
            consumer_invocation_id=consumer_invocation_id,
            payload=payload,
        )
        consumption = boundary.mark_output_consumed(
            output_id=output_id,
            acknowledgement_id=acknowledgement.acknowledgement_id,
        )
        ack_payload = acknowledgement.to_payload()
        consumption_payload = consumption.to_payload()
        run.runtime_acknowledgements.append(ack_payload)
        run.runtime_consumptions.append(consumption_payload)
        run.record_event(
            event_type="output_consumption",
            lane_id=consumption.lane_id,
            detail={
                "output_id": output_id,
                "consumer_acknowledgement_id": acknowledgement.acknowledgement_id,
                "consumption_id": consumption.consumption_id,
                "consumer_invocation_id": consumer_invocation_id,
                "artifact_sha256": consumption.artifact_hash,
            },
        )
        return consumption_payload

    @staticmethod
    def _append_participant(run: CodingLaneStateMachine, record: Mapping[str, Any]) -> None:
        normalized = json.loads(json.dumps(dict(record), sort_keys=True, default=str))
        if "consumer_acknowledgement_id" not in normalized:
            if not isinstance(run.immutable_artifact, Mapping):
                raise CodingOrchestratorError("coding_artifact_missing")
            try:
                normalized = acknowledge_coding_participant_output(
                    normalized,
                    run.immutable_artifact,
                    consumer_service="source-proxy.coding.orchestrator/v2",
                )
            except Exception as error:
                reason_code = getattr(
                    error,
                    "reason_code",
                    "coding_participant_acknowledgement_invalid",
                )
                raise CodingOrchestratorError(str(reason_code)) from error
        required = {
            "role",
            "invocation_id",
            "output_id",
            "consumer_acknowledgement_id",
            "artifact_sha256",
            "passed",
        }
        if not required.issubset(normalized):
            raise CodingOrchestratorError("coding_participant_record_invalid")
        if not isinstance(run.immutable_artifact, Mapping):
            raise CodingOrchestratorError("coding_artifact_missing")
        try:
            normalized = validate_coding_participant_record(
                normalized,
                run.immutable_artifact,
                expected_role=str(normalized.get("role") or ""),
            )
        except Exception as error:
            reason_code = getattr(error, "reason_code", "coding_participant_record_invalid")
            raise CodingOrchestratorError(str(reason_code)) from error
        if any(
            existing.get("role") == normalized["role"]
            or existing.get("invocation_id") == normalized["invocation_id"]
            or existing.get("output_id") == normalized["output_id"]
            for existing in run.participant_records
        ):
            raise CodingOrchestratorError("coding_participant_record_duplicate")
        run.participant_records.append(normalized)
        run.record_event(
            event_type="participant_output",
            detail={
                "role": normalized["role"],
                "invocation_id": normalized["invocation_id"],
                "output_id": normalized["output_id"],
                "consumer_acknowledgement_id": normalized["consumer_acknowledgement_id"],
                "artifact_sha256": normalized["artifact_sha256"],
                "passed": normalized["passed"],
            },
        )

    @staticmethod
    def _upsert_controlled_recovery(
        run: CodingLaneStateMachine,
        lineage: ControlledRecoveryLineage,
    ) -> None:
        rehydrated = ControlledRecoveryLineage.from_payload(lineage.to_payload())
        payload = rehydrated.to_payload()
        if payload["run_id"] != run.run_id or payload["task_id"] != run.task_id:
            raise CodingOrchestratorError("controlled_recovery_run_binding_mismatch")
        model_by_invocation = {
            str(record.get("invocation_id") or ""): record
            for record in run.model_invocations
        }
        failure = payload["failure"]["participant"]
        replacement = payload["replacement"]["participant"]
        if model_by_invocation.get(str(failure["invocation_id"])) != failure:
            raise CodingOrchestratorError("controlled_recovery_failure_participant_missing")
        if isinstance(replacement, Mapping) and (
            model_by_invocation.get(str(replacement.get("invocation_id") or "")) != replacement
        ):
            raise CodingOrchestratorError("controlled_recovery_replacement_participant_missing")
        if payload["state"] == "completed" and not isinstance(replacement, Mapping):
            raise CodingOrchestratorError("controlled_recovery_replacement_participant_missing")
        invocation_ids = [
            str(record.get("invocation_id") or "") for record in run.model_invocations
        ]
        output_ids = [str(record.get("output_id") or "") for record in run.model_invocations]
        if (
            "" in invocation_ids
            or "" in output_ids
            or len(set(invocation_ids)) != len(invocation_ids)
            or len(set(output_ids)) != len(output_ids)
        ):
            raise CodingOrchestratorError("controlled_recovery_model_identity_reused")
        matching_indexes = [
            index
            for index, record in enumerate(run.recovery_lineage)
            if record.get("recovery_id") == payload["recovery_id"]
        ]
        if len(matching_indexes) > 1:
            raise CodingOrchestratorError("controlled_recovery_identity_reused")
        events = list(rehydrated.events)
        if not matching_indexes:
            existing_event_ids = {
                str(event.get("event_id") or "") for event in run.causal_events
            }
            recovery_event_ids = [str(event["event_id"]) for event in events]
            if (
                len(set(recovery_event_ids)) != len(recovery_event_ids)
                or existing_event_ids.intersection(recovery_event_ids)
            ):
                raise CodingOrchestratorError("controlled_recovery_event_identity_reused")
            run.causal_events.extend(dict(event) for event in events)
            run.recovery_lineage.append(payload)
        else:
            index = matching_indexes[0]
            existing = ControlledRecoveryLineage.from_payload(
                run.recovery_lineage[index]
            ).to_payload()
            if existing["state"] != "authorized" or payload["state"] != "completed":
                raise CodingOrchestratorError("controlled_recovery_update_invalid")
            for section in ("failure", "decision"):
                if existing[section] != payload[section]:
                    raise CodingOrchestratorError("controlled_recovery_update_binding_mismatch")
            for key in ("attempt_id", "parent_attempt_id", "provider", "model", "start_event"):
                if existing["replacement"][key] != payload["replacement"][key]:
                    raise CodingOrchestratorError("controlled_recovery_update_binding_mismatch")
            outcome_event = payload["replacement"]["outcome_event"]
            if not isinstance(outcome_event, Mapping):
                raise CodingOrchestratorError("controlled_recovery_outcome_event_missing")
            if any(
                event.get("event_id") == outcome_event.get("event_id")
                for event in run.causal_events
            ):
                raise CodingOrchestratorError("controlled_recovery_event_identity_reused")
            run.causal_events.append(dict(outcome_event))
            run.recovery_lineage[index] = payload
        run.updated_at = str(events[-1]["recorded_at"])

    @staticmethod
    def _boundary(run: CodingLaneStateMachine) -> RuntimeLaneBoundary:
        return RuntimeLaneBoundary.from_payloads(
            outputs=run.runtime_outputs,
            acknowledgements=run.runtime_acknowledgements,
            consumptions=run.runtime_consumptions,
        )

    @staticmethod
    def _latest_output(run: CodingLaneStateMachine, lane_id: str) -> dict[str, Any]:
        for output in reversed(run.runtime_outputs):
            if output.get("lane_id") == lane_id:
                return output
        raise CodingOrchestratorError(f"coding_lane_output_missing:{lane_id}")

    @staticmethod
    def _matching_unconsumed_coder_output(
        run: CodingLaneStateMachine,
        approved_diff: str,
    ) -> dict[str, Any] | None:
        for output in reversed(run.runtime_outputs):
            if (
                output.get("lane_id") == "coder"
                and isinstance(output.get("payload"), Mapping)
                and output["payload"].get("approved_diff") == approved_diff
                and not CodingOrchestrator._output_consumed(run, str(output.get("output_id") or ""))
            ):
                return output
        return None

    @staticmethod
    def _require_target_plugin_proposal(
        run: CodingLaneStateMachine,
        *,
        runtime_output_id: str,
        selected_prompt_id: str,
        approved_diff: str | None = None,
        target: str | None = None,
        context_hash: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        proposal = run.target_plugin_proposal
        if not isinstance(proposal, dict):
            raise CodingOrchestratorError("target_plugin_proposal_missing")
        sealed = dict(proposal)
        recorded_hash = str(sealed.pop("proposal_binding_sha256", ""))
        if not recorded_hash or _sha256_json(sealed) != recorded_hash:
            raise CodingOrchestratorError("target_plugin_proposal_hash_mismatch")
        if (
            proposal.get("task_id") != run.task_id
            or proposal.get("run_id") != run.run_id
            or proposal.get("runtime_output_id") != runtime_output_id
            or proposal.get("selected_prompt_id") != selected_prompt_id
        ):
            raise CodingOrchestratorError("target_plugin_proposal_binding_mismatch")
        if proposal.get("status") != "ready_for_approval_preview":
            raise CodingOrchestratorError("target_plugin_proposal_not_actionable")
        if proposal.get("source_head") != current_head():
            raise CodingOrchestratorError("target_plugin_proposal_source_head_mismatch")
        plugin_identity = proposal.get("target_plugin_identity")
        if not isinstance(plugin_identity, Mapping) or (
            plugin_identity.get("source_head") != proposal.get("source_head")
            or plugin_identity.get("selected_prompt_id") != selected_prompt_id
        ):
            raise CodingOrchestratorError("target_plugin_proposal_identity_mismatch")
        context_report = proposal.get("canonical_context_report")
        persisted_context = canonical_context_broker_for_task(run.task_id)
        if (
            not isinstance(context_report, Mapping)
            or context_report.get("canonical") is not True
            or context_report.get("canonical_report_hash") != proposal.get("context_hash")
            or _sha256_json(context_report)
            != proposal.get("canonical_context_report_sha256")
            or not isinstance(persisted_context, Mapping)
            or dict(persisted_context) != dict(context_report)
        ):
            raise CodingOrchestratorError("target_plugin_proposal_context_binding_invalid")
        output = next(
            (
                item
                for item in run.runtime_outputs
                if item.get("output_id") == runtime_output_id
            ),
            None,
        )
        if not isinstance(output, dict) or output.get("lane_id") != "coder":
            raise CodingOrchestratorError("target_plugin_proposal_output_missing")
        if CodingOrchestrator._output_consumed(run, runtime_output_id):
            raise CodingOrchestratorError("target_plugin_proposal_output_already_consumed")
        if output.get("artifact_hash") != proposal.get("runtime_output_artifact_sha256"):
            raise CodingOrchestratorError("target_plugin_proposal_output_hash_mismatch")
        payload = output.get("payload")
        if not isinstance(payload, Mapping):
            raise CodingOrchestratorError("target_plugin_proposal_output_invalid")
        exact_diff = str(payload.get("approved_diff") or "")
        changed_files = [str(item) for item in payload.get("changed_files", [])]
        if (
            not exact_diff.strip()
            or hashlib.sha256(exact_diff.encode("utf-8")).hexdigest()
            != proposal.get("approved_diff_sha256")
            or changed_files != list(proposal.get("changed_files") or [])
            or proposal.get("target") not in changed_files
        ):
            raise CodingOrchestratorError("target_plugin_proposal_payload_mismatch")
        producer_invocation_id = str(output.get("producer_invocation_id") or "")
        if producer_invocation_id != proposal.get("producer_model_invocation_id"):
            raise CodingOrchestratorError("target_plugin_proposal_producer_mismatch")
        context_output = next(
            (
                item
                for item in run.runtime_outputs
                if item.get("output_id") == proposal.get("context_runtime_output_id")
            ),
            None,
        )
        context_acknowledgement = next(
            (
                item
                for item in run.runtime_acknowledgements
                if item.get("acknowledgement_id")
                == proposal.get("context_consumer_acknowledgement_id")
            ),
            None,
        )
        context_consumption = next(
            (
                item
                for item in run.runtime_consumptions
                if item.get("consumption_id") == proposal.get("context_consumption_id")
            ),
            None,
        )
        if (
            not isinstance(context_output, Mapping)
            or context_output.get("lane_id") != "context-broker"
            or context_output.get("artifact_hash")
            != proposal.get("context_runtime_artifact_sha256")
            or context_output.get("payload", {}).get("context_hash")
            != proposal.get("context_hash")
            or not isinstance(context_acknowledgement, Mapping)
            or context_acknowledgement.get("output_id") != context_output.get("output_id")
            or context_acknowledgement.get("consumer_invocation_id")
            != producer_invocation_id
            or context_acknowledgement.get("payload", {}).get("context_hash")
            != proposal.get("context_hash")
            or not isinstance(context_consumption, Mapping)
            or context_consumption.get("output_id") != context_output.get("output_id")
            or context_consumption.get("acknowledgement_id")
            != context_acknowledgement.get("acknowledgement_id")
            or context_consumption.get("consumer_invocation_id")
            != producer_invocation_id
        ):
            raise CodingOrchestratorError("target_plugin_proposal_context_consumption_invalid")
        participant = next(
            (
                item
                for item in run.model_invocations
                if item.get("invocation_id") == producer_invocation_id
            ),
            None,
        )
        model_output_provenance = proposal.get("model_output_provenance")
        adapter_provenance = proposal.get("target_adapter_provenance")
        expected_model_artifact_sha256 = _sha256_json(
            {
                "proposed_diff": exact_diff,
                "changed_files": changed_files,
            }
        )
        if (
            not isinstance(participant, Mapping)
            or participant.get("passed") is not True
            or participant.get("output_sha256") != proposal.get("producer_model_output_sha256")
            or participant.get("artifact_sha256")
            != proposal.get("producer_model_artifact_sha256")
            or participant.get("artifact_sha256") != expected_model_artifact_sha256
            or not isinstance(model_output_provenance, Mapping)
            or not isinstance(adapter_provenance, Mapping)
            or model_output_provenance.get("schema_version")
            != "coding.target-plugin-model-output-provenance/v1"
            or model_output_provenance.get("approved_diff_sha256")
            != proposal.get("approved_diff_sha256")
            or list(model_output_provenance.get("changed_files") or []) != changed_files
            or model_output_provenance.get("blocked") is not False
            or model_output_provenance.get("target_adapter_provenance")
            != adapter_provenance
            or _sha256_json(model_output_provenance)
            != participant.get("output_sha256")
        ):
            raise CodingOrchestratorError("target_plugin_proposal_model_provenance_invalid")
        if approved_diff is not None and approved_diff != exact_diff:
            raise CodingOrchestratorError("target_plugin_approved_diff_mismatch")
        if target is not None and target != proposal.get("target"):
            raise CodingOrchestratorError("target_plugin_target_mismatch")
        if context_hash is not None and context_hash != proposal.get("context_hash"):
            raise CodingOrchestratorError("target_plugin_context_mismatch")
        return dict(proposal), output

    @staticmethod
    def _output_consumed(run: CodingLaneStateMachine, output_id: str) -> bool:
        return any(item.get("output_id") == output_id for item in run.runtime_consumptions)

    @staticmethod
    def _approval_identity(run: CodingLaneStateMachine) -> tuple[str, int]:
        executor = next(
            (record for record in run.participant_records if record.get("role") == "coding-executor"),
            None,
        )
        if not isinstance(executor, Mapping) or not isinstance(run.immutable_artifact, Mapping):
            raise CodingOrchestratorError("coding_approval_identity_missing")
        return (
            str(run.immutable_artifact.get("approval_id") or ""),
            int(run.immutable_artifact.get("generation") or 0),
        )

    @staticmethod
    def _persist(run: CodingLaneStateMachine, summary: str) -> dict[str, Any]:
        receipt = run.receipt(summary=summary)
        record_coding_orchestrator_state(run.task_id, state=receipt)
        return receipt


_PRODUCTION_ORCHESTRATOR: CodingOrchestrator | None = None


def get_coding_orchestrator() -> CodingOrchestrator:
    """Return the one production service; durable state remains in Source Proxy SQLite."""

    global _PRODUCTION_ORCHESTRATOR
    if _PRODUCTION_ORCHESTRATOR is None:
        _PRODUCTION_ORCHESTRATOR = CodingOrchestrator()
    return _PRODUCTION_ORCHESTRATOR


def reset_coding_orchestrator_service_for_tests() -> None:
    global _PRODUCTION_ORCHESTRATOR
    _PRODUCTION_ORCHESTRATOR = None


def _model_evidence_for_run(run: CodingLaneStateMachine) -> dict[str, Any]:
    """Derive model-authorship truth solely from persisted proposal/run records."""

    lower_ceiling = "applied_diff_verified_no_model_authorship_proof"
    proposal = run.target_plugin_proposal
    artifact = run.immutable_artifact
    if not isinstance(proposal, Mapping) or not isinstance(artifact, Mapping):
        return {
            "provider_available": bool(run.model_invocations),
            "provider_result": "not_proven",
            "generation_source": "manual_or_legacy",
            "provider_transport": "not_proven",
            "reported_success_path": "manual_or_legacy",
            "fallback_used": False,
            "proof_eligible": False,
            "terminal_proof_eligible": False,
            "claim_ceiling_impact": lower_ceiling,
        }
    proposal_body = dict(proposal)
    recorded_proposal_hash = str(proposal_body.pop("proposal_binding_sha256", ""))
    selected_invocation_id = str(proposal.get("producer_model_invocation_id") or "")
    selected = next(
        (
            record
            for record in run.model_invocations
            if record.get("invocation_id") == selected_invocation_id
        ),
        None,
    )
    output_id = str(proposal.get("runtime_output_id") or "")
    output = next(
        (record for record in run.runtime_outputs if record.get("output_id") == output_id),
        None,
    )
    adapter = proposal.get("target_adapter_provenance")
    output_provenance = proposal.get("model_output_provenance")
    exact_output = isinstance(output, Mapping) and isinstance(output.get("payload"), Mapping)
    if exact_output:
        exact_diff = str(output["payload"].get("approved_diff") or "")
        changed_files = [str(item) for item in output["payload"].get("changed_files", [])]
        exact_output = bool(
            output.get("producer_invocation_id") == selected_invocation_id
            and output.get("artifact_hash") == proposal.get("runtime_output_artifact_sha256")
            and hashlib.sha256(exact_diff.encode("utf-8")).hexdigest()
            == artifact.get("approved_diff_sha256")
            and changed_files == list(proposal.get("changed_files") or [])
            and any(item.get("output_id") == output_id for item in run.runtime_consumptions)
        )
    fallback_used = bool(
        isinstance(selected, Mapping)
        and any(
            record.get("passed") is False
            for record in run.model_invocations
            if record.get("invocation_id") != selected_invocation_id
        )
    )
    recovery_id: str | None = None
    recovery_claim: str | None = None
    recovery_proven = not fallback_used
    if fallback_used:
        for record in run.recovery_lineage:
            try:
                lineage = ControlledRecoveryLineage.from_payload(record).to_payload()
            except Exception:
                continue
            replacement = lineage.get("replacement")
            participant = replacement.get("participant") if isinstance(replacement, Mapping) else None
            if (
                isinstance(participant, Mapping)
                and participant.get("invocation_id") == selected_invocation_id
            ):
                recovery_id = str(lineage.get("recovery_id") or "") or None
                recovery_claim = str(lineage.get("claim_ceiling_impact") or "") or None
                recovery_proven = lineage.get("proof_eligible") is True
                break
    adapter_valid = isinstance(adapter, Mapping) and (
        adapter.get("terminal_proof_eligible") is True
        and adapter.get("transport_kind") == "canonical_litellm_router"
        and adapter.get("provider_call_made") is True
        and adapter.get("provider_call_authorized") is True
        and adapter.get("generation_source") == "model"
    )
    output_provenance_valid = isinstance(output_provenance, Mapping) and isinstance(
        selected, Mapping
    ) and _sha256_json(output_provenance) == selected.get("output_sha256")
    proof_eligible = bool(
        selected
        and selected.get("passed") is True
        and selected.get("output_sha256") == proposal.get("producer_model_output_sha256")
        and selected.get("artifact_sha256")
        == proposal.get("producer_model_artifact_sha256")
        and exact_output
        and adapter_valid
        and output_provenance_valid
        and recovery_proven
        and recorded_proposal_hash
        and _sha256_json(proposal_body) == recorded_proposal_hash
        and proposal.get("source_head") == current_head()
    )
    provider_transport = (
        "litellm_router"
        if isinstance(adapter, Mapping)
        and adapter.get("transport_kind") == "canonical_litellm_router"
        else str(adapter.get("transport_kind") or "not_proven")
        if isinstance(adapter, Mapping)
        else "not_proven"
    )
    claim_ceiling = (
        recovery_claim
        if proof_eligible and fallback_used and recovery_claim
        else "model_authored_applied_diff_verified"
        if proof_eligible
        else lower_ceiling
    )
    return {
        "provider_available": bool(run.model_invocations),
        "provider_result": "success" if proof_eligible else "not_proven",
        "generation_source": (
            str(adapter.get("generation_source") or "not_proven")
            if isinstance(adapter, Mapping)
            else "not_proven"
        ),
        "provider_transport": provider_transport,
        "provider": str(selected.get("provider") or "") if isinstance(selected, Mapping) else "",
        "model": str(selected.get("model") or "") if isinstance(selected, Mapping) else "",
        "model_invocation_id": selected_invocation_id,
        "model_output_id": str(selected.get("output_id") or "") if isinstance(selected, Mapping) else "",
        "model_output_sha256": (
            str(selected.get("output_sha256") or "") if isinstance(selected, Mapping) else ""
        ),
        "raw_model_response_sha256": (
            str(adapter.get("raw_response_sha256") or "")
            if isinstance(adapter, Mapping)
            else ""
        ),
        "rendered_prompt_sha256": (
            str(adapter.get("rendered_prompt_sha256") or "")
            if isinstance(adapter, Mapping)
            else ""
        ),
        "runtime_output_id": output_id,
        "proposal_binding_sha256": recorded_proposal_hash,
        "reported_success_path": "fallback" if fallback_used else "primary",
        "fallback_used": fallback_used,
        "recovery_id": recovery_id,
        "proof_eligible": proof_eligible,
        "terminal_proof_eligible": proof_eligible,
        "claim_ceiling_impact": claim_ceiling,
    }


def _artifact_provenance_for_run(run: CodingLaneStateMachine) -> dict[str, Any]:
    transfer = run.cartographer_transfer
    finalization = run.cartographer_finalization
    cartographer_identity: dict[str, Any] = {}
    if isinstance(transfer, Mapping):
        acknowledgement = (
            finalization.get("downstream_acknowledgement")
            if isinstance(finalization, Mapping)
            else None
        )
        authority_receipt = (
            finalization.get("authority_receipt")
            if isinstance(finalization, Mapping)
            else None
        )
        cartographer_identity = {
            "proposal_id": transfer.get("proposal_id"),
            "selection_id": transfer.get("selection_id"),
            "selection_generation": transfer.get("selection_generation"),
            "transfer_event_id": transfer.get("transfer_event_id"),
            "consumer_invocation_id": transfer.get(
                "downstream_consumer_invocation_id"
            ),
            "acknowledgement_id": (
                acknowledgement.get("acknowledgement_id")
                if isinstance(acknowledgement, Mapping)
                else None
            ),
            "authority_state": (
                authority_receipt.get("state")
                if isinstance(authority_receipt, Mapping)
                else None
            ),
            "source_head": (
                transfer.get("provenance", {}).get("source_head")
                if isinstance(transfer.get("provenance"), Mapping)
                else None
            ),
        }
    proposal = run.target_plugin_proposal
    adapter = (
        proposal.get("target_adapter_provenance")
        if isinstance(proposal, Mapping)
        else None
    )
    model_bound = isinstance(adapter, Mapping) and adapter.get(
        "terminal_proof_eligible"
    ) is True
    return {
        "cartographer_identity": cartographer_identity,
        "claim_ceiling": (
            "model_authored_diff_pending_independent_verification"
            if model_bound
            else "approved_diff_pending_independent_verification_without_terminal_model_proof"
        ),
    }


def _target_plugin_model_participant(
    *,
    run: CodingLaneStateMachine,
    task_id: str,
    attempt_id: str,
    input_sha256: str,
    result: Mapping[str, Any],
    configured_alias: str | None,
    started_at: str,
    completed_at: str,
    invocation_id: str | None = None,
) -> dict[str, Any]:
    diagnostics = _coder_diagnostics(result)
    alias = str(
        configured_alias
        or diagnostics.get("selected_model_alias")
        or "server-selected-model"
    )
    provider = str(diagnostics.get("provider") or route_provider_for_alias(alias) or "model-router")
    model = str(diagnostics.get("model") or route_model_for_alias(alias) or alias)
    proposed_diff = str(result.get("proposed_diff") or "")
    blocked = bool(result.get("coder_blocked") or result.get("coderBlocked"))
    passed = bool(proposed_diff.strip()) and not blocked
    output_sha256 = _sha256_json(_target_plugin_model_output_provenance(result))
    if passed:
        artifact_sha256 = _sha256_json(
            {
                "proposed_diff": proposed_diff,
                "changed_files": diagnostics.get("changed_files", []),
            }
        )
        result_id = f"target-plugin-result-{uuid4().hex}"
        error_code = None
        error_message = None
    else:
        artifact_sha256 = None
        result_id = None
        error_code = str(
            result.get("reason_code")
            or result.get("reasonCode")
            or diagnostics.get("final_reason_code")
            or "target_plugin_model_failed"
        )
        error_message = str(
            result.get("blocked_reason")
            or result.get("blockedReason")
            or result.get("needed_context")
            or diagnostics.get("exception_message")
            or error_code
        )[:500]
    return {
        "schema_version": RECOVERY_PARTICIPANT_SCHEMA,
        "role": "target-plugin-model",
        "lane_id": "coder",
        "run_id": run.run_id,
        "task_id": task_id,
        "attempt_id": attempt_id,
        "invocation_id": invocation_id or f"target-plugin-model-invocation-{uuid4().hex}",
        "output_id": f"target-plugin-model-output-{uuid4().hex}",
        "provider": provider,
        "model": model,
        "input_sha256": input_sha256,
        "output_sha256": output_sha256,
        "artifact_sha256": artifact_sha256,
        "result_id": result_id,
        "error_code": error_code,
        "error_message": error_message,
        "started_at": started_at,
        "completed_at": completed_at,
        "passed": passed,
    }


def _target_plugin_model_output_provenance(result: Mapping[str, Any]) -> dict[str, Any]:
    diagnostics = _coder_diagnostics(result)
    proposed_diff = str(result.get("proposed_diff") or "")
    return {
        "schema_version": "coding.target-plugin-model-output-provenance/v1",
        "approved_diff_sha256": hashlib.sha256(proposed_diff.encode("utf-8")).hexdigest(),
        "changed_files": [str(value) for value in diagnostics.get("changed_files", [])],
        "blocked": bool(result.get("coder_blocked") or result.get("coderBlocked")),
        "reason_code": str(
            result.get("reason_code")
            or result.get("reasonCode")
            or diagnostics.get("final_reason_code")
            or ""
        ),
        "target_adapter_provenance": dict(
            result.get("target_adapter_provenance") or {}
        ),
    }


def _is_truthful_non_mutating_target_result(result: Mapping[str, Any]) -> bool:
    if str(result.get("proposed_diff") or "").strip():
        return False
    if bool(result.get("already_satisfied") or result.get("alreadySatisfied")):
        return True
    expected = str(
        result.get("expected_result_state")
        or result.get("expectedResultState")
        or ""
    ).upper()
    provenance = result.get("target_adapter_provenance")
    return expected in {"PASS_NOOP", "PASS_BLOCKED", "NOOP", "BLOCKED"} or (
        isinstance(provenance, Mapping)
        and provenance.get("transport_kind") == "non_model"
        and provenance.get("trust_status")
        in {"verified_non_model_noop", "verified_non_model_policy_block"}
    )


def _coder_diagnostics(result: Mapping[str, Any]) -> dict[str, Any]:
    value = result.get("coder_diagnostics")
    if not isinstance(value, Mapping):
        value = result.get("coderDiagnostics")
    return dict(value) if isinstance(value, Mapping) else {}


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
        default=str,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _mapping_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
