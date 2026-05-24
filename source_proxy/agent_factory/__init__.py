"""Agent Factory runtime foundation.

The package exposes deterministic report helpers only. It does not grant
approval, apply, command, workflow, queue, commit, push, branch/worktree,
self-approval, or background authority.
"""

from source_proxy.agent_factory.contracts import (
    AgentFactorySummary,
    AuditFinding,
    AuthorityFlags,
    DependencyGateReport,
    EvidenceReference,
    FoundationPhaseRecord,
    LaneReport,
    LaneScope,
    OperatorSummaryPacket,
    ReadinessMatrixRow,
)
from source_proxy.agent_factory.catalog import (
    DEFAULT_AGENT_CATALOG,
    CatalogEntry,
    get_catalog_entry,
    get_default_catalog,
)
from source_proxy.agent_factory.dependency_gates import (
    REQUIRED_GATES,
    evaluate_catalog_entry,
    evaluate_dependency_gates,
)
from source_proxy.agent_factory.authority_vocabulary import (
    AUTHORITY_VOCABULARY,
    AuthorityVocabularyRule,
)
from source_proxy.agent_factory.authority_auditor import (
    audit_authority_flags,
    audit_model_data,
    audit_text,
)
from source_proxy.agent_factory.lane_guard import evaluate_lane
from source_proxy.agent_factory.reporting import (
    compose_agent_factory_summary,
    format_summary_lines,
)
from source_proxy.agent_factory.integrity import (
    audit_catalog_integrity,
    audit_report_authority_integrity,
)
from source_proxy.agent_factory.foundation_review import (
    format_foundation_review,
    review_agent_factory_foundation,
)
from source_proxy.agent_factory.readiness_matrix import (
    build_readiness_matrix,
    format_readiness_matrix,
)
from source_proxy.agent_factory.api_snapshot import (
    EXPECTED_PUBLIC_API,
    audit_public_api,
    get_expected_public_api,
)
from source_proxy.agent_factory.foundation_manifest import (
    EXPECTED_FOUNDATION_PHASES,
    audit_foundation_manifest,
    build_foundation_phase_record,
    format_foundation_manifest,
)
from source_proxy.agent_factory.authority_invariants import (
    FORBIDDEN_PUBLIC_NAME_TOKENS,
    audit_authority_invariants,
    audit_public_name_invariants,
)
from source_proxy.agent_factory.foundation_completion import (
    evaluate_foundation_completion,
    format_foundation_completion,
)
from source_proxy.agent_factory.verification_manifest import (
    VerificationCommand,
    VerificationManifest,
    audit_verification_manifest,
    build_verification_manifest,
    format_verification_manifest,
)
from source_proxy.agent_factory.operator_summary import (
    build_operator_summary_packet,
    format_operator_summary_packet,
)
from source_proxy.agent_factory.final_readiness import (
    FinalReadinessDecision,
    audit_final_readiness_decision,
    build_final_readiness_decision,
    format_final_readiness_decision,
)
from source_proxy.agent_factory.phase_ledger import (
    PhaseLedgerRollup,
    build_phase_ledger_rollup,
    format_phase_ledger_rollup,
)
from source_proxy.agent_factory.foundation_packet import (
    FoundationPacket,
    build_foundation_packet,
    format_foundation_packet,
)
from source_proxy.agent_factory.boundary_snapshot import (
    BoundarySnapshot,
    build_boundary_snapshot,
    format_boundary_snapshot,
)
from source_proxy.agent_factory.foundation_digest import (
    FoundationDigest,
    build_foundation_digest,
    format_foundation_digest,
)

__all__ = [
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
    "EXPECTED_FOUNDATION_PHASES",
    "FORBIDDEN_PUBLIC_NAME_TOKENS",
    "EvidenceReference",
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
    "format_foundation_completion",
    "format_foundation_digest",
    "format_foundation_packet",
    "format_final_readiness_decision",
    "format_operator_summary_packet",
    "format_phase_ledger_rollup",
    "format_verification_manifest",
    "evaluate_lane",
    "evaluate_foundation_completion",
    "evaluate_catalog_entry",
    "evaluate_dependency_gates",
    "get_catalog_entry",
    "get_default_catalog",
    "get_expected_public_api",
    "build_foundation_phase_record",
    "build_final_readiness_decision",
    "build_boundary_snapshot",
    "build_foundation_packet",
    "build_foundation_digest",
    "build_operator_summary_packet",
    "build_phase_ledger_rollup",
    "compose_agent_factory_summary",
    "format_summary_lines",
    "review_agent_factory_foundation",
    "build_readiness_matrix",
    "build_verification_manifest",
    "format_readiness_matrix",
]
