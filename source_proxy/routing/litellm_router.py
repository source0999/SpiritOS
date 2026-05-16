from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any


@dataclass(frozen=True)
class RouteModel:
    alias: str
    provider: str
    model: str
    enabled: bool
    reason: str | None = None


def route_models() -> list[RouteModel]:
    ollama_model = os.getenv("SOURCE_PROXY_OLLAMA_MODEL") or os.getenv(
        "OLLAMA_MODEL", "hermes4"
    )
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
            enabled=True,
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
            litellm_params["api_base"] = os.getenv(
                "SOURCE_PROXY_OLLAMA_BASE_URL",
                os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            )
            litellm_params["keep_alive"] = _parse_ollama_keep_alive(
                os.getenv(
                    "SOURCE_PROXY_OLLAMA_KEEP_ALIVE",
                    os.getenv("OLLAMA_KEEP_ALIVE", "-1"),
                )
            )
            litellm_params["timeout"] = _read_timeout_seconds()

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
    return [
        {
            "alias": route_model.alias,
            "provider": route_model.provider,
            "model": route_model.model,
            "enabled": route_model.enabled,
            "reason": route_model.reason,
        }
        for route_model in route_models()
    ]


def clear_router_cache() -> None:
    get_router.cache_clear()


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
