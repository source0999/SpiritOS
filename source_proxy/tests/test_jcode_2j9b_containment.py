"""Gate 2-J.9B no-model containment proof with inert Python fixtures."""
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

import pytest

from source_proxy.jcode.cgroup_scope import CgroupScopeConfig, build_cgroup_scope_args
from source_proxy.jcode.containment import (
    ContainmentFixtureConfig,
    JCodeContainmentError,
    build_contained_fixture_args,
    containment_fixture_cleanup,
    run_contained_fixture,
)


pytestmark = pytest.mark.skipif(
    shutil.which("bwrap") is None or shutil.which("systemd-run") is None,
    reason="Gate 2-J.9B requires Bubblewrap and systemd-run",
)


def _config(tmp_path: Path, run_id: str = "fixture-9b") -> ContainmentFixtureConfig:
    run_root = tmp_path / run_id
    fixture_input = run_root / "input"
    fixture_output = run_root / "output"
    isolated_home = run_root / "home"
    isolated_tmp = run_root / "tmp"
    run_root.mkdir()
    for path in (fixture_input, fixture_output, isolated_home, isolated_tmp):
        path.mkdir()
    fixture_input.chmod(0o755)
    for path in (fixture_output, isolated_home, isolated_tmp):
        path.chmod(0o777)
    (fixture_input / "approved.txt").write_text("approved\n", encoding="utf-8")
    return ContainmentFixtureConfig(
        run_id=run_id,
        fixture_input=fixture_input,
        fixture_output=fixture_output,
        isolated_home=isolated_home,
        isolated_tmp=isolated_tmp,
    )


def _run(script: str, config: ContainmentFixtureConfig, **limits: int):
    if limits:
        config = ContainmentFixtureConfig(**{**config.__dict__, **limits})
    return run_contained_fixture(["/usr/bin/python3", "-c", script], config, timeout_seconds=15)


def test_constructs_namespace_and_cgroup_boundary(tmp_path: Path) -> None:
    config = _config(tmp_path)
    args = build_contained_fixture_args(["/bin/true"], config)
    for flag in ("--unshare-user", "--unshare-pid", "--unshare-ipc", "--unshare-uts", "--unshare-cgroup", "--unshare-net", "--clearenv", "--cap-drop"):
        assert flag in args
    assert "--tmpfs" in args
    assert "/tmp/input" in args
    assert "/tmp/output" in args
    scope = build_cgroup_scope_args(args, CgroupScopeConfig("fixture-9b", 1024, 8, 25, 1024, 32))
    assert "--property=MemoryMax=1024" in scope
    assert "--property=TasksMax=8" in scope
    assert "--property=CPUQuota=25%" in scope
    assert "LimitFSIZE" not in " ".join(scope)
    assert "--as=536870912" in args
    assert "--fsize=10485760" in args


def test_transient_scope_reports_cgroup_resource_ownership() -> None:
    config = CgroupScopeConfig("properties-9b", 33_554_432, 16, 25, 1024, 32)
    process = subprocess.Popen(build_cgroup_scope_args(["/bin/sleep", "0.25"], config))
    try:
        time.sleep(0.05)
        shown = subprocess.run(
            [
                "systemctl", "--user", "show", "jcode-run-properties-9b.scope",
                "-p", "MemoryMax", "-p", "TasksMax", "-p", "CPUQuotaPerSecUSec",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert shown.returncode == 0, shown.stderr
        assert "MemoryMax=33554432" in shown.stdout
        assert "TasksMax=16" in shown.stdout
        assert "CPUQuotaPerSecUSec=250ms" in shown.stdout
    finally:
        assert process.wait(timeout=5) == 0


def test_approved_input_and_output_succeed_with_sanitized_environment(tmp_path: Path) -> None:
    config = _config(tmp_path)
    result = _run(
        "import os,pathlib; "
        "assert pathlib.Path('/tmp/input/approved.txt').read_text() == 'approved\\n'; "
        "pathlib.Path('/tmp/output/result.txt').write_text(os.environ['HOME'] + '|' + os.environ['LANG']); "
        "assert not any(name in os.environ for name in ('SSH_AUTH_SOCK', 'AWS_ACCESS_KEY_ID', 'OLLAMA_HOST', 'DOCKER_HOST')); "
        "assert open('/proc/self/status').read().split('CapEff:\\t')[1].split('\\n', 1)[0] == '0000000000000000'; "
        "assert not pathlib.Path('/dev/sda').exists(); "
        "print(pathlib.Path('/tmp/output/result.txt').read_text())",
        config,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "/tmp/home|C"


@pytest.mark.parametrize(
    "script",
    [
        "from pathlib import Path; assert not Path('/home/source/SpiritOS').exists()",
        "from pathlib import Path; assert not Path('/home/sandbox/.ssh').exists()",
        "from pathlib import Path; assert not Path('/var/run/docker.sock').exists()",
        "from pathlib import Path; assert not Path('/var/run/tailscale/tailscaled.sock').exists()",
        "from pathlib import Path; assert not Path('/run/systemd/private').exists()",
        "from pathlib import Path; assert not Path('/benchmark-expectations').exists()",
    ],
)
def test_forbidden_host_paths_are_not_visible(tmp_path: Path, script: str) -> None:
    result = _run(script, _config(tmp_path))
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "script",
    [
        "from pathlib import Path; Path('/tmp/input/approved.txt').write_text('blocked')",
        "from pathlib import Path; Path('/tmp/input/../input/approved.txt').write_text('blocked')",
        "import os; os.setuid(1)",
    ],
)
def test_forbidden_writes_and_privilege_escalation_fail(tmp_path: Path, script: str) -> None:
    config = _config(tmp_path)
    result = _run(script, config)
    assert result.returncode != 0
    assert (config.fixture_input / "approved.txt").read_text() == "approved\n"


def test_network_dns_and_symlink_escape_are_denied(tmp_path: Path) -> None:
    config = _config(tmp_path)
    network = _run("import socket; socket.getaddrinfo('example.com', 443)", config)
    assert network.returncode != 0
    escape = _run(
        "import os; os.symlink('/tmp/input/approved.txt', '/tmp/output/escape'); "
        "open('/tmp/output/escape', 'w').write('blocked')",
        config,
    )
    assert escape.returncode != 0
    assert (config.fixture_input / "approved.txt").read_text() == "approved\n"


def test_file_size_and_process_budget_enforce_without_retained_processes(tmp_path: Path) -> None:
    size = _run(
        "from pathlib import Path; Path('/tmp/output/large.bin').write_bytes(b'x' * 4096)",
        _config(tmp_path, "fsize-9b"),
        file_size_max_bytes=1024,
    )
    assert size.returncode != 0
    pids = _run(
        """import os
import time
children = []
for _ in range(64):
    try:
        pid = os.fork()
    except OSError:
        break
    if pid == 0:
        time.sleep(0.05)
        os._exit(0)
    children.append(pid)
for pid in children:
    os.waitpid(pid, 0)
print(len(children))
""",
        _config(tmp_path, "pids-9b"),
        tasks_max=16,
    )
    assert pids.returncode == 0, pids.stderr
    assert int(pids.stdout.strip()) < 64


def test_memory_limit_and_parent_exit_cleanup_are_enforced(tmp_path: Path) -> None:
    memory = _run(
        "payload = bytearray(128 * 1024 * 1024); print(len(payload))",
        _config(tmp_path, "memory-9b"),
        memory_max_bytes=32 * 1024 * 1024,
    )
    assert memory.returncode != 0

    child = _run(
        """import os
import time
pid = os.fork()
if pid == 0:
    time.sleep(10)
    os._exit(0)
print(pid, flush=True)
""",
        _config(tmp_path, "reap-9b"),
    )
    assert child.returncode == 0, child.stderr
    assert child.stdout.strip().isdigit()
    scope = subprocess.run(
        ["systemctl", "--user", "show", "jcode-run-reap-9b.scope", "--property=ActiveState", "--value"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert scope.returncode != 0 or scope.stdout.strip() in {"inactive", "failed"}


def test_explicit_cleanup_removes_all_disposable_directories(tmp_path: Path) -> None:
    config = _config(tmp_path, "cleanup-9b")
    result = _run("print('done')", config)
    assert result.returncode == 0
    cleaned = containment_fixture_cleanup(
        [config.fixture_input, config.fixture_output, config.isolated_home, config.isolated_tmp]
    )
    assert all(cleaned.values())
    assert not any(tmp_path.iterdir())


def test_rejects_unsafe_fixture_directory(tmp_path: Path) -> None:
    config = _config(tmp_path)
    (tmp_path / "other").symlink_to(config.fixture_input)
    with pytest.raises(JCodeContainmentError, match="directory_invalid"):
        build_contained_fixture_args(
            ["/bin/true"],
            ContainmentFixtureConfig(
                run_id="bad-9b",
                fixture_input=tmp_path / "other",
                fixture_output=config.fixture_output,
                isolated_home=config.isolated_home,
                isolated_tmp=config.isolated_tmp,
            ),
        )
