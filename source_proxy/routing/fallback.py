"""Truthful, opt-in provider fallback receipts for Source Proxy callers."""
from __future__ import annotations

import dataclasses
import inspect
from collections.abc import Callable
from typing import Any


class RouteFallbackError(RuntimeError):
    def __init__(self, reason_code: str, receipt: dict[str, Any]):
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.receipt = receipt


@dataclasses.dataclass(frozen=True)
class FallbackPolicy:
    primary_provider: str
    secondary_provider: str | None = None
    allow_fallback: bool = False


def invoke_with_truthful_fallback(
    policy: FallbackPolicy,
    *,
    primary: Callable[[], Any],
    secondary: Callable[[], Any] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Run the declared primary or return an auditable, never-silent fallback."""
    receipt: dict[str, Any] = {
        "schema_version": "source-proxy-routing-fallback/v1",
        "primary_provider": policy.primary_provider,
        "secondary_provider": policy.secondary_provider,
        "fallback_allowed": policy.allow_fallback,
        "fallback_used": False,
        "primary_success": False,
        "failure_reason": None,
        "selected_provider": None,
    }
    try:
        value = primary()
    except Exception as error:
        receipt["failure_reason"] = f"primary_failed:{type(error).__name__}"
        if not policy.allow_fallback or secondary is None or not policy.secondary_provider:
            raise RouteFallbackError("primary_route_failed_no_fallback", receipt) from error
        try:
            value = secondary()
        except Exception as fallback_error:
            receipt["failure_reason"] = (
                f"{receipt['failure_reason']};secondary_failed:{type(fallback_error).__name__}"
            )
            raise RouteFallbackError("fallback_route_failed", receipt) from fallback_error
        receipt["fallback_used"] = True
        receipt["selected_provider"] = policy.secondary_provider
        return value, receipt
    receipt["primary_success"] = True
    receipt["selected_provider"] = policy.primary_provider
    return value, receipt


async def invoke_async_with_truthful_fallback(
    policy: FallbackPolicy,
    *,
    primary: Callable[[], Any],
    secondary: Callable[[], Any] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Async equivalent used by the live LiteLLM route."""
    async def resolve(call: Callable[[], Any]) -> Any:
        value = call()
        return await value if inspect.isawaitable(value) else value

    receipt: dict[str, Any] = {
        "schema_version": "source-proxy-routing-fallback/v1", "primary_provider": policy.primary_provider,
        "secondary_provider": policy.secondary_provider, "fallback_allowed": policy.allow_fallback,
        "fallback_used": False, "primary_success": False, "failure_reason": None, "selected_provider": None,
    }
    try:
        value = await resolve(primary)
    except Exception as error:
        receipt["failure_reason"] = f"primary_failed:{type(error).__name__}"
        if not policy.allow_fallback or secondary is None or not policy.secondary_provider:
            raise RouteFallbackError("primary_route_failed_no_fallback", receipt) from error
        try:
            value = await resolve(secondary)
        except Exception as fallback_error:
            receipt["failure_reason"] = f"{receipt['failure_reason']};secondary_failed:{type(fallback_error).__name__}"
            raise RouteFallbackError("fallback_route_failed", receipt) from fallback_error
        receipt["fallback_used"] = True; receipt["selected_provider"] = policy.secondary_provider
        return value, receipt
    receipt["primary_success"] = True; receipt["selected_provider"] = policy.primary_provider
    return value, receipt
