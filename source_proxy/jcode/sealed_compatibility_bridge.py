"""One-request OpenAI-compatible facade for the sealed C2-J fake bridge."""
from __future__ import annotations

import json
import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from source_proxy.jcode.inference_bridge import SealedFakeInferenceBridge, SealedInferenceBridgeError


class SealedCompatibilityBridgeError(ValueError):
    """The contained compatibility request is malformed or out of scope."""


@dataclass
class SealedCompatibilityBridge:
    socket_path: Path
    bridge: SealedFakeInferenceBridge
    _listener: socket.socket | None = field(default=None, init=False)
    request_count: int = field(default=0, init=False)
    request_bytes: int = field(default=0, init=False)

    def start(self) -> None:
        if self.socket_path.exists() or self.socket_path.is_symlink() or not self.socket_path.parent.is_dir():
            raise SealedCompatibilityBridgeError("compatibility_socket_path_invalid")
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(str(self.socket_path))
        self.socket_path.chmod(0o600)
        listener.listen(1)
        self._listener = listener

    def close(self) -> None:
        if self._listener is not None:
            self._listener.close()
        self._listener = None
        if self.socket_path.exists() or self.socket_path.is_symlink():
            self.socket_path.unlink()

    def serve_one(self, timeout_seconds: float = 30.0) -> None:
        if self._listener is None:
            raise SealedCompatibilityBridgeError("compatibility_listener_not_started")
        self._listener.settimeout(timeout_seconds)
        client, _ = self._listener.accept()
        self.serve_client(client)

    def serve_client(self, client: socket.socket) -> None:
        try:
            request = _read_request(client)
            self.request_count += 1
            self.request_bytes += int(request["byte_count"])
            response = self._request_fake_backend(request)
            _send_sse(client, response)
        except (OSError, ValueError, json.JSONDecodeError, SealedInferenceBridgeError) as error:
            _send_error(client, str(error))
        finally:
            client.close()

    def _request_fake_backend(self, request: dict[str, object]) -> dict[str, object]:
        if request["method"] != "POST" or request["path"] != "/v1/chat/completions":
            raise SealedCompatibilityBridgeError("compatibility_route_denied")
        body = request["body"]
        if not isinstance(body, dict) or body.get("model") != self.bridge.binding.model:
            raise SealedCompatibilityBridgeError("compatibility_model_denied")
        messages = body.get("messages")
        if not isinstance(messages, list):
            raise SealedCompatibilityBridgeError("compatibility_messages_invalid")
        prompt = "\n".join(
            str(item.get("content", "")) for item in messages if isinstance(item, dict)
        ).strip()
        return self.bridge.request(
            {
                "task_id": self.bridge.binding.task_id,
                "run_id": self.bridge.binding.run_id,
                "correlation_id": self.bridge.binding.correlation_id,
                "authorization_id": self.bridge.binding.authorization_id,
                "provider_profile_id": self.bridge.binding.provider_profile_id,
                "model_registry_id": self.bridge.binding.model_registry_id,
                "model": self.bridge.binding.model,
                "route": "/api/generate",
                "parameters": {"temperature": 0},
                "request_id": f"compat-{self.request_count}",
                "prompt": prompt,
            }
        )


def _read_request(client: socket.socket) -> dict[str, object]:
    data = bytearray()
    while b"\r\n\r\n" not in data and len(data) <= 65_536:
        chunk = client.recv(4096)
        if not chunk:
            raise SealedCompatibilityBridgeError("compatibility_headers_incomplete")
        data.extend(chunk)
    raw_headers, body = bytes(data).split(b"\r\n\r\n", 1)
    lines = raw_headers.decode("ascii", errors="strict").split("\r\n")
    parts = lines[0].split()
    if len(parts) != 3:
        raise SealedCompatibilityBridgeError("compatibility_request_line_invalid")
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if ":" not in line:
            raise SealedCompatibilityBridgeError("compatibility_header_invalid")
        key, value = line.split(":", 1)
        headers[key.lower()] = value.strip()
    try:
        length = int(headers.get("content-length", "-1"))
    except ValueError as error:
        raise SealedCompatibilityBridgeError("compatibility_content_length_invalid") from error
    if not 0 <= length <= 65_536:
        raise SealedCompatibilityBridgeError("compatibility_body_size_invalid")
    while len(body) < length:
        chunk = client.recv(min(4096, length - len(body)))
        if not chunk:
            raise SealedCompatibilityBridgeError("compatibility_body_incomplete")
        body += chunk
    parsed = json.loads(body[:length].decode("utf-8"))
    return {"method": parts[0], "path": parts[1], "body": parsed, "byte_count": len(raw_headers) + 4 + length}


def _send_sse(client: socket.socket, response: dict[str, object]) -> None:
    text = str(response["text"])
    model = str(response["metadata"]["provider_reported_model"])
    events = [
        {"id": "c2j-fake-1", "object": "chat.completion.chunk", "model": model, "choices": [{"index": 0, "delta": {"role": "assistant", "content": text}, "finish_reason": None}]},
        {"id": "c2j-fake-1", "object": "chat.completion.chunk", "model": model, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
    ]
    body = b"".join(b"data: " + json.dumps(event, separators=(",", ":")).encode() + b"\n\n" for event in events) + b"data: [DONE]\n\n"
    chunks = f"{len(body):X}\r\n".encode() + body + b"\r\n0\r\n\r\n"
    client.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nCache-Control: no-cache\r\nConnection: close\r\nTransfer-Encoding: chunked\r\n\r\n" + chunks)


def _send_error(client: socket.socket, reason: str) -> None:
    body = json.dumps({"error": {"message": reason, "type": "invalid_request_error"}}, separators=(",", ":")).encode()
    client.sendall(b"HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\nConnection: close\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)
