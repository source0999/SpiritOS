"""Sealed deterministic inference bridge used by Gate 2-J.9F only."""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Callable, Mapping

from source_proxy.jcode.event_schema import EVENT_SCHEMA_VERSION, EventBinding, canonical_event_hash


class SealedInferenceBridgeError(ValueError):
    """A request did not satisfy the sealed bridge contract."""


@dataclass(frozen=True)
class SealedInferenceBinding:
    task_id: str
    run_id: str
    correlation_id: str
    authorization_id: str
    provider_profile_id: str
    model_registry_id: str
    model: str
    max_requests: int = 1
    max_input_tokens: int = 128
    max_output_tokens: int = 64
    timeout_seconds: float = 5.0


@dataclass(frozen=True)
class FakeInferenceResponse:
    model: str
    text: str
    input_tokens: int
    output_tokens: int
    completed: bool = True


@dataclass
class SealedFakeInferenceBridge:
    binding: SealedInferenceBinding
    backend: Callable[[str], FakeInferenceResponse]
    _seen_request_ids: set[str] = field(default_factory=set, init=False)
    _requests: int = field(default=0, init=False)
    _events: list[dict[str, object]] = field(default_factory=list, init=False)
    _closed: bool = field(default=False, init=False)

    def close(self) -> None:
        self._closed = True

    def request(self, request: Mapping[str, object]) -> dict[str, object]:
        if self._closed:
            raise SealedInferenceBridgeError("bridge_shutdown")
        self._validate(request)
        prompt = request.get("prompt")
        if not isinstance(prompt, str) or not prompt:
            raise SealedInferenceBridgeError("bridge_prompt_invalid")
        if _tokens(prompt) > self.binding.max_input_tokens:
            raise SealedInferenceBridgeError("bridge_input_budget_exhausted")
        self._emit("model_request.started", {"request_id": request["request_id"], "model": self.binding.model})
        started = time.monotonic()
        response = self.backend(prompt)
        if time.monotonic() - started > self.binding.timeout_seconds:
            raise SealedInferenceBridgeError("bridge_timeout")
        if not isinstance(response, FakeInferenceResponse) or response.model != self.binding.model:
            raise SealedInferenceBridgeError("bridge_response_identity_invalid")
        if not response.completed:
            raise SealedInferenceBridgeError("bridge_stream_incomplete")
        if response.input_tokens != _tokens(prompt) or response.output_tokens != _tokens(response.text):
            raise SealedInferenceBridgeError("bridge_usage_missing_or_invalid")
        if response.output_tokens > self.binding.max_output_tokens:
            raise SealedInferenceBridgeError("bridge_output_budget_exhausted")
        self._requests += 1
        self._seen_request_ids.add(str(request["request_id"]))
        metadata = {"provider_profile_id": self.binding.provider_profile_id, "model_registry_id": self.binding.model_registry_id, "provider_reported_model": response.model, "usage": {"input_tokens": response.input_tokens, "output_tokens": response.output_tokens}, "streaming": "completed"}
        self._emit("model_request.completed", metadata)
        return {"text": response.text, "metadata": metadata, "events_ndjson": self.events_ndjson(final=False)}

    def events_ndjson(self, *, final: bool) -> bytes:
        events = list(self._events)
        if final:
            events.append(self._event(len(events) + 1, "run.completed", {"bridge": "sealed_fake"}))
        return b"".join(json.dumps(event, sort_keys=True, separators=(",", ":")).encode() + b"\n" for event in events)

    def _validate(self, request: Mapping[str, object]) -> None:
        required = {"task_id": self.binding.task_id, "run_id": self.binding.run_id, "correlation_id": self.binding.correlation_id, "authorization_id": self.binding.authorization_id, "provider_profile_id": self.binding.provider_profile_id, "model_registry_id": self.binding.model_registry_id, "model": self.binding.model}
        for name, expected in required.items():
            if request.get(name) != expected:
                raise SealedInferenceBridgeError(f"bridge_binding_invalid:{name}")
        if request.get("route") != "/api/generate":
            raise SealedInferenceBridgeError("bridge_route_denied")
        if request.get("fallback") or request.get("url") or request.get("redirect"):
            raise SealedInferenceBridgeError("bridge_unsealed_route_denied")
        parameters = request.get("parameters")
        if parameters != {"temperature": 0}:
            raise SealedInferenceBridgeError("bridge_generation_parameters_invalid")
        request_id = request.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            raise SealedInferenceBridgeError("bridge_request_id_invalid")
        if request_id in self._seen_request_ids:
            raise SealedInferenceBridgeError("bridge_replay_denied")
        if self._requests >= self.binding.max_requests:
            raise SealedInferenceBridgeError("bridge_request_budget_exhausted")

    def _emit(self, event_type: str, payload: dict[str, object]) -> None:
        self._events.append(self._event(len(self._events) + 1, event_type, payload))

    def _event(self, sequence: int, event_type: str, payload: dict[str, object]) -> dict[str, object]:
        previous = str(self._events[-1]["event_hash"]) if self._events else ""
        event: dict[str, object] = {"schema_version": EVENT_SCHEMA_VERSION, "event_id": f"bridge-{sequence}", "sequence": sequence, "timestamp": "2026-07-30T23:00:00Z", "task_id": self.binding.task_id, "run_id": self.binding.run_id, "correlation_id": self.binding.correlation_id, "gate_id": "2-J.9F", "type": event_type, "source": "proxy", "payload": payload, "prev_event_hash": previous}
        event["event_hash"] = canonical_event_hash(event)
        return event


def _tokens(text: str) -> int:
    return len(text.split())
