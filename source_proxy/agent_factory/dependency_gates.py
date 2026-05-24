"""Dependency gate evaluation over supplied status data only."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from source_proxy.agent_factory.catalog import CatalogEntry
from source_proxy.agent_factory.contracts import DependencyGateReport

REQUIRED_GATES: tuple[str, ...] = (
    "proxy_apply_verify_receipt_ready",
    "cartographer_live_state_ready",
    "cartographer_approval_token_boundary_ready",
    "cartographer_safe_write_ready",
    "cartographer_verification_runner_ready",
    "cartographer_workflow_queue_ready",
    "cartographer_worker_coordination_ready",
    "proxy_cartographer_daily_driver_ready",
)

_KNOWN_GATES = set(REQUIRED_GATES)


def evaluate_dependency_gates(
    required_gates: tuple[str, ...],
    supplied_status: Mapping[str, Any],
) -> DependencyGateReport:
    """Return READY, BLOCKED, or CAUTION from supplied gate data only."""

    blocked_by: list[str] = []
    reason_codes: list[str] = []
    cautions: list[str] = []

    for gate in required_gates:
        if gate not in _KNOWN_GATES:
            blocked_by.append(gate)
            reason_codes.append(f"unknown_gate:{gate}")
            continue

        value = supplied_status.get(gate, False)
        normalized = _normalize_gate_value(value)
        if normalized == "ready":
            continue
        if normalized == "caution":
            cautions.append(gate)
            reason_codes.append(f"gate_caution:{gate}")
            continue
        blocked_by.append(gate)
        reason_codes.append(f"gate_not_ready:{gate}")

    if blocked_by:
        return DependencyGateReport(
            status="BLOCKED",
            reason_codes=tuple(reason_codes),
            blocked_by=tuple(blocked_by),
        )
    if cautions:
        return DependencyGateReport(
            status="CAUTION",
            reason_codes=tuple(reason_codes),
            blocked_by=tuple(cautions),
        )
    return DependencyGateReport(status="READY", reason_codes=("all_required_gates_ready",))


def evaluate_catalog_entry(
    entry: CatalogEntry,
    supplied_status: Mapping[str, Any],
) -> DependencyGateReport:
    return evaluate_dependency_gates(entry.dependency_gates, supplied_status)


def _normalize_gate_value(value: Any) -> str:
    if value is True:
        return "ready"
    if value is False or value is None:
        return "blocked"
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"ready", "true", "pass", "passed"}:
            return "ready"
        if normalized in {"caution", "partial", "unknown"}:
            return "caution"
        return "blocked"
    if isinstance(value, Mapping):
        return _normalize_gate_value(value.get("status"))
    return "blocked"
