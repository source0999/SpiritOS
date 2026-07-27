from qualification_fixture.api import create_request
from qualification_fixture.evidence import build_receipt
from qualification_fixture.worker import emit_event


def test_correlation_is_server_owned_and_propagated() -> None:
    request = create_request({"correlation_id": "caller-value"})
    event = emit_event("started", request)
    receipt = build_receipt(event)
    assert request["correlation_id"] != "caller-value"
    assert event["correlation_id"] == request["correlation_id"]
    assert receipt["correlation_id"] == request["correlation_id"]
