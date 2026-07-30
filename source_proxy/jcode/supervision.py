"""Process-group supervision for future JCode qualification commands only."""
from __future__ import annotations

import hashlib
import json
import os
import selectors
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from source_proxy.jcode.cgroup_scope import CgroupScopeConfig, build_cgroup_scope_args


CancellationCheck = Callable[[], bool]


@dataclass(frozen=True)
class JCodeSupervisionConfig:
    timeout_seconds: float
    termination_grace_seconds: float = 1.0
    poll_interval_seconds: float = 0.05


@dataclass(frozen=True)
class FixtureSupervisionConfig:
    """Gate 2-J.9C no-model process-tree and evidence policy."""

    readiness_timeout_seconds: float = 1.0
    inactivity_timeout_seconds: float = 1.0
    total_timeout_seconds: float = 5.0
    termination_grace_seconds: float = 0.1
    max_stdout_bytes: int = 16_384
    max_stderr_bytes: int = 16_384
    max_event_bytes: int = 16_384
    evidence_path: Path | None = None
    cgroup_scope: CgroupScopeConfig | None = None


def run_supervised_fixture(
    command: Sequence[str],
    config: FixtureSupervisionConfig,
    *,
    cancellation_requested: CancellationCheck | None = None,
) -> dict[str, object]:
    """Supervise an inert fixture with a separate structured event channel."""
    if not command or min(
        config.readiness_timeout_seconds,
        config.inactivity_timeout_seconds,
        config.total_timeout_seconds,
        config.termination_grace_seconds,
    ) <= 0:
        raise ValueError("jcode_fixture_supervision_configuration_invalid")
    event_read, event_write = os.pipe()
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "C2J_EVENT_FD": str(event_write)}
    # These two values are needed only by the outer systemd-run client. A later
    # containment command still clears them before the fixture starts.
    if config.cgroup_scope is not None:
        for name in ("DBUS_SESSION_BUS_ADDRESS", "XDG_RUNTIME_DIR"):
            if name in os.environ:
                env[name] = os.environ[name]
    launched = list(command)
    if config.cgroup_scope is not None:
        launched = build_cgroup_scope_args(launched, config.cgroup_scope)
    started = time.monotonic()
    process = subprocess.Popen(
        launched,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
        start_new_session=True,
        env=env,
        pass_fds=(event_write,),
    )
    os.close(event_write)
    assert process.stdout is not None and process.stderr is not None
    for handle in (process.stdout, process.stderr):
        os.set_blocking(handle.fileno(), False)
    os.set_blocking(event_read, False)
    streams = selectors.DefaultSelector()
    streams.register(process.stdout, selectors.EVENT_READ, "stdout")
    streams.register(process.stderr, selectors.EVENT_READ, "stderr")
    streams.register(event_read, selectors.EVENT_READ, "event")
    captured = {"stdout": bytearray(), "stderr": bytearray(), "event": bytearray()}
    truncated = {"stdout": False, "stderr": False, "event": False}
    limits = {"stdout": config.max_stdout_bytes, "stderr": config.max_stderr_bytes, "event": config.max_event_bytes}
    ready = False
    last_event = started
    descendants: set[int] = set()
    status: str | None = None
    signal_sent: str | None = None
    while status is None:
        descendants.update(_descendant_pids(process.pid))
        now = time.monotonic()
        if cancellation_requested is not None and cancellation_requested():
            status = "cancelled"
        elif now - started >= config.total_timeout_seconds:
            status = "total_timeout"
        elif not ready and now - started >= config.readiness_timeout_seconds:
            status = "readiness_timeout"
        elif ready and now - last_event >= config.inactivity_timeout_seconds:
            status = "inactivity_timeout"
        elif process.poll() is not None:
            status = "completed" if process.returncode == 0 and ready else "exited_before_ready"
            if process.returncode not in (0, None):
                status = "nonzero_exit"
        for key, _ in streams.select(timeout=0.02):
            name = str(key.data)
            try:
                chunk = os.read(key.fileobj if isinstance(key.fileobj, int) else key.fileobj.fileno(), 65_536)
            except BlockingIOError:
                continue
            if not chunk:
                streams.unregister(key.fileobj)
                continue
            available = max(0, limits[name] - len(captured[name]))
            captured[name].extend(chunk[:available])
            truncated[name] = truncated[name] or len(chunk) > available
            if name == "event":
                last_event = time.monotonic()
                if b"process.started\n" in captured[name] or b"process.started\r\n" in captured[name]:
                    ready = True
            if truncated[name] and status is None:
                status = f"{name}_limit_exceeded"
        if status is not None and process.poll() is None:
            signal_sent = _terminate_process_group(process, config.termination_grace_seconds)
    if process.poll() is None:
        process.wait(timeout=config.termination_grace_seconds + 1)
    descendants.update(_descendant_pids(process.pid))
    descendants_killed = _kill_pids(descendants)
    process_group_reaped = _wait_for_process_group_reap(process.pid)
    for fileobj in tuple(streams.get_map().values()):
        try:
            streams.unregister(fileobj.fileobj)
        except KeyError:
            pass
    streams.close()
    os.close(event_read)
    result: dict[str, object] = {
        "status": status,
        "process_exit_code": process.returncode,
        "termination_signal": signal_sent,
        "process_group_reaped": process_group_reaped,
        "cgroup_empty": process_group_reaped,
        "descendants_killed": descendants_killed,
        "readiness_received": ready,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "stdout": captured["stdout"].decode("utf-8", errors="replace"),
        "stderr": captured["stderr"].decode("utf-8", errors="replace"),
        "events_ndjson": captured["event"].decode("utf-8", errors="replace"),
        "output_truncated": truncated,
    }
    result["evidence_hashes"] = {
        name: hashlib.sha256(bytes(value)).hexdigest() for name, value in captured.items()
    }
    result["evidence_sealed"] = _seal_fixture_evidence(result, config.evidence_path)
    if not result["evidence_sealed"]:
        result["status"] = "evidence_write_failed"
    return result


def _seal_fixture_evidence(result: dict[str, object], path: Path | None) -> bool:
    if path is None:
        return True
    try:
        path.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    except OSError:
        return False
    return path.is_file() and path.stat().st_size > 0


def _descendant_pids(root_pid: int) -> set[int]:
    discovered: set[int] = set()
    pending = [root_pid]
    while pending:
        pid = pending.pop()
        try:
            raw = Path(f"/proc/{pid}/task/{pid}/children").read_text(encoding="utf-8")
        except OSError:
            continue
        for value in raw.split():
            child = int(value)
            if child not in discovered:
                discovered.add(child)
                pending.append(child)
    return discovered


def _kill_pids(pids: set[int]) -> int:
    killed = 0
    for pid in sorted(pids, reverse=True):
        try:
            os.kill(pid, signal.SIGKILL)
            killed += 1
        except ProcessLookupError:
            continue
        except PermissionError:
            continue
    return killed


def reap_fixture_descendants(pids: set[int]) -> int:
    """Idempotently reap already-observed deterministic fixture descendants."""
    return _kill_pids(set(pids))


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
