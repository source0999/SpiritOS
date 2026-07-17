"""Canonical sequencing for a core coding run.

This module owns participation state only.  Context, approval, execution,
review, verification, and evidence remain owned by their existing authorities.
"""
from __future__ import annotations

import dataclasses
from collections.abc import Callable, Mapping
from typing import Any
from uuid import uuid4

from source_proxy.cartographer.lane_registry import (
    CORE_CODING_LANE_IDS,
    build_canonical_coding_lane_registry,
    validate_lane_registry_record,
)
from source_proxy.cartographer.cartographer_selection_authority import consume_cartographer_selection
from source_proxy.context.canonical_broker import (
    acknowledge_context_consumer,
    build_context_broker_report,
)
from source_proxy.planning.plan import load_plan
from source_proxy.tasks.long_running import (
    acknowledge_task_context_consumer,
    canonical_context_broker_for_task,
    coding_orchestrator_state_for_task,
    execute_approved_long_running_task,
    record_canonical_context_broker_for_task,
    record_coding_orchestrator_state,
    record_post_apply_verification,
)


LANE_SEQUENCE = CORE_CODING_LANE_IDS
LANE_TO_CONTEXT_CONSUMER = {
    "planner": "planner",
    "coder": "coder",
    "reviewer": "reviewer",
    "verifier": "verifier",
    "repair": "repair_loop",
    "evidence-recorder": "final_receipt_builder",
}
LANE_STATES = {"pending", "running", "completed", "failed", "blocked", "skipped", "recovering"}
ALLOWED_LANE_TRANSITIONS = {
    "pending": {"running", "blocked", "skipped"},
    "running": {"completed", "failed", "blocked"},
    "failed": {"recovering", "blocked"},
    "recovering": {"running", "completed", "blocked"},
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
    lane_states: dict[str, str] = dataclasses.field(
        default_factory=lambda: {lane_id: "pending" for lane_id in LANE_SEQUENCE}
    )
    lane_reasons: dict[str, str] = dataclasses.field(default_factory=dict)

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

    def receipt(self, *, summary: str) -> dict[str, Any]:
        return {
            "schema_version": "coding-orchestrator/v1",
            "run_id": self.run_id,
            "task_id": self.task_id,
            "lane_sequence": list(LANE_SEQUENCE),
            "lane_states": dict(self.lane_states),
            "lane_reasons": dict(self.lane_reasons),
            "summary": summary,
        }


class CodingOrchestrator:
    """Delegate one coding run through existing authoritative components."""

    def __init__(
        self,
        *,
        executor: Callable[..., dict[str, Any]] = execute_approved_long_running_task,
        planner_loader: Callable[[str], Any] = load_plan,
        post_apply_verifier: Callable[..., dict[str, Any]] = record_post_apply_verification,
        state_loader: Callable[[str], dict[str, Any] | None] = coding_orchestrator_state_for_task,
    ) -> None:
        self._executor = executor
        self._planner_loader = planner_loader
        self._post_apply_verifier = post_apply_verifier
        self._state_loader = state_loader
        self._runs: dict[str, CodingLaneStateMachine] = {}

    def start(self, task_id: str, *, sources: list[dict[str, Any]]) -> dict[str, Any]:
        if not task_id.strip():
            raise CodingOrchestratorError("coding_task_id_missing")
        registry = build_canonical_coding_lane_registry()
        if tuple(record.lane_id for record in registry) != LANE_SEQUENCE:
            raise CodingOrchestratorError("canonical_coding_lane_registry_mismatch")
        for record in registry:
            if not validate_lane_registry_record(record).accepted:
                raise CodingOrchestratorError(f"canonical_coding_lane_registry_invalid:{record.lane_id}")

        run = CodingLaneStateMachine(task_id=task_id, run_id=f"coding-run-{uuid4().hex}")
        report = build_context_broker_report(sources, applicable_consumers=("planner",))
        record_canonical_context_broker_for_task(
            task_id,
            report=report,
            orchestrator_run_id=run.run_id,
        )
        run.transition("context-broker", "running", reason="canonical_context_report_persisted")
        self._runs[task_id] = run
        return self._persist(run, "coding run initialized; planner context acknowledgement required")

    def start_from_cartographer_selection(
        self,
        task_id: str,
        *,
        selection_approval_id: str,
        proposal_id: str,
        target: str,
        sources: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Consume a proposal-only selection before it may enter coding execution."""
        selection = consume_cartographer_selection(
            approval_id=selection_approval_id,
            proposal_id=proposal_id,
            consumer="coding-executor:coder",
            target=target,
        )
        receipt = self.start(task_id, sources=sources)
        receipt["cartographer_selection"] = selection
        return receipt

    def acknowledge_planner(self, task_id: str) -> dict[str, Any]:
        run = self._run(task_id)
        run.transition("planner", "running", reason="loading_authoritative_plan")
        if self._planner_loader(task_id) is None:
            run.transition("planner", "blocked", reason="authoritative_plan_missing")
            self._persist(run, "planner blocked: authoritative plan missing")
            raise CodingOrchestratorError("authoritative_plan_missing")
        report = acknowledge_task_context_consumer(
            task_id,
            consumer="planner",
            evidence="authoritative_plan_loaded_for_canonical_coding_run",
            applicable=True,
            reason="planner_consumed_canonical_context",
        )
        if not isinstance(report, dict) or report.get("go_eligible") is not True:
            run.transition("planner", "blocked", reason="planner_context_acknowledgement_blocked")
            self._persist(run, "planner blocked by canonical context")
            raise CodingOrchestratorError("planner_context_acknowledgement_blocked")
        run.transition("planner", "completed", reason="authoritative_plan_loaded")
        run.transition("context-broker", "completed", reason="planner_context_acknowledged")
        return self._persist(run, "planner completed with canonical context acknowledgement")

    def execute_approved(
        self,
        task_id: str,
        *,
        approved_diff: str,
        action: str,
        approval_id: str,
        selected_prompt_id: str,
        context_hash: str,
        target: str | None = None,
        approved_by: str = "human",
        test_command: list[str] | None = None,
    ) -> dict[str, Any]:
        run = self._run(task_id)
        if run.lane_states["planner"] != "completed":
            raise CodingOrchestratorError("planner_must_complete_before_execution")
        run.transition("coder", "running", reason="dispatching_canonical_executor")
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
            execution = self._executor(
                task_id,
                approved_diff=approved_diff,
                action=action,
                approval_id=approval_id,
                selected_prompt_id=selected_prompt_id,
                context_hash=context_hash,
                target=target,
                approved_by=approved_by,
                test_command=test_command,
            )
        except Exception:
            run.transition("coder", "failed", reason="canonical_executor_failed")
            self._persist(run, "canonical executor failed")
            raise
        report = canonical_context_broker_for_task(task_id)
        acknowledgements = (
            report.get("downstream_acknowledgements", {}) if isinstance(report, Mapping) else {}
        )
        reviewer = acknowledgements.get("reviewer") if isinstance(acknowledgements, Mapping) else None
        if not isinstance(reviewer, Mapping) or reviewer.get("acknowledged") is not True:
            run.transition("coder", "blocked", reason="reviewer_context_acknowledgement_missing")
            self._persist(run, "executor returned without reviewer context acknowledgement")
            raise CodingOrchestratorError("reviewer_context_acknowledgement_missing")
        run.transition("coder", "completed", reason="canonical_executor_applied_approved_diff")
        run.transition("reviewer", "running", reason="executor_revalidated_reviewed_diff")
        run.transition("reviewer", "completed", reason="reviewer_context_acknowledgement_recorded")
        receipt = self._persist(run, "approved execution delegated to canonical executor")
        receipt["execution"] = execution
        return receipt

    def complete_post_apply(self, task_id: str, **verification_kwargs: Any) -> dict[str, Any]:
        run = self._run(task_id)
        if run.lane_states["coder"] != "completed":
            raise CodingOrchestratorError("coder_must_complete_before_verification")
        run.transition("verifier", "running", reason="delegating_post_apply_verification")
        result = self._post_apply_verifier(task_id, **verification_kwargs)
        task_status = str(result.get("status") or "")
        if task_status != "completed":
            run.transition("verifier", "failed", reason=f"post_apply_status:{task_status or 'unknown'}")
            run.transition("repair", "blocked", reason="repair_requires_lane_recovery")
            self._persist(run, "post-apply verification did not complete; repair is blocked truthfully")
            return {**run.receipt(summary="post-apply verification failed"), "verification": result}
        report = canonical_context_broker_for_task(task_id)
        acknowledgements = report.get("downstream_acknowledgements", {}) if isinstance(report, Mapping) else {}
        required = ("verifier", "final_receipt_builder")
        if not all(isinstance(acknowledgements.get(name), Mapping) and acknowledgements[name].get("acknowledged") is True for name in required):
            run.transition("verifier", "blocked", reason="final_context_acknowledgement_missing")
            self._persist(run, "verification completed without final context acknowledgement")
            raise CodingOrchestratorError("final_context_acknowledgement_missing")
        run.transition("verifier", "completed", reason="post_apply_verification_completed")
        run.transition("repair", "skipped", reason="verification_passed_no_repair_needed")
        run.transition("evidence-recorder", "running", reason="existing_receipt_builder_finalized_evidence")
        run.transition("evidence-recorder", "completed", reason="final_receipt_context_acknowledged")
        receipt = self._persist(run, "canonical coding run completed through final evidence")
        receipt["verification"] = result
        return receipt

    def recover_interrupted_lane(
        self,
        task_id: str,
        *,
        lane_id: str,
        recovery: Callable[[], bool] | None = None,
    ) -> dict[str, Any]:
        """Recover a persisted interrupted lane or expose its degraded state.

        A callback is intentionally required to claim recovery.  Reloading a
        process cannot turn an interrupted executor into a successful one.
        """

        run = self._restore(task_id)
        if lane_id not in LANE_SEQUENCE:
            raise CodingOrchestratorError("unknown_coding_lane")
        current = run.lane_states[lane_id]
        if current == "running":
            run.transition(lane_id, "failed", reason="interrupted_before_lane_completion")
        elif current != "failed":
            raise CodingOrchestratorError(f"lane_not_recoverable:{lane_id}:{current}")
        run.transition(lane_id, "recovering", reason="durable_lane_recovery_started")
        if recovery is None:
            run.transition(lane_id, "blocked", reason="recovery_action_required")
            receipt = self._persist(run, "interrupted lane degraded: explicit recovery action required")
            receipt["recovery"] = {"lane_id": lane_id, "outcome": "degraded", "recovered": False}
            return receipt
        try:
            recovered = recovery() is True
        except Exception:
            recovered = False
        if recovered:
            run.transition(lane_id, "completed", reason="explicit_lane_recovery_completed")
            receipt = self._persist(run, "interrupted lane recovered by explicit action")
            receipt["recovery"] = {"lane_id": lane_id, "outcome": "recovered", "recovered": True}
            return receipt
        run.transition(lane_id, "blocked", reason="explicit_lane_recovery_failed")
        receipt = self._persist(run, "interrupted lane degraded: explicit recovery failed")
        receipt["recovery"] = {"lane_id": lane_id, "outcome": "degraded", "recovered": False}
        return receipt

    def _run(self, task_id: str) -> CodingLaneStateMachine:
        try:
            return self._runs[task_id]
        except KeyError as error:
            raise CodingOrchestratorError("coding_run_not_started") from error

    def _restore(self, task_id: str) -> CodingLaneStateMachine:
        state = self._state_loader(task_id)
        if not isinstance(state, Mapping) or state.get("schema_version") != "coding-orchestrator/v1":
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
            lane_states={lane_id: str(lane_states[lane_id]) for lane_id in LANE_SEQUENCE},
            lane_reasons=dict(lane_reasons) if isinstance(lane_reasons, Mapping) else {},
        )
        if not run.run_id:
            raise CodingOrchestratorError("coding_orchestrator_state_invalid")
        self._runs[task_id] = run
        return run

    @staticmethod
    def _persist(run: CodingLaneStateMachine, summary: str) -> dict[str, Any]:
        receipt = run.receipt(summary=summary)
        record_coding_orchestrator_state(run.task_id, state=receipt)
        return receipt
