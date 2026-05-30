from source_proxy.agent_factory.verification_manifest import (
    VerificationCommand,
    VerificationManifest,
    audit_verification_manifest,
    build_verification_manifest,
    format_verification_manifest,
)


TEST_FILES = (
    "source_proxy/tests/test_agent_factory_contracts.py",
    "source_proxy/tests/test_agent_factory_authority_auditor.py",
    "source_proxy/tests/test_agent_factory_lane_guard.py",
)


def test_phase_12_manifest_builds_manual_commands_without_execution_grant():
    manifest = build_verification_manifest(
        phase=12,
        test_files=TEST_FILES,
        closeout_doc="docs/agent-ecosystem-plan-1-phase-12-closeout-v0.1.md",
    )

    assert manifest.phase == 12
    assert len(manifest.commands) == 3
    assert manifest.grants_execution is False
    assert manifest.grants_permission is False
    assert all(command.grants_execution is False for command in manifest.commands)


def test_phase_12_manifest_includes_closeout_in_diff_check():
    manifest = build_verification_manifest(
        phase=12,
        test_files=TEST_FILES,
        closeout_doc="docs/agent-ecosystem-plan-1-phase-12-closeout-v0.1.md",
    )

    diff_command = manifest.commands[0]

    assert diff_command.name == "whitespace_diff_check"
    assert "docs/agent-ecosystem-plan-1-phase-12-closeout-v0.1.md" in diff_command.command


def test_phase_18_manifest_compile_command_includes_recent_foundation_modules():
    manifest = build_verification_manifest(
        phase=18,
        test_files=TEST_FILES,
        closeout_doc="docs/agent-ecosystem-plan-1-phase-18-closeout-v0.1.md",
    )

    compile_command = manifest.commands[1]

    assert compile_command.name == "python_compile_check"
    assert "source_proxy/agent_factory/operator_summary.py" in compile_command.command
    assert "source_proxy/agent_factory/final_readiness.py" in compile_command.command
    assert "source_proxy/agent_factory/phase_ledger.py" in compile_command.command
    assert "source_proxy/agent_factory/foundation_packet.py" in compile_command.command


def test_phase_12_manifest_audit_clear_for_built_manifest():
    manifest = build_verification_manifest(
        phase=12,
        test_files=TEST_FILES,
        closeout_doc="docs/agent-ecosystem-plan-1-phase-12-closeout-v0.1.md",
    )

    report = audit_verification_manifest(manifest)

    assert report.status == "clear"
    assert report.findings == ()
    assert report.grants_permission is False


def test_phase_12_manifest_audit_blocks_empty_command():
    manifest = VerificationManifest(
        phase=12,
        commands=(VerificationCommand(name="empty", command=()),),
    )

    report = audit_verification_manifest(manifest)

    assert report.status == "blocked"
    assert report.findings[0].rule == "verification_command_empty"


def test_phase_12_manifest_format_never_claims_authority():
    manifest = build_verification_manifest(
        phase=12,
        test_files=TEST_FILES,
        closeout_doc="docs/agent-ecosystem-plan-1-phase-12-closeout-v0.1.md",
    )

    lines = format_verification_manifest(manifest)

    assert "Phase: 12" in lines
    assert "Execution: not granted" in lines
    assert "Permission: not granted" in lines
    assert "Approval: not granted" in lines
