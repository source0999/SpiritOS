from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

TerminalPresetKind = Literal["test_run", "coding_task", "log_output", "command_history"]


@dataclass(frozen=True)
class TerminalCommandPreset:
    id: str
    label: str
    description: str
    command: tuple[str, ...]
    session_kind: TerminalPresetKind
    network_policy: Literal["none", "trusted_command"] = "none"
    timeout_seconds: int = 30
    writes_allowed: bool = False
    approval_required_for_apply: bool = True

    def as_payload(self) -> dict[str, object]:
        return {
            **asdict(self),
            "command": list(self.command),
        }


TERMINAL_COMMAND_PRESETS: tuple[TerminalCommandPreset, ...] = (
    TerminalCommandPreset(
        id="proxy-smoke",
        label="Run proxy smoke",
        description="Run the Source Proxy dry-run smoke profile.",
        command=("python3", "-m", "source_proxy.testing.runner", "--profile", "proxy-smoke"),
        session_kind="test_run",
    ),
    TerminalCommandPreset(
        id="targeted-proxy-tests",
        label="Run targeted proxy tests",
        description="Run focused proxy tests for the current coding workflow surface.",
        command=(
            "python3",
            "-m",
            "pytest",
            "source_proxy/tests/test_sandbox_terminal_api.py",
        ),
        session_kind="test_run",
    ),
    TerminalCommandPreset(
        id="scout-tests",
        label="Run Scout tests",
        description="Run bounded Scout discovery and soak safety tests from the scout package.",
        command=(
            "python3",
            "-m",
            "pytest",
            "scout/src/scout/tests/test_discovery_jobs.py",
            "scout/src/scout/tests/test_search_candidate_extraction.py",
            "scout/src/scout/tests/test_v03_soak_safety.py",
        ),
        session_kind="test_run",
    ),
    TerminalCommandPreset(
        id="cartographer-safety-audit",
        label="Run Cartographer safety audit",
        description="Run Cartographer API and safety audit tests.",
        command=(
            "python3",
            "-m",
            "pytest",
            "source_proxy/tests/test_cartographer_api.py",
            "source_proxy/tests/test_cartographer_safety_audit.py",
        ),
        session_kind="test_run",
    ),
    TerminalCommandPreset(
        id="typecheck",
        label="Run typecheck",
        description="Run the project TypeScript check.",
        command=("npx", "tsc", "--noEmit", "--pretty", "false"),
        session_kind="test_run",
    ),
    TerminalCommandPreset(
        id="lint",
        label="Run lint",
        description="Run the project lint command.",
        command=("npm", "run", "lint"),
        session_kind="test_run",
    ),
)


def terminal_command_presets_payload() -> list[dict[str, object]]:
    return [preset.as_payload() for preset in TERMINAL_COMMAND_PRESETS]
