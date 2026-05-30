from dataclasses import replace

from source_proxy.agent_factory.contracts import AuthorityFlags
from source_proxy.agent_factory.foundation_manifest import (
    EXPECTED_FOUNDATION_PHASES,
    build_foundation_phase_record,
)
from source_proxy.agent_factory.phase_ledger import (
    build_phase_ledger_rollup,
    format_phase_ledger_rollup,
)


def _records():
    return tuple(
        build_foundation_phase_record(
            phase=phase,
            title=f"Phase {phase}",
            checks_passed=True,
        )
        for phase in EXPECTED_FOUNDATION_PHASES
    )


def test_phase_16_rollup_ready_for_complete_supplied_records():
    rollup = build_phase_ledger_rollup(_records())

    assert rollup.status == "READY"
    assert rollup.expected_phases == tuple(range(1, 16))
    assert rollup.missing_phases == ()
    assert rollup.failed_phases == ()
    assert rollup.grants_permission is False


def test_phase_16_rollup_blocks_missing_phase():
    records = tuple(record for record in _records() if record.phase != 14)

    rollup = build_phase_ledger_rollup(records)

    assert rollup.status == "BLOCKED"
    assert rollup.missing_phases == (14,)
    assert "missing_phase_records" in rollup.blocked_by


def test_phase_16_rollup_blocks_failed_phase():
    records = list(_records())
    records[4] = replace(records[4], checks_passed=False)

    rollup = build_phase_ledger_rollup(tuple(records))

    assert rollup.status == "BLOCKED"
    assert rollup.failed_phases == (5,)
    assert "phase_checks_not_passed" in rollup.blocked_by


def test_phase_16_rollup_blocks_duplicate_phase():
    records = _records() + (_records()[0],)

    rollup = build_phase_ledger_rollup(records)

    assert rollup.status == "BLOCKED"
    assert rollup.duplicate_phases == (1,)
    assert "duplicate_phase_records" in rollup.blocked_by


def test_phase_16_rollup_cautions_on_supplied_blockers():
    records = list(_records())
    records[6] = replace(records[6], blockers=("manual spot check pending",))

    rollup = build_phase_ledger_rollup(tuple(records))

    assert rollup.status == "CAUTION"
    assert rollup.cautions == ("Phase 7: manual spot check pending",)
    assert rollup.grants_permission is False


def test_phase_16_rollup_blocks_authority_grant():
    records = list(_records())
    records[9] = replace(records[9], authority=AuthorityFlags(queue_execution=True))

    rollup = build_phase_ledger_rollup(tuple(records))

    assert rollup.status == "BLOCKED"
    assert rollup.blocked_by == ("Phase 10: authority_grant_present",)


def test_phase_16_rollup_format_never_claims_authority():
    lines = format_phase_ledger_rollup(build_phase_ledger_rollup(_records()))

    assert "Permission: not granted" in lines
    assert "Approval: not granted" in lines
