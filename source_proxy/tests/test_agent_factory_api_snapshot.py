import source_proxy.agent_factory as agent_factory
from source_proxy.agent_factory.api_snapshot import (
    audit_public_api,
    get_expected_public_api,
)


def test_phase_8_expected_public_api_matches_package_exports():
    report = audit_public_api(tuple(agent_factory.__all__))

    assert report.status == "clear"
    assert report.findings == ()
    assert report.grants_permission is False


def test_phase_8_expected_public_api_is_deterministic():
    first = get_expected_public_api()
    second = get_expected_public_api()

    assert first == second
    assert "AuthorityFlags" in first
    assert "format_readiness_matrix" in first


def test_phase_8_audit_blocks_missing_public_export():
    actual = tuple(name for name in get_expected_public_api() if name != "AuthorityFlags")

    report = audit_public_api(actual)

    assert report.status == "blocked"
    assert report.findings[0].rule == "missing_public_export"
    assert report.findings[0].subject == "AuthorityFlags"


def test_phase_8_audit_cautions_on_unexpected_public_export():
    actual = get_expected_public_api() + ("execute_workflow_queue",)

    report = audit_public_api(actual)

    assert report.status == "caution"
    assert report.findings[0].rule == "unexpected_public_export"
    assert report.findings[0].subject == "execute_workflow_queue"


def test_phase_8_audit_blocks_missing_even_with_unexpected_export():
    actual = tuple(name for name in get_expected_public_api() if name != "LaneReport")
    actual = actual + ("apply_changes",)

    report = audit_public_api(actual)

    assert report.status == "blocked"
    assert {finding.rule for finding in report.findings} == {
        "missing_public_export",
        "unexpected_public_export",
    }
