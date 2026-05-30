"""Deterministic public API snapshot for Agent Factory."""

from __future__ import annotations

from source_proxy.agent_factory.contracts import AuditFinding, LaneReport

EXPECTED_PUBLIC_API: tuple[str, ...] = (
    "AgentFactorySummary",
    "AuditFinding",
    "AuthorityFlags",
    "BoundarySnapshot",
    "CatalogEntry",
    "DEFAULT_AGENT_CATALOG",
    "DependencyGateReport",
    "AUTHORITY_VOCABULARY",
    "AuthorityVocabularyRule",
    "EXPECTED_PUBLIC_API",
    "EvidenceReference",
    "EXPECTED_FOUNDATION_PHASES",
    "FORBIDDEN_PUBLIC_NAME_TOKENS",
    "FinalReadinessDecision",
    "FoundationDigest",
    "FoundationPacket",
    "FoundationPhaseRecord",
    "LaneReport",
    "LaneScope",
    "OperatorSummaryPacket",
    "PhaseLedgerRollup",
    "REQUIRED_GATES",
    "ReadinessMatrixRow",
    "VerificationCommand",
    "VerificationManifest",
    "audit_authority_flags",
    "audit_authority_invariants",
    "audit_catalog_integrity",
    "audit_foundation_manifest",
    "audit_final_readiness_decision",
    "audit_model_data",
    "audit_public_api",
    "audit_public_name_invariants",
    "audit_report_authority_integrity",
    "audit_text",
    "audit_verification_manifest",
    "format_foundation_review",
    "format_boundary_snapshot",
    "format_foundation_manifest",
    "evaluate_lane",
    "evaluate_foundation_completion",
    "evaluate_catalog_entry",
    "evaluate_dependency_gates",
    "get_catalog_entry",
    "get_default_catalog",
    "get_expected_public_api",
    "build_foundation_phase_record",
    "compose_agent_factory_summary",
    "format_summary_lines",
    "format_foundation_completion",
    "format_foundation_digest",
    "format_foundation_packet",
    "format_final_readiness_decision",
    "format_operator_summary_packet",
    "format_phase_ledger_rollup",
    "format_verification_manifest",
    "review_agent_factory_foundation",
    "build_readiness_matrix",
    "build_final_readiness_decision",
    "build_boundary_snapshot",
    "build_foundation_packet",
    "build_foundation_digest",
    "build_operator_summary_packet",
    "build_phase_ledger_rollup",
    "build_verification_manifest",
    "format_readiness_matrix",
)


def get_expected_public_api() -> tuple[str, ...]:
    return EXPECTED_PUBLIC_API


def audit_public_api(
    actual_exports: tuple[str, ...],
    *,
    expected_exports: tuple[str, ...] = EXPECTED_PUBLIC_API,
) -> LaneReport:
    """Compare supplied export names to the expected Agent Factory API."""

    expected = set(expected_exports)
    actual = set(actual_exports)
    findings: list[AuditFinding] = []

    for name in sorted(expected - actual):
        findings.append(
            AuditFinding(
                rule="missing_public_export",
                severity="blocked",
                subject=name,
                detail="Expected Agent Factory public export is missing.",
            )
        )

    for name in sorted(actual - expected):
        findings.append(
            AuditFinding(
                rule="unexpected_public_export",
                severity="caution",
                subject=name,
                detail="Public export is not in the expected Agent Factory snapshot.",
            )
        )

    return LaneReport.from_findings(tuple(findings))
