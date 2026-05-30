import source_proxy.agent_factory as agent_factory
from source_proxy.agent_factory.authority_invariants import (
    audit_authority_invariants,
    audit_public_name_invariants,
)
from source_proxy.agent_factory.contracts import (
    AgentFactorySummary,
    AuthorityFlags,
    DependencyGateReport,
    FoundationPhaseRecord,
    LaneReport,
    ReadinessMatrixRow,
)


def test_phase_10_public_api_names_do_not_imply_forbidden_runtime_authority():
    report = audit_public_name_invariants(tuple(agent_factory.__all__))

    assert report.status == "clear"
    assert report.findings == ()
    assert report.grants_permission is False


def test_phase_10_public_name_invariant_blocks_apply_like_export():
    report = audit_public_name_invariants(("apply_changes",))

    assert report.status == "blocked"
    assert report.findings[0].rule == "public_name_implies_forbidden_authority"
    assert report.findings[0].subject == "apply_changes"


def test_phase_10_authority_invariants_clear_for_fail_closed_objects():
    report = audit_authority_invariants(
        flags=(AuthorityFlags(),),
        lane_reports=(LaneReport(),),
        gate_reports=(DependencyGateReport(),),
        summaries=(AgentFactorySummary(),),
        readiness_rows=(
            ReadinessMatrixRow(
                plan="Plan 1",
                name="Agent Factory Runtime Foundation",
                status="READY",
                allowed_mode="deterministic_runtime_foundation",
            ),
        ),
        phase_records=(
            FoundationPhaseRecord(
                phase=10,
                title="Authority Invariant Proof",
                closeout_doc="docs/agent-ecosystem-plan-1-phase-10-closeout-v0.1.md",
                checks_passed=True,
            ),
        ),
    )

    assert report.status == "clear"
    assert report.findings == ()


def test_phase_10_authority_invariants_block_grants_across_objects():
    report = audit_authority_invariants(
        flags=(AuthorityFlags(apply=True),),
        lane_reports=(LaneReport(authority=AuthorityFlags(write=True)),),
        gate_reports=(DependencyGateReport(authority=AuthorityFlags(queue_execution=True)),),
        summaries=(AgentFactorySummary(authority=AuthorityFlags(approval=True)),),
        readiness_rows=(
            ReadinessMatrixRow(
                plan="Plan 5",
                name="Worker Coordination",
                status="BLOCKED",
                allowed_mode="blocked_future_worker_coordination",
                authority=AuthorityFlags(workflow_execution=True),
            ),
        ),
        phase_records=(
            FoundationPhaseRecord(
                phase=10,
                title="Authority Invariant Proof",
                closeout_doc="docs/agent-ecosystem-plan-1-phase-10-closeout-v0.1.md",
                authority=AuthorityFlags(command_execution=True),
            ),
        ),
    )

    assert report.status == "blocked"
    assert [finding.subject for finding in report.findings] == [
        "flags[0].apply",
        "lane_reports[0].write",
        "gate_reports[0].queue_execution",
        "summaries[0].approval",
        "readiness_rows[0].workflow_execution",
        "phase_records[0].command_execution",
    ]
