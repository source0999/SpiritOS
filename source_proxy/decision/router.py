from __future__ import annotations

import os
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

from source_proxy.decision.research import run_local_research_preview
from source_proxy.tasks.long_running import (
    LongRunningTaskError,
    get_long_running_task_snapshot,
)

RecommendedRoute = Literal["api_route", "manual_route", "local_route", "ask_user"]
RiskTier = Literal["low", "medium", "high"]
SwarmAgentRole = Literal["architect", "coder", "debugger"]
ResolvedTargetSource = Literal["explicit_line", "inferred"]


SWARM_AGENT_SYSTEM_PROMPTS: dict[SwarmAgentRole, str] = {
    "architect": (
        "You are the Architect in the Spirit OS swarm. Produce a compact plan, "
        "summarize AST/context state, identify risky files, and hand off only "
        "when the Coder has a specific implementation path. Do not edit files."
    ),
    "coder": (
        "You are the Coder in the Spirit OS swarm. Apply the Architect plan with "
        "the smallest coherent diff, record open_diffs, and hand off to Debugger "
        "when the change is ready. Do not broaden scope."
    ),
    "debugger": (
        "You are the Debugger in the Spirit OS swarm. Run focused verification "
        "through sandboxed tools, store compact test-output tails, mark verified "
        "diffs, and return failures to Coder when needed."
    ),
}


@dataclass(frozen=True)
class DecisionInput:
    task: str
    active_task_id: str | None = None
    current_agent_role: SwarmAgentRole | str | None = None
    context_tokens: int | None = None
    research_recommended: bool = False
    sensitive: bool = False
    needs_current_info: bool = False
    needs_codebase_context: bool = False
    wants_implementation: bool = False
    prefer_free: bool = True


@dataclass(frozen=True)
class ContextEstimate:
    input_chars: int
    estimated_task_tokens: int
    provided_context_tokens: int
    total_estimated_tokens: int
    size_class: Literal["small", "medium", "large", "huge"]

    def as_payload(self) -> dict[str, int | str]:
        return {
            "input_chars": self.input_chars,
            "estimated_task_tokens": self.estimated_task_tokens,
            "provided_context_tokens": self.provided_context_tokens,
            "total_estimated_tokens": self.total_estimated_tokens,
            "size_class": self.size_class,
        }


@dataclass(frozen=True)
class ResolvedTarget:
    path: str
    exists: bool
    source: ResolvedTargetSource

    def as_payload(self) -> dict[str, str | bool]:
        return {
            "path": self.path,
            "exists": self.exists,
            "source": self.source,
        }


@dataclass(frozen=True)
class RouteDecision:
    task_classification: str
    recommended_route: RecommendedRoute
    reason_codes: list[str]
    risk_tier: RiskTier
    context_estimate: ContextEstimate
    next_prompt_action: str
    research_recommended: bool = False
    research_sources: list[dict[str, str]] = field(default_factory=list)
    current_agent_role: SwarmAgentRole | None = None
    role_system_prompt: str | None = None
    self_correction_checks: list[dict[str, str | bool]] = field(default_factory=list)
    resolved_target: ResolvedTarget = field(
        default_factory=lambda: ResolvedTarget(path="", exists=False, source="inferred")
    )

    def as_payload(self) -> dict[str, object]:
        return {
            "task_classification": self.task_classification,
            "recommended_route": self.recommended_route,
            "reason_codes": self.reason_codes,
            "risk_tier": self.risk_tier,
            "context_estimate": self.context_estimate.as_payload(),
            "next_prompt_action": self.next_prompt_action,
            "research_recommended": self.research_recommended,
            "research_sources": self.research_sources,
            "current_agent_role": self.current_agent_role,
            "role_system_prompt": self.role_system_prompt,
            "self_correction_checks": self.self_correction_checks,
            "resolved_target": self.resolved_target.as_payload(),
        }


def decide_route(input_data: DecisionInput) -> RouteDecision:
    task = input_data.task.strip()
    normalized = task.lower()
    context_estimate = estimate_context(task, input_data.context_tokens)
    classification = classify_task(normalized, input_data)
    reason_codes = build_reason_codes(normalized, input_data, context_estimate)
    resolved_target = resolve_target_from_task(task)
    reason_codes = _reason_codes_with_target_honesty(
        reason_codes,
        resolved_target=resolved_target,
        classification=classification,
        wants_implementation=input_data.wants_implementation,
    )
    risk_tier = classify_risk(input_data, context_estimate, reason_codes)
    recommended_route = recommend_route(input_data, context_estimate, risk_tier, reason_codes)
    if classification == "implementation":
        recommended_route = "local_route"
    next_prompt_action = prompt_action_for_route(recommended_route)
    current_agent_role = resolve_active_agent_role(input_data)
    research_recommended = (
        input_data.research_recommended
        or input_data.needs_current_info
        or input_data.needs_codebase_context
        or needs_research(task, input_data.context_tokens)
        or needs_repo_first_research(task)
    )

    return RouteDecision(
        task_classification=classification,
        recommended_route=recommended_route,
        reason_codes=reason_codes,
        risk_tier=risk_tier,
        context_estimate=context_estimate,
        next_prompt_action=next_prompt_action,
        research_recommended=research_recommended,
        current_agent_role=current_agent_role,
        role_system_prompt=role_system_prompt(current_agent_role),
        resolved_target=resolved_target,
        self_correction_checks=build_self_correction_checks(
            task=task,
            active_task_id=input_data.active_task_id,
            task_classification=classification,
            recommended_route=recommended_route,
            reason_codes=reason_codes,
        ),
    )


_EXPLICIT_TARGET_LINE_RE = re.compile(
    r"^\s*target\s+file\s*:\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _workspace_root_from_router() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "package.json").is_file() and (
            (parent / "source_proxy").is_dir() or (parent / "src").is_dir()
        ):
            return parent
    return Path.cwd().resolve()


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _strip_wrapping_quotes(raw: str) -> str:
    s = raw.strip()
    while len(s) >= 2 and s[0] == s[-1] and s[0] in {'"', "'", "`"}:
        s = s[1:-1].strip()
    return s


def _parse_explicit_target_file_line(task: str) -> str:
    last = ""
    text = (task or "").strip()
    for match in _EXPLICIT_TARGET_LINE_RE.finditer(text):
        raw = _strip_wrapping_quotes(match.group(1))
        if raw:
            last = _strip_repo_path_sentence_punctuation(
                raw.replace("\\", "/").lstrip("./")
            )
    return last


_REPO_PATH_TOKEN_RE = re.compile(
    r"(?:^|[\s`'\"(\[{<,;:]|\n)"
    r"((?:docs|_blueprints|src|source_proxy|app|components|lib|scripts|public|tests|styles)/"
    r"[A-Za-z0-9._/@()[\]\-]+(?:\.(?:tsx?|jsx?|py|css|html|json|md|xml|yml|yaml|toml))?)"
    r"(?=$|[\s`'\")\]}>,.:;]|\n)",
    re.MULTILINE,
)


def _candidate_repo_paths_from_task_body(task: str) -> list[str]:
    """Recover repo-relative paths embedded in the task (not research context)."""
    text = (task or "").strip()
    if not text:
        return []
    seen: set[str] = set()
    ordered: list[str] = []
    for match in _REPO_PATH_TOKEN_RE.finditer(text):
        raw = _strip_repo_path_sentence_punctuation(
            match.group(1).strip().replace("\\", "/").lstrip("./")
        )
        if not raw or raw in seen:
            continue
        if "://" in raw or raw.startswith("http"):
            continue
        seen.add(raw)
        ordered.append(raw)
    return ordered


def _strip_repo_path_sentence_punctuation(path: str) -> str:
    """Keep natural-language periods out of inferred repo paths."""
    stripped = path.strip()
    while stripped and stripped[-1] in ".,:;!?":
        candidate = stripped[:-1]
        if re.search(r"\.(?:tsx?|jsx?|py|css|html|json|md|xml|ya?ml|toml)$", candidate):
            stripped = candidate
            continue
        break
    return stripped


def _reason_codes_with_target_honesty(
    reason_codes: list[str],
    *,
    resolved_target: ResolvedTarget,
    classification: str,
    wants_implementation: bool,
) -> list[str]:
    out = list(reason_codes)
    needs_missing_flag = wants_implementation or classification == "implementation"
    if resolved_target.path and not resolved_target.exists and needs_missing_flag:
        if "target_missing" not in out:
            out.append("target_missing")
    # Only the explicit UI toggle arms the strict "must resolve from task text" gate.
    # Heuristic implementation classification still allows Architect/Coder to pick targets.
    elif not resolved_target.path and wants_implementation:
        if "target_unresolved" not in out:
            out.append("target_unresolved")
    return out


def resolve_target_from_task(
    task: str,
    workspace_root: Path | None = None,
) -> ResolvedTarget:
    target_path = _parse_explicit_target_file_line(task)
    root = (workspace_root or _workspace_root_from_router()).resolve()

    if target_path:
        abs_target = (root / target_path).resolve()
        exists = _is_relative_to(abs_target, root) and abs_target.is_file()
        return ResolvedTarget(path=target_path, exists=exists, source="explicit_line")

    for candidate in _candidate_repo_paths_from_task_body(task):
        abs_candidate = (root / candidate).resolve()
        if not _is_relative_to(abs_candidate, root):
            continue
        if abs_candidate.is_file():
            return ResolvedTarget(path=candidate, exists=True, source="inferred")
    for candidate in _candidate_repo_paths_from_task_body(task):
        abs_candidate = (root / candidate).resolve()
        if _is_relative_to(abs_candidate, root):
            return ResolvedTarget(path=candidate, exists=False, source="inferred")

    return ResolvedTarget(path="", exists=False, source="inferred")


def build_self_correction_checks(
    *,
    task: str,
    active_task_id: str | None = None,
    task_classification: str,
    recommended_route: RecommendedRoute,
    reason_codes: list[str],
) -> list[dict[str, str | bool]]:
    normalized = task.lower()
    proactive_agent_required = _requires_proactive_agent_route(task_classification)
    codebase_like = needs_repo_first_research(task) or _contains_any(
        normalized,
        ["fix", "debug", "implement", "patch", "refactor", "/coding", "repo", "codebase"],
    )
    mentions_7c = _contains_any(normalized, ["7c", "phase 7c", "increment 7c"])

    active_swarm_coding_task = bool(active_task_id and codebase_like)
    passive_ok = (
        proactive_agent_required
        or active_swarm_coding_task
        or not codebase_like
        or recommended_route == "local_route"
    )
    repo_ok = not codebase_like or "repo_first_research" in reason_codes

    return [
        {
            "id": "passive_check",
            "question": "Am I being passive?",
            "passed": passive_ok,
            "answer": (
                "No. This is a coding/debugging task. A proactive agent route is required."
                if proactive_agent_required
                else "No. Active swarm task detected; route the planned coding increment to File Edit."
                if active_swarm_coding_task
                else "No. This task is routed to Coder Agent first."
                if passive_ok and codebase_like
                else "This is not a coding/debugging task, so a non-agent route is acceptable."
                if passive_ok
                else "Yes. Coding/debugging work should start with Coder Agent."
            ),
        },
        {
            "id": "repo_first_check",
            "question": "Did I scan the repo first?",
            "passed": repo_ok,
            "answer": (
                "Yes. repo_first_research is active, so repository sources are gathered before web sources."
                if repo_ok and codebase_like
                else "Repo-first research is not required for this prompt."
                if repo_ok
                else "No. Add repo_first_research before relying on external sources."
            ),
        },
        {
            "id": "phase_check",
            "question": "Am I on the correct phase?",
            "passed": True,
            "answer": (
                "Yes. Use Phase 7C / Increment 7C.4 for this self-correction pass."
                if mentions_7c
                else "No active phase was specified in this task; do not inherit one from prior runs."
            ),
        },
    ]


def _requires_proactive_agent_route(task_classification: str) -> bool:
    normalized = task_classification.strip().lower()
    return normalized in {
        "implementation",
        "codebase",
        "codebase_analysis",
        "codebase_intent",
    }


def resolve_active_agent_role(input_data: DecisionInput) -> SwarmAgentRole | None:
    explicit_role = normalize_agent_role(input_data.current_agent_role)
    if explicit_role:
        return explicit_role
    if not input_data.active_task_id:
        return None
    try:
        task = get_long_running_task_snapshot(input_data.active_task_id)["task"]
    except LongRunningTaskError:
        return None
    if isinstance(task, dict):
        return normalize_agent_role(task.get("current_agent_role"))
    return None


def normalize_agent_role(value: object) -> SwarmAgentRole | None:
    normalized = str(value or "").strip().lower()
    if normalized == "architect":
        return "architect"
    if normalized == "coder":
        return "coder"
    if normalized == "debugger":
        return "debugger"
    return None


def role_system_prompt(role: SwarmAgentRole | None) -> str | None:
    if role is None:
        return None
    return SWARM_AGENT_SYSTEM_PROMPTS[role]


async def enrich_route_decision_with_research(
    input_data: DecisionInput,
    decision: RouteDecision | None = None,
    max_results: int = 6,
) -> RouteDecision:
    route_decision = decision or decide_route(input_data)
    if not route_decision.research_recommended or not proxy_research_enabled():
        return route_decision

    research_sources = await run_local_research_preview(input_data.task, max_results=max_results)
    return replace(route_decision, research_sources=research_sources)


def proxy_research_enabled() -> bool:
    return _env_flag_enabled("SPIRIT_ENABLE_PROXY_RESEARCH")


def needs_research(task: str, context_tokens: int | None = None) -> bool:
    normalized = task.strip().lower()
    if not normalized:
        return False

    current_info_terms = [
        "latest",
        "current",
        "today",
        "tonight",
        "this week",
        "this month",
        "this year",
        "recent",
        "what's new",
        "whats new",
        "newly",
        "news",
        "breaking",
        "release notes",
        "changelog",
        "version",
        "updates",
        "changed",
        "changes",
        "price",
        "pricing",
        "schedule",
        "score",
        "weather",
        "lookup",
        "look up",
    ]
    verification_terms = [
        "verify",
        "fact check",
        "fact-check",
        "confirm",
        "source",
        "sources",
        "citation",
        "citations",
        "web",
        "search",
        "research",
    ]

    if _contains_any(normalized, current_info_terms):
        return True
    if _contains_any(normalized, verification_terms):
        return True
    if context_tokens and context_tokens > 0 and _contains_any(
        normalized,
        ["compare against", "validate against", "cross-check", "cross check"],
    ):
        return True
    return False


def needs_repo_first_research(task: str) -> bool:
    normalized = task.strip().lower()
    if not normalized:
        return False

    repo_terms = [
        "/coding",
        "coding page",
        "history bug",
        "bug",
        "debug",
        "fix",
        "route",
        "router",
        "endpoint",
        "decision",
        "prompt packet",
        "source proxy",
        "source_proxy",
        "phase",
        "increment",
        "repo",
        "codebase",
        "component",
        "hook",
    ]
    return _contains_any(normalized, repo_terms)


def estimate_context(task: str, provided_context_tokens: int | None = None) -> ContextEstimate:
    estimated_task_tokens = max(1, round(len(task) / 4))
    context_tokens = max(0, provided_context_tokens or 0)
    total = estimated_task_tokens + context_tokens

    if total >= 120_000:
        size_class = "huge"
    elif total >= 32_000:
        size_class = "large"
    elif total >= 8_000:
        size_class = "medium"
    else:
        size_class = "small"

    return ContextEstimate(
        input_chars=len(task),
        estimated_task_tokens=estimated_task_tokens,
        provided_context_tokens=context_tokens,
        total_estimated_tokens=total,
        size_class=size_class,
    )


def classify_task(normalized_task: str, input_data: DecisionInput) -> str:
    if _looks_like_file_change_intent(normalized_task):
        return "implementation"
    if input_data.active_task_id and (
        _looks_like_codebase_intent(normalized_task, input_data)
        or _contains_action_word(normalized_task)
    ):
        return "codebase_analysis"
    if _looks_like_codebase_intent(normalized_task, input_data):
        return "codebase_analysis"
    if input_data.needs_current_info or _contains_any(
        normalized_task,
        ["latest", "today", "current", "news", "price", "schedule", "lookup"],
    ):
        return "current_research"
    if input_data.wants_implementation or _contains_any(
        normalized_task,
        ["implement", "fix", "patch", "add endpoint", "refactor", "write code"],
    ):
        return "implementation"
    if input_data.needs_codebase_context or _contains_any(
        normalized_task,
        ["review", "debug", "trace", "architecture", "codebase", "repo"],
    ):
        return "codebase_analysis"
    if _contains_any(normalized_task, ["summarize", "rewrite", "draft", "explain"]):
        return "drafting"
    return "general_reasoning"


def _looks_like_file_change_intent(normalized_task: str) -> bool:
    ui_terms = [
        "bar",
        "button",
        "color",
        "component",
        "css",
        "font",
        "footer",
        "header",
        "indicator",
        "interface",
        "layout",
        "margin",
        "modal",
        "padding",
        "panel",
        "sidebar",
        "style",
        "styling",
        "tailwind",
        "toggle",
        "ui",
        "ux",
        "widget",
    ]
    return _contains_action_word(normalized_task) and (
        _contains_any(normalized_task, ui_terms)
        or _contains_any(
            normalized_task,
            ["file", "code", "endpoint", "route", "page", "screen", "form"],
        )
    )


def _contains_action_word(normalized_task: str) -> bool:
    return _contains_any(
        normalized_task,
        [
            "add",
            "build",
            "change",
            "create",
            "fix",
            "implement",
            "make",
            "move",
            "patch",
            "remove",
            "refactor",
            "style",
            "update",
            "write code",
        ],
    )


def _looks_like_codebase_intent(
    normalized_task: str,
    input_data: DecisionInput,
) -> bool:
    return (
        input_data.wants_implementation
        or input_data.needs_codebase_context
        or _looks_like_file_change_intent(normalized_task)
        or _contains_any(
            normalized_task,
            [
                "/coding",
                "codebase",
                "component",
                "debug",
                "endpoint",
                "file",
                "interface",
                "repo",
                "route",
                "router",
            ],
        )
    )


def build_reason_codes(
    normalized_task: str,
    input_data: DecisionInput,
    context_estimate: ContextEstimate,
) -> list[str]:
    reasons: list[str] = []
    if input_data.prefer_free:
        reasons.append("prefer_free_or_subscription_route")
    if input_data.sensitive or _contains_any(
        normalized_task,
        ["secret", "private", "token", "key", "credential", ".env", "password"],
    ):
        reasons.append("sensitive_or_secret_risk")
    if input_data.needs_current_info:
        reasons.append("needs_current_information")
    if input_data.needs_codebase_context:
        reasons.append("needs_codebase_context")
    if (
        input_data.needs_codebase_context
        or needs_repo_first_research(normalized_task)
        or _looks_like_codebase_intent(normalized_task, input_data)
    ):
        reasons.append("repo_first_research")
    if input_data.wants_implementation:
        reasons.append("implementation_requested")
    if input_data.active_task_id and (
        _looks_like_codebase_intent(normalized_task, input_data)
        or _contains_action_word(normalized_task)
    ):
        reasons.append("active_swarm_actionable_increment")
    if context_estimate.size_class in {"large", "huge"}:
        reasons.append("large_context")
    if _contains_any(normalized_task, ["quick", "short", "simple", "tiny"]):
        reasons.append("small_fast_task")
    return reasons or ["general_task"]


def classify_risk(
    input_data: DecisionInput,
    context_estimate: ContextEstimate,
    reason_codes: list[str],
) -> RiskTier:
    if input_data.sensitive or "sensitive_or_secret_risk" in reason_codes:
        return "high"
    if context_estimate.size_class == "huge":
        return "high"
    if context_estimate.size_class == "large" or input_data.wants_implementation:
        return "medium"
    return "low"


def recommend_route(
    input_data: DecisionInput,
    context_estimate: ContextEstimate,
    risk_tier: RiskTier,
    reason_codes: list[str],
) -> RecommendedRoute:
    if should_route_active_swarm_coding_task_locally(input_data, reason_codes):
        return "local_route"
    if risk_tier == "high":
        return "manual_route"
    if should_prefer_proxy_agent(input_data, context_estimate, reason_codes):
        return "local_route"
    if "small_fast_task" in reason_codes and context_estimate.size_class == "small":
        return "local_route"
    if input_data.prefer_free and context_estimate.size_class in {"large", "huge"}:
        return "manual_route"
    if input_data.needs_current_info:
        return "manual_route"
    if input_data.wants_implementation and context_estimate.size_class == "small":
        return "ask_user"
    if input_data.prefer_free:
        return "manual_route"
    return "api_route"


def should_prefer_proxy_agent(
    input_data: DecisionInput,
    context_estimate: ContextEstimate,
    reason_codes: list[str],
) -> bool:
    if context_estimate.size_class in {"large", "huge"}:
        return False
    if "sensitive_or_secret_risk" in reason_codes:
        return False
    return (
        input_data.wants_implementation
        or input_data.needs_codebase_context
        or "repo_first_research" in reason_codes
    )


def should_route_active_swarm_coding_task_locally(
    input_data: DecisionInput,
    reason_codes: list[str],
) -> bool:
    if not input_data.active_task_id:
        return False
    normalized = input_data.task.strip().lower()
    return (
        input_data.wants_implementation
        or input_data.needs_codebase_context
        or "repo_first_research" in reason_codes
        or "active_swarm_actionable_increment" in reason_codes
        or _contains_any(
            normalized,
            [
                "add",
                "bar",
                "button",
                "color",
                "component",
                "create",
                "font",
                "implement",
                "fix",
                "layout",
                "move",
                "patch",
                "debug",
                "refactor",
                "style",
                "toggle",
                "write code",
                "file edit",
            ],
        )
    )


def prompt_action_for_route(route: RecommendedRoute) -> str:
    if route == "api_route":
        return "show_api_cost_preview_and_require_approval"
    if route == "manual_route":
        return "generate_manual_prompt_packet"
    if route == "local_route":
        return "run_with_coder_agent"
    return "ask_user_to_choose_api_manual_or_local"


# NOTE: `limits.file_writes_allowed` for local_route is defined in verification.diff
# (LOCAL_ROUTE_DIFF_FILE_WRITES_AFTER_APPROVAL) — not here — to avoid import cycles and
# optional-deps explosions when router loads.


def _contains_any(value: str, needles: list[str]) -> bool:
    return any(needle in value for needle in needles)


def _env_flag_enabled(name: str) -> bool:
    value = os.environ.get(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}
