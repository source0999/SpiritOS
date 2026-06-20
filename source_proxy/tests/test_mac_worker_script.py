from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKER_SCRIPT = REPO_ROOT / "scripts" / "mac-worker" / "spirit_mac_worker.py"


def _run_worker(job: dict[str, object]) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(WORKER_SCRIPT)],
        input=json.dumps(job),
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert completed.stdout, completed.stderr
    return json.loads(completed.stdout.splitlines()[-1])


def _traced_job(input_data: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "job_id": "test-mac-write-proof",
        "job_type": "mac_isolated_write_proof",
        "node_id": "spirit-mac-mini",
        "trace_id": "trace_test",
        "invocation_event_id": "invocation_test",
        "consumer_subsystem": "cartographer_mac_assignment_consumer",
        "task_id": "task_test",
        "input": input_data or {},
    }


def test_mac_isolated_write_proof_returns_structured_result_and_rolls_back() -> None:
    with tempfile.TemporaryDirectory() as proof_dir:
        payload = _run_worker(_traced_job({"proof_dir": proof_dir, "contents": "plan2 proof"}))

    result = payload["result"]
    assert payload["success"] is True
    assert result["success"] is True
    assert result["job_type"] == "mac_isolated_write_proof"
    assert result["worker"] == "mac"
    assert result["write_performed"] is True
    assert result["verified"] is True
    assert result["rollback_performed"] is True
    assert result["rollback_status"] == "cleaned"
    assert result["checksum"] == result["content_marker"]
    assert payload["trace_id"] == "trace_test"
    assert payload["invocation_event_id"] == "invocation_test"
    assert payload["consumer_subsystem"] == "cartographer_mac_assignment_consumer"
    assert payload["task_id"] == "task_test"
    assert not Path(str(result["proof_path"])).exists()


def test_mac_isolated_write_proof_rejects_unsafe_path_without_write() -> None:
    payload = _run_worker(_traced_job({"proof_dir": str(REPO_ROOT)}))

    result = payload["result"]
    assert payload["success"] is False
    assert result["error"] == "safe_path_rejected"
    assert result["write_performed"] is False
    assert result["mac_write_performed"] is False


def test_mac_isolated_write_proof_requires_trace_fields() -> None:
    job = _traced_job()
    job.pop("trace_id")

    payload = _run_worker(job)

    result = payload["result"]
    assert payload["success"] is False
    assert result["error"] == "missing_trace"
    assert result["write_performed"] is False
    assert "trace_id" in result["missing_fields"]


def test_unsupported_job_still_fails_honestly() -> None:
    payload = _run_worker({**_traced_job(), "job_type": "dangerous_shell"})

    assert payload["success"] is False
    assert "Unsupported job_type" in str(payload["error"])


def test_system_status_alone_is_not_write_proof() -> None:
    payload = _run_worker({**_traced_job(), "job_type": "system_status", "input": {}})

    result = payload["result"]
    assert payload["success"] is True
    assert result["supported_job_types"]
    assert result.get("write_performed") is None
    assert result.get("rollback_performed") is None
