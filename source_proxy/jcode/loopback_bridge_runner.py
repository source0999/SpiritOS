"""Sandbox-local TCP to Unix-socket relay used only by 2-J qualification."""
from __future__ import annotations

import argparse
import select
import socket
import subprocess
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
    stopped = threading.Event()
    worker = threading.Thread(
        target=_serve,
        args=(listener, args.socket, stopped),
        daemon=True,
    )
    worker.start()
    try:
        return subprocess.run(command, check=False).returncode
    finally:
        stopped.set()
        listener.close()
        worker.join(timeout=2)


def _serve(listener: socket.socket, socket_path: str, stopped: threading.Event) -> None:
    while not stopped.is_set():
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
            destination.sendall(payload)


if __name__ == "__main__":
    raise SystemExit(main())
