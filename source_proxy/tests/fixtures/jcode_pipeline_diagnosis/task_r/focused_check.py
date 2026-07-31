from ledger import build_trace_receipt


def test_build_trace_receipt_binds_schema():
    assert build_trace_receipt("run-1") == {
        "schema_version": "pipeline-diagnosis/v3",
        "run_id": "run-1",
    }
