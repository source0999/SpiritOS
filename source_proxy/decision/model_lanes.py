from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass
from typing import Any

import httpx

from source_proxy.diagnostics.status_codes import (
    classify_failure,
    is_failure_status,
    serialize_failure_classification,
)


MODEL_LANE_REGISTRY_VERSION = "source-proxy-model-lane-registry-v0.1"
FIP3_MODEL_PACKET_VERSION = "source-proxy-fip3-local-model-lanes-v0.1"
DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_GEMMA_MODEL = "gemma3n:e4b"
DEFAULT_HERMES_MODEL = "hermes4:latest"
DEFAULT_QWEN_CODER_MODEL = "qwen2.5-coder:7b"


@dataclass(frozen=True)
class ModelLane:
    lane_id: str
    display_name: str
    role: str
    status: str
    allowed_uses: list[str]
    disallowed_uses: list[str]
    cost_class: str
    privacy_class: str
    approval_required: str
    evidence_required_for_promotion: list[str]
    known_failure_modes: list[str]
    promotion_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def model_lane_registry() -> dict[str, Any]:
    lanes = [_qwen(), _hermes(), _gemma(), _manual_handoff(), _cloud_future()]
    return {
        "registry_version": MODEL_LANE_REGISTRY_VERSION,
        "mode": "metadata_only_no_model_calls",
        "primary_coder_lane": "qwen_local_coder",
        "sidecar_lanes_live": False,
        "promotion_policy": "evidence_driven_operator_review",
        "global_rules": [
            "qwen_local_coder remains the primary coding/action lane",
            "preview/future sidecars cannot edit files",
            "preview/future sidecars cannot declare product success without behavior evidence",
            "cloud/API routes require Britton approval before use",
            "privacy and cost classes must be visible before lane selection",
        ],
        "lanes": [lane.to_dict() for lane in lanes],
    }


def get_model_lane(lane_id: str) -> dict[str, Any]:
    for lane in model_lane_registry()["lanes"]:
        if lane["lane_id"] == lane_id:
            return lane
    raise KeyError(f"Unknown model lane: {lane_id}")


def active_primary_coder_lane() -> dict[str, Any]:
    return get_model_lane("qwen_local_coder")


def lane_selection_observability(
    *,
    task_type: str = "disposable_artifact",
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    qwen = active_primary_coder_lane()
    sidecars = [
        get_model_lane("hermes_sidecar_verifier_preview"),
        get_model_lane("gemma_sidecar_context_preview"),
    ]
    return {
        "selected_coder_lane": qwen["lane_id"],
        "selected_coder_lane_display_name": qwen["display_name"],
        "sidecar_lanes_considered": [lane["lane_id"] for lane in sidecars],
        "sidecar_lanes_live": False,
        "verifier_lane_required": task_type in {"disposable_artifact", "repo_patch_preview", "behavior_check"},
        "lane_privacy_class": qwen["privacy_class"],
        "lane_cost_class": qwen["cost_class"],
        "lane_approval_required": qwen["approval_required"],
        "lane_selection_reason_codes": [
            "qwen_primary_local_coder_preserved",
            "sidecar_lanes_preview_only",
            "no_model_swap",
            "no_live_sidecar_call",
        ],
        "lane_evidence_refs": list(evidence_refs or []),
    }


def build_model_lanes_preview(*, task_type: str = "disposable_artifact") -> dict[str, Any]:
    registry = model_lane_registry()
    return {
        "preview_version": "source-proxy-model-lanes-preview-v0.1",
        "preview_only": True,
        "would_call_models": False,
        "would_start_workers": False,
        "would_mutate_state": False,
        "available_lanes": registry["lanes"],
        "active_primary_lane": registry["primary_coder_lane"],
        "future_sidecar_lanes": [
            lane["lane_id"]
            for lane in registry["lanes"]
            if "preview" in lane["status"] or "future" in lane["status"]
        ],
        "recommended_lane": lane_selection_observability(task_type=task_type),
        "approval_requirements": {
            lane["lane_id"]: lane["approval_required"]
            for lane in registry["lanes"]
        },
        "privacy_classes": {
            lane["lane_id"]: lane["privacy_class"]
            for lane in registry["lanes"]
        },
        "cost_classes": {
            lane["lane_id"]: lane["cost_class"]
            for lane in registry["lanes"]
        },
        "verifier_requirement": task_type in {"disposable_artifact", "repo_patch_preview", "behavior_check"},
        "reason_codes": [
            "preview_only",
            "qwen_primary_local_coder_preserved",
            "future_sidecars_not_executed",
            "operator_approval_required_for_external_routes",
        ],
    }


def fip3_model_lanes_enabled() -> bool:
    return os.environ.get("SOURCE_PROXY_FIP3_MODEL_LANES_ENABLED", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def configured_fip3_models() -> dict[str, str]:
    return {
        "gemma": (
            os.environ.get("SOURCE_PROXY_FIP3_GEMMA_MODEL", "").strip()
            or os.environ.get("SOURCE_PROXY_GEMMA_MODEL", "").strip()
            or DEFAULT_GEMMA_MODEL
        ),
        "hermes": (
            os.environ.get("SOURCE_PROXY_FIP3_HERMES_MODEL", "").strip()
            or os.environ.get("SOURCE_PROXY_HERMES_MODEL", "").strip()
            or os.environ.get("SOURCE_PROXY_OLLAMA_MODEL", "").strip()
            or os.environ.get("OLLAMA_MODEL", "").strip()
            or DEFAULT_HERMES_MODEL
        ),
        "qwen_coder": (
            os.environ.get("SOURCE_PROXY_FIP3_QWEN_CODER_MODEL", "").strip()
            or os.environ.get("SOURCE_PROXY_CODER_OLLAMA_MODEL", "").strip()
            or os.environ.get("SOURCE_PROXY_FIP4_QWEN_MODEL", "").strip()
            or DEFAULT_QWEN_CODER_MODEL
        ),
    }


async def build_fip3_model_lane_packet(
    *,
    task: str,
    route_payload: dict[str, Any],
    fip1_context_packet: dict[str, Any] | None = None,
    fip2_research_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not fip3_model_lanes_enabled():
        return {
            "packet_version": FIP3_MODEL_PACKET_VERSION,
            "scope": "FIP-3 local non-coding model lanes only",
            "gemma": _model_lane_status("skipped", "fip3_model_lanes_disabled"),
            "hermes_critic": _model_lane_status("skipped", "fip3_model_lanes_disabled"),
            "hermes_verifier": _reserved_hermes_verifier(),
            "model_route_truth": {
                "local_ollama_only": True,
                "qwen_pre_coder_reasoning_used": False,
                "cloud_provider_used": False,
                "fallback_to_qwen_attempted": False,
            },
            "no_qwen_pre_coder_reasoning": True,
        }

    models = configured_fip3_models()
    base_url = _ollama_base_url()
    inventory = await _ollama_inventory(base_url)
    names = set(inventory.get("model_names", []))
    research_packet_hash = str((fip2_research_packet or {}).get("research_packet_hash") or "")
    packet: dict[str, Any] = {
        "packet_version": FIP3_MODEL_PACKET_VERSION,
        "scope": "FIP-3 local non-coding model lanes only",
        "ollama_base_url": base_url,
        "ollama_inventory_status": inventory.get("status", "failed"),
        "ollama_inventory_models": inventory.get("model_names", []),
        "research_packet_hash_received": research_packet_hash,
        "research_packet_included_in_model_context": bool(research_packet_hash),
        "hermes_verifier": _reserved_hermes_verifier(models["hermes"]),
        "model_route_truth": {
            "local_ollama_only": True,
            "qwen_pre_coder_reasoning_used": False,
            "cloud_provider_used": False,
            "fallback_to_qwen_attempted": False,
            "qwen_coder_activated": False,
        },
        "no_qwen_pre_coder_reasoning": True,
    }
    if inventory.get("status") != "used":
        blocked = _model_lane_status(
            "blocked",
            "ollama_inventory_unavailable",
            model="",
            provider_errors=inventory.get("provider_errors", []),
            fix_command=f"Start Ollama and verify {base_url}/api/tags from the source-server runtime checkout.",
        )
        packet["gemma"] = {**blocked, "model": models["gemma"]}
        packet["hermes_critic"] = {**blocked, "model": models["hermes"]}
        packet["fip3_model_packet_hash"] = _json_hash(packet)
        return packet

    packet["gemma"] = await _run_gemma_lane(
        base_url=base_url,
        model=models["gemma"],
        inventory_names=names,
        task=task,
        route_payload=route_payload,
        fip1_context_packet=fip1_context_packet or {},
        fip2_research_packet=fip2_research_packet or {},
    )
    packet["gemma"]["research_packet_hash_received"] = research_packet_hash
    packet["hermes_critic"] = await _run_hermes_critic_lane(
        base_url=base_url,
        model=models["hermes"],
        inventory_names=names,
        task=task,
        route_payload=route_payload,
        gemma_packet=packet["gemma"],
        fip1_context_packet=fip1_context_packet or {},
        fip2_research_packet=fip2_research_packet or {},
    )
    packet["hermes_critic"]["research_packet_hash_received"] = research_packet_hash
    packet["fip3_model_packet_hash"] = _json_hash(packet)
    return packet


async def run_qwen_coder_lane(
    *,
    task: str,
    route_payload: dict[str, Any],
    gemma_packet: dict[str, Any],
    hermes_packet: dict[str, Any],
    fip1_context_packet: dict[str, Any] | None = None,
    fip2_research_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    models = configured_fip3_models()
    base_url = _ollama_base_url()
    inventory = await _ollama_inventory(base_url)
    model = models["qwen_coder"]
    if inventory.get("status") != "used":
        return _model_lane_status(
            "blocked",
            "ollama_inventory_unavailable_for_qwen_coder",
            model=model,
            activated=False,
            live_invocation=False,
            real_output=False,
            provider_errors=inventory.get("provider_errors", []),
        )
    names = set(inventory.get("model_names", []))
    missing = _missing_model_status(model, names, lane="qwen")
    if missing:
        return {
            **missing,
            "activated": False,
            "live_invocation": False,
            "real_output": False,
        }
    prompt = _qwen_coder_prompt(
        task=task,
        route_payload=route_payload,
        gemma_packet=gemma_packet,
        hermes_packet=hermes_packet,
        fip1_context_packet=fip1_context_packet or {},
        fip2_research_packet=fip2_research_packet or {},
    )
    result = await _call_json_lane(
        base_url=base_url,
        model=model,
        prompt=prompt,
        schema_validator=_normalize_qwen_coder_output,
    )
    return {
        **result,
        "activated": True,
        "live_invocation": result.get("status") == "used",
        "real_output": result.get("status") == "used" and bool(result.get("output_hash")),
        "upstream_received": {
            "gemma_output_hash": gemma_packet.get("output_hash", ""),
            "hermes_output_hash": hermes_packet.get("output_hash", ""),
            "research_packet_hash": (fip2_research_packet or {}).get("research_packet_hash", ""),
        },
    }


def fip3_lane_packet_has_qwen_fallback(packet: dict[str, Any]) -> bool:
    truth = packet.get("model_route_truth") if isinstance(packet.get("model_route_truth"), dict) else {}
    gemma = packet.get("gemma") if isinstance(packet.get("gemma"), dict) else {}
    hermes = packet.get("hermes_critic") if isinstance(packet.get("hermes_critic"), dict) else {}
    models = [str(gemma.get("model") or ""), str(hermes.get("model") or "")]
    return (
        bool(truth.get("fallback_to_qwen_attempted"))
        or bool(truth.get("qwen_pre_coder_reasoning_used"))
        or any("qwen" in model.lower() for model in models if model)
    )


async def _run_gemma_lane(
    *,
    base_url: str,
    model: str,
    inventory_names: set[str],
    task: str,
    route_payload: dict[str, Any],
    fip1_context_packet: dict[str, Any],
    fip2_research_packet: dict[str, Any],
) -> dict[str, Any]:
    if "qwen" in model.lower():
        return _model_lane_status(
            "failed",
            "qwen_model_disallowed_for_fip3_gemma_precoder_reasoning",
            model=model,
            provider_errors=["qwen_fallback_disallowed"],
        )
    missing = _missing_model_status(model, inventory_names, lane="gemma")
    if missing:
        return missing
    prompt = _gemma_prompt(
        task=task,
        route_payload=route_payload,
        fip1_context_packet=fip1_context_packet,
        fip2_research_packet=fip2_research_packet,
    )
    return await _call_json_lane(
        base_url=base_url,
        model=model,
        prompt=prompt,
        schema_validator=_normalize_gemma_output,
    )


async def _run_hermes_critic_lane(
    *,
    base_url: str,
    model: str,
    inventory_names: set[str],
    task: str,
    route_payload: dict[str, Any],
    gemma_packet: dict[str, Any],
    fip1_context_packet: dict[str, Any],
    fip2_research_packet: dict[str, Any],
) -> dict[str, Any]:
    if "qwen" in model.lower():
        return _model_lane_status(
            "failed",
            "qwen_model_disallowed_for_fip3_hermes_precoder_reasoning",
            model=model,
            provider_errors=["qwen_fallback_disallowed"],
        )
    missing = _missing_model_status(model, inventory_names, lane="hermes")
    if missing:
        return missing
    prompt = _hermes_prompt(
        task=task,
        route_payload=route_payload,
        gemma_packet=gemma_packet,
        fip1_context_packet=fip1_context_packet,
        fip2_research_packet=fip2_research_packet,
    )
    return await _call_json_lane(
        base_url=base_url,
        model=model,
        prompt=prompt,
        schema_validator=_normalize_hermes_output,
    )


async def _ollama_inventory(base_url: str) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=_timeout_seconds()) as client:
            response = await client.get(f"{base_url.rstrip('/')}/api/tags")
            response.raise_for_status()
            payload = response.json()
    except httpx.TimeoutException as error:
        return {
            "status": "blocked",
            "reason": "ollama_inventory_timeout",
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "provider_errors": [f"{type(error).__name__}: {error}"],
        }
    except (httpx.HTTPError, ValueError) as error:
        return {
            "status": "blocked",
            "reason": "ollama_inventory_unavailable",
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "provider_errors": [f"{type(error).__name__}: {error}"],
        }
    models = payload.get("models") if isinstance(payload, dict) else []
    names = [
        str(item.get("name") or item.get("model") or "")
        for item in models
        if isinstance(item, dict) and str(item.get("name") or item.get("model") or "").strip()
    ]
    return {
        "status": "used",
        "reason": "ollama_inventory_read",
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "model_names": names,
    }


async def _call_json_lane(
    *,
    base_url: str,
    model: str,
    prompt: str,
    schema_validator: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    prompt_hash = _json_hash(prompt)
    request_payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "keep_alive": os.environ.get("SOURCE_PROXY_FIP3_MODEL_KEEP_ALIVE", "10m"),
        "options": {
            "temperature": 0,
            "num_predict": int(os.environ.get("SOURCE_PROXY_FIP3_MODEL_NUM_PREDICT", "512")),
            "num_ctx": int(os.environ.get("SOURCE_PROXY_FIP3_MODEL_NUM_CTX", "8192")),
        },
    }
    try:
        async with httpx.AsyncClient(timeout=_timeout_seconds()) as client:
            response = await client.post(f"{base_url.rstrip('/')}/api/generate", json=request_payload)
            response.raise_for_status()
            payload = response.json()
    except httpx.TimeoutException as error:
        return _model_lane_status(
            "failed",
            "local_ollama_model_timeout",
            model=model,
            prompt_hash=prompt_hash,
            attempt_count=1,
            timeout_seconds=_timeout_seconds(),
            latency_ms=int((time.perf_counter() - started) * 1000),
            provider_errors=[f"{type(error).__name__}: {error}"],
        )
    except (httpx.HTTPError, ValueError) as error:
        return _model_lane_status(
            "failed",
            "local_ollama_model_call_failed",
            model=model,
            prompt_hash=prompt_hash,
            attempt_count=1,
            timeout_seconds=_timeout_seconds(),
            latency_ms=int((time.perf_counter() - started) * 1000),
            provider_errors=[f"{type(error).__name__}: {error}"],
        )
    raw = str(payload.get("response") or payload.get("thinking") or "") if isinstance(payload, dict) else ""
    output_hash = _json_hash(raw) if raw else ""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as error:
        return _model_lane_status(
            "failed",
            "local_model_output_not_json",
            model=model,
            prompt_hash=prompt_hash,
            output_hash=output_hash,
            output_schema_valid=False,
            attempt_count=1,
            timeout_seconds=_timeout_seconds(),
            latency_ms=int((time.perf_counter() - started) * 1000),
            provider_errors=[f"JSONDecodeError: {error}"],
        )
    normalized, schema_errors = schema_validator(parsed)
    status = "used" if not schema_errors else "failed"
    reason = "local_ollama_model_json_schema_valid" if not schema_errors else "local_model_output_schema_invalid"
    return {
        **_model_lane_status(
            status,
            reason,
            model=model,
            prompt_hash=prompt_hash,
            output_hash=output_hash,
            output_schema_valid=not schema_errors,
            attempt_count=1,
            timeout_seconds=_timeout_seconds(),
            latency_ms=int((time.perf_counter() - started) * 1000),
            provider_errors=schema_errors,
        ),
        **normalized,
    }


def _normalize_gemma_output(parsed: Any) -> tuple[dict[str, Any], list[str]]:
    data = parsed if isinstance(parsed, dict) else {}
    errors: list[str] = []
    intent = _string_field(data, "intent", errors)
    normalized_spec = _string_field(data, "normalized_spec", errors)
    context_needed = data.get("context_needed")
    if not isinstance(context_needed, bool):
        errors.append("context_needed must be boolean")
        context_needed = False
    search_needed_review = data.get("search_needed_review")
    if not isinstance(search_needed_review, bool):
        errors.append("search_needed_review must be boolean")
        search_needed_review = False
    criteria = _gemma_acceptance_criteria(data, errors)
    return {
        "intent": intent,
        "normalized_spec": normalized_spec,
        "context_needed": bool(context_needed),
        "search_needed_review": bool(search_needed_review),
        "acceptance_criteria": criteria,
    }, errors


def _normalize_hermes_output(parsed: Any) -> tuple[dict[str, Any], list[str]]:
    data = parsed if isinstance(parsed, dict) else {}
    errors: list[str] = []
    return {
        "ambiguities": _string_list_field(data, "ambiguities", errors),
        "risks": _string_list_field(data, "risks", errors),
        "requirement_conflicts": _string_list_field(data, "requirement_conflicts", errors),
        "pre_coder_notes": _string_list_field(data, "pre_coder_notes", errors),
    }, errors


def _normalize_qwen_coder_output(parsed: Any) -> tuple[dict[str, Any], list[str]]:
    data = parsed if isinstance(parsed, dict) else {}
    errors: list[str] = []
    return {
        "implementation_summary": _string_field(data, "implementation_summary", errors),
        "proposed_action": _string_field(data, "proposed_action", errors),
        "acceptance_notes": _string_list_field(data, "acceptance_notes", errors),
        "risk_notes": _string_list_field(data, "risk_notes", errors),
    }, errors


def _gemma_acceptance_criteria(data: dict[str, Any], errors: list[str]) -> list[str]:
    value = data.get("acceptance_criteria")
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if not isinstance(value, list):
        errors.append("acceptance_criteria must be a list of strings")
        return []
    criteria: list[str] = []
    for item in value:
        if isinstance(item, str):
            stripped = item.strip()
            if stripped:
                criteria.append(stripped)
            continue
        if isinstance(item, dict):
            for key in ("criterion", "criteria", "text", "description", "name"):
                nested = item.get(key)
                if isinstance(nested, str) and nested.strip():
                    criteria.append(nested.strip())
                    break
            continue
        if item is not None:
            stripped = str(item).strip()
            if stripped:
                criteria.append(stripped)
    return criteria


def _string_field(data: dict[str, Any], key: str, errors: list[str]) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{key} must be a non-empty string")
        return ""
    return value.strip()


def _string_list_field(data: dict[str, Any], key: str, errors: list[str]) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        errors.append(f"{key} must be a list of strings")
        return []
    return [item.strip() for item in value if item.strip()]


def _missing_model_status(model: str, inventory_names: set[str], *, lane: str) -> dict[str, Any] | None:
    if model in inventory_names:
        return None
    family = {"gemma": "Gemma", "hermes": "Hermes", "qwen": "Qwen"}.get(lane, lane.title())
    return _model_lane_status(
        "blocked",
        f"{lane}_model_missing_from_local_ollama_inventory",
        model=model,
        output_schema_valid=False,
        provider_errors=[f"{model} not present in local Ollama inventory"],
        fix_command=f"ssh source@10.0.0.186 'ollama pull {model}' # then restart npm run proxy:https:lan",
        config_target=f"SOURCE_PROXY_FIP3_{family.upper()}_MODEL",
    )


def _gemma_prompt(
    *,
    task: str,
    route_payload: dict[str, Any],
    fip1_context_packet: dict[str, Any],
    fip2_research_packet: dict[str, Any],
) -> str:
    compact = {
        "task": task,
        "route": _compact_json(route_payload),
        "fip1_context_status": _compact_json(fip1_context_packet.get("source_status", {})),
        "fip2_research": {
            "search_needed": bool(fip2_research_packet.get("search_needed")),
            "research_packet_hash": fip2_research_packet.get("research_packet_hash", ""),
            "research_sources_count": len(fip2_research_packet.get("research_sources", []) or []),
        },
    }
    return (
        "You are the FIP-3 Gemma local advisory lane. Normalize the messy prompt and shape a pre-coder spec. "
        "Do not write code. Do not call tools. Return only JSON with keys: intent string, normalized_spec string, "
        "context_needed boolean, search_needed_review boolean, acceptance_criteria array of strings.\n\n"
        f"Input:\n{json.dumps(compact, sort_keys=True)}"
    )


def _hermes_prompt(
    *,
    task: str,
    route_payload: dict[str, Any],
    gemma_packet: dict[str, Any],
    fip1_context_packet: dict[str, Any],
    fip2_research_packet: dict[str, Any],
) -> str:
    compact = {
        "task": task,
        "route": _compact_json(route_payload),
        "gemma": {
            "status": gemma_packet.get("status"),
            "intent": gemma_packet.get("intent", ""),
            "normalized_spec": gemma_packet.get("normalized_spec", ""),
            "acceptance_criteria": gemma_packet.get("acceptance_criteria", []),
        },
        "fip1_context_status": _compact_json(fip1_context_packet.get("source_status", {})),
        "fip2_research": {
            "search_needed": bool(fip2_research_packet.get("search_needed")),
            "research_packet_hash": fip2_research_packet.get("research_packet_hash", ""),
            "research_sources_count": len(fip2_research_packet.get("research_sources", []) or []),
        },
    }
    return (
        "You are the FIP-3 Hermes local critic lane. Critique the pre-coder packet for ambiguity, risk, and conflicts. "
        "Do not verify final code. Do not write code. Return only JSON with keys: ambiguities array of strings, risks "
        "array of strings, requirement_conflicts array of strings, pre_coder_notes array of strings.\n\n"
        f"Input:\n{json.dumps(compact, sort_keys=True)}"
    )


def _qwen_coder_prompt(
    *,
    task: str,
    route_payload: dict[str, Any],
    gemma_packet: dict[str, Any],
    hermes_packet: dict[str, Any],
    fip1_context_packet: dict[str, Any],
    fip2_research_packet: dict[str, Any],
) -> str:
    compact = {
        "task": task,
        "route": _compact_json(route_payload),
        "gemma": {
            "status": gemma_packet.get("status"),
            "intent": gemma_packet.get("intent", ""),
            "normalized_spec": gemma_packet.get("normalized_spec", ""),
            "acceptance_criteria": gemma_packet.get("acceptance_criteria", []),
        },
        "hermes": {
            "status": hermes_packet.get("status"),
            "risks": hermes_packet.get("risks", []),
            "pre_coder_notes": hermes_packet.get("pre_coder_notes", []),
        },
        "fip1_context_status": _compact_json(fip1_context_packet.get("source_status", {})),
        "fip2_research": {
            "search_needed": bool(fip2_research_packet.get("search_needed")),
            "research_packet_hash": fip2_research_packet.get("research_packet_hash", ""),
            "research_sources_count": len(fip2_research_packet.get("research_sources", []) or []),
        },
    }
    return (
        "You are the Plan 2 Qwen local coder lane. This bounded proof must not edit files or call tools. "
        "Use the upstream Gemma/Hermes/research state and return only JSON with keys: implementation_summary "
        "string, proposed_action string, acceptance_notes array of strings, risk_notes array of strings. "
        "The proposed_action should describe the next safe coding action, not perform it.\n\n"
        f"Input:\n{json.dumps(compact, sort_keys=True)}"
    )


def _reserved_hermes_verifier(model: str = "") -> dict[str, Any]:
    return {
        "status": "skipped",
        "reason": "hermes_verifier_role_reserved_for_future_fip5_not_authoritative",
        "model": model,
        "role_reserved": True,
        "authority": "future_fip5_necessary_not_sufficient",
    }


def _model_lane_status(status: str, reason: str, **extra: Any) -> dict[str, Any]:
    payload = {"status": status, "reason": reason, **extra}
    if is_failure_status(status):
        classification = classify_failure(
            status=status,
            reason=reason,
            source=str(extra.get("lane") or extra.get("source") or "model_lane"),
            provider_errors=extra.get("provider_errors", []),
        )
        payload["reason_code"] = classification.reason_code
        payload["failure_classification"] = serialize_failure_classification(classification)
    return payload


def _ollama_base_url() -> str:
    return (
        os.environ.get("SOURCE_PROXY_FIP3_OLLAMA_BASE_URL", "").strip()
        or os.environ.get("SOURCE_PROXY_OLLAMA_BASE_URL", "").strip()
        or os.environ.get("OLLAMA_BASE_URL", "").strip()
        or os.environ.get("OLLAMA_URL", "").strip()
        or DEFAULT_OLLAMA_BASE_URL
    ).rstrip("/")


def _timeout_seconds() -> float:
    return float(os.environ.get("SOURCE_PROXY_FIP3_MODEL_TIMEOUT_SECONDS", "180"))


def _compact_json(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str)) if value is not None else {}


def _json_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _qwen() -> ModelLane:
    return ModelLane(
        lane_id="qwen_local_coder",
        display_name="Qwen local coder",
        role="coding/action",
        status="active_primary_local_lane",
        allowed_uses=["disposable artifact generation", "bounded local coding/action lane"],
        disallowed_uses=["unreviewed autonomy", "provider/cloud escalation", "declaring product PASS without verifier evidence"],
        cost_class="local_compute",
        privacy_class="local",
        approval_required="normal_source_proxy_gate",
        evidence_required_for_promotion=["behavior retest results", "receipt evidence", "false-positive audit"],
        known_failure_modes=["malformed action JSON", "weak UI state changes", "missing behavior evidence"],
        promotion_status="primary_preserved_not_promoted_by_this_task",
    )


def _hermes() -> ModelLane:
    return ModelLane(
        lane_id="hermes_sidecar_verifier_preview",
        display_name="Hermes sidecar verifier preview",
        role="verifier/critic",
        status="preview_future_only",
        allowed_uses=["future advisory verifier", "risk and unknown extraction preview"],
        disallowed_uses=["file editing", "coding/action lane", "product PASS override", "hidden benchmark hints"],
        cost_class="local_compute_if_available",
        privacy_class="local_if_available_runtime_explicit_required",
        approval_required="future_operator_approval_before_live_call",
        evidence_required_for_promotion=["advisory accuracy samples", "false-positive audit", "no-PASS-inflation proof"],
        known_failure_modes=["overtrusting model claims", "critic hallucination", "missing browser evidence"],
        promotion_status="not_promoted_preview_only",
    )


def _gemma() -> ModelLane:
    return ModelLane(
        lane_id="gemma_sidecar_context_preview",
        display_name="Gemma sidecar context preview",
        role="intent/context/spec/verifier",
        status="preview_future_only",
        allowed_uses=["future intent interpretation", "context/spec packet preview", "acceptance criteria preview"],
        disallowed_uses=["file editing", "coding/action lane", "success declaration without evidence", "implicit cloud use"],
        cost_class="runtime_dependent_must_be_explicit",
        privacy_class="local_or_cloud_runtime_must_be_explicit",
        approval_required="future_operator_approval_before_live_call",
        evidence_required_for_promotion=["context quality samples", "privacy route proof", "behavior-verifier comparison"],
        known_failure_modes=["scope drift", "privacy ambiguity", "over-specific acceptance criteria"],
        promotion_status="not_promoted_preview_only",
    )


def _manual_handoff() -> ModelLane:
    return ModelLane(
        lane_id="manual_handoff",
        display_name="Manual handoff",
        role="handoff",
        status="active_fallback",
        allowed_uses=["operator review", "approval request", "handoff packet routing"],
        disallowed_uses=["automatic escalation", "silent provider use"],
        cost_class="human_review",
        privacy_class="operator_visible",
        approval_required="operator_review",
        evidence_required_for_promotion=["not applicable"],
        known_failure_modes=["insufficient evidence packet", "ambiguous next route"],
        promotion_status="fallback_active",
    )


def _cloud_future() -> ModelLane:
    return ModelLane(
        lane_id="cloud_or_api_route_future",
        display_name="Cloud/API route future",
        role="stronger external route",
        status="future_approval_only",
        allowed_uses=["future approved stronger-route comparison"],
        disallowed_uses=["default coding lane", "silent execution", "secret or private context without approval"],
        cost_class="paid_or_metered",
        privacy_class="external_cloud",
        approval_required="explicit_britton_approval_before_send",
        evidence_required_for_promotion=["spend approval", "privacy review", "comparative proof", "false-positive audit"],
        known_failure_modes=["cost overrun", "privacy leakage", "overreliance on self-report"],
        promotion_status="not_promoted_future_only",
    )
