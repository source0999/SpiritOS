from source_proxy.agent_factory.contracts import LaneScope
from source_proxy.agent_factory.lane_guard import evaluate_lane


def test_lane_guard_clear_for_allowed_files_only():
    report = evaluate_lane(
        LaneScope(
            allowed_files=(
                "source_proxy/agent_factory/contracts.py",
                "source_proxy/tests/test_agent_factory_contracts.py",
            )
        ),
        proposed_files=(
            "source_proxy/agent_factory/contracts.py",
            "source_proxy/tests/test_agent_factory_contracts.py",
        ),
    )

    assert report.status == "clear"
    assert report.findings == ()
    assert report.grants_permission is False


def test_lane_guard_blocks_forbidden_file_even_if_glob_allowed():
    report = evaluate_lane(
        LaneScope(
            allowed_files=("source_proxy/agent_factory/*.py",),
            forbidden_files=("source_proxy/agent_factory/runner.py",),
        ),
        proposed_files=("source_proxy/agent_factory/runner.py",),
    )

    assert report.status == "blocked"
    assert {finding.rule for finding in report.findings} == {"forbidden_file"}


def test_lane_guard_blocks_file_outside_allowed_scope():
    report = evaluate_lane(
        LaneScope(allowed_files=("source_proxy/agent_factory/*.py",)),
        proposed_files=("src/app/page.tsx",),
    )

    assert report.status == "blocked"
    assert report.findings[0].rule == "outside_allowed_files"


def test_lane_guard_cautions_on_dirty_file_outside_lane_without_claiming_it():
    report = evaluate_lane(
        LaneScope(allowed_files=("source_proxy/agent_factory/*.py",)),
        dirty_files=("docs/user-owned.md",),
    )

    assert report.status == "caution"
    assert report.findings[0].rule == "dirty_file_outside_lane"
    assert "does not claim, clean, or modify it" in report.findings[0].detail


def test_lane_guard_cautions_on_file_family_overlap():
    report = evaluate_lane(
        LaneScope(
            allowed_files=("source_proxy/agent_factory/*.py", "source_proxy/tests/*.py"),
            file_families={
                "runtime": ("source_proxy/agent_factory/*.py",),
                "tests": ("source_proxy/tests/*.py",),
            },
        ),
        proposed_files=(
            "source_proxy/agent_factory/lane_guard.py",
            "source_proxy/tests/test_agent_factory_lane_guard.py",
        ),
    )

    assert report.status == "caution"
    assert report.findings[0].rule == "file_family_overlap"


def test_lane_guard_findings_include_evidence_without_verification_claim():
    report = evaluate_lane(
        LaneScope(allowed_files=("source_proxy/agent_factory/*.py",)),
        proposed_files=("src/app/page.tsx",),
    )

    assert report.status == "blocked"
    assert report.findings[0].evidence.file == "src/app/page.tsx"
    assert report.findings[0].evidence.source == "proposed_files"
    assert report.findings[0].evidence.verification_run is False
