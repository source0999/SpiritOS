from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from source_proxy.approval.gate import (
    SpendEstimationUnavailable,
    projected_spend_breakdown,
)
from source_proxy.decision.prompt_packet import PromptPacketInput, build_prompt_packet
from source_proxy.decision.recommendation import (
    ModelRecommendationInput,
    recommend_model,
)
from source_proxy.routing.litellm_router import route_model_for_alias, route_provider_for_alias


@dataclass(frozen=True)
class ApiVsManualPreviewInput:
    task: str
    api_model_alias: str = "openai"
    max_completion_tokens: int = 1024
    relevant_context: str | None = None
    context_tokens: int | None = None
    sensitive: bool = False
    needs_current_info: bool = False
    needs_codebase_context: bool = False
    wants_implementation: bool = False
    prefer_free: bool = True


def build_api_vs_manual_preview(input_data: ApiVsManualPreviewInput) -> dict[str, Any]:
    manual_model_recommendation = recommend_model(
        ModelRecommendationInput(
            task=input_data.task,
            context_tokens=input_data.context_tokens,
            sensitive=input_data.sensitive,
            needs_current_info=input_data.needs_current_info,
            needs_codebase_context=input_data.needs_codebase_context,
            wants_implementation=input_data.wants_implementation,
            prefer_free=input_data.prefer_free,
        )
    )
    prompt_packet = build_prompt_packet(
        PromptPacketInput(
            task=input_data.task,
            target_model_hint=manual_model_recommendation.primary_model,
            relevant_context=input_data.relevant_context,
            context_tokens=input_data.context_tokens,
            sensitive=input_data.sensitive,
            needs_current_info=input_data.needs_current_info,
            needs_codebase_context=input_data.needs_codebase_context,
            wants_implementation=input_data.wants_implementation,
            prefer_free=input_data.prefer_free,
        )
    )
    projected_api_cost = _project_api_cost(input_data)
    context_estimate = manual_model_recommendation.route_decision.context_estimate
    privacy_flags = _privacy_flags(input_data)
    api_model_option = {
        "model_alias": input_data.api_model_alias,
        "max_completion_tokens": input_data.max_completion_tokens,
        "enabled": projected_api_cost.get("available", False),
        "fail_closed": projected_api_cost.get("fail_closed", True),
    }
    default_choice = _default_choice(projected_api_cost, manual_model_recommendation.route_type)

    return {
        "preview_version": "2.7B-2",
        "execution_status": "paused_for_human_decision",
        "would_execute": False,
        "projected_api_cost": projected_api_cost,
        "context_tokens": context_estimate.total_estimated_tokens,
        "context_estimate": context_estimate.as_payload(),
        "manual_model_recommendation": manual_model_recommendation.as_payload(),
        "api_model_option": api_model_option,
        "privacy_flags": privacy_flags,
        "decision_summary": _decision_summary(
            projected_api_cost=projected_api_cost,
            context_tokens=context_estimate.total_estimated_tokens,
            manual_primary_model=manual_model_recommendation.primary_model,
            api_model_alias=input_data.api_model_alias,
            privacy_flags=privacy_flags,
            default_choice=default_choice,
        ),
        "manual_prompt_packet": prompt_packet.as_payload(),
        "required_human_decision": {
            "question": "Use paid API route, manual browser route, or local route?",
            "allowed_choices": ["api", "manual", "local", "cancel"],
            "default_choice": default_choice,
            "api_choice_requires_approval": True,
            "source_will_not_execute_until_choice_is_confirmed": True,
        },
    }


def _project_api_cost(input_data: ApiVsManualPreviewInput) -> dict[str, Any]:
    routed_model = route_model_for_alias(input_data.api_model_alias)
    provider = route_provider_for_alias(input_data.api_model_alias)
    if routed_model is None:
        return {
            "available": False,
            "model_alias": input_data.api_model_alias,
            "error": "API model alias is not enabled.",
            "fail_closed": True,
        }

    context = (input_data.relevant_context or "").strip()
    content = input_data.task if not context else f"{input_data.task}\n\n{context}"
    try:
        breakdown = projected_spend_breakdown(
            model_alias=input_data.api_model_alias,
            routed_model=routed_model,
            provider=provider,
            messages=[{"role": "user", "content": content}],
            max_completion_tokens=input_data.max_completion_tokens,
        )
    except SpendEstimationUnavailable as error:
        return {
            "available": False,
            "model_alias": input_data.api_model_alias,
            "error": str(error),
            "fail_closed": True,
        }

    payload = breakdown.as_payload()
    payload["available"] = True
    payload["fail_closed"] = False
    return payload


def _privacy_flags(input_data: ApiVsManualPreviewInput) -> list[str]:
    flags: list[str] = []
    lowered = f"{input_data.task}\n{input_data.relevant_context or ''}".lower()
    if input_data.sensitive:
        flags.append("user_marked_sensitive")
    if any(token in lowered for token in ["secret", "password", "api_key", ".env", "token"]):
        flags.append("possible_secret_or_env_content")
    if input_data.needs_codebase_context:
        flags.append("codebase_context_requested")
    if not flags:
        flags.append("no_privacy_flags_detected")
    return flags


def _default_choice(projected_api_cost: dict[str, Any], manual_route_type: str) -> str:
    if manual_route_type == "manual_route":
        return "manual"
    if manual_route_type == "local_route":
        return "local"
    if projected_api_cost.get("available"):
        return "api"
    return "manual"


def _decision_summary(
    *,
    projected_api_cost: dict[str, Any],
    context_tokens: int,
    manual_primary_model: str,
    api_model_alias: str,
    privacy_flags: list[str],
    default_choice: str,
) -> dict[str, Any]:
    return {
        "recommended_default": default_choice,
        "manual_route": {
            "available": True,
            "primary_model": manual_primary_model,
            "requires_external_paste": True,
            "source_spend_usd": "$0.00000000",
        },
        "api_route": {
            "model_alias": api_model_alias,
            "available": projected_api_cost.get("available", False),
            "fail_closed": projected_api_cost.get("fail_closed", True),
            "projected_cost_usd": projected_api_cost.get("projected_cost_usd"),
            "requires_spend_approval": True,
        },
        "context": {
            "tokens": context_tokens,
            "size_class": _context_size_class(context_tokens),
        },
        "privacy": {
            "flags": privacy_flags,
            "has_flags": privacy_flags != ["no_privacy_flags_detected"],
        },
        "decision_copy": _decision_copy(
            default_choice=default_choice,
            projected_api_cost=projected_api_cost,
            manual_primary_model=manual_primary_model,
        ),
    }


def _context_size_class(context_tokens: int) -> str:
    if context_tokens >= 120_000:
        return "huge"
    if context_tokens >= 32_000:
        return "large"
    if context_tokens >= 8_000:
        return "medium"
    return "small"


def _decision_copy(
    *,
    default_choice: str,
    projected_api_cost: dict[str, Any],
    manual_primary_model: str,
) -> str:
    if default_choice == "manual":
        return (
            f"Manual browser route is recommended first using {manual_primary_model}; "
            "Source will not send a paid API request unless you explicitly choose API."
        )
    if default_choice == "local":
        return "Local route is recommended first; no paid API request will be sent."
    if projected_api_cost.get("available"):
        return (
            "API route is available, but Source is paused until you approve the "
            "spend-before-send preview."
        )
    return "API route is unavailable or fail-closed; manual route is the default."
