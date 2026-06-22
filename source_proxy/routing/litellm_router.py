from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from source_proxy.decision.escalation_contract import advisory_from_route_statuses
from source_proxy.routing.ollama_route import (
    clear_ollama_route_cache,
    ollama_coder_route_status_entry,
    ollama_classifier_route_status_entry,
    ollama_route_status_entry,
    resolve_classifier_ollama_model_name,
    resolve_coder_ollama_model_name,
    resolve_ollama_model_name,
    resolve_ollama_route,
)


@dataclass(frozen=True)
class RouteModel:
    alias: str
    provider: str
    model: str
    enabled: bool
    reason: str | None = None


def brain_switch_advisory_for_route_statuses(
    route_statuses: list[dict[str, Any]],
    *,
    task_shape: str = "unknown",
    evidence_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Return a dry-run escalation advisory from supplied route status snapshots.

    This helper deliberately does not call route_models(), get_router(), LiteLLM,
    Ollama, or external providers. Callers must supply already-collected status.
    """
    return advisory_from_route_statuses(
        route_statuses=route_statuses,
        task_shape=task_shape,
        evidence_ids=evidence_ids or [],
    )


def route_models() -> list[RouteModel]:
    ollama_resolution = resolve_ollama_route(probe=True)
    ollama_model = ollama_resolution.model
    coder_ollama_model = resolve_coder_ollama_model_name(probe=True)
    classifier_ollama_model = resolve_classifier_ollama_model_name(probe=True)
    local_status = ollama_route_status_entry()
    coder_status = ollama_coder_route_status_entry()
    classifier_status = ollama_classifier_route_status_entry()
    openai_model = os.getenv("SOURCE_PROXY_OPENAI_MODEL", "gpt-4o-mini")
    anthropic_model = os.getenv(
        "SOURCE_PROXY_ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219"
    )
    deepseek_model = os.getenv("SOURCE_PROXY_DEEPSEEK_MODEL", "deepseek/deepseek-chat")

    return [
        RouteModel(
            alias="local",
            provider="ollama",
            model=f"ollama_chat/{ollama_model}",
            enabled=local_status.get("enabled") is True,
            reason=str(local_status.get("reason") or "") or None,
        ),
        RouteModel(
            alias="coder",
            provider="ollama",
            model=f"ollama_chat/{coder_ollama_model}",
            enabled=coder_status.get("enabled") is True,
            reason=str(coder_status.get("reason") or "") or None,
        ),
        RouteModel(
            alias="classifier",
            provider="ollama",
            model=f"ollama_chat/{classifier_ollama_model}",
            enabled=classifier_status.get("enabled") is True,
            reason=str(classifier_status.get("reason") or "") or None,
        ),
        RouteModel(
            alias="openai",
            provider="openai",
            model=openai_model,
            enabled=bool(os.getenv("OPENAI_API_KEY")),
            reason=None if os.getenv("OPENAI_API_KEY") else "OPENAI_API_KEY is not set",
        ),
        RouteModel(
            alias="anthropic",
            provider="anthropic",
            model=f"anthropic/{anthropic_model}",
            enabled=bool(os.getenv("ANTHROPIC_API_KEY")),
            reason=(
                None
                if os.getenv("ANTHROPIC_API_KEY")
                else "ANTHROPIC_API_KEY is not set"
            ),
        ),
        RouteModel(
            alias="deepseek",
            provider="deepseek",
            model=deepseek_model,
            enabled=bool(os.getenv("DEEPSEEK_API_KEY")),
            reason=(
                None if os.getenv("DEEPSEEK_API_KEY") else "DEEPSEEK_API_KEY is not set"
            ),
        ),
    ]


@lru_cache(maxsize=1)
def get_router():
    from litellm import Router

    model_list = []
    for route_model in route_models():
        if not route_model.enabled:
            continue

        litellm_params: dict[str, Any] = {"model": route_model.model}
        if route_model.provider == "ollama":
            litellm_params["api_base"] = resolve_ollama_route(probe=True).api_base
            litellm_params["keep_alive"] = _parse_ollama_keep_alive(
                os.getenv(
                    "SOURCE_PROXY_OLLAMA_KEEP_ALIVE",
                    os.getenv("OLLAMA_KEEP_ALIVE", "-1"),
                )
            )
            litellm_params["timeout"] = (
                _read_coder_timeout_seconds()
                if route_model.alias == "coder"
                else _read_timeout_seconds()
            )

        model_list.append(
            {
                "model_name": route_model.alias,
                "litellm_params": litellm_params,
                "model_info": {
                    "id": f"source-{route_model.alias}",
                    "provider": route_model.provider,
                },
            }
        )

    return Router(
        model_list=model_list,
        set_verbose=False,
        timeout=_read_timeout_seconds(),
    )


def available_model_aliases() -> set[str]:
    return {route_model.alias for route_model in route_models() if route_model.enabled}


def route_provider_for_alias(alias: str) -> str | None:
    return next(
        (
            route_model.provider
            for route_model in route_models()
            if route_model.alias == alias and route_model.enabled
        ),
        None,
    )


def route_model_for_alias(alias: str) -> str | None:
    return next(
        (
            route_model.model
            for route_model in route_models()
            if route_model.alias == alias and route_model.enabled
        ),
        None,
    )


def routing_status() -> list[dict[str, str | bool | None]]:
    statuses: list[dict[str, str | bool | None]] = []
    local_status = ollama_route_status_entry()
    for route_model in route_models():
        item: dict[str, str | bool | None] = {
            "alias": route_model.alias,
            "provider": route_model.provider,
            "model": route_model.model,
            "enabled": route_model.enabled,
            "reason": route_model.reason,
        }
        if route_model.alias == "local" and route_model.provider == "ollama":
            item.update(local_status)
        if route_model.alias == "coder" and route_model.provider == "ollama":
            item.update(ollama_coder_route_status_entry())
        if route_model.alias == "classifier" and route_model.provider == "ollama":
            item.update(ollama_classifier_route_status_entry())
        statuses.append(item)
    return statuses


def clear_router_cache() -> None:
    get_router.cache_clear()
    clear_ollama_route_cache()


def configured_local_ollama_model() -> str:
    return resolve_ollama_model_name()


def configured_local_ollama_base_url() -> str:
    return resolve_ollama_route(probe=False).api_base


def _parse_ollama_keep_alive(value: str) -> int | str:
    stripped = value.strip()
    if stripped.lstrip("-").isdigit():
        return int(stripped)
    return stripped


def _read_timeout_seconds() -> float:
    raw_value = os.getenv("SOURCE_PROXY_REQUEST_TIMEOUT_SECONDS", "120")
    try:
        timeout = float(raw_value)
    except ValueError as error:
        raise ValueError(
            f"SOURCE_PROXY_REQUEST_TIMEOUT_SECONDS must be numeric, got {raw_value!r}."
        ) from error

    if timeout <= 0:
        raise ValueError("SOURCE_PROXY_REQUEST_TIMEOUT_SECONDS must be greater than 0.")
    return timeout


def _read_coder_timeout_seconds() -> float:
    raw_value = os.getenv("SOURCE_PROXY_CODER_TIMEOUT_SECONDS", "180")
    try:
        timeout = float(raw_value)
    except ValueError as error:
        raise ValueError(
            f"SOURCE_PROXY_CODER_TIMEOUT_SECONDS must be numeric, got {raw_value!r}."
        ) from error
    if timeout <= 0:
        raise ValueError("SOURCE_PROXY_CODER_TIMEOUT_SECONDS must be greater than 0.")
    return max(timeout, _read_timeout_seconds())
