from __future__ import annotations

import dataclasses


GAUNTLET_ALLOWED_TASK_CLASSES: tuple[str, ...] = (
    "docs_freshness_review",
    "manual_check_reminder",
    "roadmap_drift_review",
    "dirty_worktree_summary",
    "open_gate_summary",
)

GAUNTLET_FORBIDDEN_TASK_CLASSES: tuple[str, ...] = (
    "write_file",
    "execute_command",
    "create_branch",
    "create_worktree",
    "commit",
    "push",
    "merge",
    "cleanup",
    "auto_closeout",
)

PROTECTED_PATH_PREFIXES: tuple[str, ...] = (
    "src/",
    "source_proxy/api/",
    "source_proxy/verification/",
    "source_proxy/codex/",
    "source_proxy/testing/runner.py",
)


@dataclasses.dataclass(frozen=True)
class CartographerFinalProofStage1Task:
    task_id: str
    task_class: str
    lane: str
    target_files: tuple[str, ...]
    approval_present: bool
    approval_expired: bool
    kill_switch_active: bool
    expected_result: str


@dataclasses.dataclass(frozen=True)
class CartographerFinalProofStage1TaskResult:
    task_id: str
    eligible_for_dry_run: bool
    would_execute: bool
    would_write_files: bool
    would_run_commands: bool
    blocked_reasons: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class CartographerFinalProofStage1GauntletResult:
    stage: str
    status: str
    full_auto_granted: bool
    limited_unattended_operation_granted: bool
    queue_execution_authority_granted: bool
    task_results: tuple[CartographerFinalProofStage1TaskResult, ...]
    unsafe_task_count: int
    blocked_unsafe_task_count: int
    passed: bool
    next_increment: str


def evaluate_final_proof_stage_1_task_dry_run(
    task: CartographerFinalProofStage1Task,
) -> CartographerFinalProofStage1TaskResult:
    reasons: list[str] = []

    if not task.task_id:
        reasons += ["missing_task_id"]
    if task.task_class in GAUNTLET_FORBIDDEN_TASK_CLASSES:
        reasons += ["forbidden_task_class"]
    if task.task_class not in GAUNTLET_ALLOWED_TASK_CLASSES:
        reasons += ["unsupported_task_class"]
    if any(path.startswith(PROTECTED_PATH_PREFIXES) for path in task.target_files):
        reasons += ["protected_path_in_scope"]
    if not task.approval_present:
        reasons += ["missing_approval"]
    if task.approval_expired:
        reasons += ["approval_expired"]
    if task.kill_switch_active:
        reasons += ["kill_switch_active"]

    return CartographerFinalProofStage1TaskResult(
        task_id=task.task_id,
        eligible_for_dry_run=not reasons,
        would_execute=False,
        would_write_files=False,
        would_run_commands=False,
        blocked_reasons=tuple(dict.fromkeys(reasons)),
    )


def run_final_proof_stage_1_gauntlet_dry_run(
    tasks: tuple[CartographerFinalProofStage1Task, ...],
) -> CartographerFinalProofStage1GauntletResult:
    results = tuple(evaluate_final_proof_stage_1_task_dry_run(task) for task in tasks)
    unsafe_task_ids = {
        task.task_id
        for task in tasks
        if task.task_class in GAUNTLET_FORBIDDEN_TASK_CLASSES
        or any(path.startswith(PROTECTED_PATH_PREFIXES) for path in task.target_files)
        or task.approval_expired
        or task.kill_switch_active
    }
    blocked_unsafe_task_ids = {
        result.task_id for result in results if result.task_id in unsafe_task_ids and result.blocked_reasons
    }

    return CartographerFinalProofStage1GauntletResult(
        stage="Final Proof Stage 1",
        status="real-task-gauntlet-dry-run-only",
        full_auto_granted=False,
        limited_unattended_operation_granted=False,
        queue_execution_authority_granted=False,
        task_results=results,
        unsafe_task_count=len(unsafe_task_ids),
        blocked_unsafe_task_count=len(blocked_unsafe_task_ids),
        passed=bool(tasks) and len(unsafe_task_ids) == len(blocked_unsafe_task_ids),
        next_increment="Final Proof Stage 2: 24 To 72 Hour Soak Dry Run",
    )
