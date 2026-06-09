from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, Response, status
from pydantic import BaseModel, Field

from source_proxy.approval.gate import (
    SpendApprovalRequired,
    SpendEstimationUnavailable,
    async_pre_call_hook,
)
from source_proxy.approval.external_gate import ExternalGateError, central_gate_check
from source_proxy.expenditure.logger import (
    build_expenditure_record,
    log_completion_expenditure,
)
from source_proxy.routing.litellm_router import (
    available_model_aliases,
    get_router,
    route_model_for_alias,
    route_provider_for_alias,
    routing_status,
)

router = APIRouter(prefix="/v1")


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: Any
    name: str | None = None
    tool_call_id: str | None = None


class ChatCompletionRequest(BaseModel):
    model: str = Field(default="local")
    messages: list[ChatMessage]
    user_id: str | None = None
    project_id: str | None = None
    approval: Literal["y", "n"] | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False


@router.get("/models")
async def list_models() -> dict[str, Any]:
    return {"object": "list", "data": routing_status()}


@router.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    response: Response,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    try:
        central_gate_check("model_call", run_id="source_proxy_chat_completions")
    except ExternalGateError as gate_error:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={
                "message": str(gate_error),
                "reason_code": gate_error.reason_code,
                **gate_error.payload,
            },
        ) from gate_error

    if request.stream:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Streaming responses are not enabled in Increment 1.1.",
        )

    if request.model not in available_model_aliases():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model alias {request.model!r} is not enabled.",
        )

    kwargs: dict[str, Any] = {}
    if request.temperature is not None:
        kwargs["temperature"] = request.temperature
    if request.max_tokens is not None:
        kwargs["max_tokens"] = request.max_tokens
    kwargs["timeout"] = _read_request_timeout_seconds()
    request_messages = [
        message.model_dump(exclude_none=True) for message in request.messages
    ]
    routed_model = route_model_for_alias(request.model)
    provider = route_provider_for_alias(request.model)
    if routed_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model alias {request.model!r} is not enabled.",
        )

    try:
        spend_breakdown = await async_pre_call_hook(
            model_alias=request.model,
            routed_model=routed_model,
            provider=provider,
            messages=request_messages,
            max_completion_tokens=request.max_tokens or 0,
            approval=request.approval,
        )
    except SpendApprovalRequired as approval_error:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": "Spend approval required before provider request.",
                "spend_before_send": approval_error.breakdown.as_payload(),
            },
        ) from approval_error
    except SpendEstimationUnavailable as estimation_error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Could not calculate pre-flight spend for this paid route; "
                "provider request was not sent."
            ),
        ) from estimation_error

    started = time.perf_counter()
    try:
        completion = await asyncio.wait_for(
            get_router().acompletion(
                model=request.model,
                messages=request_messages,
                stream=False,
                **kwargs,
            ),
            timeout=_read_request_timeout_seconds() + 5,
        )
    except TimeoutError as error:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["x-source-proxy-response-ms"] = str(elapsed_ms)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=(
                "LiteLLM route timed out. Check Ollama model availability, "
                "model load time, and SOURCE_PROXY_REQUEST_TIMEOUT_SECONDS."
            ),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LiteLLM route failed: {error}",
        ) from error

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["x-source-proxy-response-ms"] = str(elapsed_ms)

    payload = (
        completion.model_dump() if hasattr(completion, "model_dump") else dict(completion)
    )
    expenditure_record = build_expenditure_record(
        completion_payload=payload,
        model_alias=request.model,
        provider=route_provider_for_alias(request.model),
        user_id=request.user_id
        or os.getenv("SOURCE_PROXY_DEFAULT_USER_ID", "source"),
        project_id=request.project_id
        or os.getenv("SOURCE_PROXY_DEFAULT_PROJECT_ID", "source"),
        latency_ms=elapsed_ms,
    )
    payload["source_proxy"] = {
        "model_alias": request.model,
        "response_ms": elapsed_ms,
        "spend_before_send": spend_breakdown.as_payload(),
    }
    background_tasks.add_task(
        log_completion_expenditure,
        expenditure_record,
    )
    return payload


def _read_request_timeout_seconds() -> float:
    raw_value = os.getenv("SOURCE_PROXY_REQUEST_TIMEOUT_SECONDS", "120")
    try:
        timeout = float(raw_value)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "SOURCE_PROXY_REQUEST_TIMEOUT_SECONDS must be numeric, "
                f"got {raw_value!r}."
            ),
        ) from error

    if timeout <= 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SOURCE_PROXY_REQUEST_TIMEOUT_SECONDS must be greater than 0.",
        )
    return timeout
