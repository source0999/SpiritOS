import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta

import pytest

from source_proxy.approval.operator_session import OperatorSessionError, verify_operator_approval_assertion


def assertion(secret: str, *, session_id: str = "session-1", action: str = "approve") -> str:
    payload = {
        "action": action,
        "expires_at": (datetime.now(UTC) + timedelta(seconds=60)).isoformat(),
        "generation": 1,
        "operator": "spiritos-local-operator",
        "preview_id": "prv_server_persisted",
        "role": "approval-issuer",
        "session_id": session_id,
        "task_id": "task-server-persisted",
    }
    encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=").decode()
    signature = base64.urlsafe_b64encode(hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).digest()).rstrip(b"=").decode()
    return f"{encoded}.{signature}"


def test_operator_assertion_requires_live_signed_server_session(tmp_path, monkeypatch):
    state_path = tmp_path / "sessions.json"
    state_path.write_text(json.dumps({"sessions": {"session-1": {"expires_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(), "id": "session-1", "csrf_hash": "redacted"}}}))
    monkeypatch.setenv("SPIRITOS_OPERATOR_E2E_MODE", "true")
    monkeypatch.setenv("SPIRITOS_OPERATOR_E2E_SECRET", "test-only-operator-secret")
    monkeypatch.setenv("SPIRITOS_OPERATOR_E2E_STATE_PATH", str(state_path))
    assert verify_operator_approval_assertion(assertion("test-only-operator-secret"))["preview_id"] == "prv_server_persisted"
    with pytest.raises(OperatorSessionError, match="operator_assertion_invalid"):
        verify_operator_approval_assertion(assertion("wrong-secret"))
    state_path.write_text(json.dumps({"sessions": {"session-1": {"expires_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(), "id": "session-1", "csrf_hash": "redacted", "revoked_at": datetime.now(UTC).isoformat()}}}))
    with pytest.raises(OperatorSessionError, match="operator_session_revoked"):
        verify_operator_approval_assertion(assertion("test-only-operator-secret"))
