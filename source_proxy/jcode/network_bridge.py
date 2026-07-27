"""Single-endpoint network bridge for the JCode qualification sandbox.

The JCode process remains in Bubblewrap's network namespace.  It can reach
only a TCP listener on its own loopback interface; that listener forwards over
one read-only Unix-domain socket to this host-side bridge.  The host-side
bridge, in turn, dials only the configured loopback inference endpoint.
"""
from __future__ import annotations

import select
import socket
import stat
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from source_proxy.jcode.containment import (
    JCodeContainmentConfig,
    build_jcode_containment_args,
)

class JCodeNetworkBridgeError(ValueError):
    """The one-endpoint bridge cannot be configured safely."""


@dataclass(frozen=True)
class JCodeInferenceEndpoint:
    host: str
    port: int

    def validate(self) -> None:
        if self.host not in {"127.0.0.1", "::1"}:
            raise JCodeNetworkBridgeError("jcode_bridge_endpoint_not_loopback")
        if not 1 <= self.port <= 65535:
            raise JCodeNetworkBridgeError("jcode_bridge_endpoint_port_invalid")


class FixedLoopbackUnixBridge:
    """Expose one Unix socket that forwards only to one loopback endpoint."""

    def __init__(
        self,
        *,
        socket_path: Path,
        endpoint: JCodeInferenceEndpoint,
        connect_timeout_seconds: float = 5.0,
    ) -> None:
        endpoint.validate()
        self.socket_path = socket_path.resolve()
        self.endpoint = endpoint
        self.connect_timeout_seconds = connect_timeout_seconds
        self._listener: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stopped = threading.Event()

    def start(self) -> None:
        parent = self.socket_path.parent
        if not parent.is_dir() or parent.is_symlink() or self.socket_path.exists():
            raise JCodeNetworkBridgeError("jcode_bridge_socket_parent_invalid")
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(str(self.socket_path))
        self.socket_path.chmod(0o600)
        listener.listen(8)
        listener.settimeout(0.2)
        self._listener = listener
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._stopped.set()
        if self._listener is not None:
            self._listener.close()
        if self._thread is not None:
            self._thread.join(timeout=2)
        if self.socket_path.exists() or self.socket_path.is_symlink():
            self.socket_path.unlink()

    def __enter__(self) -> "FixedLoopbackUnixBridge":
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _serve(self) -> None:
        assert self._listener is not None
        while not self._stopped.is_set():
            try:
                client, _ = self._listener.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            threading.Thread(target=self._forward_client, args=(client,), daemon=True).start()

    def _forward_client(self, client: socket.socket) -> None:
        try:
            upstream = socket.create_connection(
                (self.endpoint.host, self.endpoint.port),
                timeout=self.connect_timeout_seconds,
            )
        except OSError:
            client.close()
            return
        try:
            _copy_bidirectionally(client, upstream)
        finally:
            client.close()
            upstream.close()


def build_jcode_loopback_bridge_args(
    command: Sequence[str],
    containment: JCodeContainmentConfig,
    *,
    bridge_directory: Path,
    sandbox_listen_port: int,
) -> list[str]:
    """Wrap a command with a sandbox-local TCP to Unix-socket relay."""
    if not 1 <= sandbox_listen_port <= 65535:
        raise JCodeNetworkBridgeError("jcode_bridge_sandbox_port_invalid")
    directory = _validated_bridge_directory(bridge_directory)
    socket_path = directory / "inference.sock"
    if not stat.S_ISSOCK(socket_path.stat().st_mode):
        raise JCodeNetworkBridgeError("jcode_bridge_socket_missing")
    runner = Path(__file__).with_name("loopback_bridge_runner.py").resolve()
    if not runner.is_file() or runner.is_symlink():
        raise JCodeNetworkBridgeError("jcode_bridge_runner_missing")
    runner_source = runner.read_text(encoding="utf-8")
    args = build_jcode_containment_args(command, containment)
    chdir_index = args.index("--chdir")
    extra_mounts = [
        "--ro-bind",
        str(directory),
        "/run/jcode-bridge",
    ]
    command_index = args.index("--")
    wrapped_command = [
        "/usr/bin/python3",
        "-c",
        runner_source,
        "--socket",
        "/run/jcode-bridge/inference.sock",
        "--listen-port",
        str(sandbox_listen_port),
        "--",
        *command,
    ]
    return [
        *args[:chdir_index],
        *extra_mounts,
        *args[chdir_index:command_index],
        "--",
        *wrapped_command,
    ]


def _validated_bridge_directory(value: Path) -> Path:
    directory = value.resolve()
    if not directory.is_dir() or directory.is_symlink():
        raise JCodeNetworkBridgeError("jcode_bridge_directory_invalid")
    if any(entry.name != "inference.sock" for entry in directory.iterdir()):
        raise JCodeNetworkBridgeError("jcode_bridge_directory_not_dedicated")
    return directory


def _copy_bidirectionally(left: socket.socket, right: socket.socket) -> None:
    sockets = (left, right)
    while True:
        readable, _, _ = select.select(sockets, (), (), 0.2)
        if not readable:
            continue
        for source in readable:
            destination = right if source is left else left
            payload = source.recv(64 * 1024)
            if not payload:
                return
            try:
                destination.sendall(payload)
            except OSError:
                # A client may close after a complete response; do not leave a
                # bridge worker exception or continue forwarding stale bytes.
                return
