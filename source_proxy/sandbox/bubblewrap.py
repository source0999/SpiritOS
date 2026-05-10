from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


class BubblewrapUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class BubblewrapConfig:
    workspace: Path | None = None
    bwrap_path: str = "bwrap"
    seccomp_profile: Path | None = None
    network_policy: str = "none"
    clearenv: bool = True


def build_bubblewrap_args(
    command: Sequence[str],
    config: BubblewrapConfig | None = None,
    *,
    seccomp_fd: int | None = None,
) -> list[str]:
    if not command:
        raise ValueError("Sandbox command must not be empty.")

    cfg = config or BubblewrapConfig()
    args = [
        cfg.bwrap_path,
        "--unshare-user",
        "--unshare-pid",
        "--unshare-ipc",
        "--unshare-uts",
        "--unshare-cgroup",
        "--new-session",
        "--die-with-parent",
        "--cap-drop",
        "ALL",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--dir",
        "/run",
        "--dir",
        "/var",
        "--ro-bind",
        "/usr",
        "/usr",
        "--ro-bind",
        "/bin",
        "/bin",
        "--ro-bind",
        "/lib",
        "/lib",
        "--ro-bind-try",
        "/lib64",
        "/lib64",
        "--ro-bind-try",
        "/etc/alternatives",
        "/etc/alternatives",
        "--ro-bind-try",
        "/etc/ssl",
        "/etc/ssl",
        "--ro-bind-try",
        "/etc/resolv.conf",
        "/etc/resolv.conf",
        "--ro-bind-try",
        "/etc/hosts",
        "/etc/hosts",
        "--ro-bind-try",
        "/etc/nsswitch.conf",
        "/etc/nsswitch.conf",
        "--setenv",
        "HOME",
        "/tmp",
        "--setenv",
        "TMPDIR",
        "/tmp",
    ]

    if cfg.network_policy == "none":
        args.insert(1, "--unshare-net")
    elif cfg.network_policy != "trusted_command":
        raise ValueError("network_policy must be 'none' or 'trusted_command'.")

    if cfg.clearenv:
        args.insert(1, "--clearenv")

    if cfg.workspace is not None:
        workspace = cfg.workspace.resolve()
        args.extend(["--ro-bind", str(workspace), "/workspace", "--chdir", "/workspace"])

    if seccomp_fd is not None:
        args.extend(["--seccomp", str(seccomp_fd)])

    args.extend(["--", *command])
    return args


def run_bubblewrap(
    command: Sequence[str],
    config: BubblewrapConfig | None = None,
    *,
    timeout_seconds: int = 30,
) -> subprocess.CompletedProcess[str]:
    cfg = config or BubblewrapConfig()
    if cfg.network_policy == "trusted_command" and not is_trusted_network_command(command):
        return subprocess.CompletedProcess(
            args=list(command),
            returncode=126,
            stdout="",
            stderr=(
                "Source sandbox blocked network command: only trusted registry "
                "probes are allowed in trusted_command mode.\n"
            ),
        )

    if shutil.which(cfg.bwrap_path) is None:
        raise BubblewrapUnavailable(
            f"{cfg.bwrap_path!r} was not found. Install Bubblewrap on the Linux host."
        )

    if cfg.seccomp_profile is None:
        args = build_bubblewrap_args(command, cfg)
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )

    with cfg.seccomp_profile.open("rb") as seccomp_file:
        args = build_bubblewrap_args(command, cfg, seccomp_fd=seccomp_file.fileno())
        return subprocess.run(
            args,
            pass_fds=(seccomp_file.fileno(),),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )


def probe_home_is_hidden(config: BubblewrapConfig | None = None) -> dict[str, object]:
    result = run_bubblewrap(["/bin/ls", "/home"], config)
    stderr = result.stderr.strip()
    setup_error = _bubblewrap_setup_error(stderr)
    return {
        "status": "setup_failed" if setup_error else "completed",
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": stderr,
        "home_hidden": not setup_error
        and result.returncode != 0
        and "no such file or directory" in stderr.lower(),
        "setup_error": setup_error,
        "recommended_fix": _setup_recommended_fix(stderr) if setup_error else None,
    }


def probe_network_denied(config: BubblewrapConfig | None = None) -> dict[str, object]:
    cfg = config or BubblewrapConfig(network_policy="none")
    result = run_bubblewrap(["/usr/bin/curl", "-IsS", "--max-time", "5", "https://google.com"], cfg)
    stderr = result.stderr.strip()
    setup_error = _bubblewrap_setup_error(stderr)
    return {
        "status": "setup_failed" if setup_error else "completed",
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": stderr,
        "network_denied": setup_error is None and result.returncode != 0,
        "setup_error": setup_error,
        "recommended_fix": _setup_recommended_fix(stderr) if setup_error else None,
    }


def probe_npm_registry_allowed(config: BubblewrapConfig | None = None) -> dict[str, object]:
    cfg = config or BubblewrapConfig(network_policy="trusted_command")
    result = run_bubblewrap(["/usr/bin/npm", "ping", "--registry", "https://registry.npmjs.org"], cfg)
    stderr = result.stderr.strip()
    setup_error = _bubblewrap_setup_error(stderr)
    return {
        "status": "setup_failed" if setup_error else "completed",
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": stderr,
        "registry_allowed": setup_error is None and result.returncode == 0,
        "trusted_command_gate": True,
        "setup_error": setup_error,
        "recommended_fix": _setup_recommended_fix(stderr) if setup_error else None,
    }


def is_trusted_network_command(command: Sequence[str]) -> bool:
    if len(command) < 2:
        return False
    executable = Path(command[0]).name
    if executable != "npm":
        return False
    if command[1] != "ping":
        return False
    joined = " ".join(command)
    return "https://registry.npmjs.org" in joined and "google.com" not in joined


def _bubblewrap_setup_error(stderr: str) -> str | None:
    lowered = stderr.lower()
    if "setting up uid map" in lowered and "permission denied" in lowered:
        return "uid_map_permission_denied"
    if "no permissions to create new namespace" in lowered:
        return "user_namespace_unavailable"
    if "creating new namespace failed" in lowered and "permission denied" in lowered:
        return "apparmor_userns_denied"
    if "operation not permitted" in lowered:
        return "operation_not_permitted"
    if "can't read /proc/sys/kernel/overflow" in lowered:
        return "apparmor_proc_sys_kernel_denied"
    if "failed to make / slave" in lowered:
        return "apparmor_mount_setup_denied"
    if "pivot root" in lowered or "pivot_root" in lowered:
        return "apparmor_pivot_root_denied"
    if "can't mkdir /proc" in lowered:
        return "apparmor_proc_mountpoint_denied"
    if "can't open /proc/self/mountinfo" in lowered:
        return "apparmor_mountinfo_denied"
    return None


def _setup_recommended_fix(stderr: str) -> str:
    setup_error = _bubblewrap_setup_error(stderr)
    if setup_error == "uid_map_permission_denied":
        return (
            "Enable unprivileged user namespaces or install Bubblewrap with the "
            "host-supported setuid/newuidmap configuration."
        )
    if setup_error == "user_namespace_unavailable":
        return "Enable kernel unprivileged user namespaces for this host."
    if setup_error == "apparmor_userns_denied":
        return "Allow user namespace creation in the Source AppArmor profile."
    if setup_error == "apparmor_proc_sys_kernel_denied":
        return "Allow Bubblewrap read access to /proc/sys/kernel/overflowuid and overflowgid in the Source AppArmor profile."
    if setup_error == "apparmor_mount_setup_denied":
        return "Allow Bubblewrap mount setup mediation in the Source AppArmor profile."
    if setup_error == "apparmor_pivot_root_denied":
        return "Allow Bubblewrap pivot_root mediation in the Source AppArmor profile."
    if setup_error == "apparmor_proc_mountpoint_denied":
        return "Allow Bubblewrap to create the sandbox /proc mount point in the Source AppArmor profile."
    if setup_error == "apparmor_mountinfo_denied":
        return "Allow Bubblewrap read access to /proc/self/mountinfo in the Source AppArmor profile."
    return "Check Bubblewrap permissions and user namespace support on the Linux host."


def main() -> None:
    parser = argparse.ArgumentParser(description="Run commands inside Source Bubblewrap sandbox.")
    parser.add_argument("--workspace", type=Path, default=None)
    parser.add_argument(
        "--seccomp-profile",
        type=Path,
        default=os.getenv("SOURCE_PROXY_BWRAP_SECCOMP_PROFILE"),
    )
    parser.add_argument("--timeout", type=int, default=30)

    subparsers = parser.add_subparsers(dest="command_name", required=True)
    subparsers.add_parser("probe-home")
    subparsers.add_parser("probe-network-deny")
    subparsers.add_parser("probe-npm-registry")

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument(
        "--network-policy",
        choices=["none", "trusted_command"],
        default="none",
    )
    run_parser.add_argument("command", nargs=argparse.REMAINDER)

    args = parser.parse_args()
    config = BubblewrapConfig(
        workspace=args.workspace,
        seccomp_profile=args.seccomp_profile,
        network_policy=getattr(args, "network_policy", "none"),
    )

    if args.command_name == "probe-home":
        payload = probe_home_is_hidden(config)
        print(json.dumps(payload, indent=2))
        sys.exit(0 if payload["home_hidden"] else 1)
    if args.command_name == "probe-network-deny":
        payload = probe_network_denied(config)
        print(json.dumps(payload, indent=2))
        sys.exit(0 if payload["network_denied"] else 1)
    if args.command_name == "probe-npm-registry":
        payload = probe_npm_registry_allowed(
            BubblewrapConfig(
                workspace=args.workspace,
                seccomp_profile=args.seccomp_profile,
                network_policy="trusted_command",
            )
        )
        print(json.dumps(payload, indent=2))
        sys.exit(0 if payload["registry_allowed"] else 1)

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("run requires a command after --")

    result = run_bubblewrap(command, config, timeout_seconds=args.timeout)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
