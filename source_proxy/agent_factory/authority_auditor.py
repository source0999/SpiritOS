"""Deterministic authority drift checks for supplied data."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from source_proxy.agent_factory.authority_vocabulary import AUTHORITY_VOCABULARY
from source_proxy.agent_factory.contracts import (
    AuditFinding,
    AuthorityFlags,
    EvidenceReference,
    LaneReport,
)

_AUTHORITY_KEYS = {
    "approval",
    "approval_authority",
    "apply",
    "apply_authority",
    "write",
    "write_authority",
    "command_execution",
    "command_execution_authority",
    "workflow_execution",
    "workflow_execution_authority",
    "queue_execution",
    "queue_execution_authority",
    "commit",
    "commit_authority",
    "push",
    "push_authority",
    "branch_worktree",
    "branch_worktree_authority",
    "self_approval",
    "self_approval_authority",
    "background_autonomy",
}


def audit_text(text: str, *, source: str = "supplied_text") -> LaneReport:
    """Scan supplied text for authority drift phrases."""

    findings: list[AuditFinding] = []
    for vocabulary_rule in AUTHORITY_VOCABULARY:
        for match in vocabulary_rule.pattern.finditer(text):
            findings.append(
                AuditFinding(
                    rule=vocabulary_rule.rule,
                    severity=vocabulary_rule.severity,
                    subject=source,
                    detail=f"{vocabulary_rule.detail} Matched: {match.group(0)!r}.",
                    evidence=EvidenceReference(
                        source=source,
                        rule=vocabulary_rule.rule,
                        detail=match.group(0),
                    ),
                )
            )
    return LaneReport.from_findings(tuple(findings))


def audit_authority_flags(
    flags: AuthorityFlags, *, source: str = "authority_flags"
) -> LaneReport:
    """Report any supplied authority flag that is already true."""

    findings = tuple(
        AuditFinding(
            rule="authority_flag_true",
            severity="blocked",
            subject=f"{source}.{name}",
            detail="Supplied authority flag is true; Agent Factory defaults must fail closed.",
            evidence=EvidenceReference(
                source=source,
                rule="authority_flag_true",
                detail=name,
            ),
        )
        for name in flags.granted()
    )
    return LaneReport.from_findings(findings)


def audit_model_data(data: Any, *, source: str = "model_data") -> LaneReport:
    """Scan supplied mappings/sequences/strings for authority drift."""

    findings = _audit_value(data, source)
    return LaneReport.from_findings(tuple(findings))


def _audit_value(value: Any, source: str) -> list[AuditFinding]:
    if isinstance(value, AuthorityFlags):
        return list(audit_authority_flags(value, source=source).findings)
    if isinstance(value, str):
        return list(audit_text(value, source=source).findings)
    if isinstance(value, Mapping):
        findings: list[AuditFinding] = []
        for raw_key, nested in value.items():
            key = str(raw_key)
            nested_source = f"{source}.{key}"
            normalized_key = key.lower().replace("-", "_").replace(" ", "_")
            if normalized_key in _AUTHORITY_KEYS and nested is True:
                findings.append(
                    AuditFinding(
                        rule="authority_model_true",
                        severity="blocked",
                        subject=nested_source,
                        detail="Supplied model data sets a blocked authority to true.",
                        evidence=EvidenceReference(
                            source=nested_source,
                            rule="authority_model_true",
                            detail=str(nested),
                        ),
                    )
                )
            findings.extend(_audit_value(nested, nested_source))
        return findings
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        findings = []
        for index, nested in enumerate(value):
            findings.extend(_audit_value(nested, f"{source}[{index}]"))
        return findings
    return []
