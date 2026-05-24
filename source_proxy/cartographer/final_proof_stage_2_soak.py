from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class CartographerFinalProofStage2SoakSample:
    sample_id: str
    hour: int
    queue_run_count: int
    blocked_task_count: int
    kill_switch_checked: bool
    hidden_mutation_detected: bool
    head_changed: bool
    dirty_worktree_explained: bool
    manual_intervention_required: bool


@dataclasses.dataclass(frozen=True)
class CartographerFinalProofStage2SoakResult:
    stage: str
    status: str
    duration_hours: int
    valid_for_dry_run: bool
    would_schedule_background_job: bool
    would_execute_queue: bool
    would_write_evidence: bool
    full_auto_granted: bool
    limited_unattended_operation_granted: bool
    blocked_reasons: tuple[str, ...]
    next_increment: str


def validate_final_proof_stage_2_soak_dry_run(
    samples: tuple[CartographerFinalProofStage2SoakSample, ...],
    *,
    requested_duration_hours: int,
) -> CartographerFinalProofStage2SoakResult:
    reasons: list[str] = []

    if requested_duration_hours < 24 or requested_duration_hours > 72:
        reasons += ["duration_outside_24_to_72_hour_window"]
    if not samples:
        reasons += ["missing_soak_samples"]
    if samples and samples[0].hour != 0:
        reasons += ["soak_must_start_at_hour_zero"]
    if samples and samples[-1].hour > requested_duration_hours:
        reasons += ["sample_exceeds_requested_duration"]
    if len({sample.sample_id for sample in samples}) != len(samples):
        reasons += ["duplicate_sample_id"]

    previous_hour = -1
    for sample in samples:
        if sample.hour <= previous_hour:
            reasons += ["sample_hours_not_increasing"]
        previous_hour = sample.hour
        if sample.queue_run_count < 0 or sample.blocked_task_count < 0:
            reasons += ["invalid_negative_count"]
        if not sample.kill_switch_checked:
            reasons += [f"kill_switch_not_checked:{sample.sample_id}"]
        if sample.hidden_mutation_detected:
            reasons += [f"hidden_mutation_detected:{sample.sample_id}"]
        if sample.head_changed:
            reasons += [f"head_changed:{sample.sample_id}"]
        if not sample.dirty_worktree_explained:
            reasons += [f"dirty_worktree_unexplained:{sample.sample_id}"]
        if sample.manual_intervention_required:
            reasons += [f"manual_intervention_required:{sample.sample_id}"]

    return CartographerFinalProofStage2SoakResult(
        stage="Final Proof Stage 2",
        status="soak-dry-run-only",
        duration_hours=requested_duration_hours,
        valid_for_dry_run=not reasons,
        would_schedule_background_job=False,
        would_execute_queue=False,
        would_write_evidence=False,
        full_auto_granted=False,
        limited_unattended_operation_granted=False,
        blocked_reasons=tuple(dict.fromkeys(reasons)),
        next_increment="Final Proof Stage 3: Hidden Mutation And Dirty Worktree Drills Dry Run",
    )
