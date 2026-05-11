from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from source_proxy.decision.prompt_packet import PromptPacketInput, build_prompt_packet
from source_proxy.decision.preview import (
    ApiVsManualPreviewInput,
    build_api_vs_manual_preview,
)
from source_proxy.decision.recommendation import (
    ModelRecommendationInput,
    recommend_model,
)
from source_proxy.decision.router import (
    DecisionInput,
    decide_route,
    enrich_route_decision_with_research,
)

router = APIRouter(prefix="/v1/decisions")


class RouteDecisionRequest(BaseModel):
    task: str = Field(min_length=1)
    context_tokens: int | None = Field(default=None, ge=0)
    research_recommended: bool = False
    sensitive: bool = False
    needs_current_info: bool = False
    needs_codebase_context: bool = False
    wants_implementation: bool = False
    prefer_free: bool = True


class PromptPacketRequest(RouteDecisionRequest):
    target_model_hint: str | None = None
    relevant_context: str | None = None


class ApiVsManualPreviewRequest(PromptPacketRequest):
    api_model_alias: str = "openai"
    max_completion_tokens: int = Field(default=1024, ge=0)


@router.post("/route")
async def route_decision(request: RouteDecisionRequest) -> dict[str, Any]:
    decision_input = _decision_input_from_request(request)
    decision = await enrich_route_decision_with_research(
        decision_input,
        decision=decide_route(decision_input),
    )
    return decision.as_payload()


@router.post("/prompt-packet")
async def prompt_packet(request: PromptPacketRequest) -> dict[str, Any]:
    decision_input = _decision_input_from_request(request)
    decision = await enrich_route_decision_with_research(
        decision_input,
        decision=decide_route(decision_input),
    )
    packet = build_prompt_packet(
        PromptPacketInput(
            task=request.task,
            target_model_hint=request.target_model_hint,
            relevant_context=request.relevant_context,
            context_tokens=request.context_tokens,
            sensitive=request.sensitive,
            needs_current_info=request.needs_current_info,
            needs_codebase_context=request.needs_codebase_context,
            wants_implementation=request.wants_implementation,
            prefer_free=request.prefer_free,
        )
    )
    payload = packet.as_payload()
    payload["route_decision"] = decision.as_payload()
    payload["research_sources"] = decision.research_sources
    return payload


def _decision_input_from_request(request: RouteDecisionRequest) -> DecisionInput:
    return DecisionInput(
        task=request.task,
        context_tokens=request.context_tokens,
        research_recommended=request.research_recommended,
        sensitive=request.sensitive,
        needs_current_info=request.needs_current_info,
        needs_codebase_context=request.needs_codebase_context,
        wants_implementation=request.wants_implementation,
        prefer_free=request.prefer_free,
    )


@router.post("/recommend-model")
async def model_recommendation(request: RouteDecisionRequest) -> dict[str, Any]:
    recommendation = recommend_model(
        ModelRecommendationInput(
            task=request.task,
            context_tokens=request.context_tokens,
            sensitive=request.sensitive,
            needs_current_info=request.needs_current_info,
            needs_codebase_context=request.needs_codebase_context,
            wants_implementation=request.wants_implementation,
            prefer_free=request.prefer_free,
        )
    )
    return recommendation.as_payload()


@router.post("/api-vs-manual-preview")
async def api_vs_manual_preview(request: ApiVsManualPreviewRequest) -> dict[str, Any]:
    return build_api_vs_manual_preview(
        ApiVsManualPreviewInput(
            task=request.task,
            api_model_alias=request.api_model_alias,
            max_completion_tokens=request.max_completion_tokens,
            relevant_context=request.relevant_context,
            context_tokens=request.context_tokens,
            sensitive=request.sensitive,
            needs_current_info=request.needs_current_info,
            needs_codebase_context=request.needs_codebase_context,
            wants_implementation=request.wants_implementation,
            prefer_free=request.prefer_free,
        )
    )
