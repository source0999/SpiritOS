"""Final read-only readiness decision packet for Agent Factory."""

from __future__ import annotations

from dataclasses import dataclass, field

from source_proxy.agent_factory.contracts import (
    AgentFactorySummary,
    AuditFinding,
    LaneReport,
    OperatorSummaryPacket,
    SummaryStatus,
)


@dataclass(frozen=True)
class FinalReadinessDecision:
    """Read-only final readiness decision. It is not approval."""

    status: SummaryStatus
    decision: str
    reasons: tuple[str, ...] = field(default_factory=tuple)
    blockers: tuple[str, ...] = field(default_factory=tuple)
    cautions: tuple[str, ...] = field(default_factory=tuple)

    @property
    def grants_approval(self) -> bool:
        return False

    @property
    def grants_permission(self) -> bool:
        return False


def build_final_readiness_decision(
    *,
    completion_summary: AgentFactorySummary,
    operator_packet: OperatorSummaryPacket,
    invariant_report: LaneReport,
) -> FinalReadinessDecision:
    """Build a deterministic decision packet from supplied reports."""

    blockers = list(completion_summary.blocked_by)
    blockers.extend(operator_packet.blockers)
    cautions = list(completion_summary.caution_items)
    cautions.extend(operator_packet.cautions)
    reasons = list(completion_summary.reason_codes)

    if invariant_report.status == "blocked":
        blockers.extend(finding.subject for finding in invariant_report.findings)
        reasons.append("authority_invariants_blocked")
    elif invariant_report.status == "caution":
        cautions.extend(finding.subject for finding in invariant_report.findings)
        reasons.append("authority_invariants_caution")

    status = _status(completion_summary.status, operator_packet.status, invariant_report.status)
    decision = {
        "READY": "agent_factory_foundation_ready_for_operator_review",
        "CAUTION": "agent_factory_foundation_ready_with_cautions",
        "BLOCKED": "agent_factory_foundation_blocked",
    }[status]

    return FinalReadinessDecision(
        status=status,
        decision=decision,
        reasons=_dedupe(reasons) or ("phase_14_final_readiness",),
        blockers=_dedupe(blockers),
        cautions=_dedupe(cautions),
    )


def audit_final_readiness_decision(decision: FinalReadinessDecision) -> LaneReport:
    """Audit final decision language for non-approval boundaries."""

    findings: list[AuditFinding] = []
    if "approved" in decision.decision or "permission" in decision.decision:
        findings.append(
            AuditFinding(
                rule="final_decision_implies_permission",
                severity="blocked",
                subject=decision.decision,
                detail="Final readiness decision must not imply approval or permission.",
            )
        )
    return LaneReport.from_findings(tuple(findings))


def format_final_readiness_decision(decision: FinalReadinessDecision) -> tuple[str, ...]:
    """Format final readiness without granting authority."""

    lines = [
        f"Status: {decision.status}",
        f"Decision: {decision.decision}",
        "Permission: not granted",
        "Approval: not granted",
    ]
    if decision.reasons:
        lines.append(f"Reasons: {', '.join(decision.reasons)}")
    if decision.blockers:
        lines.append(f"Blockers: {', '.join(decision.blockers)}")
    if decision.cautions:
        lines.append(f"Cautions: {', '.join(decision.cautions)}")
    return tuple(lines)


def _status(
    completion_status: SummaryStatus,
    operator_status: SummaryStatus,
    invariant_status: str,
) -> SummaryStatus:
    if "BLOCKED" in {completion_status, operator_status, invariant_status.upper()}:
        return "BLOCKED"
    if "CAUTION" in {completion_status, operator_status, invariant_status.upper()}:
        return "CAUTION"
    return "READY"


def _dedupe(items: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return tuple(result)
