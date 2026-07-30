from __future__ import annotations

import pytest
import time

from source_proxy.jcode.event_schema import EventBinding, parse_strict_event_stream
from source_proxy.jcode.inference_bridge import FakeInferenceResponse, SealedFakeInferenceBridge, SealedInferenceBinding, SealedInferenceBridgeError


def _bridge() -> SealedFakeInferenceBridge:
    binding = SealedInferenceBinding("task", "run", "corr", "auth", "profile", "registry", "qwen2.5-coder:7b")
    return SealedFakeInferenceBridge(binding, lambda prompt: FakeInferenceResponse("qwen2.5-coder:7b", "deterministic answer", len(prompt.split()), 2))


def _request(**changes: object) -> dict[str, object]:
    request: dict[str, object] = {"task_id":"task","run_id":"run","correlation_id":"corr","authorization_id":"auth","provider_profile_id":"profile","model_registry_id":"registry","model":"qwen2.5-coder:7b","route":"/api/generate","parameters":{"temperature":0},"request_id":"one","prompt":"inspect authority envelope"}
    request.update(changes)
    return request


def test_valid_fake_request_is_attested_and_strict_events_validate() -> None:
    bridge = _bridge()
    result = bridge.request(_request())
    assert result["metadata"]["provider_reported_model"] == "qwen2.5-coder:7b"
    parsed = parse_strict_event_stream(bridge.events_ndjson(final=True), EventBinding("task", "run", "corr", gate_id="2-J.9F"))
    assert parsed["status"] == "evidence_ready"


@pytest.mark.parametrize("changes,reason", [
    ({"task_id":"wrong"},"task_id"), ({"run_id":"wrong"},"run_id"), ({"correlation_id":"wrong"},"correlation_id"), ({"authorization_id":"wrong"},"authorization_id"), ({"provider_profile_id":"wrong"},"provider_profile_id"), ({"model_registry_id":"wrong"},"model_registry_id"), ({"model":"other"},"model"), ({"route":"/coding"},"route_denied"), ({"route":"/v1/chat"},"route_denied"), ({"fallback":True},"unsealed_route"), ({"url":"http://example.test"},"unsealed_route"), ({"redirect":"http://127.0.0.1:11434"},"unsealed_route"), ({"parameters":{"temperature":1}},"parameters"), ({"request_id":""},"request_id"), ({"prompt":""},"prompt_invalid"), ({"prompt":"x " * 129},"input_budget"),
])
def test_unsealed_or_malformed_requests_fail_closed(changes: dict[str, object], reason: str) -> None:
    with pytest.raises(SealedInferenceBridgeError, match=reason): _bridge().request(_request(**changes))


def test_replay_request_exhaustion_and_bad_backend_fail_closed() -> None:
    bridge = _bridge(); bridge.request(_request())
    with pytest.raises(SealedInferenceBridgeError, match="replay_denied"): bridge.request(_request())
    with pytest.raises(SealedInferenceBridgeError, match="request_budget"): bridge.request(_request(request_id="two"))
    bad = SealedFakeInferenceBridge(_bridge().binding, lambda _: FakeInferenceResponse("wrong", "x", 1, 1))
    with pytest.raises(SealedInferenceBridgeError, match="identity_invalid"): bad.request(_request())


def test_timeout_and_shutdown_fail_closed() -> None:
    binding = SealedInferenceBinding("task", "run", "corr", "auth", "profile", "registry", "qwen2.5-coder:7b", timeout_seconds=0.001)
    slow = SealedFakeInferenceBridge(binding, lambda _: (time.sleep(0.01), FakeInferenceResponse("qwen2.5-coder:7b", "x", 1, 1))[1])
    with pytest.raises(SealedInferenceBridgeError, match="timeout"): slow.request(_request(prompt="x"))
    bridge = _bridge(); bridge.close()
    with pytest.raises(SealedInferenceBridgeError, match="shutdown"): bridge.request(_request())
