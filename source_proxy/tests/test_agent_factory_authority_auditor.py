from source_proxy.agent_factory.authority_auditor import (
    audit_authority_flags,
    audit_model_data,
    audit_text,
)
from source_proxy.agent_factory.authority_vocabulary import AUTHORITY_VOCABULARY
from source_proxy.agent_factory.contracts import AuthorityFlags


def test_audit_text_blocks_explicit_authority_grants():
    report = audit_text("This helper grants apply authority.", source="prompt")

    assert report.status == "blocked"
    assert report.grants_permission is False
    assert report.findings[0].rule == "authority_grant"


def test_audit_text_does_not_treat_negative_scope_as_grant():
    report = audit_text(
        "No apply authority. No command execution authority.",
        source="prompt",
    )

    assert report.status == "clear"
    assert report.findings == ()
    assert report.grants_permission is False


def test_audit_text_blocks_clean_report_as_permission():
    report = audit_text("Audit success authorizes apply.", source="packet")

    assert report.status == "blocked"
    assert report.findings[0].rule == "clean_report_permission"


def test_audit_authority_flags_reports_true_values_only():
    report = audit_authority_flags(
        AuthorityFlags(apply=True, self_approval=True),
        source="flags",
    )

    assert report.status == "blocked"
    assert [finding.subject for finding in report.findings] == [
        "flags.apply",
        "flags.self_approval",
    ]


def test_audit_model_data_recurses_over_supplied_data():
    report = audit_model_data(
        {
            "name": "tester",
            "authority": {"command_execution": True},
            "notes": ["clean report is permission"],
        },
        source="agent",
    )

    assert report.status == "blocked"
    assert {finding.rule for finding in report.findings} == {
        "authority_model_true",
        "clean_report_permission",
    }


def test_authority_vocabulary_is_centralized_and_fail_closed():
    rule_names = {rule.rule for rule in AUTHORITY_VOCABULARY}

    assert "authority_grant" in rule_names
    assert "background_autonomy_request" in rule_names
    assert {rule.severity for rule in AUTHORITY_VOCABULARY} == {"blocked"}


def test_audit_findings_include_evidence_without_verification_claim():
    report = audit_text("continue autonomously", source="prompt")

    assert report.status == "blocked"
    assert report.findings[0].evidence.source == "prompt"
    assert report.findings[0].evidence.rule == "background_autonomy_request"
    assert report.findings[0].evidence.verification_run is False
