"""Read-only readiness matrix for Agent Factory catalog entries."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from source_proxy.agent_factory.catalog import CatalogEntry, DEFAULT_AGENT_CATALOG
from source_proxy.agent_factory.contracts import ReadinessMatrixRow
from source_proxy.agent_factory.dependency_gates import evaluate_catalog_entry


def build_readiness_matrix(
    *,
    catalog: tuple[CatalogEntry, ...] = DEFAULT_AGENT_CATALOG,
    supplied_gate_status: Mapping[str, Any] | None = None,
) -> tuple[ReadinessMatrixRow, ...]:
    """Build deterministic readiness rows from supplied catalog and gates."""

    gate_status = supplied_gate_status or {}
    rows: list[ReadinessMatrixRow] = []
    for entry in catalog:
        gate_report = evaluate_catalog_entry(entry, gate_status)
        blocked_by = _blocked_by(entry, gate_report.blocked_by)
        status = gate_report.status
        if blocked_by:
            status = "BLOCKED"
        rows.append(
            ReadinessMatrixRow(
                plan=entry.plan,
                name=entry.name,
                status=status,
                allowed_mode=entry.allowed_mode,
                required_gates=entry.dependency_gates,
                blocked_by=blocked_by,
                reason_codes=_reason_codes(entry, gate_report.reason_codes, blocked_by),
            )
        )
    return tuple(rows)


def format_readiness_matrix(rows: tuple[ReadinessMatrixRow, ...]) -> tuple[str, ...]:
    """Format readiness rows without implying approval or permission."""

    lines = ("Plan | Status | Name | Blocked By",)
    for row in rows:
        blocked_by = ", ".join(row.blocked_by) if row.blocked_by else "none"
        lines += (f"{row.plan} | {row.status} | {row.name} | {blocked_by}",)
    lines += ("Permission: not granted", "Approval: not granted")
    return lines


def _blocked_by(
    entry: CatalogEntry,
    gate_blockers: tuple[str, ...],
) -> tuple[str, ...]:
    blockers: list[str] = []
    blockers.extend(gate_blockers)
    if not entry.can_run_now:
        blockers.extend(blocker for blocker in entry.blocked_by if blocker not in blockers)
    return tuple(blockers)


def _reason_codes(
    entry: CatalogEntry,
    gate_reasons: tuple[str, ...],
    blocked_by: tuple[str, ...],
) -> tuple[str, ...]:
    reasons: list[str] = list(gate_reasons)
    if blocked_by and reasons == ["all_required_gates_ready"]:
        reasons = []
    if blocked_by and not gate_reasons:
        reasons.append(f"catalog_blocked:{entry.plan}")
    elif blocked_by and not reasons:
        reasons.append(f"catalog_blocked:{entry.plan}")
    if not reasons:
        reasons.append("catalog_entry_ready")
    return tuple(reasons)
