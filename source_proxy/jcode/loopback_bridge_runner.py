"""Sandbox-local TCP to Unix-socket relay used only by 2-J qualification."""
from __future__ import annotations

import argparse
import ctypes
import os
import resource
import select
import socket
import threading
from typing import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", required=True)
    parser.add_argument("--listen-port", required=True, type=int)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = list(args.command)
    if command[:1] == ["--"]:
        command = command[1:]
    if not command or not 1 <= args.listen_port <= 65535:
        return 64
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", args.listen_port))
    listener.listen(8)
    listener.settimeout(0.2)
    listener_pid = os.fork()
    if listener_pid == 0:
        _set_parent_death_signal()
        if os.getppid() == 1:
            return 70
        _serve(listener, args.socket)
        return 0

    # Do not make JCode a child of the relay. Replacing the original sandbox
    # process preserves the direct-launch PID, namespace, session, stdio, and
    # environment while leaving the listener as a supervised sibling.
    listener.close()
    _close_nonstandard_fds()
    os.execvpe(command[0], command, os.environ)
    return 70


def _serve(listener: socket.socket, socket_path: str) -> None:
    while True:
        try:
            client, _ = listener.accept()
        except TimeoutError:
            continue
        except OSError:
            return
        threading.Thread(
            target=_forward_client,
            args=(client, socket_path),
            daemon=True,
        ).start()


def _set_parent_death_signal() -> None:
    # Linux PR_SET_PDEATHSIG keeps the sidecar from surviving the exec'd JCode
    # process. Failure is fatal because a detached listener would break cleanup
    # evidence and leave a stale authority boundary behind.
    if ctypes.CDLL(None, use_errno=True).prctl(1, 15, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "prctl(PR_SET_PDEATHSIG) failed")


def _close_nonstandard_fds() -> None:
    soft_limit, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
    upper = 65_536 if soft_limit == resource.RLIM_INFINITY else int(soft_limit)
    if upper > 3:
        os.closerange(3, upper)


def _forward_client(client: socket.socket, socket_path: str) -> None:
    upstream = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        upstream.connect(socket_path)
        _copy_bidirectionally(client, upstream)
    except OSError:
        pass
    finally:
        client.close()
        upstream.close()


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
                return


if __name__ == "__main__":
    raise SystemExit(main())
