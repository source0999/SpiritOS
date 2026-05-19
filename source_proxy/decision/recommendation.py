from __future__ import annotations

from dataclasses import dataclass

from source_proxy.agents.registry import provider_capability
from source_proxy.decision.router import DecisionInput, RouteDecision, decide_route


@dataclass(frozen=True)
class ModelRecommendationInput:
    task: str
    active_task_id: str | None = None
    current_agent_role: str | None = None
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
    provider_capability: dict[str, object] | None = None

    def as_payload(self) -> dict[str, object]:
        return {
            "primary_model": self.primary_model,
            "fallback_model": self.fallback_model,
            "route_type": self.route_type,
            "rationale": self.rationale,
            "expected_user_action": self.expected_user_action,
            "route_decision": self.route_decision.as_payload(),
            "provider_capability": self.provider_capability,
        }


def recommend_model(input_data: ModelRecommendationInput) -> ModelRecommendation:
    decision = decide_route(
        DecisionInput(
            task=input_data.task,
            active_task_id=input_data.active_task_id,
            current_agent_role=input_data.current_agent_role,
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
        provider_capability=_provider_capability_payload(primary),
    )


def _choose_models(
    input_data: ModelRecommendationInput,
    decision: RouteDecision,
) -> tuple[str, str, str]:
    if decision.recommended_route == "local_route":
        if input_data.active_task_id and _is_active_swarm_file_change(decision):
            return (
                "coder_agent",
                "chatgpt",
                "Active swarm plan increments with file-change targets stay on the local File Edit route so the Coder can produce a reviewable diff.",
            )
        return (
            "coder_agent",
            "chatgpt",
            "Coding and debugging work should start in the Coder Agent so it can inspect repo context and try the fix directly.",
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

    if input_data.sensitive or decision.risk_tier == "high":
        return (
            "local_ollama",
            "chatgpt",
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
        return "Run with the Coder Agent first; use a manual prompt only if the task is blocked by missing access."
    if route_type == "api_route":
        return "Show API cost preview and require explicit approval before sending."
    return "Ask the user to choose manual browser, local, or paid API route."


def _provider_capability_payload(primary_model: str) -> dict[str, object] | None:
    provider_id = {
        "coder_agent": "codex_cli",
        "local_ollama": "local_ollama",
        "gemini": "gemini_cli",
        "chatgpt": "api_adapter",
        "claude": "api_adapter",
    }.get(primary_model)
    if provider_id is None:
        return None
    capability = provider_capability(provider_id)
    if capability is None:
        return None
    return capability.as_payload()


def _is_active_swarm_file_change(decision: RouteDecision) -> bool:
    return (
        decision.task_classification == "implementation"
        or "implementation_requested" in decision.reason_codes
        or "active_swarm_actionable_increment" in decision.reason_codes
        or "repo_first_research" in decision.reason_codes
    )


def _looks_visual_or_design(task: str) -> bool:
    normalized = task.lower()
    return any(
        word in normalized
        for word in ["design", "visual", "screenshot", "image", "ui", "ux", "layout"]
    )
