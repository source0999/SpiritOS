"""Process-group supervision for future JCode qualification commands only."""
from __future__ import annotations

import os
import signal
import subprocess
import time
from dataclasses import dataclass
from typing import Callable, Sequence


CancellationCheck = Callable[[], bool]


@dataclass(frozen=True)
class JCodeSupervisionConfig:
    timeout_seconds: float
    termination_grace_seconds: float = 1.0
    poll_interval_seconds: float = 0.05


def run_supervised_jcode_command(
    command: Sequence[str],
    config: JCodeSupervisionConfig,
    *,
    cancellation_requested: CancellationCheck | None = None,
) -> dict[str, object]:
    """Run one process group and always return a terminal, reaped receipt."""
    if not command or config.timeout_seconds <= 0 or config.termination_grace_seconds <= 0:
        raise ValueError("jcode_supervision_configuration_invalid")
    started = time.monotonic()
    process = subprocess.Popen(
        list(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    disposition = "completed"
    signal_sent: str | None = None
    while process.poll() is None:
        if cancellation_requested is not None and cancellation_requested():
            disposition = "cancelled"
            signal_sent = _terminate_process_group(process, config.termination_grace_seconds)
            break
        if time.monotonic() - started >= config.timeout_seconds:
            disposition = "timed_out"
            signal_sent = _terminate_process_group(process, config.termination_grace_seconds)
            break
        time.sleep(config.poll_interval_seconds)
    stdout, stderr = process.communicate()
    return {
        "status": disposition,
        "process_exit_code": process.returncode,
        "termination_signal": signal_sent,
        "process_group_reaped": _wait_for_process_group_reap(process.pid),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "stdout": stdout,
        "stderr": stderr,
    }


def _terminate_process_group(process: subprocess.Popen[str], grace_seconds: float) -> str:
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        pass
    if process.poll() is not None and _process_group_is_gone(process.pid):
        return "SIGTERM"
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return "SIGTERM"
    return "SIGKILL"


def _process_group_is_gone(pid: int) -> bool:
    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False


def _wait_for_process_group_reap(pid: int, timeout_seconds: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if _process_group_is_gone(pid):
            return True
        time.sleep(0.02)
    return _process_group_is_gone(pid)
