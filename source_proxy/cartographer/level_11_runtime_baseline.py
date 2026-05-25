from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class CartographerLevel11RuntimeBaseline:
    level: str
    title: str
    status: str
    authority_state: str
    allowed_current_modes: tuple[str, ...]
    forbidden_authority: tuple[str, ...]
    required_user_controls: tuple[str, ...]
    protected_lanes: tuple[str, ...]
    next_increment: str


def build_level_11_runtime_baseline() -> CartographerLevel11RuntimeBaseline:
    return CartographerLevel11RuntimeBaseline(
        level="11.1",
        title="Runtime Authority Baseline And Source-of-Truth Audit",
        status="locked-baseline",
        authority_state="locked",
        allowed_current_modes=(
            "observe",
            "recommend",
            "preview",
            "dry_run",
        ),
        forbidden_authority=(
            "autonomous_execution",
            "automatic_execution",
            "automatic_promotion",
            "self_approval",
            "write_authority",
            "local_execution_authority",
            "branch_worktree_authority",
            "commit_push_merge_authority",
            "cleanup_authority",
            "proxy_ui_mutation",
            "coding_ui_mutation",
            "source_proxy_stress_mutation",
        ),
        required_user_controls=(
            "explicit approval",
            "human-readable receipts",
            "human-readable ledger",
            "fail-closed validation",
            "rollback metadata before future writes",
            "stop condition before unsafe action",
        ),
        protected_lanes=(
            "proxy_ui_makeover",
            "coding_ui_implementation_wiring",
            "source_proxy_stress_testing",
            "codex_adapter_lane",
        ),
        next_increment=(
            "Cartographer Level 11.2: Approval Token Runtime Schema And "
            "Validation Dry Run"
        ),
    )


def level_11_runtime_baseline_is_safe_to_proceed(
    baseline: CartographerLevel11RuntimeBaseline | None = None,
) -> bool:
    candidate = baseline or build_level_11_runtime_baseline()
    forbidden = set(candidate.forbidden_authority)
    protected = set(candidate.protected_lanes)
    controls = set(candidate.required_user_controls)

    return all(
        (
            candidate.authority_state == "locked",
            "automatic_execution" in forbidden,
            "self_approval" in forbidden,
            "write_authority" in forbidden,
            "local_execution_authority" in forbidden,
            bool(protected),
            "fail-closed validation" in controls,
            candidate.next_increment
            == (
                "Cartographer Level 11.2: Approval Token Runtime Schema And "
                "Validation Dry Run"
            ),
        )
    )
