from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from source_proxy.jcode.inference_bridge import SealedInferenceBinding, SealedInferenceBridgeError
from source_proxy.jcode.real_inference_bridge import SealedOllamaInferenceBridge


def _request() -> dict[str, object]:
    return {"task_id": "task", "run_id": "run", "correlation_id": "corr", "authorization_id": "auth", "provider_profile_id": "profile", "model_registry_id": "registry", "model": "qwen2.5-coder:14b", "route": "/api/generate", "parameters": {"temperature": 0}, "request_id": "one", "prompt": "make a bounded edit"}


class _Response:
    def read(self) -> bytes:
        return json.dumps({"model": "qwen2.5-coder:14b", "done": True, "response": "bounded answer"}).encode()

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_real_bridge_records_only_the_bound_local_model() -> None:
    binding = SealedInferenceBinding("task", "run", "corr", "auth", "profile", "registry", "qwen2.5-coder:14b", max_output_tokens=16)
    bridge = SealedOllamaInferenceBridge(binding, "digest")
    with patch("urllib.request.urlopen", return_value=_Response()):
        response = bridge.request(_request())
    assert response["metadata"]["provider_reported_model"] == "qwen2.5-coder:14b"
    assert bridge.records[0]["model_digest"] == "digest"


def test_real_bridge_rejects_fallback_and_second_request_before_transport() -> None:
    binding = SealedInferenceBinding("task", "run", "corr", "auth", "profile", "registry", "qwen2.5-coder:14b")
    bridge = SealedOllamaInferenceBridge(binding, "digest")
    invalid = _request() | {"fallback": True}
    with pytest.raises(SealedInferenceBridgeError, match="route"):
        bridge.request(invalid)
