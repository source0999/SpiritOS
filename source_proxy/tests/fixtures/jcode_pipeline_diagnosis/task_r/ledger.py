TRACE_SCHEMA_VERSION = "pipeline-diagnosis/v3"


def build_trace_receipt(run_id: str) -> dict[str, str]:
    return {"schema_version": TRACE_SCHEMA_VERSION, "run_id": run_id}
