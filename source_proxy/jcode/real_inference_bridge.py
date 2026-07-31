"""One-request, exact-model local bridge for Gate 2-J.9I only."""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Mapping

from source_proxy.jcode.inference_bridge import SealedInferenceBinding, SealedInferenceBridgeError


@dataclass
class SealedOllamaInferenceBridge:
    binding: SealedInferenceBinding
    expected_digest: str
    endpoint: str = "http://127.0.0.1:11434/api/generate"
    _request_count: int = field(default=0, init=False)
    records: list[dict[str, object]] = field(default_factory=list, init=False)

    def request(self, request: Mapping[str, object]) -> dict[str, object]:
        self._validate(request)
        prompt = request.get("prompt")
        if not isinstance(prompt, str) or not prompt:
            raise SealedInferenceBridgeError("real_bridge_prompt_invalid")
        if len(prompt.split()) > self.binding.max_input_tokens:
            raise SealedInferenceBridgeError("real_bridge_input_budget_exhausted")
        payload = {"model": self.binding.model, "prompt": prompt, "stream": False, "options": {"temperature": 0, "seed": 7}}
        started = time.monotonic()
        try:
            response = urllib.request.urlopen(
                urllib.request.Request(self.endpoint, data=json.dumps(payload, separators=(",", ":")).encode(), headers={"Content-Type": "application/json"}, method="POST"),
                timeout=self.binding.timeout_seconds,
            )
            body = json.loads(response.read().decode("utf-8"))
        except Exception as error:
            raise SealedInferenceBridgeError("real_bridge_request_failed") from error
        if time.monotonic() - started > self.binding.timeout_seconds:
            raise SealedInferenceBridgeError("real_bridge_timeout")
        if body.get("model") != self.binding.model or body.get("done") is not True:
            raise SealedInferenceBridgeError("real_bridge_response_identity_invalid")
        text = body.get("response")
        if not isinstance(text, str) or not text:
            raise SealedInferenceBridgeError("real_bridge_response_invalid")
        if len(text.split()) > self.binding.max_output_tokens:
            raise SealedInferenceBridgeError("real_bridge_output_budget_exhausted")
        self._request_count += 1
        record = {"request_id": request["request_id"], "model": self.binding.model, "model_digest": self.expected_digest, "provider_reported_model": body["model"], "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "response_sha256": hashlib.sha256(text.encode()).hexdigest(), "done": True}
        self.records.append(record)
        return {"text": text, "metadata": {"provider_profile_id": self.binding.provider_profile_id, "model_registry_id": self.binding.model_registry_id, "provider_reported_model": body["model"], "model_digest": self.expected_digest, "streaming": "completed"}}

    def _validate(self, request: Mapping[str, object]) -> None:
        expected = {"task_id": self.binding.task_id, "run_id": self.binding.run_id, "correlation_id": self.binding.correlation_id, "authorization_id": self.binding.authorization_id, "provider_profile_id": self.binding.provider_profile_id, "model_registry_id": self.binding.model_registry_id, "model": self.binding.model}
        for name, value in expected.items():
            if request.get(name) != value:
                raise SealedInferenceBridgeError(f"real_bridge_binding_invalid:{name}")
        if request.get("route") != "/api/generate" or request.get("fallback") or request.get("url") or request.get("redirect"):
            raise SealedInferenceBridgeError("real_bridge_route_denied")
        if request.get("parameters") != {"temperature": 0} or self._request_count >= self.binding.max_requests:
            raise SealedInferenceBridgeError("real_bridge_budget_or_parameters_denied")
