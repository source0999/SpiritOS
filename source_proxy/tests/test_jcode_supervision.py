from __future__ import annotations

import sys
import time

from source_proxy.jcode.supervision import JCodeSupervisionConfig, run_supervised_jcode_command


def test_supervision_returns_normal_reaped_receipt() -> None:
    result = run_supervised_jcode_command(
        [sys.executable, "-c", "print('complete')"],
        JCodeSupervisionConfig(timeout_seconds=2),
    )

    assert result["status"] == "completed"
    assert result["process_exit_code"] == 0
    assert result["process_group_reaped"] is True
    assert result["stdout"] == "complete\n"


def test_timeout_escalates_to_sigkill_and_reaps_process_group() -> None:
    result = run_supervised_jcode_command(
        [
            sys.executable,
            "-c",
            "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)",
        ],
        JCodeSupervisionConfig(timeout_seconds=0.1, termination_grace_seconds=0.1),
    )

    assert result["status"] == "timed_out"
    assert result["termination_signal"] == "SIGKILL"
    assert result["process_group_reaped"] is True


def test_cancellation_terminates_before_timeout() -> None:
    deadline = time.monotonic() + 0.1
    result = run_supervised_jcode_command(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        JCodeSupervisionConfig(timeout_seconds=5, termination_grace_seconds=0.2),
        cancellation_requested=lambda: time.monotonic() >= deadline,
    )

    assert result["status"] == "cancelled"
    assert result["termination_signal"] == "SIGTERM"
    assert result["process_group_reaped"] is True


def test_timeout_kills_ignored_term_descendant_process_group() -> None:
    child = (
        "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)"
    )
    parent = (
        "import subprocess,sys,time; "
        f"subprocess.Popen([sys.executable, '-c', {child!r}]); "
        "time.sleep(30)"
    )
    result = run_supervised_jcode_command(
        [sys.executable, "-c", parent],
        JCodeSupervisionConfig(timeout_seconds=0.1, termination_grace_seconds=0.1),
    )

    assert result["status"] == "timed_out"
    assert result["termination_signal"] == "SIGKILL"
    assert result["process_group_reaped"] is True
