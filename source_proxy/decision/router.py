from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RecommendedRoute = Literal["api_route", "manual_route", "local_route", "ask_user"]
RiskTier = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class DecisionInput:
    task: str
    context_tokens: int | None = None
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
class RouteDecision:
    task_classification: str
    recommended_route: RecommendedRoute
    reason_codes: list[str]
    risk_tier: RiskTier
    context_estimate: ContextEstimate
    next_prompt_action: str

    def as_payload(self) -> dict[str, object]:
        return {
            "task_classification": self.task_classification,
            "recommended_route": self.recommended_route,
            "reason_codes": self.reason_codes,
            "risk_tier": self.risk_tier,
            "context_estimate": self.context_estimate.as_payload(),
            "next_prompt_action": self.next_prompt_action,
        }


def decide_route(input_data: DecisionInput) -> RouteDecision:
    task = input_data.task.strip()
    normalized = task.lower()
    context_estimate = estimate_context(task, input_data.context_tokens)
    classification = classify_task(normalized, input_data)
    reason_codes = build_reason_codes(normalized, input_data, context_estimate)
    risk_tier = classify_risk(input_data, context_estimate, reason_codes)
    recommended_route = recommend_route(input_data, context_estimate, risk_tier, reason_codes)
    next_prompt_action = prompt_action_for_route(recommended_route)

    return RouteDecision(
        task_classification=classification,
        recommended_route=recommended_route,
        reason_codes=reason_codes,
        risk_tier=risk_tier,
        context_estimate=context_estimate,
        next_prompt_action=next_prompt_action,
    )


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
    if input_data.wants_implementation:
        reasons.append("implementation_requested")
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
    if risk_tier == "high":
        return "manual_route"
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


def prompt_action_for_route(route: RecommendedRoute) -> str:
    if route == "api_route":
        return "show_api_cost_preview_and_require_approval"
    if route == "manual_route":
        return "generate_manual_prompt_packet"
    if route == "local_route":
        return "run_local_model_or_local_tooling"
    return "ask_user_to_choose_api_manual_or_local"


def _contains_any(value: str, needles: list[str]) -> bool:
    return any(needle in value for needle in needles)
