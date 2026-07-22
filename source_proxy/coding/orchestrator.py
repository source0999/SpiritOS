"""Durable production owner for the core SpiritOS coding lifecycle."""
from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import os
import subprocess
import sys
import time
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
    render_evidence_guided_repair_model_task,
    target_plugin_model_input_sha256,
)
from source_proxy.context.canonical_broker import build_context_broker_report
from source_proxy.contracts.coding_lane_contracts import canonical_coding_lane_contracts
from source_proxy.diagnostics.status_codes import classify_repair_failure
from source_proxy.approval.campaign_authority import (
    CampaignApprovalError,
    current_head,
    finalize_coding_execution_approval,
)
from source_proxy.planning.plan import (
    ArchitectPlan,
    load_plan,
    save_plan,
    task_spec_from_plan,
)
from source_proxy.planning.reviewer import review_diff_deterministically
from source_proxy.routing.litellm_router import route_model_for_alias, route_provider_for_alias
from source_proxy.target_plugins.adapter import (
    GENERIC_WORKSPACE_PLUGIN_ID,
    ResolvedTargetPlugin,
    execute_target_plugin_command,
    target_adapter_producer_identity_valid,
)
from source_proxy.target_plugins.selection import (
    expected_target_plugin_id,
    is_target_plugin_prompt_id,
)
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
REPAIR_ATTEMPT_SEAL_SCHEMA = "coding.repair-attempt-seal/v1"
REPAIR_REQUEST_SCHEMA = "coding.evidence-guided-repair-request/v1"
REPAIR_APPROVAL_DISPOSITION_SCHEMA = "coding.repair-approval-disposition/v1"
REPAIR_DIAGNOSTIC_SCHEMA = "coding.deterministic-repair-diagnostic/v1"
REPAIR_DEBUGGER_TRACE_SCHEMA = "coding.deterministic-debugger-trace/v1"
MAX_CODING_ATTEMPTS = 3
MAX_REPAIR_DEBUGGER_FILES = 128
REPAIR_DEBUGGER_TIMEOUT_SECONDS = 10
_DETERMINISTIC_DEBUGGER_SCRIPT = r'''import ast
import hashlib
import json
import pathlib
import sys

payload = json.loads(sys.stdin.read())
files = []
probe_failed = False
for item in payload.get("files", []):
    path = pathlib.Path(item["absolute_path"])
    exists = path.is_file()
    expected_exists = item.get("expected_exists") is True
    result = {
        "path": item.get("path"),
        "exists": exists,
        "expected_exists": expected_exists,
        "sha256": None,
        "expected_sha256": item.get("expected_sha256"),
        "state_matches": exists == expected_exists,
        "python_syntax": "not_applicable",
        "syntax_error": None,
    }
    data = b""
    if exists:
        data = path.read_bytes()
        result["sha256"] = hashlib.sha256(data).hexdigest()
        result["state_matches"] = (
            result["state_matches"]
            and result["sha256"] == item.get("expected_sha256")
        )
    if exists and path.suffix.lower() == ".py":
        try:
            ast.parse(data.decode("utf-8"), filename=str(item.get("path") or path))
            result["python_syntax"] = "passed"
        except (SyntaxError, UnicodeDecodeError) as error:
            result["python_syntax"] = "failed"
            result["syntax_error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "line": getattr(error, "lineno", None),
                "offset": getattr(error, "offset", None),
            }
    if not result["state_matches"] or result["python_syntax"] == "failed":
        probe_failed = True
    files.append(result)

feedback = payload.get("exact_failure_output")
post_apply = feedback.get("post_apply_verification", {}) if isinstance(feedback, dict) else {}
checks = post_apply.get("checks", []) if isinstance(post_apply, dict) else []
failed_checks = [
    dict(check)
    for check in checks
    if isinstance(check, dict) and str(check.get("status", "")).lower() == "failed"
]
findings = {
    "schema_version": "coding.deterministic-debugger-findings/v1",
    "classification_input": payload.get("classification_input"),
    "failed_checks": failed_checks,
    "files": files,
    "probe_passed": not probe_failed,
}
print(json.dumps(findings, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True))
raise SystemExit(1 if probe_failed else 0)
'''
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
    attempt_number: int = 1
    attempt_history: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    attempt_dispositions: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    repair_request: dict[str, Any] | None = None
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
            "attempt_number": self.attempt_number,
            "max_attempts": MAX_CODING_ATTEMPTS,
            "attempt_history": list(self.attempt_history),
            "attempt_dispositions": list(self.attempt_dispositions),
            "repair_request": dict(self.repair_request) if self.repair_request else None,
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
        attempt_failure_finalizer: Callable[..., dict[str, Any]] | None = None,
    ) -> None:
        self._executor = executor
        self._planner_loader = planner_loader
        self._post_apply_verifier = post_apply_verifier
        self._state_loader = state_loader
        self._reviewer = reviewer
        self._verifier = verifier
        self._anti_cheat = anti_cheat
        self._evidence_recorder = evidence_recorder
        self._attempt_failure_finalizer = (
            attempt_failure_finalizer or fail_orchestrated_coding_execution
        )

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
            if not isinstance(acknowledgement, Mapping):
                raise CodingOrchestratorError(
                    "cartographer_transfer_consumer_invocation_mismatch"
                )
            if acknowledgement.get("consumer_invocation_id") != consumer_invocation_id:
                if not isinstance(run.repair_request, Mapping):
                    raise CodingOrchestratorError(
                        "cartographer_transfer_consumer_invocation_mismatch"
                    )
                if (
                    str(transfer.get("target") or "") != target
                    or not run.attempt_history
                    or run.repair_request.get("parent_attempt_seal_sha256")
                    != run.attempt_history[-1].get("seal_sha256")
                ):
                    raise CodingOrchestratorError(
                        "cartographer_repair_scope_inheritance_invalid"
                    )
                run.record_event(
                    event_type="cartographer_scope_inherited_by_repair_attempt",
                    lane_id="coder",
                    detail={
                        "original_consumer_invocation_id": acknowledgement.get(
                            "consumer_invocation_id"
                        ),
                        "repair_consumer_invocation_id": consumer_invocation_id,
                        "target": target,
                        "parent_attempt_seal_sha256": run.repair_request.get(
                            "parent_attempt_seal_sha256"
                        ),
                    },
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
                "plan_id": str(
                    plan_payload.get("plan_id")
                    or plan_payload.get("task_id")
                    or task_id
                ),
                "task_spec": plan_payload,
            },
        )
        run.transition("planner", "completed", reason="authoritative_plan_loaded")
        run.transition("context-broker", "completed", reason="planner_context_consumed")
        return self._persist(run, "planner completed with consumed canonical context")

    def _persist_adapter_architect_plan(
        self,
        task_id: str,
        plan: ArchitectPlan,
    ) -> dict[str, Any]:
        """Persist the exact generic-adapter plan before its coder provider call."""

        if not isinstance(plan, ArchitectPlan) or plan.task_id != task_id:
            raise CodingOrchestratorError(
                "target_plugin_architect_plan_identity_mismatch"
            )
        run = self._restore(task_id)
        if run.lane_states["planner"] != "completed":
            save_plan(task_id, plan)
            return self.acknowledge_planner(task_id)

        report = self._acknowledge_persisted_context(
            task_id,
            consumer="planner",
            evidence="generic_adapter_architect_plan_ready",
            reason="planner_consumed_context_for_generic_adapter_attempt",
        )
        if report.get("go_eligible") is not True:
            raise CodingOrchestratorError(
                "target_plugin_architect_plan_context_blocked"
            )
        context_output = self._issue_refreshed_context_output(
            run,
            report=report,
            refresh_reason="generic_adapter_architect_plan_ready_before_coder",
        )
        self._persist(
            run,
            "generic-adapter planner context persisted before refreshed plan",
        )
        predecessor_planner_output = self._latest_output(run, "planner")
        planner_invocation_id = f"planner-adapter-invocation-{uuid4().hex}"
        self._consume_output(
            run,
            output_id=context_output["output_id"],
            consumer_invocation_id=planner_invocation_id,
            payload={
                "consumer": "planner",
                "context_hash": str(report["canonical_report_hash"]),
            },
        )
        if not self._output_consumed(
            run, str(predecessor_planner_output["output_id"])
        ):
            self._consume_output(
                run,
                output_id=str(predecessor_planner_output["output_id"]),
                consumer_invocation_id=planner_invocation_id,
                payload={"context_hash": str(report["canonical_report_hash"])},
            )
        save_plan(task_id, plan)
        plan_payload = plan.to_dict()
        planner_output = self._enforce_runtime_contract_output(
            run,
            lane_id="planner",
            producer_invocation_id=planner_invocation_id,
            payload={
                "plan_id": plan.plan_id,
                "task_spec": plan_payload,
            },
        )
        run.record_event(
            event_type="generic_adapter_architect_plan_persisted",
            lane_id="planner",
            detail={
                "attempt_id": run.attempt_id,
                "plan_id": plan.plan_id,
                "plan_sha256": _sha256_json(plan_payload),
                "planner_output_id": planner_output["output_id"],
                "planner_invocation_id": planner_invocation_id,
            },
        )
        return self._persist(
            run,
            "exact generic-adapter architect plan persisted before coder invocation",
        )

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
        if _sealed_attempt_awaits_disposition(run):
            self._resume_sealed_attempt_disposition(run)
            run = self._restore(task_id)
        generic_adapter_plan_required = (
            plugin.plugin_id == GENERIC_WORKSPACE_PLUGIN_ID
        )
        deferred_generic_plan = bool(
            run.lane_states["planner"] != "completed"
            and generic_adapter_plan_required
        )
        if isinstance(run.target_plugin_proposal, Mapping) and run.target_plugin_proposal.get(
            "status"
        ) == "ready_for_approval_preview":
            raise CodingOrchestratorError("target_plugin_proposal_already_pending")
        if str(plugin.source_head or "") != current_head():
            raise CodingOrchestratorError("target_plugin_source_head_mismatch")
        if expected_target_plugin_id(plugin.selected_prompt_id) != plugin.plugin_id:
            raise CodingOrchestratorError("target_plugin_prompt_identity_mismatch")
        target_source_head = str(plugin.target_source_head or plugin.source_head or "")
        if not target_source_head:
            raise CodingOrchestratorError("target_plugin_target_source_head_missing")
        plugin_identity = plugin.evidence_identity()
        if isinstance(run.repair_request, Mapping):
            _validate_repair_target_baseline(
                repair_request=run.repair_request,
                target_plugin_identity=plugin_identity,
            )
        if run.lane_states["planner"] != "completed" and not deferred_generic_plan:
            self.acknowledge_planner(task_id)
            run = self._restore(task_id)
        original_task = (
            str(run.repair_request.get("original_task") or task)
            if isinstance(run.repair_request, Mapping)
            else task
        )
        model_task, repair_prompt_sha256 = _model_task_with_repair_context(run, task)
        if isinstance(run.repair_request, Mapping):
            if run.lane_states["repair"] == "pending":
                run.transition(
                    "repair",
                    "running",
                    reason="evidence_guided_repair_model_dispatch_started",
                )
            elif run.lane_states["repair"] != "running":
                raise CodingOrchestratorError("repair_lane_not_dispatchable")
            run.record_event(
                event_type="repair_prompt_built",
                lane_id="repair",
                detail={
                    "repair_input_sha256": run.repair_request.get("repair_input_sha256"),
                    "repair_prompt_sha256": repair_prompt_sha256,
                    "parent_attempt_id": run.parent_attempt_id,
                },
            )
            self._persist(run, "evidence-guided repair prompt persisted before model dispatch")
        primary_invocation_id = f"target-plugin-model-invocation-{uuid4().hex}"
        persisted_context = canonical_context_broker_for_task(task_id)
        if not isinstance(persisted_context, Mapping):
            raise CodingOrchestratorError("canonical_context_report_missing")
        context: Mapping[str, Any] = persisted_context
        primary_context_binding: dict[str, Any] | None = None
        invocation_event: dict[str, Any] | None = None

        def begin_coder_invocation() -> None:
            nonlocal run, context, primary_context_binding, invocation_event
            run = self._restore(task_id)
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
                    "target_plugin_identity": plugin_identity,
                    "canonical_context_report_hash": context["canonical_report_hash"],
                    "context_runtime_output_id": primary_context_binding["output_id"],
                    "context_consumer_acknowledgement_id": primary_context_binding[
                        "acknowledgement_id"
                    ],
                    "context_consumption_id": primary_context_binding["consumption_id"],
                },
            )
            self._persist(run, "target-plugin model invocation started")

        plan_ready_callback: Callable[[ArchitectPlan], Mapping[str, Any]] | None = None
        primary_plan_ready = False
        if generic_adapter_plan_required:
            def persist_adapter_plan(plan: ArchitectPlan) -> Mapping[str, Any]:
                nonlocal primary_plan_ready
                if primary_plan_ready:
                    raise CodingOrchestratorError(
                        "target_plugin_architect_plan_callback_repeated"
                    )
                primary_plan_ready = True
                self._persist_adapter_architect_plan(task_id, plan)
                begin_coder_invocation()
                return context

            plan_ready_callback = persist_adapter_plan
        else:
            begin_coder_invocation()

        primary_alias_variable = (
            "SOURCE_PROXY_CODER_REPAIR_MODEL_ALIAS"
            if isinstance(run.repair_request, Mapping)
            else "SPIRITOS_CODING_PRIMARY_MODEL_ALIAS"
        )
        primary_alias = os.getenv(primary_alias_variable, "").strip() or None
        primary_started_at = _utc_now()
        primary_result = execute_target_plugin_command(
            plugin,
            task=model_task,
            workspace_root=Path(plugin.workspace_root),
            canonical_context=context,
            canonical_context_text=json.dumps(context, sort_keys=True),
            model_alias=primary_alias,
            architect_task_id=task_id,
            plan_ready_callback=plan_ready_callback,
        )
        primary_completed_at = _utc_now()
        if _is_truthful_non_mutating_target_result(primary_result):
            outcome = {
                "schema_version": "coding.target-plugin-outcome/v1",
                "task_id": task_id,
                "run_id": run.run_id,
                "target_plugin_identity": plugin_identity,
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
                lane_id="coder" if invocation_event is not None else "planner",
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
        if primary_context_binding is None or invocation_event is None:
            raise CodingOrchestratorError(
                "target_plugin_architect_plan_not_persisted_before_coder"
            )
        input_sha256 = _target_plugin_model_input_sha256(
            task=model_task,
            target_plugin_identity=plugin_identity,
            canonical_context=context,
        )
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
            fallback_context: Mapping[str, Any] = context
            fallback_context_binding: dict[str, Any] | None = None
            fallback_invocation_event: dict[str, Any] | None = None

            def begin_fallback_invocation() -> None:
                nonlocal run, fallback_context, fallback_context_binding
                nonlocal fallback_invocation_event
                run = self._restore(task_id)
                fallback_context = self._acknowledge_persisted_context(
                    task_id,
                    consumer="coder",
                    evidence="authorized_fallback_consumed_canonical_context",
                    reason="coder_consumed_context_before_authorized_fallback",
                )
                if fallback_context.get("go_eligible") is not True:
                    raise CodingOrchestratorError(
                        "target_plugin_fallback_context_blocked"
                    )
                fallback_context_binding = self._bind_context_to_invocation(
                    run,
                    report=fallback_context,
                    consumer_invocation_id=fallback_invocation_id,
                    refresh_reason="canonical_context_reissued_for_authorized_fallback",
                )
                fallback_invocation_event = run.record_event(
                    event_type="target_plugin_model_invocation",
                    lane_id="coder",
                    detail={
                        "invocation_id": fallback_invocation_id,
                        "plugin_id": plugin.plugin_id,
                        "selected_prompt_id": plugin.selected_prompt_id,
                        "target_plugin_identity": plugin_identity,
                        "canonical_context_report_hash": fallback_context[
                            "canonical_report_hash"
                        ],
                        "context_runtime_output_id": fallback_context_binding[
                            "output_id"
                        ],
                        "context_consumer_acknowledgement_id": fallback_context_binding[
                            "acknowledgement_id"
                        ],
                        "context_consumption_id": fallback_context_binding[
                            "consumption_id"
                        ],
                        "recovery_id": authorization.to_payload()["recovery_id"],
                    },
                )
                self._persist(
                    run,
                    "fallback context consumption persisted before replacement call",
                )

            fallback_plan_ready_callback: (
                Callable[[ArchitectPlan], Mapping[str, Any]] | None
            ) = None
            fallback_plan_ready = False
            if generic_adapter_plan_required:
                def persist_fallback_adapter_plan(
                    plan: ArchitectPlan,
                ) -> Mapping[str, Any]:
                    nonlocal fallback_plan_ready
                    if fallback_plan_ready:
                        raise CodingOrchestratorError(
                            "target_plugin_fallback_plan_callback_repeated"
                        )
                    fallback_plan_ready = True
                    self._persist_adapter_architect_plan(task_id, plan)
                    begin_fallback_invocation()
                    return fallback_context

                fallback_plan_ready_callback = persist_fallback_adapter_plan
            else:
                begin_fallback_invocation()

            fallback_result = execute_target_plugin_command(
                plugin,
                task=model_task,
                workspace_root=Path(plugin.workspace_root),
                canonical_context=(
                    context if generic_adapter_plan_required else fallback_context
                ),
                canonical_context_text=json.dumps(
                    context if generic_adapter_plan_required else fallback_context,
                    sort_keys=True,
                ),
                model_alias=fallback_alias,
                architect_task_id=task_id,
                plan_ready_callback=fallback_plan_ready_callback,
            )
            fallback_completed_at = _utc_now()
            if (
                fallback_context_binding is None
                or fallback_invocation_event is None
            ):
                raise CodingOrchestratorError(
                    "target_plugin_fallback_plan_not_persisted_before_coder"
                )
            fallback_input_sha256 = _target_plugin_model_input_sha256(
                task=model_task,
                target_plugin_identity=plugin_identity,
                canonical_context=fallback_context,
            )
            fallback_participant = _target_plugin_model_participant(
                run=run,
                task_id=task_id,
                attempt_id=replacement_attempt_id,
                input_sha256=fallback_input_sha256,
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
            selected_context = fallback_context
            if completed_recovery.proof_eligible is not True:
                self._persist(run, "target-plugin fallback failed in the same run lineage")
                raise CodingOrchestratorError(str(fallback_participant["error_code"]))
        else:
            selected_context_binding = primary_context_binding
            selected_context = context

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
        planner_output = self._latest_output(run, "planner")
        if self._output_consumed(run, str(planner_output["output_id"])):
            raise CodingOrchestratorError(
                "target_plugin_planner_output_consumed_before_proposal"
            )
        planner_payload = planner_output.get("payload")
        if not isinstance(planner_payload, Mapping):
            raise CodingOrchestratorError("target_plugin_planner_output_invalid")
        planner_consumption = self._consume_output(
            run,
            output_id=str(planner_output["output_id"]),
            consumer_invocation_id=str(selected_participant["invocation_id"]),
            payload={
                "context_hash": str(
                    selected_context.get("canonical_report_hash") or ""
                )
            },
        )
        planner_acknowledgement = next(
            item
            for item in run.runtime_acknowledgements
            if item.get("acknowledgement_id")
            == planner_consumption.get("acknowledgement_id")
        )
        self._persist(
            run,
            "selected target-plugin model consumed exact planner output before proposal review",
        )
        semantic_review_binding = _build_semantic_review_binding(
            task_id=task_id,
            run_id=run.run_id,
            attempt_id=run.attempt_id,
            planner_output=planner_output,
            proposed_diff=proposed_diff,
            changed_files=changed_files,
            adapter_diagnostics=diagnostics,
            adapter_architect_plan_required=generic_adapter_plan_required,
            repair_request=(
                run.repair_request
                if isinstance(run.repair_request, Mapping)
                else None
            ),
        )
        run.record_event(
            event_type="semantic_preview_review_passed",
            lane_id="reviewer",
            detail={
                "server_plan_sha256": semantic_review_binding[
                    "server_plan_sha256"
                ],
                "acceptance_criteria_sha256": semantic_review_binding[
                    "acceptance_criteria_sha256"
                ],
                "preview_review_receipt_sha256": semantic_review_binding[
                    "preview_review_receipt_sha256"
                ],
                "semantic_review_binding_sha256": semantic_review_binding[
                    "semantic_review_binding_sha256"
                ],
            },
        )
        repair_strategy_signature: str | None = None
        if isinstance(run.repair_request, Mapping):
            repair_strategy_signature = _repair_strategy_signature(
                repair_request=run.repair_request,
                approved_diff=proposed_diff,
                participant=selected_participant,
                selected_prompt_id=plugin.selected_prompt_id,
                selected_context_id=plugin.selected_context_id,
            )
            prior_signatures = {
                str(item.get("repair_strategy_signature") or "")
                for item in run.attempt_history
                if str(item.get("repair_strategy_signature") or "")
            }
            if repair_strategy_signature in prior_signatures:
                run.record_event(
                    event_type="repair_strategy_rejected",
                    lane_id="repair",
                    detail={
                        "repair_strategy_signature": repair_strategy_signature,
                        "reason_code": "repair_attempt_requires_new_evidence_or_strategy",
                    },
                )
                self._persist(run, "duplicate evidence-guided repair strategy rejected")
                raise CodingOrchestratorError(
                    "repair_attempt_requires_new_evidence_or_strategy"
                )
        if isinstance(run.cartographer_transfer, dict):
            transfer_target = str(run.cartographer_transfer.get("target") or "")
            fixture_root = str(plugin.fixture_root or "").strip().strip("/")
            if fixture_root not in {"", "."} and not transfer_target.startswith(
                f"{fixture_root}/"
            ):
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
            "attempt_id": run.attempt_id,
            "parent_attempt_id": run.parent_attempt_id,
            "attempt_number": run.attempt_number,
            "original_task": original_task,
            "runtime_output_id": output["output_id"],
            "runtime_output_artifact_sha256": output["artifact_hash"],
            "producer_model_invocation_id": selected_participant["invocation_id"],
            "producer_model_output_sha256": selected_participant["output_sha256"],
            "producer_model_artifact_sha256": selected_participant["artifact_sha256"],
            "producer_model_alias": (
                selected_result.get("target_adapter_provenance", {}).get(
                    "selected_model_alias"
                )
                if isinstance(
                    selected_result.get("target_adapter_provenance"), Mapping
                )
                else diagnostics.get("selected_model_alias")
            ),
            "producer_model_provider": selected_participant["provider"],
            "producer_model_name": selected_participant["model"],
            "producer_adapter_call_index": (
                selected_result.get("target_adapter_provenance", {}).get(
                    "producer_call_index"
                )
                if isinstance(
                    selected_result.get("target_adapter_provenance"), Mapping
                )
                else None
            ),
            "planner_runtime_output_id": planner_output["output_id"],
            "planner_runtime_artifact_sha256": planner_output["artifact_hash"],
            "planner_consumer_acknowledgement_id": planner_acknowledgement[
                "acknowledgement_id"
            ],
            "planner_consumption_id": planner_consumption["consumption_id"],
            "model_output_provenance": _target_plugin_model_output_provenance(
                selected_result
            ),
            "target_adapter_provenance": dict(
                selected_result.get("target_adapter_provenance") or {}
            ),
            "target_plugin_identity": plugin_identity,
            "selected_prompt_id": plugin.selected_prompt_id,
            "selected_context_id": plugin.selected_context_id,
            "context_hash": str(selected_context.get("canonical_report_hash") or ""),
            "canonical_context_report": selected_context,
            "canonical_context_report_sha256": _sha256_json(selected_context),
            "context_runtime_output_id": selected_context_binding["output_id"],
            "context_runtime_artifact_sha256": selected_context_binding["artifact_hash"],
            "context_consumer_acknowledgement_id": selected_context_binding[
                "acknowledgement_id"
            ],
            "context_consumption_id": selected_context_binding["consumption_id"],
            "source_head": current_head(),
            "target_source_head": target_source_head,
            "target_workspace_state_sha256": plugin_identity.get(
                "target_workspace_state_sha256"
            ),
            "target_workspace_state_paths": list(
                plugin_identity.get("target_workspace_state_paths") or []
            ),
            "target": proposal_target,
            "approved_diff_sha256": hashlib.sha256(proposed_diff.encode("utf-8")).hexdigest(),
            "changed_files": changed_files,
            "semantic_review_binding": semantic_review_binding,
            "semantic_review_binding_sha256": semantic_review_binding[
                "semantic_review_binding_sha256"
            ],
            "status": "ready_for_approval_preview",
        }
        if isinstance(run.repair_request, Mapping):
            proposal_body.update(
                {
                    "repair_context": json.loads(
                        json.dumps(dict(run.repair_request), sort_keys=True, default=str)
                    ),
                    "repair_input_sha256": run.repair_request["repair_input_sha256"],
                    "repair_prompt_sha256": repair_prompt_sha256,
                    "repair_strategy_signature": repair_strategy_signature,
                }
            )
        proposal_body["proposal_binding_sha256"] = _sha256_json(proposal_body)
        run.target_plugin_proposal = proposal_body
        run.record_event(
            event_type="target_plugin_proposal_ready",
            lane_id="coder",
            detail={
                "output_id": output["output_id"],
                "selected_prompt_id": plugin.selected_prompt_id,
                "target_plugin_identity": plugin_identity,
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
        repair_execution = isinstance(run.repair_request, Mapping)
        if repair_execution and approval_id in _sealed_approval_ids(run):
            raise CodingOrchestratorError("repair_approval_reuse_detected")
        if repair_execution or is_target_plugin_prompt_id(selected_prompt_id):
            if not runtime_output_id:
                raise CodingOrchestratorError(
                    "repair_target_plugin_runtime_output_id_missing"
                    if repair_execution
                    else "target_plugin_runtime_output_id_missing"
                )
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
                provenance=_artifact_provenance_for_run(run),
            )
        run.immutable_artifact = dict(artifact)
        expected_diff_sha256 = hashlib.sha256(approved_diff.encode("utf-8")).hexdigest()
        if (
            run.immutable_artifact.get("approval_id") != approval_id
            or run.immutable_artifact.get("approved_diff_sha256") != expected_diff_sha256
        ):
            raise CodingOrchestratorError("coding_artifact_approval_binding_mismatch")
        if isinstance(proposal, Mapping) and (
            run.immutable_artifact.get("semantic_review_identity")
            != proposal.get("semantic_review_binding")
        ):
            raise CodingOrchestratorError(
                "coding_artifact_semantic_review_binding_mismatch"
            )
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
            if is_target_plugin_prompt_id(selected_prompt_id):
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
                "blocked_reasons": list(
                    reviewer_record.get("result", {}).get("blocked_reasons") or []
                ),
                "semantic_review": dict(
                    reviewer_record.get("result", {}).get("semantic_review") or {}
                ),
                "semantic_review_input_sha256": reviewer_record.get(
                    "result", {}
                ).get("semantic_review_input_sha256"),
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
            reviewer_feedback = {
                "source_lane": "reviewer",
                "participant_invocation_id": str(reviewer_record.get("invocation_id") or ""),
                "runtime_output_id": str(reviewer_output.get("output_id") or ""),
                "findings": list(reviewer_record.get("result", {}).get("findings") or []),
                "blocked_reasons": list(
                    reviewer_record.get("result", {}).get("blocked_reasons") or []
                ),
                "participant_result": dict(reviewer_record.get("result") or {}),
            }
            if run.attempt_number < MAX_CODING_ATTEMPTS:
                self._queue_evidence_guided_repair(
                    run,
                    failure_class="reviewer_rejection",
                    source_lane="reviewer",
                    exact_feedback=reviewer_feedback,
                )
                raise CodingOrchestratorError(
                    "independent_review_failed_repair_required"
                )
            self._mark_repair_exhausted(
                run,
                reason_code="independent_review_failed",
                failure_class="reviewer_rejection",
                source_lane="reviewer",
                exact_feedback=reviewer_feedback,
            )
            self._persist(run, "independent reviewer failed after bounded repair attempts")
            raise CodingOrchestratorError(
                "repair_attempt_limit_exhausted:independent_review_failed"
            )
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
            verifier_feedback = {
                "source_lane": "verifier",
                "participant_invocation_id": str(verifier_record.get("invocation_id") or ""),
                "runtime_output_id": str(verifier_output.get("output_id") or ""),
                "verdict": str(verifier_record.get("result", {}).get("verdict") or "FAIL"),
                "checks": list(verifier_record.get("result", {}).get("checks") or []),
                "blocked_reasons": list(
                    verification.get("blocked_reasons")
                    or verifier_record.get("result", {}).get("blocked_reasons")
                    or []
                ),
                "participant_result": dict(verifier_record.get("result") or {}),
                "post_apply_verification": dict(verification),
            }
            if run.attempt_number < MAX_CODING_ATTEMPTS:
                receipt = self._queue_evidence_guided_repair(
                    run,
                    failure_class="verifier_rejection",
                    source_lane="verifier",
                    exact_feedback=verifier_feedback,
                )
            else:
                self._mark_repair_exhausted(
                    run,
                    reason_code="independent_verification_failed",
                    failure_class="verifier_rejection",
                    source_lane="verifier",
                    exact_feedback=verifier_feedback,
                )
                receipt = self._persist(
                    run,
                    "independent verifier failed after bounded repair attempts",
                )
            response = dict(result)
            response["coding_orchestrator"] = receipt
            response["repair_required"] = isinstance(
                receipt.get("repair_request"), Mapping
            )
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
        if run.attempt_history:
            if run.lane_states["repair"] != "running":
                raise CodingOrchestratorError("repair_lane_success_state_invalid")
            run.transition(
                "repair",
                "completed",
                reason="evidence_guided_repair_verified",
            )
        else:
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

    def _queue_evidence_guided_repair(
        self,
        run: CodingLaneStateMachine,
        *,
        failure_class: str,
        source_lane: str,
        exact_feedback: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Seal one failed apply attempt, then open a fresh approval-bound attempt."""

        if run.attempt_number >= MAX_CODING_ATTEMPTS:
            raise CodingOrchestratorError("repair_attempt_limit_exhausted")
        next_attempt_id = f"coding-attempt-{uuid4().hex}"
        self._seal_failed_attempt(
            run,
            failure_class=failure_class,
            source_lane=source_lane,
            exact_feedback=exact_feedback,
            next_attempt_id=next_attempt_id,
            terminal=False,
        )
        return self._resume_sealed_attempt_disposition(run)

    def _resume_sealed_attempt_disposition(
        self,
        run: CodingLaneStateMachine,
    ) -> dict[str, Any]:
        """Finalize a sealed approval, then deterministically open its linked attempt."""

        if not run.attempt_history:
            raise CodingOrchestratorError("repair_attempt_seal_missing")
        seal = run.attempt_history[-1]
        if (
            seal.get("attempt_id") != run.attempt_id
            or seal.get("attempt_number") != run.attempt_number
        ):
            raise CodingOrchestratorError("repair_attempt_seal_resume_binding_invalid")
        disposition = self._finalize_sealed_attempt_approval(run, seal)
        next_attempt_id = str(seal.get("next_attempt_id") or "")
        if not next_attempt_id:
            return self._persist(
                run,
                "terminal failed attempt approval invalidated after durable seal",
            )

        attempt_state = seal.get("attempt_state")
        if not isinstance(attempt_state, Mapping):
            raise CodingOrchestratorError("repair_attempt_state_missing")
        planner_output = next(
            (
                item
                for item in _mapping_list(attempt_state.get("runtime_outputs"))
                if item.get("lane_id") == "planner"
            ),
            None,
        )
        planner_payload = (
            planner_output.get("payload")
            if isinstance(planner_output, Mapping)
            else None
        )
        if not isinstance(planner_payload, Mapping):
            raise CodingOrchestratorError("repair_planner_output_invalid")
        report = canonical_context_broker_for_task(run.task_id)
        if (
            not isinstance(report, Mapping)
            or report.get("canonical") is not True
            or not str(report.get("canonical_report_hash") or "")
        ):
            raise CodingOrchestratorError("repair_canonical_context_missing")

        failed_attempt_id = run.attempt_id
        sealed_attempt_state = seal.get("attempt_state")
        sealed_proposal = (
            sealed_attempt_state.get("target_plugin_proposal")
            if isinstance(sealed_attempt_state, Mapping)
            else None
        )
        sealed_failure = seal.get("failure")
        if not isinstance(sealed_failure, Mapping):
            raise CodingOrchestratorError("repair_failure_evidence_missing")
        repair_diagnostic = seal.get("repair_diagnostic")
        if not _valid_repair_diagnostic(
            repair_diagnostic,
            task_id=run.task_id,
            run_id=run.run_id,
            attempt_id=failed_attempt_id,
            failure=sealed_failure,
            current_state_manifest=seal.get("current_state_manifest"),
            current_state_manifest_sha256=str(
                seal.get("current_state_manifest_sha256") or ""
            ),
        ):
            raise CodingOrchestratorError("repair_diagnostic_invalid")
        repair_request_body = {
            "schema_version": REPAIR_REQUEST_SCHEMA,
            "task_id": run.task_id,
            "run_id": run.run_id,
            "attempt_id": next_attempt_id,
            "parent_attempt_id": failed_attempt_id,
            "attempt_number": run.attempt_number + 1,
            "max_attempts": MAX_CODING_ATTEMPTS,
            "failure_class": sealed_failure.get("failure_class"),
            "source_lane": sealed_failure.get("source_lane"),
            "exact_feedback": seal["failure"]["exact_feedback"],
            "feedback_sha256": seal["failure"]["feedback_sha256"],
            "current_state_manifest": seal["current_state_manifest"],
            "current_state_manifest_sha256": seal[
                "current_state_manifest_sha256"
            ],
            "repair_diagnostic": repair_diagnostic,
            "repair_diagnostic_sha256": repair_diagnostic[
                "diagnostic_sha256"
            ],
            "parent_attempt_seal_sha256": seal["seal_sha256"],
            "prior_approval_id": seal["approval_binding"]["approval_id"],
            "prior_approved_diff_sha256": seal["approval_binding"][
                "approved_diff_sha256"
            ],
            "prior_approval_disposition": disposition,
            "prior_approval_disposition_sha256": disposition[
                "disposition_sha256"
            ],
            "original_task": (
                str(sealed_proposal.get("original_task") or "")
                if isinstance(sealed_proposal, Mapping)
                else ""
            ),
            "requirements": {
                "fresh_proposal_required": True,
                "fresh_approval_required": True,
                "current_applied_state_is_baseline": True,
                "new_evidence_or_changed_strategy_required": True,
            },
        }
        repair_request = dict(repair_request_body)
        repair_request["repair_input_sha256"] = _sha256_json(repair_request_body)

        run.attempt_id = next_attempt_id
        run.parent_attempt_id = failed_attempt_id
        run.attempt_number += 1
        run.lane_states = {lane_id: "pending" for lane_id in LANE_SEQUENCE}
        run.lane_states["context-broker"] = "running"
        run.lane_reasons = {
            "context-broker": "canonical_context_reissued_for_repair",
            "planner": "fresh_attempt_plan_required",
        }
        run.causal_events = []
        run.runtime_outputs = []
        run.runtime_acknowledgements = []
        run.runtime_consumptions = []
        run.required_output_ids = []
        run.participant_records = []
        run.immutable_artifact = None
        run.target_plugin_proposal = None
        run.authority_finalization = None
        run.recovery_lineage = []
        run.model_invocations = []
        run.repair_request = repair_request
        run.record_event(
            event_type="repair_attempt_created",
            lane_id="repair",
            status_after="pending",
            detail={
                "parent_attempt_id": failed_attempt_id,
                "parent_attempt_seal_sha256": seal["seal_sha256"],
                "failure_class": sealed_failure.get("failure_class"),
                "repair_input_sha256": repair_request["repair_input_sha256"],
                "attempt_number": run.attempt_number,
                "max_attempts": MAX_CODING_ATTEMPTS,
            },
        )
        context_invocation_id = f"context-broker-repair-{uuid4().hex}"
        context_output = self._enforce_runtime_contract_output(
            run,
            lane_id="context-broker",
            producer_invocation_id=context_invocation_id,
            payload={
                "context_hash": str(report["canonical_report_hash"]),
                "verdict": str(report.get("verdict") or "UNKNOWN"),
            },
        )
        refresh_invocation_id = f"context-broker-repair-refresh-{uuid4().hex}"
        self._consume_output(
            run,
            output_id=str(context_output["output_id"]),
            consumer_invocation_id=refresh_invocation_id,
            payload={
                "consumer": "context-broker",
                "context_hash": str(report["canonical_report_hash"]),
            },
        )
        return self._persist(
            run,
            "failed attempt sealed; fresh evidence-guided repair attempt awaiting an exact plan",
        )

    def _finalize_sealed_attempt_approval(
        self,
        run: CodingLaneStateMachine,
        seal: Mapping[str, Any],
    ) -> dict[str, Any]:
        seal_sha256 = str(seal.get("seal_sha256") or "")
        existing = next(
            (
                item
                for item in run.attempt_dispositions
                if item.get("attempt_seal_sha256") == seal_sha256
            ),
            None,
        )
        if isinstance(existing, Mapping):
            body = dict(existing)
            recorded = str(body.pop("disposition_sha256", ""))
            if (
                existing.get("schema_version") != REPAIR_APPROVAL_DISPOSITION_SCHEMA
                or existing.get("authority_state") != "invalidated"
                or not recorded
                or _sha256_json(body) != recorded
            ):
                raise CodingOrchestratorError(
                    "repair_approval_disposition_invalid"
                )
            return dict(existing)

        attempt_state = seal.get("attempt_state")
        participant_records = (
            _mapping_list(attempt_state.get("participant_records"))
            if isinstance(attempt_state, Mapping)
            else []
        )
        failure = seal.get("failure")
        failure_class = (
            str(failure.get("failure_class") or "")
            if isinstance(failure, Mapping)
            else ""
        )
        result = self._attempt_failure_finalizer(
            run.task_id,
            reason_code=f"repair_attempt_superseded:{failure_class}",
            participant_records=participant_records,
        )
        task = result.get("task") if isinstance(result, Mapping) else None
        snapshot = task.get("ast_snapshot") if isinstance(task, Mapping) else None
        approval = (
            snapshot.get("campaign_2_approval")
            if isinstance(snapshot, Mapping)
            else None
        )
        binding = seal.get("approval_binding")
        if (
            not isinstance(approval, Mapping)
            or not isinstance(binding, Mapping)
            or approval.get("approval_id") != binding.get("approval_id")
            or int(approval.get("generation") or 0)
            != int(binding.get("generation") or 0)
            or approval.get("state") != "invalidated"
        ):
            raise CodingOrchestratorError("repair_approval_finalization_failed")
        body = {
            "schema_version": REPAIR_APPROVAL_DISPOSITION_SCHEMA,
            "task_id": run.task_id,
            "run_id": run.run_id,
            "attempt_id": seal.get("attempt_id"),
            "attempt_seal_sha256": seal_sha256,
            "approval_id": binding.get("approval_id"),
            "generation": binding.get("generation"),
            "authority_state": "invalidated",
            "failure_reason": approval.get("failure_reason"),
        }
        disposition = dict(body)
        disposition["disposition_sha256"] = _sha256_json(body)
        run.attempt_dispositions.append(disposition)
        run.record_event(
            event_type="repair_approval_invalidated",
            lane_id=str(failure.get("source_lane") or "repair")
            if isinstance(failure, Mapping)
            else "repair",
            detail={
                "attempt_seal_sha256": seal_sha256,
                "approval_id": binding.get("approval_id"),
                "disposition_sha256": disposition["disposition_sha256"],
            },
        )
        self._persist(
            run,
            "sealed failed-attempt approval invalidated before repair attempt opened",
        )
        return disposition

    def _seal_failed_attempt(
        self,
        run: CodingLaneStateMachine,
        *,
        failure_class: str,
        source_lane: str,
        exact_feedback: Mapping[str, Any],
        next_attempt_id: str | None,
        terminal: bool,
    ) -> dict[str, Any]:
        if failure_class not in {"reviewer_rejection", "verifier_rejection"}:
            raise CodingOrchestratorError("repair_failure_class_invalid")
        if source_lane not in {"reviewer", "verifier"}:
            raise CodingOrchestratorError("repair_failure_source_invalid")
        if len(run.attempt_history) != run.attempt_number - 1:
            raise CodingOrchestratorError("repair_attempt_history_not_appendable")
        if not isinstance(run.immutable_artifact, Mapping):
            raise CodingOrchestratorError("repair_current_artifact_missing")

        if terminal:
            if run.lane_states["repair"] == "pending":
                run.transition("repair", "blocked", reason="repair_attempt_limit_exhausted")
            elif run.lane_states["repair"] == "running":
                run.transition("repair", "failed", reason="repair_attempt_limit_exhausted")
        elif run.lane_states["repair"] == "pending":
            run.transition("repair", "running", reason="evidence_guided_repair_queued")
        elif run.lane_states["repair"] == "running":
            run.transition("repair", "failed", reason="evidence_guided_repair_attempt_failed")
        else:
            raise CodingOrchestratorError("repair_lane_failure_state_invalid")

        feedback = json.loads(
            json.dumps(dict(exact_feedback), sort_keys=True, default=str)
        )
        feedback_sha256 = _sha256_json(feedback)
        current_state_manifest = _current_applied_state_manifest(run.immutable_artifact)
        current_state_manifest_sha256 = _sha256_json(current_state_manifest)
        classification_input = _structured_repair_diagnostic_input(
            failure_class=failure_class,
            source_lane=source_lane,
            exact_feedback=feedback,
        )
        classification_details = _repair_classification_details(
            classification_input,
            feedback_sha256=feedback_sha256,
            current_state_manifest_sha256=current_state_manifest_sha256,
        )
        classification = classify_repair_failure(
            diagnostic_code=classification_input["diagnostic_code"],
            stage=classification_input["stage"],
            reason=classification_input["reason"],
            details=classification_details,
        ).to_dict()
        debugger_trace: dict[str, Any] | None = None
        if classification.get("failure_kind") in {
            "runtime_error",
            "test_environment_error",
        }:
            debugger_trace = _run_deterministic_repair_debugger(
                task_id=run.task_id,
                run_id=run.run_id,
                attempt_id=run.attempt_id,
                classification_input=classification_input,
                exact_failure_output=feedback,
                feedback_sha256=feedback_sha256,
                current_state_manifest=current_state_manifest,
                current_state_manifest_sha256=current_state_manifest_sha256,
            )
            run.record_event(
                event_type="deterministic_debugger_executed",
                lane_id=source_lane,
                detail={
                    "trace_sha256": debugger_trace["trace_sha256"],
                    "argv_sha256": debugger_trace["argv_sha256"],
                    "input_sha256": debugger_trace["input_sha256"],
                    "stdout_sha256": debugger_trace["stdout_sha256"],
                    "stderr_sha256": debugger_trace["stderr_sha256"],
                    "findings_sha256": debugger_trace["findings_sha256"],
                    "exit_status": debugger_trace["exit_status"],
                    "timed_out": debugger_trace["timed_out"],
                    "duration_ms": debugger_trace["duration_ms"],
                    "model_debugger_invoked": False,
                },
            )
        diagnostic_body = {
            "schema_version": REPAIR_DIAGNOSTIC_SCHEMA,
            "hook": "deterministic_failure_classifier",
            "model_debugger_invoked": False,
            "task_id": run.task_id,
            "run_id": run.run_id,
            "attempt_id": run.attempt_id,
            "failure_class": failure_class,
            "source_lane": source_lane,
            "classification_input": classification_input,
            "classification": classification,
            "deterministic_debugger_invoked": debugger_trace is not None,
            "debugger_trace": debugger_trace,
            "exact_failure_output": feedback,
            "exact_failure_output_sha256": feedback_sha256,
            "current_state_manifest": current_state_manifest,
            "current_state_manifest_sha256": current_state_manifest_sha256,
        }
        repair_diagnostic = dict(diagnostic_body)
        repair_diagnostic["diagnostic_sha256"] = _sha256_json(diagnostic_body)
        proposal = run.target_plugin_proposal
        approval_binding = {
            "approval_id": str(run.immutable_artifact.get("approval_id") or ""),
            "generation": int(run.immutable_artifact.get("generation") or 0),
            "approved_diff_sha256": str(
                run.immutable_artifact.get("approved_diff_sha256") or ""
            ),
            "artifact_sha256": str(run.immutable_artifact.get("artifact_sha256") or ""),
            "proposal_binding_sha256": (
                str(proposal.get("proposal_binding_sha256") or "")
                if isinstance(proposal, Mapping)
                else ""
            ),
        }
        if not approval_binding["approval_id"] or approval_binding["approval_id"] in {
            str(item.get("approval_binding", {}).get("approval_id") or "")
            for item in run.attempt_history
            if isinstance(item.get("approval_binding"), Mapping)
        }:
            raise CodingOrchestratorError("repair_approval_reuse_detected")
        failure = {
            "failure_class": failure_class,
            "source_lane": source_lane,
            "exact_feedback": feedback,
            "feedback_sha256": feedback_sha256,
        }
        run.record_event(
            event_type="deterministic_repair_diagnostic_recorded",
            lane_id=source_lane,
            detail={
                "diagnostic_sha256": repair_diagnostic["diagnostic_sha256"],
                "failure_kind": classification["failure_kind"],
                "failure_class": classification["failure_class"],
                "feedback_sha256": feedback_sha256,
                "current_state_manifest_sha256": current_state_manifest_sha256,
                "deterministic_debugger_invoked": debugger_trace is not None,
                "debugger_trace_sha256": (
                    debugger_trace["trace_sha256"] if debugger_trace else None
                ),
                "model_debugger_invoked": False,
            },
        )
        run.record_event(
            event_type="repair_attempt_seal_requested",
            lane_id=source_lane,
            detail={
                "failure_class": failure_class,
                "feedback_sha256": feedback_sha256,
                "current_state_manifest_sha256": current_state_manifest_sha256,
                "next_attempt_id": next_attempt_id,
                "terminal": terminal,
            },
        )
        attempt_state = {
            "lane_states": dict(run.lane_states),
            "lane_reasons": dict(run.lane_reasons),
            "causal_events": json.loads(
                json.dumps(run.causal_events, sort_keys=True, default=str)
            ),
            "runtime_outputs": json.loads(
                json.dumps(run.runtime_outputs, sort_keys=True, default=str)
            ),
            "runtime_acknowledgements": json.loads(
                json.dumps(run.runtime_acknowledgements, sort_keys=True, default=str)
            ),
            "runtime_consumptions": json.loads(
                json.dumps(run.runtime_consumptions, sort_keys=True, default=str)
            ),
            "required_output_ids": list(run.required_output_ids),
            "participant_records": json.loads(
                json.dumps(run.participant_records, sort_keys=True, default=str)
            ),
            "immutable_artifact": json.loads(
                json.dumps(dict(run.immutable_artifact), sort_keys=True, default=str)
            ),
            "target_plugin_proposal": (
                json.loads(json.dumps(dict(proposal), sort_keys=True, default=str))
                if isinstance(proposal, Mapping)
                else None
            ),
            "cartographer_selection_consumption": (
                json.loads(
                    json.dumps(
                        dict(run.cartographer_selection_consumption),
                        sort_keys=True,
                        default=str,
                    )
                )
                if isinstance(run.cartographer_selection_consumption, Mapping)
                else None
            ),
            "cartographer_transfer": (
                json.loads(
                    json.dumps(dict(run.cartographer_transfer), sort_keys=True, default=str)
                )
                if isinstance(run.cartographer_transfer, Mapping)
                else None
            ),
            "cartographer_finalization": (
                json.loads(
                    json.dumps(
                        dict(run.cartographer_finalization),
                        sort_keys=True,
                        default=str,
                    )
                )
                if isinstance(run.cartographer_finalization, Mapping)
                else None
            ),
            "recovery_lineage": json.loads(
                json.dumps(run.recovery_lineage, sort_keys=True, default=str)
            ),
            "model_invocations": json.loads(
                json.dumps(run.model_invocations, sort_keys=True, default=str)
            ),
        }
        seal_body = {
            "schema_version": REPAIR_ATTEMPT_SEAL_SCHEMA,
            "task_id": run.task_id,
            "run_id": run.run_id,
            "attempt_id": run.attempt_id,
            "parent_attempt_id": run.parent_attempt_id,
            "attempt_number": run.attempt_number,
            "next_attempt_id": next_attempt_id,
            "outcome": f"{failure_class}_terminal" if terminal else failure_class,
            "failure": failure,
            "repair_diagnostic": repair_diagnostic,
            "current_state_manifest": current_state_manifest,
            "current_state_manifest_sha256": current_state_manifest_sha256,
            "approval_binding": approval_binding,
            "repair_strategy_signature": (
                str(proposal.get("repair_strategy_signature") or "") or None
                if isinstance(proposal, Mapping)
                else None
            ),
            "attempt_state": attempt_state,
            "sealed_at": _utc_now(),
        }
        seal = dict(seal_body)
        seal["seal_sha256"] = _sha256_json(seal_body)
        run.attempt_history.append(seal)
        self._persist(run, "failed coding attempt durably sealed before disposition")
        return seal

    def _mark_repair_exhausted(
        self,
        run: CodingLaneStateMachine,
        *,
        reason_code: str,
        failure_class: str,
        source_lane: str,
        exact_feedback: Mapping[str, Any],
    ) -> None:
        seal = self._seal_failed_attempt(
            run,
            failure_class=failure_class,
            source_lane=source_lane,
            exact_feedback=exact_feedback,
            next_attempt_id=None,
            terminal=True,
        )
        self._finalize_sealed_attempt_approval(run, seal)
        run.repair_request = None
        run.record_event(
            event_type="repair_attempt_limit_exhausted",
            lane_id="repair",
            status_after=run.lane_states["repair"],
            detail={
                "reason_code": reason_code,
                "attempt_number": run.attempt_number,
                "max_attempts": MAX_CODING_ATTEMPTS,
                "terminal_attempt_seal_sha256": seal["seal_sha256"],
            },
        )

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
            attempt_number=int(state.get("attempt_number") or 1),
            attempt_history=_mapping_list(state.get("attempt_history")),
            attempt_dispositions=_mapping_list(state.get("attempt_dispositions")),
            repair_request=(
                dict(state["repair_request"])
                if isinstance(state.get("repair_request"), Mapping)
                else None
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
        history_count_valid = len(run.attempt_history) == run.attempt_number - 1 or (
            len(run.attempt_history) == run.attempt_number
            and run.lane_states["repair"] in {"running", "failed", "blocked"}
            and run.attempt_history[-1].get("attempt_id") == run.attempt_id
        )
        if (
            run.attempt_number < 1
            or run.attempt_number > MAX_CODING_ATTEMPTS
            or not history_count_valid
            or len(run.attempt_dispositions) > len(run.attempt_history)
        ):
            raise CodingOrchestratorError("coding_orchestrator_attempt_state_invalid")
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
            or proposal.get("attempt_id") != run.attempt_id
            or proposal.get("runtime_output_id") != runtime_output_id
            or proposal.get("selected_prompt_id") != selected_prompt_id
        ):
            raise CodingOrchestratorError("target_plugin_proposal_binding_mismatch")
        if isinstance(run.repair_request, Mapping):
            if (
                proposal.get("parent_attempt_id") != run.parent_attempt_id
                or proposal.get("attempt_number") != run.attempt_number
                or proposal.get("repair_context") != run.repair_request
                or proposal.get("repair_input_sha256")
                != run.repair_request.get("repair_input_sha256")
                or not str(proposal.get("repair_prompt_sha256") or "")
                or not str(proposal.get("repair_strategy_signature") or "")
            ):
                raise CodingOrchestratorError(
                    "target_plugin_repair_context_binding_invalid"
                )
            _validate_repair_target_baseline(
                repair_request=run.repair_request,
                target_plugin_identity=(
                    proposal.get("target_plugin_identity")
                    if isinstance(proposal.get("target_plugin_identity"), Mapping)
                    else {}
                ),
            )
        elif any(
            key in proposal
            for key in (
                "repair_context",
                "repair_input_sha256",
                "repair_prompt_sha256",
                "repair_strategy_signature",
            )
        ):
            raise CodingOrchestratorError("unexpected_target_plugin_repair_context")
        if proposal.get("status") != "ready_for_approval_preview":
            raise CodingOrchestratorError("target_plugin_proposal_not_actionable")
        if proposal.get("source_head") != current_head():
            raise CodingOrchestratorError("target_plugin_proposal_source_head_mismatch")
        plugin_identity = proposal.get("target_plugin_identity")
        if not isinstance(plugin_identity, Mapping) or (
            plugin_identity.get("source_head") != proposal.get("source_head")
            or plugin_identity.get("selected_prompt_id") != selected_prompt_id
            or expected_target_plugin_id(selected_prompt_id)
            != plugin_identity.get("plugin_id")
            or str(
                plugin_identity.get("target_source_head")
                or plugin_identity.get("source_head")
                or ""
            )
            != proposal.get("target_source_head")
            or proposal.get("target_workspace_state_sha256")
            != plugin_identity.get("target_workspace_state_sha256")
            or list(proposal.get("target_workspace_state_paths") or [])
            != list(plugin_identity.get("target_workspace_state_paths") or [])
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
        semantic_review_binding = proposal.get("semantic_review_binding")
        latest_planner_output = CodingOrchestrator._latest_output(run, "planner")
        latest_planner_payload = latest_planner_output.get("payload")
        bound_server_plan = (
            semantic_review_binding.get("server_plan")
            if isinstance(semantic_review_binding, Mapping)
            else None
        )
        if (
            proposal.get("semantic_review_binding_sha256")
            != (
                semantic_review_binding.get("semantic_review_binding_sha256")
                if isinstance(semantic_review_binding, Mapping)
                else None
            )
            or not isinstance(latest_planner_payload, Mapping)
            or not isinstance(bound_server_plan, Mapping)
            or latest_planner_payload.get("task_spec") != bound_server_plan
            or latest_planner_payload.get("plan_id")
            != bound_server_plan.get("plan_id")
            or not _valid_semantic_review_binding(
                semantic_review_binding,
                task_id=run.task_id,
                run_id=run.run_id,
                attempt_id=run.attempt_id,
                proposed_diff=exact_diff,
                changed_files=changed_files,
                adapter_architect_plan_required=(
                    isinstance(plugin_identity, Mapping)
                    and plugin_identity.get("plugin_id")
                    == GENERIC_WORKSPACE_PLUGIN_ID
                ),
                repair_request=(
                    run.repair_request
                    if isinstance(run.repair_request, Mapping)
                    else None
                ),
            )
        ):
            raise CodingOrchestratorError(
                "target_plugin_semantic_review_binding_invalid"
            )
        producer_invocation_id = str(output.get("producer_invocation_id") or "")
        if producer_invocation_id != proposal.get("producer_model_invocation_id"):
            raise CodingOrchestratorError("target_plugin_proposal_producer_mismatch")
        planner_acknowledgement = next(
            (
                item
                for item in run.runtime_acknowledgements
                if item.get("acknowledgement_id")
                == proposal.get("planner_consumer_acknowledgement_id")
            ),
            None,
        )
        planner_consumption = next(
            (
                item
                for item in run.runtime_consumptions
                if item.get("consumption_id")
                == proposal.get("planner_consumption_id")
            ),
            None,
        )
        if (
            latest_planner_output.get("output_id")
            != proposal.get("planner_runtime_output_id")
            or latest_planner_output.get("artifact_hash")
            != proposal.get("planner_runtime_artifact_sha256")
            or not isinstance(planner_acknowledgement, Mapping)
            or planner_acknowledgement.get("output_id")
            != latest_planner_output.get("output_id")
            or planner_acknowledgement.get("consumer_invocation_id")
            != producer_invocation_id
            or not isinstance(planner_consumption, Mapping)
            or planner_consumption.get("output_id")
            != latest_planner_output.get("output_id")
            or planner_consumption.get("acknowledgement_id")
            != planner_acknowledgement.get("acknowledgement_id")
            or planner_consumption.get("consumer_invocation_id")
            != producer_invocation_id
        ):
            raise CodingOrchestratorError(
                "target_plugin_proposal_planner_consumption_invalid"
            )
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
            or participant.get("provider")
            != proposal.get("producer_model_provider")
            or participant.get("model") != proposal.get("producer_model_name")
            or not isinstance(model_output_provenance, Mapping)
            or not isinstance(adapter_provenance, Mapping)
            or not target_adapter_producer_identity_valid(adapter_provenance)
            or adapter_provenance.get("plugin_id")
            != plugin_identity.get("plugin_id")
            or adapter_provenance.get("selected_prompt_id")
            != selected_prompt_id
            or proposal.get("producer_model_alias")
            != adapter_provenance.get("selected_model_alias")
            or proposal.get("producer_model_provider")
            != adapter_provenance.get("provider")
            or proposal.get("producer_model_name")
            != adapter_provenance.get("model")
            or proposal.get("producer_adapter_call_index")
            != adapter_provenance.get("producer_call_index")
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
        and target_adapter_producer_identity_valid(adapter)
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


def _model_task_with_repair_context(
    run: CodingLaneStateMachine,
    task: str,
) -> tuple[str, str | None]:
    repair_request = run.repair_request
    if not isinstance(repair_request, Mapping):
        return task, None
    if (
        repair_request.get("schema_version") != REPAIR_REQUEST_SCHEMA
        or repair_request.get("task_id") != run.task_id
        or repair_request.get("run_id") != run.run_id
        or repair_request.get("attempt_id") != run.attempt_id
        or repair_request.get("parent_attempt_id") != run.parent_attempt_id
        or repair_request.get("attempt_number") != run.attempt_number
        or not run.attempt_history
        or repair_request.get("parent_attempt_seal_sha256")
        != run.attempt_history[-1].get("seal_sha256")
    ):
        raise CodingOrchestratorError("repair_request_binding_invalid")
    request_body = dict(repair_request)
    recorded_repair_input_sha256 = str(
        request_body.pop("repair_input_sha256", "")
    )
    if (
        not recorded_repair_input_sha256
        or _sha256_json(request_body) != recorded_repair_input_sha256
    ):
        raise CodingOrchestratorError("repair_request_hash_mismatch")
    bound_original_task = str(repair_request.get("original_task") or "").strip()
    if bound_original_task and task.strip() != bound_original_task:
        raise CodingOrchestratorError("repair_original_task_mismatch")
    original_task = bound_original_task or task.strip()
    return render_evidence_guided_repair_model_task(
        original_task,
        repair_request,
    )


def _repair_strategy_signature(
    *,
    repair_request: Mapping[str, Any],
    approved_diff: str,
    participant: Mapping[str, Any],
    selected_prompt_id: str,
    selected_context_id: str,
) -> str:
    return _sha256_json(
        {
            "feedback_sha256": repair_request.get("feedback_sha256"),
            "current_state_manifest_sha256": repair_request.get(
                "current_state_manifest_sha256"
            ),
            "original_task_sha256": hashlib.sha256(
                str(repair_request.get("original_task") or "").encode("utf-8")
            ).hexdigest(),
            "approved_diff_sha256": hashlib.sha256(
                approved_diff.encode("utf-8")
            ).hexdigest(),
            "provider": participant.get("provider"),
            "model": participant.get("model"),
            "selected_prompt_id": selected_prompt_id,
            "selected_context_id": selected_context_id,
        }
    )


def _current_applied_state_manifest(artifact: Mapping[str, Any]) -> dict[str, Any]:
    changed_files = artifact.get("changed_files")
    workspace_root_text = str(artifact.get("workspace_root") or "").strip()
    workspace_root = Path(workspace_root_text).resolve()
    if not workspace_root_text or not workspace_root.is_dir():
        raise CodingOrchestratorError("repair_current_state_workspace_invalid")
    normalized_files: list[dict[str, Any]] = []
    for item in (changed_files if isinstance(changed_files, list) else []):
        if not isinstance(item, Mapping):
            continue
        relative = str(item.get("path") or "").replace("\\", "/").strip()
        candidate = workspace_root / relative
        if (
            not relative
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or candidate.is_symlink()
        ):
            raise CodingOrchestratorError("repair_current_state_path_invalid")
        resolved = candidate.resolve()
        try:
            resolved.relative_to(workspace_root)
        except ValueError as error:
            raise CodingOrchestratorError("repair_current_state_path_invalid") from error
        current_exists = resolved.is_file()
        current_sha256 = (
            hashlib.sha256(resolved.read_bytes()).hexdigest()
            if current_exists
            else None
        )
        normalized_files.append(
            {
                "path": relative,
                "sha256_before": item.get("sha256_before"),
                "sha256_after": item.get("sha256_after"),
                "expected_sha256_after": item.get("sha256_after"),
                "current_sha256": current_sha256,
                "current_exists": current_exists,
                "missing_before_apply": bool(item.get("missing_before_apply")),
            }
        )
    normalized_files.sort(key=lambda item: item["path"])
    target_identity = artifact.get("target_plugin_identity")
    stable_target_identity = _stable_target_plugin_identity(target_identity)
    target_source_head = str(
        target_identity.get("target_source_head")
        or target_identity.get("source_head")
        or ""
    ) if isinstance(target_identity, Mapping) else ""
    target_workspace_state_sha256: str | None = None
    target_workspace_state_paths: list[str] = []
    if stable_target_identity.get("plugin_id") == "generic-workspace":
        try:
            actual_target_head = subprocess.check_output(
                ["git", "-C", str(workspace_root), "rev-parse", "HEAD"],
                text=True,
                timeout=15,
            ).strip()
            from source_proxy.benchmarks.campaign_3_5_fixture_authority import (
                Campaign35FixtureAuthorityError,
                campaign_3_5_workspace_state_commitment,
            )

            state_sha256, state_paths = campaign_3_5_workspace_state_commitment(
                workspace_root,
                writable_paths=tuple(
                    str(value)
                    for value in target_identity.get("allowed_actions", ())
                ),
            )
        except (
            OSError,
            subprocess.SubprocessError,
            Campaign35FixtureAuthorityError,
        ) as error:
            raise CodingOrchestratorError(
                "repair_current_workspace_state_invalid"
            ) from error
        if actual_target_head != target_source_head:
            raise CodingOrchestratorError(
                "repair_current_target_source_head_mismatch"
            )
        target_workspace_state_sha256 = str(state_sha256)
        target_workspace_state_paths = [str(value) for value in state_paths]
    manifest = {
        "schema_version": "coding.current-applied-state-manifest/v1",
        "live_state_captured": True,
        "artifact_sha256": str(artifact.get("artifact_sha256") or ""),
        "approval_id": str(artifact.get("approval_id") or ""),
        "generation": int(artifact.get("generation") or 0),
        "approved_diff_sha256": str(artifact.get("approved_diff_sha256") or ""),
        "result_sha256": str(artifact.get("result_sha256") or ""),
        "workspace_root": str(workspace_root),
        "changed_files": normalized_files,
        "stable_target_plugin_identity": stable_target_identity,
        "target_source_head": target_source_head,
        "target_workspace_state_sha256": target_workspace_state_sha256,
        "target_workspace_state_paths": target_workspace_state_paths,
    }
    if not manifest["artifact_sha256"] or not manifest["approved_diff_sha256"]:
        raise CodingOrchestratorError("repair_current_state_manifest_invalid")
    return manifest


def _stable_target_plugin_identity(identity: object) -> dict[str, Any]:
    if not isinstance(identity, Mapping):
        return {}
    mutable = {
        "target_workspace_state_sha256",
        "target_workspace_state_paths",
        "approval_id",
        "approval_generation",
        "evidence_pointer",
        "failure_reason",
        "acknowledgement_status",
    }
    return {
        str(key): json.loads(json.dumps(value, sort_keys=True, default=str))
        for key, value in identity.items()
        if str(key) not in mutable
    }


def _structured_repair_diagnostic_input(
    *,
    failure_class: str,
    source_lane: str,
    exact_feedback: Mapping[str, Any],
) -> dict[str, Any]:
    """Select a structured failure signal without inferring from prose output."""

    def selected(
        code: str,
        stage: str,
        source: str,
        evidence: Mapping[str, Any],
    ) -> dict[str, Any]:
        normalized_code = str(code or failure_class).strip() or failure_class
        normalized_stage = str(stage or source_lane).strip().lower() or source_lane
        return {
            "diagnostic_code": normalized_code,
            "stage": normalized_stage,
            "reason": normalized_code,
            "input_source": source,
            "structured_evidence": json.loads(
                json.dumps(dict(evidence), sort_keys=True, default=str)
            ),
        }

    def structured_code(record: Mapping[str, Any]) -> str:
        for key in (
            "diagnostic_code",
            "reason_code",
            "error_code",
            "failure_kind",
            "failure_class",
        ):
            value = record.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def structured_stage(record: Mapping[str, Any], default: str) -> str:
        for key in ("diagnostic_stage", "failure_stage", "stage"):
            value = record.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip().lower()
        category = str(
            record.get("failure_category")
            or record.get("category")
            or record.get("failure_kind")
            or record.get("failure_class")
            or ""
        ).strip().lower()
        if any(
            token in category
            for token in ("environment", "dependency", "service", "tool")
        ):
            return "environment"
        if "runtime" in category:
            return "runtime"
        if any(token in category for token in ("test", "assertion", "fixture")):
            return "tests"
        return default

    direct_code = structured_code(exact_feedback)
    if direct_code:
        return selected(
            direct_code,
            structured_stage(exact_feedback, source_lane),
            "exact_feedback",
            exact_feedback,
        )

    post_apply = exact_feedback.get("post_apply_verification")
    if isinstance(post_apply, Mapping):
        post_code = structured_code(post_apply)
        generic_post_codes = {
            "post_apply_verification_failed",
            "verification_failed",
            "server_verification_not_verified",
        }
        if post_code and post_code.lower() not in generic_post_codes:
            return selected(
                post_code,
                structured_stage(post_apply, source_lane),
                "post_apply_verification",
                post_apply,
            )
        checks = post_apply.get("checks")
        if isinstance(checks, list):
            for index, check in enumerate(checks):
                if not isinstance(check, Mapping) or str(
                    check.get("status") or ""
                ).strip().lower() != "failed":
                    continue
                check_code = structured_code(check)
                check_stage = structured_stage(check, "tests")
                if not check_code:
                    exit_code = check.get("exit_code")
                    check_id = str(
                        check.get("id") or check.get("command_text") or "unknown"
                    ).strip()
                    if isinstance(exit_code, int) and not isinstance(exit_code, bool) and exit_code == 124:
                        check_code = f"test_timeout:{check_id}"
                        check_stage = "environment"
                    else:
                        check_code = f"visible_tests_failed:{check_id}"
                return selected(
                    check_code,
                    check_stage,
                    f"post_apply_verification.checks[{index}]",
                    check,
                )
        browser = post_apply.get("browser_evidence")
        if isinstance(browser, Mapping) and any(
            str(browser.get(key) or "").strip().lower() == "failed"
            for key in (
                "status",
                "browser_verification_status",
                "storefront_runtime_status",
            )
        ):
            return selected(
                structured_code(browser) or "browser_runtime_failed",
                structured_stage(browser, "runtime"),
                "post_apply_verification.browser_evidence",
                browser,
            )
        snapshot = post_apply.get("snapshot_verification")
        if isinstance(snapshot, Mapping):
            issue_key = next(
                (
                    str(key)
                    for key, value in snapshot.items()
                    if str(key).endswith("_issue")
                    and isinstance(value, str)
                    and value.strip()
                ),
                "",
            )
            if issue_key:
                return selected(
                    str(snapshot[issue_key]),
                    "tests",
                    f"post_apply_verification.snapshot_verification.{issue_key}",
                    {issue_key: snapshot[issue_key]},
                )
        if post_code:
            return selected(
                post_code,
                structured_stage(post_apply, source_lane),
                "post_apply_verification",
                post_apply,
            )

    participant_result = exact_feedback.get("participant_result")
    if isinstance(participant_result, Mapping):
        result_code = structured_code(participant_result)
        if result_code:
            return selected(
                result_code,
                structured_stage(participant_result, source_lane),
                "participant_result",
                participant_result,
            )
        findings = participant_result.get("findings")
        if isinstance(findings, list):
            finding = next(
                (
                    item.strip()
                    for item in findings
                    if isinstance(item, str)
                    and item.strip()
                    and not any(character.isspace() for character in item.strip())
                ),
                "",
            )
            if finding:
                return selected(
                    finding,
                    source_lane,
                    "participant_result.findings[0]",
                    {"finding": finding},
                )

    return selected(
        failure_class,
        source_lane,
        "orchestrator_failure_binding",
        {"failure_class": failure_class, "source_lane": source_lane},
    )


def _repair_classification_details(
    classification_input: Mapping[str, Any],
    *,
    feedback_sha256: str,
    current_state_manifest_sha256: str,
) -> dict[str, Any]:
    return {
        "feedback_sha256": feedback_sha256,
        "current_state_manifest_sha256": current_state_manifest_sha256,
        "classification_input_sha256": _sha256_json(classification_input),
        "input_source": classification_input.get("input_source"),
        "structured_evidence_sha256": _sha256_json(
            classification_input.get("structured_evidence")
        ),
    }


def _deterministic_debugger_input_payload(
    *,
    task_id: str,
    run_id: str,
    attempt_id: str,
    classification_input: Mapping[str, Any],
    exact_failure_output: Mapping[str, Any],
    feedback_sha256: str,
    current_state_manifest: Mapping[str, Any],
    current_state_manifest_sha256: str,
) -> tuple[Path, dict[str, Any]]:
    workspace_text = str(current_state_manifest.get("workspace_root") or "").strip()
    workspace = Path(workspace_text).resolve()
    changed_files = current_state_manifest.get("changed_files")
    if (
        not workspace_text
        or not workspace.is_dir()
        or not isinstance(changed_files, list)
        or len(changed_files) > MAX_REPAIR_DEBUGGER_FILES
    ):
        raise CodingOrchestratorError("repair_debugger_input_invalid")
    files: list[dict[str, Any]] = []
    for item in changed_files:
        if not isinstance(item, Mapping):
            raise CodingOrchestratorError("repair_debugger_input_invalid")
        relative = str(item.get("path") or "").replace("\\", "/").strip()
        candidate = workspace / relative
        if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise CodingOrchestratorError("repair_debugger_input_invalid")
        resolved = candidate.resolve()
        try:
            resolved.relative_to(workspace)
        except ValueError as error:
            raise CodingOrchestratorError("repair_debugger_input_invalid") from error
        files.append(
            {
                "path": relative,
                "absolute_path": str(resolved),
                "expected_exists": item.get("current_exists") is True,
                "expected_sha256": item.get("current_sha256"),
            }
        )
    return workspace, {
        "schema_version": "coding.deterministic-debugger-input/v1",
        "task_id": task_id,
        "run_id": run_id,
        "attempt_id": attempt_id,
        "classification_input": json.loads(
            json.dumps(dict(classification_input), sort_keys=True, default=str)
        ),
        "exact_failure_output": json.loads(
            json.dumps(dict(exact_failure_output), sort_keys=True, default=str)
        ),
        "feedback_sha256": feedback_sha256,
        "current_state_manifest_sha256": current_state_manifest_sha256,
        "files": files,
    }


def _run_deterministic_repair_debugger(
    *,
    task_id: str,
    run_id: str,
    attempt_id: str,
    classification_input: Mapping[str, Any],
    exact_failure_output: Mapping[str, Any],
    feedback_sha256: str,
    current_state_manifest: Mapping[str, Any],
    current_state_manifest_sha256: str,
) -> dict[str, Any]:
    """Run a bounded non-model state/syntax probe for test and runtime failures."""

    workspace, input_payload = _deterministic_debugger_input_payload(
        task_id=task_id,
        run_id=run_id,
        attempt_id=attempt_id,
        classification_input=classification_input,
        exact_failure_output=exact_failure_output,
        feedback_sha256=feedback_sha256,
        current_state_manifest=current_state_manifest,
        current_state_manifest_sha256=current_state_manifest_sha256,
    )
    stdin_text = json.dumps(
        input_payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    argv = [sys.executable, "-I", "-c", _DETERMINISTIC_DEBUGGER_SCRIPT]
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            argv,
            cwd=workspace,
            input=stdin_text,
            text=True,
            capture_output=True,
            check=False,
            timeout=REPAIR_DEBUGGER_TIMEOUT_SECONDS,
            env={
                "PATH": os.environ.get("PATH", ""),
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONIOENCODING": "utf-8",
            },
        )
        exit_status = int(completed.returncode)
        stdout = str(completed.stdout or "")
        stderr = str(completed.stderr or "")
        timed_out = False
    except subprocess.TimeoutExpired as error:
        exit_status = 124
        stdout = _subprocess_output_text(error.stdout)
        stderr = _subprocess_output_text(error.stderr)
        timed_out = True
    except OSError as error:
        raise CodingOrchestratorError("repair_debugger_execution_failed") from error
    duration_ms = int((time.perf_counter() - started) * 1000)
    if len(stdout.encode("utf-8")) > 1_000_000 or len(stderr.encode("utf-8")) > 1_000_000:
        raise CodingOrchestratorError("repair_debugger_output_too_large")
    try:
        findings = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise CodingOrchestratorError("repair_debugger_output_invalid") from error
    if not isinstance(findings, Mapping):
        raise CodingOrchestratorError("repair_debugger_output_invalid")
    finding_files = findings.get("files")
    if not isinstance(finding_files, list) or any(
        not isinstance(item, Mapping) or item.get("state_matches") is not True
        for item in finding_files
    ):
        raise CodingOrchestratorError("repair_debugger_state_changed")
    trace_body = {
        "schema_version": REPAIR_DEBUGGER_TRACE_SCHEMA,
        "tool_kind": "deterministic_python_ast_state_probe",
        "deterministic_debugger_invoked": True,
        "model_debugger_invoked": False,
        "task_id": task_id,
        "run_id": run_id,
        "attempt_id": attempt_id,
        "argv": argv,
        "argv_sha256": _sha256_json(argv),
        "tool_script_sha256": _sha256_text(_DETERMINISTIC_DEBUGGER_SCRIPT),
        "cwd": str(workspace),
        "input_payload": input_payload,
        "input_sha256": _sha256_text(stdin_text),
        "feedback_sha256": feedback_sha256,
        "current_state_manifest_sha256": current_state_manifest_sha256,
        "exit_status": exit_status,
        "timed_out": timed_out,
        "duration_ms": duration_ms,
        "stdout": stdout,
        "stdout_sha256": _sha256_text(stdout),
        "stderr": stderr,
        "stderr_sha256": _sha256_text(stderr),
        "findings": dict(findings),
        "findings_sha256": _sha256_json(findings),
    }
    trace = dict(trace_body)
    trace["trace_sha256"] = _sha256_json(trace_body)
    return trace


def _subprocess_output_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _valid_deterministic_debugger_trace(
    trace: object,
    *,
    task_id: str,
    run_id: str,
    attempt_id: str,
    classification_input: Mapping[str, Any],
    exact_failure_output: Mapping[str, Any],
    feedback_sha256: str,
    current_state_manifest: Mapping[str, Any],
    current_state_manifest_sha256: str,
) -> bool:
    if not isinstance(trace, Mapping):
        return False
    try:
        workspace, expected_payload = _deterministic_debugger_input_payload(
            task_id=task_id,
            run_id=run_id,
            attempt_id=attempt_id,
            classification_input=classification_input,
            exact_failure_output=exact_failure_output,
            feedback_sha256=feedback_sha256,
            current_state_manifest=current_state_manifest,
            current_state_manifest_sha256=current_state_manifest_sha256,
        )
    except CodingOrchestratorError:
        return False
    body = dict(trace)
    recorded_sha256 = str(body.pop("trace_sha256", ""))
    argv = trace.get("argv")
    stdout = trace.get("stdout")
    stderr = trace.get("stderr")
    findings = trace.get("findings")
    stdin_text = json.dumps(
        expected_payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    if not (
        isinstance(argv, list)
        and len(argv) == 4
        and isinstance(argv[0], str)
        and bool(argv[0])
        and argv[1:] == ["-I", "-c", _DETERMINISTIC_DEBUGGER_SCRIPT]
        and isinstance(stdout, str)
        and isinstance(stderr, str)
        and isinstance(findings, Mapping)
    ):
        return False
    try:
        parsed_stdout = json.loads(stdout)
    except json.JSONDecodeError:
        return False
    feedback_post_apply = exact_failure_output.get("post_apply_verification")
    expected_failed_checks = [
        dict(check)
        for check in (
            feedback_post_apply.get("checks", [])
            if isinstance(feedback_post_apply, Mapping)
            else []
        )
        if isinstance(check, Mapping)
        and str(check.get("status") or "").strip().lower() == "failed"
    ]
    finding_files = findings.get("files")
    expected_files = expected_payload["files"]
    if not isinstance(finding_files, list) or len(finding_files) != len(expected_files):
        return False
    for result, expected in zip(finding_files, expected_files, strict=True):
        if (
            not isinstance(result, Mapping)
            or result.get("path") != expected.get("path")
            or result.get("expected_exists") != expected.get("expected_exists")
            or result.get("expected_sha256") != expected.get("expected_sha256")
            or result.get("state_matches") is not True
            or result.get("python_syntax")
            not in {"passed", "failed", "not_applicable"}
        ):
            return False
    exit_status = trace.get("exit_status")
    probe_passed = findings.get("probe_passed")
    return bool(
        trace.get("schema_version") == REPAIR_DEBUGGER_TRACE_SCHEMA
        and trace.get("tool_kind") == "deterministic_python_ast_state_probe"
        and trace.get("deterministic_debugger_invoked") is True
        and trace.get("model_debugger_invoked") is False
        and trace.get("task_id") == task_id
        and trace.get("run_id") == run_id
        and trace.get("attempt_id") == attempt_id
        and trace.get("argv_sha256") == _sha256_json(argv)
        and trace.get("tool_script_sha256")
        == _sha256_text(_DETERMINISTIC_DEBUGGER_SCRIPT)
        and trace.get("cwd") == str(workspace)
        and trace.get("input_payload") == expected_payload
        and trace.get("input_sha256") == _sha256_text(stdin_text)
        and trace.get("feedback_sha256") == feedback_sha256
        and trace.get("current_state_manifest_sha256")
        == current_state_manifest_sha256
        and isinstance(exit_status, int)
        and not isinstance(exit_status, bool)
        and exit_status in {0, 1}
        and trace.get("timed_out") is False
        and isinstance(trace.get("duration_ms"), int)
        and not isinstance(trace.get("duration_ms"), bool)
        and trace.get("duration_ms") >= 0
        and trace.get("stdout_sha256") == _sha256_text(stdout)
        and trace.get("stderr_sha256") == _sha256_text(stderr)
        and parsed_stdout == findings
        and findings.get("schema_version")
        == "coding.deterministic-debugger-findings/v1"
        and findings.get("classification_input") == classification_input
        and findings.get("failed_checks") == expected_failed_checks
        and isinstance(probe_passed, bool)
        and probe_passed is (exit_status == 0)
        and trace.get("findings_sha256") == _sha256_json(findings)
        and recorded_sha256
        and _sha256_json(body) == recorded_sha256
    )


def _valid_repair_diagnostic(
    diagnostic: object,
    *,
    task_id: str,
    run_id: str,
    attempt_id: str,
    failure: Mapping[str, Any],
    current_state_manifest: object,
    current_state_manifest_sha256: str,
) -> bool:
    """Verify the deterministic, non-model failure record consumed by repair."""

    if not isinstance(diagnostic, Mapping) or not isinstance(
        current_state_manifest, Mapping
    ):
        return False
    body = dict(diagnostic)
    recorded_sha256 = str(body.pop("diagnostic_sha256", ""))
    feedback = failure.get("exact_feedback")
    feedback_sha256 = str(failure.get("feedback_sha256") or "")
    failure_class = str(failure.get("failure_class") or "")
    source_lane = str(failure.get("source_lane") or "")
    expected_input = _structured_repair_diagnostic_input(
        failure_class=failure_class,
        source_lane=source_lane,
        exact_feedback=(feedback if isinstance(feedback, Mapping) else {}),
    )
    expected_classification = classify_repair_failure(
        diagnostic_code=expected_input["diagnostic_code"],
        stage=expected_input["stage"],
        reason=expected_input["reason"],
        details=_repair_classification_details(
            expected_input,
            feedback_sha256=feedback_sha256,
            current_state_manifest_sha256=current_state_manifest_sha256,
        ),
    ).to_dict()
    debugger_required = expected_classification.get("failure_kind") in {
        "runtime_error",
        "test_environment_error",
    }
    debugger_trace = diagnostic.get("debugger_trace")
    debugger_trace_valid = (
        _valid_deterministic_debugger_trace(
            debugger_trace,
            task_id=task_id,
            run_id=run_id,
            attempt_id=attempt_id,
            classification_input=expected_input,
            exact_failure_output=(
                feedback if isinstance(feedback, Mapping) else {}
            ),
            feedback_sha256=feedback_sha256,
            current_state_manifest=current_state_manifest,
            current_state_manifest_sha256=current_state_manifest_sha256,
        )
        if debugger_required
        else debugger_trace is None
    )
    return bool(
        diagnostic.get("schema_version") == REPAIR_DIAGNOSTIC_SCHEMA
        and diagnostic.get("hook") == "deterministic_failure_classifier"
        and diagnostic.get("model_debugger_invoked") is False
        and diagnostic.get("task_id") == task_id
        and diagnostic.get("run_id") == run_id
        and diagnostic.get("attempt_id") == attempt_id
        and diagnostic.get("failure_class") == failure_class
        and diagnostic.get("source_lane") == source_lane
        and diagnostic.get("classification_input") == expected_input
        and diagnostic.get("classification") == expected_classification
        and diagnostic.get("deterministic_debugger_invoked")
        is debugger_required
        and debugger_trace_valid
        and diagnostic.get("exact_failure_output") == feedback
        and diagnostic.get("exact_failure_output_sha256") == feedback_sha256
        and diagnostic.get("current_state_manifest") == current_state_manifest
        and diagnostic.get("current_state_manifest_sha256")
        == current_state_manifest_sha256
        and current_state_manifest_sha256 == _sha256_json(current_state_manifest)
        and recorded_sha256
        and _sha256_json(body) == recorded_sha256
    )


def _validate_repair_target_baseline(
    *,
    repair_request: Mapping[str, Any],
    target_plugin_identity: Mapping[str, Any],
) -> None:
    manifest = repair_request.get("current_state_manifest")
    if not isinstance(manifest, Mapping) or manifest.get("live_state_captured") is not True:
        raise CodingOrchestratorError("repair_current_state_manifest_invalid")
    stable = manifest.get("stable_target_plugin_identity")
    if (
        not isinstance(stable, Mapping)
        or dict(stable) != _stable_target_plugin_identity(target_plugin_identity)
    ):
        raise CodingOrchestratorError("repair_target_plugin_identity_changed")
    expected_head = str(manifest.get("target_source_head") or "")
    actual_head = str(
        target_plugin_identity.get("target_source_head")
        or target_plugin_identity.get("source_head")
        or ""
    )
    if not expected_head or actual_head != expected_head:
        raise CodingOrchestratorError("repair_target_source_head_changed")
    for item in manifest.get("changed_files", []):
        if not isinstance(item, Mapping):
            raise CodingOrchestratorError("repair_current_state_manifest_invalid")
        root = Path(str(manifest.get("workspace_root") or "")).resolve()
        relative = str(item.get("path") or "")
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise CodingOrchestratorError("repair_current_state_path_invalid") from error
        exists = candidate.is_file()
        current_sha256 = (
            hashlib.sha256(candidate.read_bytes()).hexdigest() if exists else None
        )
        if (
            exists is not bool(item.get("current_exists"))
            or current_sha256 != item.get("current_sha256")
        ):
            raise CodingOrchestratorError("repair_current_state_changed")
    if stable.get("plugin_id") == "generic-workspace":
        if (
            target_plugin_identity.get("target_workspace_state_sha256")
            != manifest.get("target_workspace_state_sha256")
            or list(target_plugin_identity.get("target_workspace_state_paths") or [])
            != list(manifest.get("target_workspace_state_paths") or [])
        ):
            raise CodingOrchestratorError("repair_target_workspace_state_changed")


def _sealed_attempt_awaits_disposition(run: CodingLaneStateMachine) -> bool:
    if len(run.attempt_history) != run.attempt_number or not run.attempt_history:
        return False
    seal = run.attempt_history[-1]
    if seal.get("attempt_id") != run.attempt_id:
        return False
    seal_hash = str(seal.get("seal_sha256") or "")
    disposition_exists = any(
        item.get("attempt_seal_sha256") == seal_hash
        for item in run.attempt_dispositions
    )
    return bool(seal.get("next_attempt_id")) or not disposition_exists


def _sealed_approval_ids(run: CodingLaneStateMachine) -> set[str]:
    return {
        str(binding.get("approval_id") or "")
        for item in run.attempt_history
        for binding in [item.get("approval_binding")]
        if isinstance(binding, Mapping) and str(binding.get("approval_id") or "")
    }


def _build_semantic_review_binding(
    *,
    task_id: str,
    run_id: str,
    attempt_id: str,
    planner_output: Mapping[str, Any],
    proposed_diff: str,
    changed_files: list[str],
    adapter_diagnostics: Mapping[str, Any],
    adapter_architect_plan_required: bool,
    repair_request: Mapping[str, Any] | None,
) -> dict[str, Any]:
    planner_payload = planner_output.get("payload")
    serialized_plan = (
        planner_payload.get("task_spec")
        if isinstance(planner_payload, Mapping)
        else None
    )
    if not isinstance(serialized_plan, Mapping):
        raise CodingOrchestratorError("coding_semantic_plan_missing")
    try:
        plan = ArchitectPlan.from_dict(dict(serialized_plan))
    except (TypeError, ValueError) as error:
        raise CodingOrchestratorError("coding_semantic_plan_invalid") from error
    if plan.task_id != task_id:
        raise CodingOrchestratorError("coding_semantic_plan_task_mismatch")
    acceptance_criteria = [
        {
            "id": item.id,
            "description": item.description,
            "kind": item.kind,
        }
        for item in plan.coder_packet.acceptance_criteria
    ]
    if not acceptance_criteria:
        raise CodingOrchestratorError("coding_acceptance_criteria_missing")
    target = str(plan.coder_packet.target_file.path or "")
    if target not in changed_files:
        raise CodingOrchestratorError("coding_semantic_plan_target_mismatch")
    review_report = review_diff_deterministically(plan, proposed_diff).to_dict()
    if review_report.get("passed") is not True:
        raise CodingOrchestratorError("coding_preview_semantic_review_failed")
    plan_payload = json.loads(
        json.dumps(dict(serialized_plan), sort_keys=True, default=str)
    )
    task_spec = task_spec_from_plan(plan).to_dict()
    diff_sha256 = hashlib.sha256(proposed_diff.encode("utf-8")).hexdigest()
    plan_sha256 = _sha256_json(plan_payload)
    acceptance_sha256 = _sha256_json(acceptance_criteria)
    adapter_preview_evidence = _adapter_preview_evidence(
        adapter_diagnostics,
        proposed_diff_sha256=diff_sha256,
    )
    if not (
        isinstance(adapter_preview_evidence, Mapping)
        and _adapter_architect_plan_evidence_matches(
            adapter_preview_evidence,
            plan_payload=plan_payload,
            plan_id=plan.plan_id,
            acceptance_criteria=acceptance_criteria,
            required=adapter_architect_plan_required,
        )
    ) and (adapter_architect_plan_required or adapter_preview_evidence is not None):
        raise CodingOrchestratorError("coding_adapter_architect_plan_mismatch")
    repair_feedback_binding = _semantic_repair_feedback_binding(repair_request)
    receipt_body = {
        "schema_version": "coding.preview-review-receipt/v1",
        "reviewer": "source-proxy.planning.reviewer.deterministic/v1",
        "task_id": task_id,
        "run_id": run_id,
        "attempt_id": attempt_id,
        "server_plan_id": plan.plan_id,
        "server_plan_sha256": plan_sha256,
        "server_task_spec_sha256": _sha256_json(task_spec),
        "acceptance_criteria_sha256": acceptance_sha256,
        "acceptance_criterion_ids": [
            str(item["id"]) for item in acceptance_criteria
        ],
        "proposed_diff_sha256": diff_sha256,
        "changed_files": list(changed_files),
        "deterministic_review_report": review_report,
        "deterministic_review_report_sha256": _sha256_json(review_report),
        "adapter_preview_evidence": adapter_preview_evidence,
        "adapter_preview_evidence_sha256": (
            _sha256_json(adapter_preview_evidence)
            if isinstance(adapter_preview_evidence, Mapping)
            else None
        ),
        "adapter_architect_plan_required": adapter_architect_plan_required,
        "repair_feedback_sha256": (
            repair_feedback_binding["repair_feedback_sha256"]
            if repair_feedback_binding
            else None
        ),
        "blocked_reasons": [],
        "status": "passed",
    }
    receipt = dict(receipt_body)
    receipt["receipt_sha256"] = _sha256_json(receipt_body)
    binding_body = {
        "schema_version": "coding.semantic-review-binding/v1",
        "server_plan": plan_payload,
        "server_plan_sha256": plan_sha256,
        "server_task_spec": task_spec,
        "server_task_spec_sha256": _sha256_json(task_spec),
        "acceptance_criteria": acceptance_criteria,
        "acceptance_criteria_sha256": acceptance_sha256,
        "preview_review_receipt": receipt,
        "preview_review_receipt_sha256": receipt["receipt_sha256"],
        "adapter_architect_plan_required": adapter_architect_plan_required,
        "repair_feedback": repair_feedback_binding,
        "repair_feedback_sha256": (
            repair_feedback_binding["repair_feedback_sha256"]
            if repair_feedback_binding
            else None
        ),
    }
    binding = dict(binding_body)
    binding["semantic_review_binding_sha256"] = _sha256_json(binding_body)
    return binding


def _adapter_preview_evidence(
    diagnostics: Mapping[str, Any],
    *,
    proposed_diff_sha256: str,
) -> dict[str, Any] | None:
    attempts = _mapping_list(diagnostics.get("attempts"))
    matching = next(
        (
            item
            for item in reversed(attempts)
            if item.get("proposed_diff_sha256") == proposed_diff_sha256
        ),
        None,
    )
    if not isinstance(matching, Mapping):
        return None
    git_apply_check = matching.get("git_apply_check")
    if (
        str(matching.get("preview_status") or "") == "blocked"
        or not isinstance(git_apply_check, Mapping)
        or git_apply_check.get("passed") is not True
    ):
        raise CodingOrchestratorError("coding_adapter_preview_receipt_invalid")
    return {
        "architect_plan_id": diagnostics.get("architect_plan_id"),
        "architect_plan_sha256": diagnostics.get("architect_plan_sha256"),
        "acceptance_criteria": json.loads(
            json.dumps(
                list(diagnostics.get("acceptance_criteria") or []),
                sort_keys=True,
                default=str,
            )
        ),
        "attempt": json.loads(
            json.dumps(dict(matching), sort_keys=True, default=str)
        ),
    }


def _adapter_architect_plan_evidence_matches(
    evidence: Mapping[str, Any],
    *,
    plan_payload: Mapping[str, Any],
    plan_id: str,
    acceptance_criteria: Sequence[Mapping[str, Any]],
    required: bool = False,
) -> bool:
    adapter_plan_id = str(evidence.get("architect_plan_id") or "")
    adapter_plan_sha256 = str(evidence.get("architect_plan_sha256") or "")
    adapter_criteria = evidence.get("acceptance_criteria")
    claimed = bool(adapter_plan_id or adapter_plan_sha256 or adapter_criteria)
    if not claimed:
        return not required
    expected_sha256 = hashlib.sha256(
        json.dumps(
            plan_payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
    return bool(
        adapter_plan_id == plan_id
        and adapter_plan_sha256.removeprefix("sha256:") == expected_sha256
        and isinstance(adapter_criteria, list)
        and adapter_criteria
        == json.loads(
            json.dumps(list(acceptance_criteria), sort_keys=True, default=str)
        )
    )


def _semantic_repair_feedback_binding(
    repair_request: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(repair_request, Mapping):
        return None
    exact_feedback = repair_request.get("exact_feedback")
    if (
        not isinstance(exact_feedback, Mapping)
        or _sha256_json(exact_feedback) != repair_request.get("feedback_sha256")
    ):
        raise CodingOrchestratorError("coding_semantic_repair_feedback_invalid")
    body = {
        "schema_version": "coding.semantic-repair-feedback/v1",
        "parent_attempt_id": repair_request.get("parent_attempt_id"),
        "parent_attempt_seal_sha256": repair_request.get(
            "parent_attempt_seal_sha256"
        ),
        "failure_class": repair_request.get("failure_class"),
        "source_lane": repair_request.get("source_lane"),
        "exact_feedback": json.loads(
            json.dumps(dict(exact_feedback), sort_keys=True, default=str)
        ),
        "feedback_sha256": repair_request.get("feedback_sha256"),
        "blocked_reasons": list(exact_feedback.get("blocked_reasons") or []),
        "repair_diagnostic_sha256": repair_request.get(
            "repair_diagnostic_sha256"
        ),
    }
    binding = dict(body)
    binding["repair_feedback_sha256"] = _sha256_json(body)
    return binding


def _valid_semantic_review_binding(
    binding: object,
    *,
    task_id: str,
    run_id: str,
    attempt_id: str,
    proposed_diff: str,
    changed_files: list[str],
    adapter_architect_plan_required: bool = False,
    repair_request: Mapping[str, Any] | None = None,
) -> bool:
    if not isinstance(binding, Mapping):
        return False
    body = dict(binding)
    recorded_binding_sha256 = str(
        body.pop("semantic_review_binding_sha256", "")
    )
    plan_payload = binding.get("server_plan")
    task_spec = binding.get("server_task_spec")
    acceptance = binding.get("acceptance_criteria")
    receipt = binding.get("preview_review_receipt")
    repair_feedback = binding.get("repair_feedback")
    try:
        expected_repair_feedback = _semantic_repair_feedback_binding(
            repair_request
        )
    except CodingOrchestratorError:
        return False
    if not (
        isinstance(plan_payload, Mapping)
        and isinstance(task_spec, Mapping)
        and isinstance(acceptance, list)
        and acceptance
        and isinstance(receipt, Mapping)
    ):
        return False
    try:
        plan = ArchitectPlan.from_dict(dict(plan_payload))
    except (TypeError, ValueError):
        return False
    expected_acceptance = [
        {"id": item.id, "description": item.description, "kind": item.kind}
        for item in plan.coder_packet.acceptance_criteria
    ]
    expected_task_spec = task_spec_from_plan(plan).to_dict()
    review_report = review_diff_deterministically(plan, proposed_diff).to_dict()
    receipt_body = dict(receipt)
    recorded_receipt_sha256 = str(receipt_body.pop("receipt_sha256", ""))
    adapter_evidence = receipt.get("adapter_preview_evidence")
    adapter_plan_matches = (
        _adapter_architect_plan_evidence_matches(
            adapter_evidence,
            plan_payload=plan_payload,
            plan_id=plan.plan_id,
            acceptance_criteria=expected_acceptance,
            required=adapter_architect_plan_required,
        )
        if isinstance(adapter_evidence, Mapping)
        else not adapter_architect_plan_required
    )
    return bool(
        plan.task_id == task_id
        and plan.coder_packet.target_file.path in changed_files
        and list(acceptance) == expected_acceptance
        and dict(task_spec) == expected_task_spec
        and binding.get("server_plan_sha256") == _sha256_json(plan_payload)
        and binding.get("server_task_spec_sha256") == _sha256_json(task_spec)
        and binding.get("acceptance_criteria_sha256")
        == _sha256_json(acceptance)
        and receipt.get("schema_version")
        == "coding.preview-review-receipt/v1"
        and receipt.get("reviewer")
        == "source-proxy.planning.reviewer.deterministic/v1"
        and receipt.get("task_id") == task_id
        and receipt.get("run_id") == run_id
        and receipt.get("attempt_id") == attempt_id
        and receipt.get("server_plan_id") == plan.plan_id
        and receipt.get("server_plan_sha256") == _sha256_json(plan_payload)
        and receipt.get("server_task_spec_sha256") == _sha256_json(task_spec)
        and receipt.get("acceptance_criteria_sha256")
        == _sha256_json(acceptance)
        and receipt.get("acceptance_criterion_ids")
        == [str(item.get("id") or "") for item in acceptance]
        and receipt.get("adapter_architect_plan_required")
        is adapter_architect_plan_required
        and receipt.get("proposed_diff_sha256")
        == hashlib.sha256(proposed_diff.encode("utf-8")).hexdigest()
        and receipt.get("changed_files") == changed_files
        and receipt.get("deterministic_review_report") == review_report
        and receipt.get("deterministic_review_report_sha256")
        == _sha256_json(review_report)
        and receipt.get("repair_feedback_sha256")
        == (
            expected_repair_feedback.get("repair_feedback_sha256")
            if isinstance(expected_repair_feedback, Mapping)
            else None
        )
        and receipt.get("status") == "passed"
        and receipt.get("blocked_reasons") == []
        and review_report.get("passed") is True
        and repair_feedback == expected_repair_feedback
        and binding.get("adapter_architect_plan_required")
        is adapter_architect_plan_required
        and binding.get("repair_feedback_sha256")
        == (
            expected_repair_feedback.get("repair_feedback_sha256")
            if isinstance(expected_repair_feedback, Mapping)
            else None
        )
        and adapter_plan_matches
        and (
            (
                isinstance(adapter_evidence, Mapping)
                and receipt.get("adapter_preview_evidence_sha256")
                == _sha256_json(adapter_evidence)
                and isinstance(adapter_evidence.get("attempt"), Mapping)
                and adapter_evidence["attempt"].get("proposed_diff_sha256")
                == receipt.get("proposed_diff_sha256")
                and adapter_evidence["attempt"].get("preview_status")
                != "blocked"
                and isinstance(
                    adapter_evidence["attempt"].get("git_apply_check"), Mapping
                )
                and adapter_evidence["attempt"]["git_apply_check"].get(
                    "passed"
                )
                is True
            )
            or (
                adapter_architect_plan_required is False
                and
                adapter_evidence is None
                and receipt.get("adapter_preview_evidence_sha256") is None
            )
        )
        and recorded_receipt_sha256
        and _sha256_json(receipt_body) == recorded_receipt_sha256
        and binding.get("preview_review_receipt_sha256")
        == recorded_receipt_sha256
        and recorded_binding_sha256
        and _sha256_json(body) == recorded_binding_sha256
    )


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
        "semantic_review_identity": (
            json.loads(
                json.dumps(
                    dict(proposal.get("semantic_review_binding") or {}),
                    sort_keys=True,
                    default=str,
                )
            )
            if isinstance(proposal, Mapping)
            and isinstance(proposal.get("semantic_review_binding"), Mapping)
            else {}
        ),
        "claim_ceiling": (
            "model_authored_diff_pending_independent_verification"
            if model_bound
            else "approved_diff_pending_independent_verification_without_terminal_model_proof"
        ),
    }


def _target_plugin_model_input_sha256(
    *,
    task: str,
    target_plugin_identity: Mapping[str, Any],
    canonical_context: Mapping[str, Any],
) -> str:
    """Bind recovery to the same task/plugin call, not lifecycle receipt churn.

    A fallback receives a newly acknowledged canonical-context report, so the
    report hash itself is expected to change.  The exact report remains bound
    to the model invocation by the runtime context output/acknowledgement/
    consumption records.  Recovery identity instead binds the stable call and
    source material, preventing an unrelated task, plugin, or context payload
    from being presented as the authorized replacement.
    """

    return target_plugin_model_input_sha256(
        task=task,
        target_plugin_identity=target_plugin_identity,
        canonical_context=canonical_context,
    )


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
    adapter = result.get("target_adapter_provenance")
    adapter = adapter if isinstance(adapter, Mapping) else {}
    alias = str(
        adapter.get("selected_model_alias")
        or diagnostics.get("selected_model_alias")
        or configured_alias
        or "server-selected-model"
    )
    provider = str(
        adapter.get("provider")
        or diagnostics.get("provider")
        or route_provider_for_alias(alias)
        or "model-router"
    )
    model = str(
        adapter.get("model")
        or diagnostics.get("model")
        or adapter.get("routed_model")
        or diagnostics.get("routed_model")
        or route_model_for_alias(alias)
        or alias
    )
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


def _sha256_text(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _mapping_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
