from dataclasses import replace

from source_proxy.agent_factory.contracts import AuthorityFlags
from source_proxy.agent_factory.foundation_manifest import (
    EXPECTED_FOUNDATION_PHASES,
    audit_foundation_manifest,
    build_foundation_phase_record,
    format_foundation_manifest,
)


def _complete_records():
    return tuple(
        build_foundation_phase_record(
            phase=phase,
            title=f"Phase {phase}",
            checks_passed=True,
        )
        for phase in EXPECTED_FOUNDATION_PHASES
    )


def test_phase_9_manifest_clear_for_complete_supplied_records():
    report = audit_foundation_manifest(_complete_records())

    assert report.status == "clear"
    assert report.findings == ()
    assert report.grants_permission is False


def test_phase_15_manifest_expects_full_foundation_phase_range():
    assert EXPECTED_FOUNDATION_PHASES == tuple(range(1, 16))


def test_phase_9_manifest_blocks_missing_phase():
    records = tuple(record for record in _complete_records() if record.phase != 8)

    report = audit_foundation_manifest(records)

    assert report.status == "blocked"
    assert report.findings[0].rule == "missing_phase_record"
    assert report.findings[0].subject == "Phase 8"


def test_phase_9_manifest_blocks_failed_checks():
    records = list(_complete_records())
    records[0] = replace(records[0], checks_passed=False)

    report = audit_foundation_manifest(tuple(records))

    assert report.status == "blocked"
    assert report.findings[0].rule == "phase_checks_not_passed"


def test_phase_9_manifest_cautions_on_blockers_without_permission():
    records = list(_complete_records())
    records[1] = replace(records[1], blockers=("manual review pending",))

    report = audit_foundation_manifest(tuple(records))

    assert report.status == "caution"
    assert report.findings[0].rule == "phase_blockers_present"
    assert report.grants_permission is False


def test_phase_9_manifest_blocks_authority_grant():
    records = list(_complete_records())
    records[2] = replace(records[2], authority=AuthorityFlags(apply=True))

    report = audit_foundation_manifest(tuple(records))

    assert report.status == "blocked"
    assert report.findings[0].rule == "phase_authority_grant"
    assert report.findings[0].subject == "Phase 3.apply"


def test_phase_9_manifest_format_never_claims_approval():
    lines = format_foundation_manifest(_complete_records())

    assert lines[0] == "Phase | Checks | Closeout"
    assert "Permission: not granted" in lines
    assert "Approval: not granted" in lines
