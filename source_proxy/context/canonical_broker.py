"""Canonical context-source and downstream-consumption truth for Coding Proxy."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any


VALID_STATUSES = {"used", "available", "skipped", "blocked", "unavailable", "failed"}
CANONICAL_CONTEXT_CONSUMERS = (
    "planner",
    "coder",
    "reviewer",
    "verifier",
    "repair_loop",
    "final_receipt_builder",
)
ARCHITECT_REPOSITORY_CONTEXT_SOURCE = "architect_repository_context"
DERIVED_ARCHITECT_CONTEXT_AUTHORITY_SCHEMA = (
    "source-proxy-derived-architect-context-authority/v1"
)


def derived_architect_context_authority() -> dict[str, Any]:
    """Return the stable authority marker for plan-derived repository context.

    The packet itself is bound by the authoritative planner runtime output and
    semantic review.  This marker lets recovery identity distinguish that
    per-attempt derived material from stable upstream task/source material.
    """

    return {
        "schema_version": DERIVED_ARCHITECT_CONTEXT_AUTHORITY_SCHEMA,
        "kind": "derived_planner_output",
        "producer": "source_proxy.planning.architect",
        "separately_bound_by": [
            "planner_runtime_output",
            "adapter_plan_sha256",
            "semantic_review_binding",
        ],
    }


def is_derived_architect_context_source(source: Mapping[str, Any]) -> bool:
    """Recognize only the server-owned architect source eligible for projection."""

    authority = source.get("authority")
    return bool(
        str(source.get("source") or "") == ARCHITECT_REPOSITORY_CONTEXT_SOURCE
        and isinstance(authority, Mapping)
        and authority.get("schema_version")
        == DERIVED_ARCHITECT_CONTEXT_AUTHORITY_SCHEMA
        and authority.get("kind") == "derived_planner_output"
        and authority.get("producer") == "source_proxy.planning.architect"
        and list(authority.get("separately_bound_by") or [])
        == [
            "planner_runtime_output",
            "adapter_plan_sha256",
            "semantic_review_binding",
        ]
    )


def build_context_broker_report(
    sources: list[dict[str, Any]],
    *,
    downstream_consumers: Mapping[str, Any] | None = None,
    applicable_consumers: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build the only decision-bearing context report.

    ``downstream_consumers`` accepts the current lifecycle shape (consumer name to
    acknowledgement record) and the original Plan 3 compatibility shape (source
    name to bool).  Acknowledgements are evidence, not labels: a consumer only
    consumes the selected sources explicitly listed in its record.
    """

    raw_consumers = dict(downstream_consumers or {})
    requested_consumer_names = tuple(
        dict.fromkeys(
            str(name).strip()
            for name in (applicable_consumers or ())
            if str(name).strip()
        )
    )
    explicit_consumer_names = tuple(
        name for name in requested_consumer_names if name in CANONICAL_CONTEXT_CONSUMERS
    )
    acknowledged_consumer_names = tuple(
        str(name).strip()
        for name, value in raw_consumers.items()
        if (
            str(name).strip() in CANONICAL_CONTEXT_CONSUMERS
            and isinstance(value, Mapping)
            and value.get("applicable") is not False
        )
    )
    consumer_names = tuple(
        dict.fromkeys((*explicit_consumer_names, *acknowledged_consumer_names))
    )
    acknowledgements = _normalize_consumer_acknowledgements(
        raw_consumers,
        applicable_consumers=consumer_names,
    )
    legacy_source_consumption = {
        str(name): value is True
        for name, value in raw_consumers.items()
        if isinstance(value, bool) and str(name) not in CANONICAL_CONTEXT_CONSUMERS
    }

    normalized: list[dict[str, Any]] = []
    blockers: list[str] = [
        f"unsupported_context_consumer:{str(name).strip()}"
        for name, value in raw_consumers.items()
        if (
            isinstance(value, Mapping)
            and str(name).strip() not in CANONICAL_CONTEXT_CONSUMERS
        )
    ]
    blockers.extend(
        f"unsupported_context_consumer:{name}"
        for name in requested_consumer_names
        if name not in CANONICAL_CONTEXT_CONSUMERS
    )
    blockers.extend(
        f"invalid_context_acknowledgement:{str(name).strip()}"
        for name, value in raw_consumers.items()
        if str(name).strip() in CANONICAL_CONTEXT_CONSUMERS
        and not isinstance(value, Mapping)
    )
    raw_source_names = [
        str((raw_source or {}).get("source") or "unknown").strip() or "unknown"
        for raw_source in sources
    ]
    duplicate_source_names = {
        name for name in raw_source_names if raw_source_names.count(name) > 1
    }
    blockers.extend(
        f"duplicate_context_source:{name}" for name in sorted(duplicate_source_names)
    )
    known_source_names = set(raw_source_names)
    for consumer, acknowledgement in acknowledgements.items():
        if acknowledgement.get("acknowledged_claimed") and not str(
            acknowledgement.get("evidence") or ""
        ).strip():
            blockers.append(f"context_acknowledgement_missing_evidence:{consumer}")
        if acknowledgement.get("acknowledged_claimed") and not acknowledgement.get(
            "sources"
        ):
            blockers.append(f"context_acknowledgement_missing_sources:{consumer}")
        blockers.extend(
            f"context_acknowledges_unknown_source:{consumer}:{source_name}"
            for source_name in acknowledgement.get("sources", [])
            if source_name not in known_source_names
        )
    for raw_source in sources:
        source = dict(raw_source or {})
        name = str(source.get("source") or "unknown").strip() or "unknown"
        status = str(source.get("status") or "unavailable").strip().lower()
        reason = str(source.get("reason") or "status_not_reported").strip()
        if status not in VALID_STATUSES:
            status = "unavailable"
            reason = "invalid_context_status"

        considered = source.get("considered") is not False
        required = source.get("required") is True
        selected = source.get("selected") is True
        included = (
            source.get("included") is True
            or source.get("included_in_packet") is True
        )
        per_consumer = {
            consumer: _source_acknowledgement(
                acknowledgements.get(consumer, {}),
                source=name,
            )
            for consumer in consumer_names
        }
        acknowledged_by = [
            consumer
            for consumer, acknowledgement in per_consumer.items()
            if acknowledgement["applicable"] and acknowledgement["acknowledged"]
        ]
        missing_acknowledgements = [
            consumer
            for consumer, acknowledgement in per_consumer.items()
            if acknowledgement["applicable"] and not acknowledgement["acknowledged"]
        ]
        applicable_acknowledgements = [
            acknowledgement
            for acknowledgement in per_consumer.values()
            if acknowledgement["applicable"]
        ]
        declared_consumed = source.get("consumed") is True
        legacy_consumption_claim = legacy_source_consumption.get(name) is True
        consumed = bool(
            selected
            and included
            and applicable_acknowledgements
            and not missing_acknowledgements
        )
        skip_or_block_reason = (
            reason if status in {"skipped", "blocked", "unavailable", "failed"} else ""
        )

        if required:
            if not considered:
                blockers.append(f"required_context_unconsidered:{name}")
            elif status not in {"used", "available"}:
                blockers.append(f"required_context_{status}:{name}")
            elif not selected:
                blockers.append(f"required_context_unselected:{name}")
            elif not included:
                blockers.append(f"required_context_unincluded:{name}")
            elif missing_acknowledgements:
                blockers.extend(
                    f"required_context_unacknowledged:{name}:{consumer}"
                    for consumer in missing_acknowledgements
                )
            elif not consumed:
                blockers.append(f"required_context_unconsumed:{name}")

        if selected:
            if not considered:
                blockers.append(f"selected_context_unconsidered:{name}")
            if status not in {"used", "available"}:
                blockers.append(f"selected_context_{status}:{name}")
            if not included:
                blockers.append(f"selected_context_unincluded:{name}")
            elif not applicable_acknowledgements:
                blockers.append(f"selected_context_no_applicable_consumer:{name}")
            elif missing_acknowledgements:
                blockers.extend(
                    f"selected_context_unacknowledged:{name}:{consumer}"
                    for consumer in missing_acknowledgements
                )
            elif not consumed:
                blockers.append(f"selected_context_unconsumed:{name}")
        elif included:
            blockers.append(f"context_included_unselected:{name}")

        if (declared_consumed or legacy_consumption_claim) and not consumed:
            blockers.append(f"context_consumption_claim_unproven:{name}")

        normalized.append(
            {
                "source": name,
                "considered": considered,
                "status": status,
                "reason": reason,
                "skipped_or_blocked_reason": skip_or_block_reason,
                "required": required,
                "requirement": "required" if required else "optional",
                "selected": selected,
                "included": included,
                "included_in_packet": included,
                "consumed": consumed,
                "consumed_claimed": declared_consumed,
                "legacy_consumption_claim": legacy_consumption_claim,
                "acknowledged_by": acknowledged_by,
                "missing_acknowledgements": missing_acknowledgements,
                "downstream_acknowledgements": per_consumer,
                "packet": source.get("packet") if isinstance(source.get("packet"), dict) else {},
                "diagnostics": (
                    source.get("diagnostics")
                    if isinstance(source.get("diagnostics"), dict)
                    else {}
                ),
                "authority": (
                    source.get("authority")
                    if isinstance(source.get("authority"), dict)
                    else {}
                ),
            }
        )

    blockers = list(dict.fromkeys(blockers))
    report: dict[str, Any] = {
        "schema_version": 2,
        "canonical": True,
        "sources_considered": normalized,
        "source_status": {item["source"]: item["status"] for item in normalized},
        "selected_sources": [item["source"] for item in normalized if item["selected"]],
        "included_sources": [item["source"] for item in normalized if item["included"]],
        "consumed_sources": [item["source"] for item in normalized if item["consumed"]],
        "applicable_consumers": list(consumer_names),
        "downstream_acknowledgements": acknowledgements,
        "required_context_blockers": blockers,
        "go_eligible": not blockers,
        "verdict": "GO_ELIGIBLE" if not blockers else "NO_GO_REQUIRED_CONTEXT",
    }
    report["canonical_report_hash"] = _report_hash(report)
    return report


def acknowledge_context_consumer(
    report: Mapping[str, Any],
    *,
    consumer: str,
    evidence: str,
    source_names: Iterable[str] | None = None,
    applicable: bool = True,
    reason: str = "",
) -> dict[str, Any]:
    """Return a rebuilt canonical report with one real lifecycle acknowledgement."""

    consumer_name = str(consumer).strip()
    if consumer_name not in CANONICAL_CONTEXT_CONSUMERS:
        raise ValueError(f"unsupported_context_consumer:{consumer_name or 'empty'}")
    sources: list[dict[str, Any]] = []
    for item in report.get("sources_considered", []):
        if not isinstance(item, dict):
            continue
        source = dict(item)
        # ``consumed`` on a broker report is derived lifecycle truth.  Do not
        # feed it back as a caller claim when rebuilding the report.
        source["consumed"] = source.get("consumed_claimed") is True
        sources.append(source)
    selected = [
        str(item.get("source") or "")
        for item in sources
        if item.get("selected") is True and item.get("included") is True
    ]
    acknowledged_sources = list(
        dict.fromkeys(
            str(name).strip()
            for name in (source_names if source_names is not None else selected)
            if str(name).strip()
        )
    )
    acknowledgements = {
        str(name): dict(value)
        for name, value in dict(report.get("downstream_acknowledgements") or {}).items()
        if isinstance(value, Mapping)
    }
    acknowledgements[consumer_name] = {
        "applicable": bool(applicable),
        "acknowledged": bool(applicable and acknowledged_sources and evidence.strip()),
        "sources": acknowledged_sources,
        "evidence": evidence.strip(),
        "reason": reason.strip(),
    }
    applicable_consumers = [
        str(name)
        for name in report.get("applicable_consumers", [])
        if str(name).strip()
    ]
    if applicable and consumer_name not in applicable_consumers:
        applicable_consumers.append(consumer_name)
    if not applicable:
        applicable_consumers = [
            name for name in applicable_consumers if name != consumer_name
        ]
    rebuilt = build_context_broker_report(
        sources,
        downstream_consumers=acknowledgements,
        applicable_consumers=applicable_consumers,
    )
    # Runtime correlation fields are intentionally outside the decision-bearing
    # canonical hash, but must survive progressive lifecycle acknowledgements.
    for field_name in ("task_id", "trace_id", "explicit_target", "finalized"):
        if field_name in report:
            rebuilt[field_name] = report[field_name]
    return rebuilt


def extend_context_broker_sources(
    report: Mapping[str, Any],
    sources_to_add: Iterable[Mapping[str, Any]],
    *,
    planner_evidence: str,
) -> dict[str, Any]:
    """Add late-bound planner sources without creating a second truth system.

    Architect-owned context is not available when the initial route packet is
    assembled.  Generic Coder execution calls this helper after planning and
    before any model request.  Existing lifecycle acknowledgements are kept,
    while the planner acknowledgement is deliberately rebuilt to cover every
    selected source in the expanded report.
    """

    additions = [dict(item) for item in sources_to_add if isinstance(item, Mapping)]
    addition_names = {
        str(item.get("source") or "").strip()
        for item in additions
        if str(item.get("source") or "").strip()
    }
    sources: list[dict[str, Any]] = []
    for item in report.get("sources_considered", []):
        if not isinstance(item, Mapping):
            continue
        source = dict(item)
        if str(source.get("source") or "").strip() in addition_names:
            continue
        source["consumed"] = source.get("consumed_claimed") is True
        sources.append(source)
    sources.extend(additions)

    selected_names = [
        str(item.get("source") or "")
        for item in sources
        if item.get("selected") is True and item.get("included") is True
    ]
    acknowledgements = {
        str(name): dict(value)
        for name, value in dict(report.get("downstream_acknowledgements") or {}).items()
        if isinstance(value, Mapping)
    }
    acknowledgements["planner"] = {
        "applicable": True,
        "acknowledged": bool(selected_names and planner_evidence.strip()),
        "sources": selected_names,
        "evidence": planner_evidence.strip(),
        "reason": "planner_selected_and_brokered_late_bound_architect_context",
    }
    applicable_consumers = [
        str(name)
        for name in report.get("applicable_consumers", [])
        if str(name).strip()
    ]
    if "planner" not in applicable_consumers:
        applicable_consumers.insert(0, "planner")
    rebuilt = build_context_broker_report(
        sources,
        downstream_consumers=acknowledgements,
        applicable_consumers=applicable_consumers,
    )
    for field_name in ("task_id", "trace_id", "explicit_target", "finalized"):
        if field_name in report:
            rebuilt[field_name] = report[field_name]
    return rebuilt


def render_context_broker_prompt(report: Mapping[str, Any], *, max_chars: int = 12000) -> str:
    """Render only broker-selected packets for downstream model execution."""

    rendered: list[str] = []
    for source in report.get("sources_considered", []):
        if not isinstance(source, Mapping) or source.get("selected") is not True:
            continue
        packet = source.get("packet") if isinstance(source.get("packet"), Mapping) else {}
        packet_text = json.dumps(packet, sort_keys=True, default=str)
        rendered.append(
            f"[{source.get('source')} packet; required={bool(source.get('required'))}] "
            f"{packet_text[:2400]}"
        )
    return "\n".join(rendered)[:max_chars]


def _normalize_consumer_acknowledgements(
    values: Mapping[str, Any],
    *,
    applicable_consumers: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for consumer in dict.fromkeys((*CANONICAL_CONTEXT_CONSUMERS, *applicable_consumers)):
        value = values.get(consumer)
        if isinstance(value, Mapping):
            sources = [
                str(item).strip()
                for item in value.get("sources", [])
                if str(item).strip()
            ]
            applicable = consumer in applicable_consumers and value.get("applicable") is not False
            evidence = str(value.get("evidence") or "").strip()
            acknowledged_claimed = value.get("acknowledged") is True
            normalized[consumer] = {
                "applicable": applicable,
                "acknowledged": bool(
                    acknowledged_claimed and applicable and sources and evidence
                ),
                "acknowledged_claimed": acknowledged_claimed,
                "sources": list(dict.fromkeys(sources)),
                "evidence": evidence,
                "reason": str(value.get("reason") or ""),
            }
        else:
            normalized[consumer] = {
                "applicable": consumer in applicable_consumers,
                "acknowledged": False,
                "acknowledged_claimed": False,
                "sources": [],
                "evidence": "",
                "reason": "consumer_acknowledgement_missing"
                if consumer in applicable_consumers
                else "consumer_not_yet_applicable",
            }
    return normalized


def _source_acknowledgement(
    acknowledgement: Mapping[str, Any],
    *,
    source: str,
) -> dict[str, Any]:
    applicable = acknowledgement.get("applicable") is True
    sources = {
        str(item)
        for item in acknowledgement.get("sources", [])
        if str(item).strip()
    }
    acknowledged = bool(
        applicable
        and acknowledgement.get("acknowledged") is True
        and source in sources
        and str(acknowledgement.get("evidence") or "").strip()
    )
    return {
        "applicable": applicable,
        "acknowledged": acknowledged,
        "evidence": str(acknowledgement.get("evidence") or ""),
        "reason": str(acknowledgement.get("reason") or ""),
    }


def _report_hash(report: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()
