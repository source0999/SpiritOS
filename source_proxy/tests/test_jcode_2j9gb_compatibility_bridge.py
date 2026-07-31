from __future__ import annotations

import socket
import threading
from pathlib import Path

from source_proxy.jcode.inference_bridge import FakeInferenceResponse, SealedFakeInferenceBridge, SealedInferenceBinding
from source_proxy.jcode.sealed_compatibility_bridge import SealedCompatibilityBridge


def _bridge(path: Path) -> SealedCompatibilityBridge:
    binding = SealedInferenceBinding("task", "run", "corr", "auth", "profile", "registry", "qwen2.5-coder:7b")
    fake = SealedFakeInferenceBridge(binding, lambda prompt: FakeInferenceResponse("qwen2.5-coder:7b", "deterministic answer", len(prompt.split()), 2))
    return SealedCompatibilityBridge(path, fake)


def _request(path: Path, body: bytes) -> bytes:
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(str(path))
    client.sendall(b"POST /v1/chat/completions HTTP/1.1\r\nHost: local\r\nContent-Type: application/json\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)
    chunks: list[bytes] = []
    while chunk := client.recv(4096):
        chunks.append(chunk)
    client.close()
    return b"".join(chunks)


def test_compatibility_bridge_maps_one_openai_request_to_the_sealed_fake_backend(tmp_path: Path) -> None:
    bridge = _bridge(tmp_path / "inference.sock"); bridge.start()
    worker = threading.Thread(target=bridge.serve_one); worker.start()
    response = _request(bridge.socket_path, b'{"model":"qwen2.5-coder:7b","messages":[{"role":"user","content":"inspect authority"}]}')
    worker.join(timeout=2); bridge.close()
    assert b"HTTP/1.1 200 OK" in response and b"Transfer-Encoding: chunked" in response and b"deterministic answer" in response and b"[DONE]" in response
    assert bridge.request_count == 1 and bridge.request_bytes > 0


def test_compatibility_bridge_rejects_an_unregistered_model_without_fake_backend_use(tmp_path: Path) -> None:
    bridge = _bridge(tmp_path / "inference.sock"); bridge.start()
    worker = threading.Thread(target=bridge.serve_one); worker.start()
    response = _request(bridge.socket_path, b'{"model":"other","messages":[]}')
    worker.join(timeout=2); bridge.close()
    assert b"HTTP/1.1 400 Bad Request" in response
    assert bridge.request_count == 1
    assert bridge.bridge.events_ndjson(final=False) == b""


def test_compatibility_bridge_accepts_a_supervisor_owned_socketpair(tmp_path: Path) -> None:
    bridge = _bridge(tmp_path / "inference.sock")
    server, client = socket.socketpair()
    worker = threading.Thread(target=bridge.serve_client, args=(server,)); worker.start()
    body = b'{"model":"qwen2.5-coder:7b","messages":[{"content":"x"}]}'
    client.sendall(b"POST /v1/chat/completions HTTP/1.1\r\nHost: local\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)
    response = client.recv(4096); client.close(); worker.join(timeout=2)
    assert b"HTTP/1.1 200 OK" in response
