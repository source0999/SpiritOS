from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

SwarmAgentRole = Literal[
    "architect",
    "coder",
    "reviewer",
    "tester",
    "documenter",
    "researcher",
    "blueprinter",
    "cartographer",
    "oracle",
    "debugger",
]

MAX_DEFAULT_AUTHORITY_LEVEL = 3
BASE_FORBIDDEN_ACTIONS = (
    "approve",
    "apply",
    "commit",
    "push",
    "destructive_cleanup",
    "write_without_approval",
)


@dataclass(frozen=True)
class AgentRegistryEntry:
    role: SwarmAgentRole
    display_name: str
    authority_level: int
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    input_sources: tuple[str, ...]
    output_type: str
    required_approval_gates: tuple[str, ...]
    system_prompt: str

    def as_payload(self) -> dict[str, object]:
        return asdict(self)


AGENT_REGISTRY: dict[SwarmAgentRole, AgentRegistryEntry] = {
    "architect": AgentRegistryEntry(
        "architect",
        "Architect Agent",
        3,
        ("plan", "classify_task", "select_context", "define_acceptance_criteria"),
        ("edit_files", *BASE_FORBIDDEN_ACTIONS),
        ("task_description", "repo_context", "decision_memory", "safety_policy"),
        "architect_plan",
        ("approval_before_apply",),
        "You are the Architect in the Spirit OS swarm. Produce a compact plan, summarize AST/context state, identify risky files, and hand off only when the Coder has a specific implementation path. Do not edit files.",
    ),
    "coder": AgentRegistryEntry(
        "coder",
        "Coder Agent",
        3,
        ("draft_diff", "prepare_replacement_content", "record_open_diff"),
        ("broaden_scope", *BASE_FORBIDDEN_ACTIONS),
        ("architect_plan", "coder_packet", "repo_context", "task_spec"),
        "proposed_diff",
        ("deterministic_review", "human_approval_before_apply"),
        "You are the Coder in the Spirit OS swarm. Apply the Architect plan with the smallest coherent diff, record open_diffs, and hand off to Debugger when the change is ready. Do not broaden scope.",
    ),
    "reviewer": AgentRegistryEntry(
        "reviewer",
        "Reviewer Agent",
        2,
        ("critique_diff", "check_requirements", "flag_regression_risk"),
        ("edit_files", *BASE_FORBIDDEN_ACTIONS),
        ("proposed_diff", "task_spec", "verification_preview"),
        "review_report",
        ("review_before_approval",),
        "You are the Reviewer in the Spirit OS swarm. Critique proposed diffs, check target and requirement coverage, and report blockers before approval. Do not edit files.",
    ),
    "tester": AgentRegistryEntry(
        "tester",
        "Tester Agent",
        3,
        ("propose_tests", "run_dry_run_tests", "summarize_verification"),
        ("install_harness_without_approval", *BASE_FORBIDDEN_ACTIONS),
        ("task_spec", "proposed_diff", "existing_test_plan", "sandbox_output"),
        "test_plan_or_dry_run_report",
        ("approval_before_new_harness",),
        "You are the Tester in the Spirit OS swarm. Propose focused harness cases and run dry-run verification when allowed. Do not install tests or mutate files without approval.",
    ),
    "documenter": AgentRegistryEntry(
        "documenter",
        "Documenter Agent",
        3,
        ("draft_docs", "summarize_changes", "propose_receipts"),
        ("publish_docs_without_approval", *BASE_FORBIDDEN_ACTIONS),
        ("completed_work_summary", "diff_summary", "manual_check_results"),
        "documentation_proposal",
        ("dashboard_approval_before_write",),
        "You are the Documenter in the Spirit OS swarm. Draft documentation proposals from verified evidence only. Do not apply documentation changes yourself.",
    ),
    "researcher": AgentRegistryEntry(
        "researcher",
        "Researcher Agent",
        2,
        ("gather_references", "summarize_evidence", "label_trust_status"),
        ("treat_research_as_approval", *BASE_FORBIDDEN_ACTIONS),
        ("repo_research", "scout_packets", "web_research"),
        "research_evidence",
        ("human_review_before_use_as_authority",),
        "You are the Researcher in the Spirit OS swarm. Gather and label evidence, separating facts from assumptions. Research is evidence only, never approval.",
    ),
    "blueprinter": AgentRegistryEntry(
        "blueprinter",
        "Blueprinter Agent",
        3,
        ("map_blueprints", "draft_blueprint_updates", "flag_drift"),
        ("apply_blueprint_without_dashboard_approval", *BASE_FORBIDDEN_ACTIONS),
        ("blueprint_registry", "repo_map", "drift_report"),
        "blueprint_proposal",
        ("dashboard_approval_before_blueprint_write",),
        "You are the Blueprinter in the Spirit OS swarm. Propose blueprint updates from registry and drift evidence. Do not apply blueprint writes.",
    ),
    "cartographer": AgentRegistryEntry(
        "cartographer",
        "Cartographer Agent",
        2,
        ("map_project_state", "index_repo", "report_drift"),
        ("write_project_files", *BASE_FORBIDDEN_ACTIONS),
        ("project_roots", "git_status", "blueprint_registry", "repo_map"),
        "cartographer_report",
        ("approval_before_any_write_action",),
        "You are the Cartographer in the Spirit OS swarm. Map project and repo state read-only, report drift, and keep write actions disabled unless separately approved.",
    ),
    "oracle": AgentRegistryEntry(
        "oracle",
        "Oracle Agent",
        1,
        ("surface_interface_state", "relay_voice_or_ui_context"),
        ("execute_commands", *BASE_FORBIDDEN_ACTIONS),
        ("ui_state", "voice_context", "user_intent"),
        "interface_context",
        ("human_confirmation_before_action",),
        "You are the Oracle in the Spirit OS swarm. Surface voice and front-end interaction context without executing commands or approving changes.",
    ),
    "debugger": AgentRegistryEntry(
        "debugger",
        "Debugger Agent",
        3,
        ("run_focused_verification", "store_test_output_tail", "return_failures"),
        ("edit_files", *BASE_FORBIDDEN_ACTIONS),
        ("proposed_diff", "verification_plan", "sandbox_output"),
        "verification_report",
        ("approval_before_apply",),
        "You are the Debugger in the Spirit OS swarm. Run focused verification through sandboxed tools, store compact test-output tails, mark verified diffs, and return failures to Coder when needed.",
    ),
}


def get_agent_registry() -> dict[SwarmAgentRole, AgentRegistryEntry]:
    return dict(AGENT_REGISTRY)


def get_agent_registry_payload() -> dict[str, dict[str, object]]:
    return {role: entry.as_payload() for role, entry in AGENT_REGISTRY.items()}


def normalize_agent_role(value: object) -> SwarmAgentRole | None:
    normalized = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {f"{role}_agent": role for role in AGENT_REGISTRY}
    normalized = aliases.get(normalized, normalized)
    if normalized in AGENT_REGISTRY:
        return normalized  # type: ignore[return-value]
    return None


def role_system_prompt(role: SwarmAgentRole | None) -> str | None:
    if role is None:
        return None
    return AGENT_REGISTRY[role].system_prompt


def validate_registry_authority() -> list[str]:
    violations: list[str] = []
    for role, entry in AGENT_REGISTRY.items():
        if entry.authority_level > MAX_DEFAULT_AUTHORITY_LEVEL:
            violations.append(f"{role}: authority_level_above_default")
        for action in BASE_FORBIDDEN_ACTIONS:
            if action not in entry.forbidden_actions:
                violations.append(f"{role}: missing_forbidden_action:{action}")
    return violations
