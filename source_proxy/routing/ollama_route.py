from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

_DEFAULT_OLLAMA_MODEL = "hermes4"
_DEFAULT_OLLAMA_BASE = "http://127.0.0.1:11434"
_DEFAULT_OLLAMA_HOME = "/usr/share/ollama/.ollama"
_SPIRIT_8TB_ROOT = "/mnt/spirit-8tb"
_PROBE_TIMEOUT_SECONDS = 2.0
_PROBE_CACHE_SECONDS = 60.0

_probe_cache: tuple[float, str, dict[str, Any]] | None = None


@dataclass(frozen=True)
class OllamaRouteResolution:
    api_base: str
    requested_model: str
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


_CODER_MODEL_CANDIDATES = (
    "qwen2.5-coder:7b",
    "qwen2.5-coder:14b",
    "qwen2.5-coder:latest",
    "deepseek-coder:6.7b",
    "codellama:7b",
)

_DEFAULT_CLASSIFIER_MODEL = "phi4-mini:latest"
_CLASSIFIER_MODEL_CANDIDATES = (
    "phi4-mini:latest",
    "phi4-mini",
)


def resolve_coder_ollama_model_name(*, probe: bool = True) -> str:
    """Local coding trials: prefer Qwen 7B until larger coders pass contract tests."""
    explicit = os.getenv("SOURCE_PROXY_CODER_OLLAMA_MODEL", "").strip()
    if explicit:
        return explicit
    route = resolve_ollama_route(probe=probe)
    if route.probe_ok and route.available_models:
        for candidate in _CODER_MODEL_CANDIDATES:
            if candidate in route.available_models:
                return candidate
    return resolve_ollama_model_name()


def resolve_classifier_ollama_model_name(*, probe: bool = True) -> str:
    """Local routing/classifier lane: prefer Phi-4 Mini when installed."""
    explicit = os.getenv("SOURCE_PROXY_CLASSIFIER_OLLAMA_MODEL", "").strip()
    if explicit:
        return explicit
    route = resolve_ollama_route(probe=probe)
    if route.probe_ok and route.available_models:
        for candidate in _CLASSIFIER_MODEL_CANDIDATES:
            if candidate in route.available_models:
                return candidate
    return _DEFAULT_CLASSIFIER_MODEL


def _ollama_model_available(model: str, available_models: tuple[str, ...]) -> bool | None:
    if not available_models:
        return None
    if model in available_models:
        return True
    if not model.endswith(":latest") and f"{model}:latest" in available_models:
        return True
    if model.endswith(":latest") and model.removesuffix(":latest") in available_models:
        return True
    return False


def _first_available_ollama_model(available_models: tuple[str, ...]) -> str | None:
    for preferred in (
        "qwen2.5-coder:7b",
        "qwen2.5-coder:14b",
        "qwen2.5-coder:latest",
        "phi4-mini:latest",
        "llama3.1:latest",
        "Spirit:latest",
        "dolphin-llama3:latest",
        "gpt-4o-mini:latest",
    ):
        if preferred in available_models:
            return preferred
    return available_models[0] if available_models else None


def _ollama_missing_model_reason(model: str, available_models: tuple[str, ...]) -> str:
    if not available_models:
        return "ollama_models_unavailable"
    sample = ", ".join(available_models[:5])
    return f"ollama_model_missing:{model}; available={sample}"


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
    explicit_model = bool(
        os.getenv("SOURCE_PROXY_OLLAMA_MODEL", "").strip()
        or os.getenv("OLLAMA_MODEL", "").strip()
    )
    selected_via = "default"
    api_base = candidates[-1]
    probe_ok = False
    available_models: tuple[str, ...] = ()

    if probe:
        api_base, probe_ok, available_models, selected_via = _select_reachable_base(candidates)
    else:
        api_base = candidates[0]
        selected_via = "env_first"

    if probe_ok and available_models and model not in available_models and not explicit_model:
        available_hermes = _preferred_available_hermes_model(available_models)
        if available_hermes:
            model = available_hermes
            selected_via = f"{selected_via}+available_hermes"

    return OllamaRouteResolution(
        api_base=api_base.rstrip("/"),
        requested_model=resolve_ollama_model_name(),
        model=model,
        litellm_model=f"ollama_chat/{model}",
        configured_candidates=tuple(candidates),
        selected_via=selected_via,
        probe_ok=probe_ok,
        available_models=available_models,
    )


def _preferred_available_hermes_model(available_models: tuple[str, ...]) -> str | None:
    hermes_models = [model for model in available_models if "hermes" in model.lower()]
    if not hermes_models:
        return None
    return sorted(
        hermes_models,
        key=lambda model: (
            0 if "hermes4" in model.lower() else 1,
            0 if "latest" in model.lower() else 1,
            model,
        ),
    )[0]


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


def ollama_coder_route_status_entry() -> dict[str, str | bool | None]:
    chat_route = resolve_ollama_route(probe=True)
    coder_model = resolve_coder_ollama_model_name(probe=True)
    model_available = _ollama_model_available(coder_model, chat_route.available_models)
    enabled = chat_route.probe_ok and model_available is not False
    fallback_model = _first_available_candidate_after(
        coder_model,
        _CODER_MODEL_CANDIDATES,
        chat_route.available_models,
    )
    storage = _ollama_model_storage_proof()
    return {
        "alias": "coder",
        "provider": "ollama",
        "model": f"ollama_chat/{coder_model}",
        "requested_ollama_model": os.getenv("SOURCE_PROXY_CODER_OLLAMA_MODEL", "").strip()
        or "auto:qwen2.5-coder:7b",
        "ollama_model": coder_model,
        "api_base_host": safe_ollama_host_label(chat_route.api_base),
        "api_base": chat_route.api_base,
        "enabled": enabled,
        "probe_ok": chat_route.probe_ok,
        "model_available": model_available,
        "available_ollama_model_fallback": fallback_model,
        "selected_via": "coder_lane",
        "model_storage_status": storage["status"],
        "model_storage_path": storage["path"],
        "model_storage_proof": storage["proof"],
        "reason": (
            None
            if enabled
            else "ollama_unreachable"
            if not chat_route.probe_ok
            else _ollama_missing_model_reason(coder_model, chat_route.available_models)
        ),
    }


def ollama_classifier_route_status_entry() -> dict[str, str | bool | None]:
    chat_route = resolve_ollama_route(probe=True)
    classifier_model = resolve_classifier_ollama_model_name(probe=True)
    model_available = _ollama_model_available(classifier_model, chat_route.available_models)
    enabled = chat_route.probe_ok and model_available is not False
    fallback_model = _first_available_candidate_after(
        classifier_model,
        _CLASSIFIER_MODEL_CANDIDATES,
        chat_route.available_models,
    )
    storage = _ollama_model_storage_proof()
    return {
        "alias": "classifier",
        "provider": "ollama",
        "model": f"ollama_chat/{classifier_model}",
        "requested_ollama_model": os.getenv("SOURCE_PROXY_CLASSIFIER_OLLAMA_MODEL", "").strip()
        or f"auto:{_DEFAULT_CLASSIFIER_MODEL}",
        "ollama_model": classifier_model,
        "api_base_host": safe_ollama_host_label(chat_route.api_base),
        "api_base": chat_route.api_base,
        "enabled": enabled,
        "probe_ok": chat_route.probe_ok,
        "model_available": model_available,
        "available_ollama_model_fallback": fallback_model,
        "selected_via": "classifier_lane",
        "model_storage_status": storage["status"],
        "model_storage_path": storage["path"],
        "model_storage_proof": storage["proof"],
        "reason": (
            None
            if enabled
            else "ollama_unreachable"
            if not chat_route.probe_ok
            else _ollama_missing_model_reason(classifier_model, chat_route.available_models)
        ),
    }


def ollama_route_status_entry() -> dict[str, str | bool | None]:
    route = resolve_ollama_route(probe=True)
    model_available = _ollama_model_available(route.model, route.available_models)
    enabled = route.probe_ok and model_available is not False
    fallback_model = _first_available_ollama_model(route.available_models)
    storage = _ollama_model_storage_proof()
    return {
        "alias": "local",
        "provider": "ollama",
        "model": route.litellm_model,
        "requested_ollama_model": route.requested_model,
        "ollama_model": route.model,
        "api_base_host": safe_ollama_host_label(route.api_base),
        "api_base": route.api_base,
        "enabled": enabled,
        "probe_ok": route.probe_ok,
        "model_available": model_available,
        "available_ollama_model_fallback": fallback_model,
        "selected_via": route.selected_via,
        "model_storage_status": storage["status"],
        "model_storage_path": storage["path"],
        "model_storage_proof": storage["proof"],
        "reason": (
            None
            if enabled
            else "ollama_unreachable"
            if not route.probe_ok
            else _ollama_missing_model_reason(route.model, route.available_models)
        ),
    }


def _ollama_model_storage_proof() -> dict[str, str]:
    env_path = os.getenv("OLLAMA_MODELS", "").strip()
    if env_path:
        if env_path.replace("\\", "/").startswith(_SPIRIT_8TB_ROOT):
            return {
                "status": "proven",
                "path": env_path,
                "proof": "OLLAMA_MODELS",
            }
        real_env_path = os.path.realpath(env_path)
        return {
            "status": "proven" if real_env_path.startswith(_SPIRIT_8TB_ROOT) else "not_proven",
            "path": real_env_path,
            "proof": "OLLAMA_MODELS",
        }

    real_home = os.path.realpath(_DEFAULT_OLLAMA_HOME)
    if real_home != _DEFAULT_OLLAMA_HOME:
        return {
            "status": "proven" if real_home.startswith(_SPIRIT_8TB_ROOT) else "not_proven",
            "path": real_home,
            "proof": f"{_DEFAULT_OLLAMA_HOME} symlink",
        }

    return {
        "status": "not_proven",
        "path": real_home,
        "proof": "default_ollama_home",
    }


def _first_available_candidate_after(
    selected_model: str,
    candidates: tuple[str, ...],
    available_models: tuple[str, ...],
) -> str | None:
    try:
        start_index = candidates.index(selected_model) + 1
    except ValueError:
        start_index = 0
    for candidate in candidates[start_index:]:
        if _ollama_model_names_equivalent(candidate, selected_model):
            continue
        if _ollama_model_available(candidate, available_models):
            return candidate
    return None


def _ollama_model_names_equivalent(left: str, right: str) -> bool:
    return left == right or left.removesuffix(":latest") == right.removesuffix(":latest")


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
