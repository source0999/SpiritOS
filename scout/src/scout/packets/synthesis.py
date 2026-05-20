from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time
import uuid

import litellm
from pydantic import ValidationError

from scout.config import ScoutSettings, get_settings
from scout.debugger.content_injection import (
    filter_entity_tags_reserved_injection_signal,
)
from scout.packets.schema import IntelligencePacket, PacketProvenance
from scout.packets.untrusted_envelope import TIER_0_SYSTEM_PROMPT, wrap_untrusted

litellm.enable_json_schema_validation = True

# ── Model-authored keys (Ollama JSON path) ────────────────────────────────
# Everything else is Scout-owned and clobbers whatever the model hallucinated.
_MODEL_AUTHORED_KEYS: frozenset[str] = frozenset(
    {
        "schema_version",
        "entity_tags",
        "summary",
        "impact_analysis",
        "confidence_score",
        "graph_relations",
    }
)

_REQUIRED_MODEL_PACKET_KEYS: frozenset[str] = frozenset(
    {"summary", "impact_analysis", "confidence_score"}
)

_LOG_SNIP_LEN = 1500

_JSON_ELLIPSIS_LINE_RE = re.compile(r"^\s*\.\.\.\s*,?\s*$")
_JSON_TRAILING_COMMA_RE = re.compile(r",(\s*[\]}])")


class PacketSynthesisFatalModelError(RuntimeError):
    pass


class PacketSynthesisJsonInvalid(ValueError):
    """JSON from the model could not be turned into a valid IntelligencePacket."""

    def __init__(
        self,
        message: str,
        *,
        raw_model_output_truncated: str = "",
        parsed_model_truncated: str = "",
    ) -> None:
        super().__init__(message)
        self.raw_model_output_truncated = raw_model_output_truncated
        self.parsed_model_truncated = parsed_model_truncated


def _is_ollama_model(model: str) -> bool:
    return model.lower().startswith("ollama/")


def _truncate_for_log(text: str, limit: int = _LOG_SNIP_LEN) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}…(truncated,len={len(text)})"


def _normalize_llm_message_content(content: object) -> str:
    """Ollama / LiteLLM sometimes returns list-shaped content; coerce to a string."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for part in content:
            if isinstance(part, dict):
                if part.get("type") == "text" and part.get("text") is not None:
                    chunks.append(str(part["text"]))
                elif part.get("text") is not None:
                    chunks.append(str(part["text"]))
            elif isinstance(part, str):
                chunks.append(part)
        return "".join(chunks)
    return str(content)


def _strip_json_ellipsis_placeholders(content: str) -> str:
    lines = [
        line for line in content.splitlines() if not _JSON_ELLIPSIS_LINE_RE.match(line)
    ]
    without_ellipsis = "\n".join(lines)
    return _JSON_TRAILING_COMMA_RE.sub(r"\1", without_ellipsis)


def _extract_first_json_object(
    content: str, *, required_keys: frozenset[str] | None = None
) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    candidates = [stripped]
    stripped_without_placeholders = _strip_json_ellipsis_placeholders(stripped).strip()
    if stripped_without_placeholders != stripped:
        candidates.append(stripped_without_placeholders)

    decoder = json.JSONDecoder()
    decoded_any_object = False
    for candidate in candidates:
        for index, char in enumerate(candidate):
            if char != "{":
                continue
            try:
                obj, end = decoder.raw_decode(candidate[index:])
            except json.JSONDecodeError:
                continue
            decoded_any_object = True
            if required_keys and (
                not isinstance(obj, dict) or not required_keys.issubset(obj.keys())
            ):
                continue
            return candidate[index : index + end]
    if decoded_any_object and required_keys:
        raise PacketSynthesisJsonInvalid(
            "model response did not contain an IntelligencePacket JSON object"
        )
    raise PacketSynthesisJsonInvalid("model response did not contain a JSON object")


def _is_fatal_model_exception(exc: Exception) -> bool:
    message = str(exc).lower()
    fatal_markers = (
        "connection",
        "connect",
        "connection refused",
        "timed out",
        "timeout",
        "model runner",
        "runner has unexpectedly stopped",
        "server disconnected",
        "service unavailable",
    )
    return any(marker in message for marker in fatal_markers)


def _authoritative_packet_fields(
    *,
    raw_event_id: str,
    source_uri: str,
    extracted_artifact_path: Path | None,
    source_timestamp: datetime,
    settings: ScoutSettings,
    latency_ms: int,
) -> dict:
    return {
        "packet_id": str(uuid.uuid4()),
        "source_uri": source_uri,
        "timestamp": source_timestamp,
        "provenance": PacketProvenance(
            raw_event_id=raw_event_id,
            extracted_artifact_path=str(extracted_artifact_path)
            if extracted_artifact_path
            else None,
            llm_model=settings.litellm_model,
            llm_latency_ms=latency_ms,
            synthesized_at=datetime.now(timezone.utc),
        ),
        "status": "debugger_pending",
    }


def _model_authored_subset(model: dict) -> dict:
    """Strip junk keys; trusted envelope fields are applied afterward."""
    return {k: model[k] for k in _MODEL_AUTHORED_KEYS if k in model}


def _merge_trusted_into_packet_payload(
    model_payload: dict,
    *,
    raw_event_id: str,
    source_uri: str,
    extracted_artifact_path: Path | None,
    source_timestamp: datetime,
    settings: ScoutSettings,
    latency_ms: int,
) -> dict:
    merged = dict(model_payload)
    merged.update(
        _authoritative_packet_fields(
            raw_event_id=raw_event_id,
            source_uri=source_uri,
            extracted_artifact_path=extracted_artifact_path,
            source_timestamp=source_timestamp,
            settings=settings,
            latency_ms=latency_ms,
        )
    )
    return merged


def _ollama_json_instruction_preamble() -> str:
    return (
        "Return exactly one JSON object describing an IntelligencePacket. "
        "Do not include markdown fences, prose, or commentary outside the JSON object. "
        "Scout will overwrite packet_id, source_uri, timestamp, provenance, and status; "
        "you may omit those keys or supply placeholders.\n"
        "Include these keys: entity_tags (array of strings, topical tags only such as "
        "python, fastapi, security, docker), summary (string, at least 80 characters), "
        "impact_analysis (string, at least 80 characters), confidence_score "
        "(number from 0.0 to 1.0), graph_relations (array of at most 5 objects with "
        "source_entity, target_entity, relation_label). Do not use ellipses, trailing "
        "comments, omitted items, or placeholders. Never include reserved safety labels "
        "like injection_signal in entity_tags.\n\n"
    )


def _repair_user_message_parse(human_err: str) -> str:
    return (
        "Your previous reply was not usable JSON for an IntelligencePacket object. "
        "Return exactly one JSON object, no markdown fences, no surrounding prose.\n"
        f"Parse/schema issue: {human_err}\n"
        "Required keys: entity_tags (topical tags only, never injection_signal), "
        "summary (>=80 chars), impact_analysis (>=80 chars), "
        "confidence_score (0.0-1.0), graph_relations (array of at most 5 complete "
        "objects, may be empty)."
    )


def _repair_user_message_validation(exc: ValidationError) -> str:
    return (
        "Your previous JSON failed IntelligencePacket validation. "
        "Return exactly one corrected JSON object with the same output rules as before.\n"
        f"Validation errors:\n{exc}\n"
        "Ensure summary and impact_analysis are each at least 80 characters, "
        "confidence_score is a number between 0 and 1, graph_relations contains at "
        "most 5 complete relation objects, and all required keys are present."
    )


def _ollama_attempt_parse_merge_validate(
    raw_text: str,
    *,
    raw_event_id: str,
    source_uri: str,
    extracted_content: str,
    extracted_artifact_path: Path | None,
    source_timestamp: datetime,
    settings: ScoutSettings,
    latency_ms: int,
) -> IntelligencePacket:
    packet_json = _extract_first_json_object(
        raw_text, required_keys=_REQUIRED_MODEL_PACKET_KEYS
    )
    parsed = json.loads(packet_json)
    if not isinstance(parsed, dict):
        raise PacketSynthesisJsonInvalid("model JSON was not an object")
    model_subset = _model_authored_subset(parsed)
    merged = _merge_trusted_into_packet_payload(
        model_subset,
        raw_event_id=raw_event_id,
        source_uri=source_uri,
        extracted_artifact_path=extracted_artifact_path,
        source_timestamp=source_timestamp,
        settings=settings,
        latency_ms=latency_ms,
    )
    raw_tags = merged.get("entity_tags")
    tags_list = raw_tags if isinstance(raw_tags, list) else []
    merged["entity_tags"] = filter_entity_tags_reserved_injection_signal(
        tags_list, source_text=extracted_content
    )
    return IntelligencePacket.model_validate(merged)


def _synthesize_ollama_with_repairs(
    base_messages: list[dict],
    *,
    raw_event_id: str,
    source_uri: str,
    extracted_content: str,
    extracted_artifact_path: Path | None,
    source_timestamp: datetime,
    settings: ScoutSettings,
) -> IntelligencePacket:
    messages: list[dict] = list(base_messages)
    total_latency_ms = 0
    last_raw = ""
    last_parsed_fragment = ""

    for attempt in range(2):
        started = time.perf_counter()
        completion_kwargs: dict = {
            "model": settings.litellm_model,
            "messages": messages,
            "temperature": 0.1,
            "timeout": settings.litellm_timeout_seconds,
            "max_tokens": 1400,
        }
        if settings.litellm_api_base:
            completion_kwargs["api_base"] = settings.litellm_api_base
        try:
            response = litellm.completion(**completion_kwargs)
        except Exception as exc:
            if _is_fatal_model_exception(exc):
                raise PacketSynthesisFatalModelError(str(exc)) from exc
            raise
        total_latency_ms += int((time.perf_counter() - started) * 1000)
        last_raw = _normalize_llm_message_content(
            response.choices[0].message.content
        )

        try:
            return _ollama_attempt_parse_merge_validate(
                last_raw,
                raw_event_id=raw_event_id,
                source_uri=source_uri,
                extracted_content=extracted_content,
                extracted_artifact_path=extracted_artifact_path,
                source_timestamp=source_timestamp,
                settings=settings,
                latency_ms=total_latency_ms,
            )
        except json.JSONDecodeError as exc:
            try:
                last_parsed_fragment = _truncate_for_log(
                    _extract_first_json_object(last_raw)
                )
            except Exception:
                last_parsed_fragment = _truncate_for_log(last_raw)
            if attempt == 0:
                messages = messages + [
                    {"role": "assistant", "content": last_raw},
                    {"role": "user", "content": _repair_user_message_parse(str(exc))},
                ]
                continue
            raise PacketSynthesisJsonInvalid(
                str(exc),
                raw_model_output_truncated=_truncate_for_log(last_raw),
                parsed_model_truncated=_truncate_for_log(last_parsed_fragment),
            ) from exc
        except PacketSynthesisJsonInvalid as exc:
            try:
                last_parsed_fragment = _truncate_for_log(
                    _extract_first_json_object(last_raw)
                )
            except Exception:
                last_parsed_fragment = _truncate_for_log(last_raw)
            if attempt == 0:
                messages = messages + [
                    {"role": "assistant", "content": last_raw},
                    {
                        "role": "user",
                        "content": _repair_user_message_parse(str(exc)),
                    },
                ]
                continue
            raise PacketSynthesisJsonInvalid(
                str(exc),
                raw_model_output_truncated=_truncate_for_log(last_raw),
                parsed_model_truncated=_truncate_for_log(last_parsed_fragment),
            ) from exc
        except ValidationError as exc:
            try:
                last_parsed_fragment = _extract_first_json_object(last_raw)
            except Exception:
                last_parsed_fragment = _truncate_for_log(last_raw)
            if attempt == 0:
                messages = messages + [
                    {"role": "assistant", "content": last_raw},
                    {
                        "role": "user",
                        "content": _repair_user_message_validation(exc),
                    },
                ]
                continue
            raise PacketSynthesisJsonInvalid(
                str(exc),
                raw_model_output_truncated=_truncate_for_log(last_raw),
                parsed_model_truncated=_truncate_for_log(last_parsed_fragment),
            ) from exc


def synthesize_packet(
    *,
    raw_event_id: str,
    source_uri: str,
    extracted_content: str,
    extracted_artifact_path: Path | None,
    source_timestamp: datetime,
    settings: ScoutSettings | None = None,
) -> IntelligencePacket:
    settings = settings or get_settings()
    user_msg = wrap_untrusted(source_uri, extracted_content)
    if _is_ollama_model(settings.litellm_model):
        user_msg = f"{_ollama_json_instruction_preamble()}{user_msg}"
    messages = [
        {"role": "system", "content": TIER_0_SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    if _is_ollama_model(settings.litellm_model):
        return _synthesize_ollama_with_repairs(
            messages,
            raw_event_id=raw_event_id,
            source_uri=source_uri,
            extracted_content=extracted_content,
            extracted_artifact_path=extracted_artifact_path,
            source_timestamp=source_timestamp,
            settings=settings,
        )

    started = time.perf_counter()
    completion_kwargs = {
        "model": settings.litellm_model,
        "messages": messages,
        "temperature": 0.1,
        "timeout": settings.litellm_timeout_seconds,
        "max_tokens": 900,
        "response_format": IntelligencePacket,
    }
    if settings.litellm_api_base:
        completion_kwargs["api_base"] = settings.litellm_api_base
    try:
        response = litellm.completion(**completion_kwargs)
    except Exception as exc:
        if _is_fatal_model_exception(exc):
            raise PacketSynthesisFatalModelError(str(exc)) from exc
        raise
    latency_ms = int((time.perf_counter() - started) * 1000)
    raw_json = _normalize_llm_message_content(response.choices[0].message.content)

    try:
        packet = IntelligencePacket.model_validate_json(raw_json)
        packet_fields = _authoritative_packet_fields(
            raw_event_id=raw_event_id,
            source_uri=source_uri,
            extracted_artifact_path=extracted_artifact_path,
            source_timestamp=source_timestamp,
            settings=settings,
            latency_ms=latency_ms,
        )
        for field_name, value in packet_fields.items():
            setattr(packet, field_name, value)
        clean_tags = filter_entity_tags_reserved_injection_signal(
            packet.entity_tags, source_text=extracted_content
        )
        if clean_tags != list(packet.entity_tags):
            packet = packet.model_copy(update={"entity_tags": clean_tags})
        return packet
    except (json.JSONDecodeError, ValidationError) as exc:
        raise PacketSynthesisJsonInvalid(
            str(exc),
            raw_model_output_truncated=_truncate_for_log(str(raw_json)),
            parsed_model_truncated="",
        ) from exc
