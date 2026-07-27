from __future__ import annotations

import http.server
import shutil
import socket
import subprocess
import threading
from pathlib import Path

import pytest

from source_proxy.jcode.containment import JCodeContainmentConfig
from source_proxy.jcode.network_bridge import (
    FixedLoopbackUnixBridge,
    JCodeInferenceEndpoint,
    JCodeNetworkBridgeError,
    build_jcode_loopback_bridge_args,
)


class _QualifiedHandler(http.server.BaseHTTPRequestHandler):
    requests = 0

    def do_GET(self) -> None:  # noqa: N802
        type(self).requests += 1
        body = b"qualified-loopback-only"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_: object) -> None:
        return


def _containment(tmp_path: Path) -> JCodeContainmentConfig:
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    workspace.mkdir()
    home.mkdir()
    (workspace / "input.txt").write_text("input\n", encoding="utf-8")
    return JCodeContainmentConfig(
        workspace=workspace,
        jcode_home=home,
        allowed_files=("input.txt",),
    )


def _server() -> tuple[http.server.ThreadingHTTPServer, threading.Thread]:
    _QualifiedHandler.requests = 0
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _QualifiedHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


@pytest.mark.skipif(shutil.which("bwrap") is None, reason="bubblewrap unavailable")
def test_sandbox_can_reach_only_local_relay_for_fixed_loopback_endpoint(tmp_path: Path) -> None:
    containment = _containment(tmp_path)
    bridge_directory = tmp_path / "bridge"
    bridge_directory.mkdir()
    server, thread = _server()
    endpoint = JCodeInferenceEndpoint("127.0.0.1", server.server_port)
    try:
        with FixedLoopbackUnixBridge(
            socket_path=bridge_directory / "inference.sock",
            endpoint=endpoint,
        ):
            command = [
                "/usr/bin/python3",
                "-c",
                (
                    "import socket; "
                    "direct = socket.socket(); direct.settimeout(0.5); "
                    f"assert direct.connect_ex(('127.0.0.1', {server.server_port})) != 0; "
                    "direct.close(); "
                    "from urllib.request import urlopen; "
                    "print(urlopen('http://127.0.0.1:43123/v1/models', timeout=3).read().decode())"
                ),
            ]
            args = build_jcode_loopback_bridge_args(
                command,
                containment,
                bridge_directory=bridge_directory,
                sandbox_listen_port=43123,
            )
            result = subprocess.run(args, capture_output=True, text=True, check=False)

        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "qualified-loopback-only"
        assert _QualifiedHandler.requests == 1
        assert "--unshare-net" in args
        assert str(bridge_directory.resolve()) in args
        assert str(server.server_port) not in args
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def test_bridge_rejects_non_loopback_and_nondedicated_socket_directory(tmp_path: Path) -> None:
    with pytest.raises(JCodeNetworkBridgeError, match="not_loopback"):
        JCodeInferenceEndpoint("10.0.0.9", 11434).validate()

    containment = _containment(tmp_path)
    bridge_directory = tmp_path / "bridge"
    bridge_directory.mkdir()
    (bridge_directory / "unexpected.txt").write_text("no", encoding="utf-8")
    with pytest.raises(JCodeNetworkBridgeError, match="not_dedicated"):
        build_jcode_loopback_bridge_args(
            ["/bin/true"],
            containment,
            bridge_directory=bridge_directory,
            sandbox_listen_port=43123,
        )


def test_host_bridge_dials_exact_configured_endpoint(tmp_path: Path) -> None:
    bridge_directory = tmp_path / "bridge"
    bridge_directory.mkdir()
    server, thread = _server()
    try:
        with FixedLoopbackUnixBridge(
            socket_path=bridge_directory / "inference.sock",
            endpoint=JCodeInferenceEndpoint("127.0.0.1", server.server_port),
        ):
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.connect(str(bridge_directory / "inference.sock"))
            client.sendall(b"GET /v1/models HTTP/1.1\r\nHost: qualified\r\n\r\n")
            response = client.recv(4096)
            client.close()

        assert b"qualified-loopback-only" in response
        assert _QualifiedHandler.requests == 1
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()
