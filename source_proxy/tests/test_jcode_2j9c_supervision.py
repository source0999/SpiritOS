"""Gate 2-J.9C deterministic fake-executor supervision proofs."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from source_proxy.jcode.cgroup_scope import CgroupScopeConfig
from source_proxy.jcode.supervision import (
    FixtureSupervisionConfig,
    reap_fixture_descendants,
    run_supervised_fixture,
)


def _code(body: str) -> list[str]:
    return [sys.executable, "-c", body]


def _event_then(body: str = "") -> str:
    return "import os; os.write(int(os.environ['C2J_EVENT_FD']), b'process.started\\n'); " + body


def test_success_captures_separate_channels_and_seals_evidence(tmp_path: Path) -> None:
    evidence = tmp_path / "receipt.json"
    result = run_supervised_fixture(
        _code(_event_then("print('out'); print('err', file=__import__('sys').stderr)")),
        FixtureSupervisionConfig(evidence_path=evidence),
    )
    assert result["status"] == "completed"
    assert result["readiness_received"] is True
    assert result["stdout"] == "out\n"
    assert result["stderr"] == "err\n"
    assert result["events_ndjson"] == "process.started\n"
    assert result["evidence_sealed"] is True
    assert evidence.is_file()


def test_supervisor_can_launch_fixture_under_its_transient_scope() -> None:
    result = run_supervised_fixture(
        _code(_event_then("print('scoped')")),
        FixtureSupervisionConfig(
            cgroup_scope=CgroupScopeConfig("supervisor-9c", 64 * 1024 * 1024, 16, 25, 1024, 32)
        ),
    )
    assert result["status"] == "completed"
    assert result["stdout"] == "scoped\n"


def test_nonzero_crash_and_missing_readiness_map_truthfully() -> None:
    nonzero = run_supervised_fixture(
        _code(_event_then("raise SystemExit(7)")), FixtureSupervisionConfig()
    )
    assert nonzero["status"] == "nonzero_exit"
    assert nonzero["process_exit_code"] == 7
    no_ready = run_supervised_fixture(
        _code("import time; time.sleep(2)"),
        FixtureSupervisionConfig(readiness_timeout_seconds=0.05, total_timeout_seconds=1),
    )
    assert no_ready["status"] == "readiness_timeout"
    assert no_ready["process_group_reaped"] is True


def test_inactivity_total_timeout_and_ignored_term_cleanup() -> None:
    inactive = run_supervised_fixture(
        _code(_event_then("import time; time.sleep(2)")),
        FixtureSupervisionConfig(inactivity_timeout_seconds=0.05, total_timeout_seconds=1),
    )
    assert inactive["status"] == "inactivity_timeout"
    ignored = run_supervised_fixture(
        _code(_event_then("import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(2)")),
        FixtureSupervisionConfig(inactivity_timeout_seconds=1, total_timeout_seconds=0.05, termination_grace_seconds=0.05),
    )
    assert ignored["status"] == "total_timeout"
    assert ignored["termination_signal"] == "SIGKILL"
    assert ignored["process_group_reaped"] is True


def test_output_flood_cancellation_race_and_unwritable_evidence(tmp_path: Path) -> None:
    flood = run_supervised_fixture(
        _code(_event_then("print('x' * 10000)")),
        FixtureSupervisionConfig(max_stdout_bytes=32),
    )
    assert flood["status"] == "stdout_limit_exceeded"
    assert flood["output_truncated"]["stdout"] is True
    deadline = time.monotonic() + 0.05
    cancelled = run_supervised_fixture(
        _code(_event_then("import time; time.sleep(2)")),
        FixtureSupervisionConfig(inactivity_timeout_seconds=1),
        cancellation_requested=lambda: time.monotonic() >= deadline,
    )
    assert cancelled["status"] == "cancelled"
    bad = run_supervised_fixture(
        _code(_event_then()),
        FixtureSupervisionConfig(evidence_path=tmp_path / "missing" / "receipt.json"),
    )
    assert bad["status"] == "evidence_write_failed"
    assert bad["evidence_sealed"] is False


def test_descendant_is_killed_after_parent_exit() -> None:
    result = run_supervised_fixture(
        _code(
            _event_then(
                "import subprocess,sys; child=subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(5)']); print(child.pid, flush=True)"
            )
        ),
        FixtureSupervisionConfig(inactivity_timeout_seconds=1),
    )
    assert result["status"] == "completed"
    child_pid = int(str(result["stdout"]).strip())
    time.sleep(0.05)
    try:
        os.kill(child_pid, 0)
    except ProcessLookupError:
        pass
    else:
        raise AssertionError("descendant remained after supervisor exit")


def test_grandchild_race_and_idempotent_reap() -> None:
    grandchild = run_supervised_fixture(
        _code(
            _event_then(
                "import subprocess,sys,time; child=subprocess.Popen([sys.executable, '-c', \"import subprocess,sys,time; subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(5)']); time.sleep(5)\"]); time.sleep(.1)"
            )
        ),
        FixtureSupervisionConfig(total_timeout_seconds=0.15, inactivity_timeout_seconds=1),
    )
    assert grandchild["status"] == "total_timeout"
    assert int(grandchild["descendants_killed"]) >= 1
    raced = run_supervised_fixture(
        _code(_event_then()),
        FixtureSupervisionConfig(),
        cancellation_requested=lambda: True,
    )
    assert raced["status"] in {"cancelled", "completed"}
    assert reap_fixture_descendants(set()) == 0
    assert reap_fixture_descendants(set()) == 0
