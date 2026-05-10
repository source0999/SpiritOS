from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class SpendBreakdown:
    model_alias: str
    routed_model: str
    provider: str | None
    prompt_tokens: int
    max_completion_tokens: int
    prompt_cost_usd: Decimal
    completion_cost_usd: Decimal

    @property
    def projected_cost_usd(self) -> Decimal:
        return self.prompt_cost_usd + self.completion_cost_usd

    def as_payload(self) -> dict[str, Any]:
        return {
            "model_alias": self.model_alias,
            "routed_model": self.routed_model,
            "provider": self.provider,
            "prompt_tokens": self.prompt_tokens,
            "max_completion_tokens": self.max_completion_tokens,
            "prompt_cost_usd": _format_usd(self.prompt_cost_usd),
            "completion_cost_usd": _format_usd(self.completion_cost_usd),
            "projected_cost_usd": _format_usd(self.projected_cost_usd),
            "approval_required": self.projected_cost_usd > 0,
            "confirmation": "Resend with approval='y' to spend before send.",
        }


class SpendApprovalRequired(RuntimeError):
    def __init__(self, breakdown: SpendBreakdown):
        super().__init__("Paid route requires explicit spend approval.")
        self.breakdown = breakdown


class SpendEstimationUnavailable(RuntimeError):
    def __init__(self, routed_model: str, last_error: Exception):
        super().__init__(
            f"Could not calculate pre-flight spend for {routed_model!r}: {last_error}"
        )
        self.routed_model = routed_model
        self.last_error = last_error


async def async_pre_call_hook(
    *,
    model_alias: str,
    routed_model: str,
    provider: str | None,
    messages: list[dict[str, Any]],
    max_completion_tokens: int,
    approval: str | None,
) -> SpendBreakdown:
    breakdown = projected_spend_breakdown(
        model_alias=model_alias,
        routed_model=routed_model,
        provider=provider,
        messages=messages,
        max_completion_tokens=max_completion_tokens,
    )
    if breakdown.projected_cost_usd > 0 and approval != "y":
        raise SpendApprovalRequired(breakdown)
    return breakdown


def projected_spend_breakdown(
    *,
    model_alias: str,
    routed_model: str,
    provider: str | None,
    messages: list[dict[str, Any]],
    max_completion_tokens: int,
) -> SpendBreakdown:
    if provider in {None, "ollama"}:
        return SpendBreakdown(
            model_alias=model_alias,
            routed_model=routed_model,
            provider=provider,
            prompt_tokens=0,
            max_completion_tokens=max_completion_tokens,
            prompt_cost_usd=Decimal("0"),
            completion_cost_usd=Decimal("0"),
        )

    import litellm

    last_error: Exception | None = None
    for pricing_model in _pricing_model_candidates(routed_model):
        try:
            prompt_tokens = int(
                litellm.token_counter(model=pricing_model, messages=messages)
            )
            prompt_cost, completion_cost = litellm.cost_per_token(
                model=pricing_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=max_completion_tokens,
            )
            break
        except Exception as error:  # pragma: no cover - provider catalog dependent
            last_error = error
    else:
        if last_error is None:
            last_error = RuntimeError("No pricing model candidates were available.")
        raise SpendEstimationUnavailable(routed_model, last_error)

    return SpendBreakdown(
        model_alias=model_alias,
        routed_model=routed_model,
        provider=provider,
        prompt_tokens=prompt_tokens,
        max_completion_tokens=max_completion_tokens,
        prompt_cost_usd=Decimal(str(prompt_cost)),
        completion_cost_usd=Decimal(str(completion_cost)),
    )


def _format_usd(value: Decimal) -> str:
    return f"${value:.8f}"


def _pricing_model_candidates(routed_model: str) -> list[str]:
    candidates = [routed_model]
    if "/" in routed_model:
        candidates.append(routed_model.split("/", 1)[1])
    return list(dict.fromkeys(candidates))
