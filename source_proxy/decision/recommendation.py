from __future__ import annotations

from dataclasses import dataclass

from source_proxy.decision.router import DecisionInput, RouteDecision, decide_route


@dataclass(frozen=True)
class ModelRecommendationInput:
    task: str
    context_tokens: int | None = None
    sensitive: bool = False
    needs_current_info: bool = False
    needs_codebase_context: bool = False
    wants_implementation: bool = False
    prefer_free: bool = True


@dataclass(frozen=True)
class ModelRecommendation:
    primary_model: str
    fallback_model: str
    route_type: str
    rationale: str
    expected_user_action: str
    route_decision: RouteDecision

    def as_payload(self) -> dict[str, object]:
        return {
            "primary_model": self.primary_model,
            "fallback_model": self.fallback_model,
            "route_type": self.route_type,
            "rationale": self.rationale,
            "expected_user_action": self.expected_user_action,
            "route_decision": self.route_decision.as_payload(),
        }


def recommend_model(input_data: ModelRecommendationInput) -> ModelRecommendation:
    decision = decide_route(
        DecisionInput(
            task=input_data.task,
            context_tokens=input_data.context_tokens,
            sensitive=input_data.sensitive,
            needs_current_info=input_data.needs_current_info,
            needs_codebase_context=input_data.needs_codebase_context,
            wants_implementation=input_data.wants_implementation,
            prefer_free=input_data.prefer_free,
        )
    )
    primary, fallback, rationale = _choose_models(input_data, decision)
    return ModelRecommendation(
        primary_model=primary,
        fallback_model=fallback,
        route_type=decision.recommended_route,
        rationale=rationale,
        expected_user_action=_expected_action(decision.recommended_route, primary),
        route_decision=decision,
    )


def _choose_models(
    input_data: ModelRecommendationInput,
    decision: RouteDecision,
) -> tuple[str, str, str]:
    if decision.recommended_route == "local_route":
        return (
            "local_ollama",
            "chatgpt",
            "Small, low-risk work should stay local before spending API or subscription attention.",
        )

    if input_data.needs_current_info or decision.task_classification == "current_research":
        return (
            "gemini",
            "chatgpt",
            "Current research benefits from browser-grounded answers and source checking.",
        )

    if _looks_visual_or_design(input_data.task):
        return (
            "chatgpt",
            "gemini",
            "Design critique benefits from multimodal/browser review and concise implementation follow-up.",
        )

    if input_data.needs_codebase_context or decision.context_estimate.size_class in {"large", "huge"}:
        return (
            "claude",
            "chatgpt",
            "Long codebase review is best handled manually in a large-context subscription model to avoid API spend.",
        )

    if input_data.wants_implementation:
        return (
            "chatgpt",
            "claude",
            "Implementation planning benefits from strong coding output and a Codex-ready final instruction block.",
        )

    if decision.risk_tier == "high":
        return (
            "chatgpt",
            "local_ollama",
            "Sensitive work should stay manual or local so you can inspect what leaves the machine.",
        )

    return (
        "chatgpt",
        "claude",
        "General reasoning is cheapest to run manually first, then paste the result back into Source.",
    )


def _expected_action(route_type: str, primary_model: str) -> str:
    if route_type == "manual_route":
        return f"Generate a prompt packet and paste it into {primary_model} in the browser."
    if route_type == "local_route":
        return "Use the local Ollama route or local tooling first."
    if route_type == "api_route":
        return "Show API cost preview and require explicit approval before sending."
    return "Ask the user to choose manual browser, local, or paid API route."


def _looks_visual_or_design(task: str) -> bool:
    normalized = task.lower()
    return any(
        word in normalized
        for word in ["design", "visual", "screenshot", "image", "ui", "ux", "layout"]
    )
