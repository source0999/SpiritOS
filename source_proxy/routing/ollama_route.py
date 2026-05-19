from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

_DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:7b"
_DEFAULT_OLLAMA_BASE = "http://127.0.0.1:11434"
_PROBE_TIMEOUT_SECONDS = 2.0
_PROBE_CACHE_SECONDS = 60.0

_probe_cache: tuple[float, str, dict[str, Any]] | None = None


@dataclass(frozen=True)
class OllamaRouteResolution:
    api_base: str
    model: str
    litellm_model: str
    configured_candidates: tuple[str, ...]
    selected_via: str
    probe_ok: bool
    available_models: tuple[str, ...]


def ollama_base_url_candidates() -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for key in (
        "SOURCE_PROXY_OLLAMA_BASE_URL",
        "OLLAMA_BASE_URL",
        "OLLAMA_URL",
    ):
        raw = os.getenv(key, "").strip().rstrip("/")
        if not raw or raw in seen:
            continue
        seen.add(raw)
        ordered.append(raw)
    if not ordered:
        ordered.append(_DEFAULT_OLLAMA_BASE)
    return ordered


def resolve_ollama_model_name() -> str:
    explicit = (
        os.getenv("SOURCE_PROXY_OLLAMA_MODEL", "").strip()
        or os.getenv("OLLAMA_MODEL", "").strip()
    )
    if explicit:
        return explicit
    return _DEFAULT_OLLAMA_MODEL


def safe_ollama_host_label(api_base: str) -> str:
    parsed = urlparse(api_base)
    host = parsed.hostname or api_base
    port = parsed.port
    if port and port not in {80, 443}:
        return f"{host}:{port}"
    return host


def clear_ollama_route_cache() -> None:
    global _probe_cache
    _probe_cache = None


def resolve_ollama_route(*, probe: bool = True) -> OllamaRouteResolution:
    candidates = ollama_base_url_candidates()
    model = resolve_ollama_model_name()
    selected_via = "default"
    api_base = candidates[-1]
    probe_ok = False
    available_models: tuple[str, ...] = ()

    if probe:
        api_base, probe_ok, available_models, selected_via = _select_reachable_base(candidates)
    else:
        api_base = candidates[0]
        selected_via = "env_first"

    if probe_ok and available_models and model not in available_models:
        if _DEFAULT_OLLAMA_MODEL in available_models:
            model = _DEFAULT_OLLAMA_MODEL
            selected_via = f"{selected_via}+default_model_fallback"

    return OllamaRouteResolution(
        api_base=api_base.rstrip("/"),
        model=model,
        litellm_model=f"ollama_chat/{model}",
        configured_candidates=tuple(candidates),
        selected_via=selected_via,
        probe_ok=probe_ok,
        available_models=available_models,
    )


def local_model_unavailable_from_error(error: BaseException | str) -> bool:
    text = str(error).lower()
    markers = (
        "connection refused",
        "apiconnectionerror",
        "ollama_chatexception",
        "ollamaexception",
        "failed to connect",
        "errno 111",
        "model group=local",
    )
    return any(marker in text for marker in markers)


def local_model_unavailable_payload(
    error: BaseException | str,
    *,
    model_alias: str = "local",
) -> dict[str, str]:
    route = resolve_ollama_route(probe=False)
    host = safe_ollama_host_label(route.api_base)
    return {
        "reason_code": "local_model_unavailable",
        "model_group": model_alias,
        "provider": "ollama",
        "litellm_model": route.litellm_model,
        "ollama_model": route.model,
        "api_base_host": host,
        "selected_via": route.selected_via,
        "message": (
            f"Local coder route ({model_alias}) could not reach Ollama at {host} "
            f"for model {route.model}."
        ),
        "error_excerpt": str(error)[:240],
    }


def ollama_route_status_entry() -> dict[str, str | bool | None]:
    route = resolve_ollama_route(probe=True)
    return {
        "alias": "local",
        "provider": "ollama",
        "model": route.litellm_model,
        "ollama_model": route.model,
        "api_base_host": safe_ollama_host_label(route.api_base),
        "api_base": route.api_base,
        "enabled": True,
        "probe_ok": route.probe_ok,
        "selected_via": route.selected_via,
        "reason": None if route.probe_ok else "ollama_unreachable",
    }


def _select_reachable_base(
    candidates: list[str],
) -> tuple[str, bool, tuple[str, ...], str]:
    global _probe_cache
    now = time.monotonic()
    if _probe_cache is not None:
        cached_at, cached_base, meta = _probe_cache
        if now - cached_at < _PROBE_CACHE_SECONDS and cached_base in candidates:
            return (
                cached_base,
                bool(meta.get("probe_ok")),
                tuple(meta.get("available_models") or ()),
                str(meta.get("selected_via") or "probe_cache"),
            )

    for index, candidate in enumerate(candidates):
        ok, models = _probe_ollama_tags(candidate)
        if ok:
            selected_via = (
                "SOURCE_PROXY_OLLAMA_BASE_URL"
                if index == 0 and os.getenv("SOURCE_PROXY_OLLAMA_BASE_URL", "").strip()
                else (
                    "OLLAMA_BASE_URL"
                    if candidate == os.getenv("OLLAMA_BASE_URL", "").strip().rstrip("/")
                    else (
                        "OLLAMA_URL"
                        if candidate == os.getenv("OLLAMA_URL", "").strip().rstrip("/")
                        else "fallback_default"
                    )
                )
            )
            meta = {
                "probe_ok": True,
                "available_models": list(models),
                "selected_via": f"probe:{selected_via}",
            }
            _probe_cache = (now, candidate, meta)
            return candidate, True, models, meta["selected_via"]

    fallback = candidates[0]
    meta = {"probe_ok": False, "available_models": [], "selected_via": "probe_failed_use_first_env"}
    _probe_cache = (now, fallback, meta)
    return fallback, False, (), meta["selected_via"]


def _probe_ollama_tags(api_base: str) -> tuple[bool, tuple[str, ...]]:
    url = f"{api_base.rstrip('/')}/api/tags"
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=_PROBE_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return False, ()
    models_raw = payload.get("models") if isinstance(payload, dict) else None
    if not isinstance(models_raw, list):
        return True, ()
    names: list[str] = []
    for item in models_raw:
        if isinstance(item, dict):
            name = str(item.get("name") or "").strip()
            if name:
                names.append(name)
    return True, tuple(names)
