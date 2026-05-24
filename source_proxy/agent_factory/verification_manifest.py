"""Manual verification manifest for the Agent Factory foundation."""

from __future__ import annotations

from dataclasses import dataclass, field

from source_proxy.agent_factory.contracts import AuditFinding, LaneReport


@dataclass(frozen=True)
class VerificationCommand:
    """A suggested manual verification command. It does not execute."""

    name: str
    command: tuple[str, ...]
    required: bool = True

    @property
    def grants_execution(self) -> bool:
        return False

    @property
    def grants_permission(self) -> bool:
        return False


@dataclass(frozen=True)
class VerificationManifest:
    """Read-only verification checklist for Agent Factory."""

    phase: int
    commands: tuple[VerificationCommand, ...] = field(default_factory=tuple)

    @property
    def grants_execution(self) -> bool:
        return False

    @property
    def grants_permission(self) -> bool:
        return False


def build_verification_manifest(
    *,
    phase: int,
    test_files: tuple[str, ...],
    closeout_doc: str,
) -> VerificationManifest:
    """Build a deterministic manual verification manifest."""

    agent_factory_files = (
        "source_proxy/agent_factory/*.py",
        "source_proxy/tests/test_agent_factory_*.py",
        closeout_doc,
    )
    return VerificationManifest(
        phase=phase,
        commands=(
            VerificationCommand(
                name="whitespace_diff_check",
                command=("git", "diff", "--check", "--", *agent_factory_files),
            ),
            VerificationCommand(
                name="python_compile_check",
                command=(
                    "python3",
                    "-m",
                    "py_compile",
                    "source_proxy/agent_factory/__init__.py",
                    "source_proxy/agent_factory/contracts.py",
                    "source_proxy/agent_factory/authority_auditor.py",
                    "source_proxy/agent_factory/authority_vocabulary.py",
                    "source_proxy/agent_factory/lane_guard.py",
                    "source_proxy/agent_factory/catalog.py",
                    "source_proxy/agent_factory/dependency_gates.py",
                    "source_proxy/agent_factory/reporting.py",
                    "source_proxy/agent_factory/integrity.py",
                    "source_proxy/agent_factory/foundation_review.py",
                    "source_proxy/agent_factory/readiness_matrix.py",
                    "source_proxy/agent_factory/api_snapshot.py",
                    "source_proxy/agent_factory/foundation_manifest.py",
                    "source_proxy/agent_factory/authority_invariants.py",
                    "source_proxy/agent_factory/foundation_completion.py",
                    "source_proxy/agent_factory/verification_manifest.py",
                    "source_proxy/agent_factory/operator_summary.py",
                    "source_proxy/agent_factory/final_readiness.py",
                    "source_proxy/agent_factory/phase_ledger.py",
                    "source_proxy/agent_factory/foundation_packet.py",
                    *test_files,
                ),
            ),
            VerificationCommand(
                name="focused_pytest_check",
                command=(".venv/bin/python", "-m", "pytest", *test_files, "-q"),
            ),
        ),
    )


def audit_verification_manifest(manifest: VerificationManifest) -> LaneReport:
    """Validate supplied verification commands without running them."""

    findings: list[AuditFinding] = []
    for command in manifest.commands:
        if not command.command:
            findings.append(
                AuditFinding(
                    rule="verification_command_empty",
                    severity="blocked",
                    subject=command.name,
                    detail="Verification command must not be empty.",
                )
            )
        if command.grants_execution:
            findings.append(
                AuditFinding(
                    rule="verification_command_execution_grant",
                    severity="blocked",
                    subject=command.name,
                    detail="Verification command object must not grant execution.",
                )
            )
    return LaneReport.from_findings(tuple(findings))


def format_verification_manifest(manifest: VerificationManifest) -> tuple[str, ...]:
    """Format manual verification commands without claiming execution."""

    lines = (f"Phase: {manifest.phase}", "Execution: not granted")
    for command in manifest.commands:
        lines += (f"{command.name}: {' '.join(command.command)}",)
    lines += ("Permission: not granted", "Approval: not granted")
    return lines
