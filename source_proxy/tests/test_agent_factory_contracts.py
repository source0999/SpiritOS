from source_proxy.agent_factory.contracts import (
    AuditFinding,
    AuthorityFlags,
    EvidenceReference,
    LaneReport,
    LaneScope,
)


def test_authority_flags_default_fail_closed():
    flags = AuthorityFlags()

    assert flags.is_fail_closed is True
    assert flags.granted() == ()


def test_authority_flags_report_explicit_grants_without_authorizing_them():
    flags = AuthorityFlags(apply=True, command_execution=True)

    assert flags.is_fail_closed is False
    assert flags.granted() == ("apply", "command_execution")


def test_lane_scope_defaults_to_empty_supplied_data():
    scope = LaneScope()

    assert scope.allowed_files == ()
    assert scope.forbidden_files == ()
    assert scope.file_families == {}


def test_lane_report_defaults_clear_without_granting_permission():
    report = LaneReport()

    assert report.status == "clear"
    assert report.findings == ()
    assert report.authority.is_fail_closed is True
    assert report.grants_permission is False


def test_lane_report_status_follows_findings():
    caution = AuditFinding(
        rule="dirty_state",
        severity="caution",
        subject="source_proxy/example.py",
        detail="Dirty file was supplied outside this lane.",
    )
    blocked = AuditFinding(
        rule="forbidden_file",
        severity="blocked",
        subject="src/app/page.tsx",
        detail="Path is forbidden by supplied lane scope.",
    )

    assert LaneReport.from_findings((caution,)).status == "caution"
    assert LaneReport.from_findings((caution, blocked)).status == "blocked"


def test_evidence_reference_does_not_claim_verification_by_default():
    evidence = EvidenceReference(
        file="source_proxy/agent_factory/contracts.py",
        source="contract_test",
        rule="evidence_shape",
        detail="shape only",
    )

    assert evidence.verification_run is False


def test_audit_finding_carries_stable_evidence_shape():
    finding = AuditFinding(
        rule="authority_grant",
        severity="blocked",
        subject="prompt",
        detail="Blocked authority phrase.",
        evidence=EvidenceReference(
            file="docs/example.md",
            source="prompt",
            rule="authority_grant",
            detail="grants apply",
        ),
    )

    assert finding.evidence.file == "docs/example.md"
    assert finding.evidence.source == "prompt"
    assert finding.evidence.rule == "authority_grant"
    assert finding.evidence.detail == "grants apply"
    assert finding.evidence.verification_run is False
