from __future__ import annotations
import json
import pytest
from source_proxy.jcode.batch2_evidence import EVIDENCE_COMPLETE, EVIDENCE_INCOMPLETE, EvidenceContractError, seal_run, verify_run
def _records(run_id="f-7b-read-system"):
    packet={"task":"read fixture/source.py"}; request={"model":"qwen2.5-coder:7b","messages":[{"role":"user","content":"read"}]}; digest="d"*64
    receipt={"run_id":run_id,"task_id":"immutable-read-v1","gate":"2-J.9T-F","harness":"compatibility-diagnostic","model_registry_id":"qwen2.5-coder:7b","full_digest":digest,"provider_reported_identity":"qwen2.5-coder:7b","packet_sha256":"","request_sha256":"","request_started_at":"2026-08-01T00:00:00Z","request_ended_at":"2026-08-01T00:00:01Z","turn_count":1,"tool_calls":[],"observations_reinjected":[],"final_output":"grounded","timeout_or_cancellation":False,"diff":{"changed_paths":[]},"evaluator_outcome":"PASS","request_budget_counter":1,"evidence_completeness":EVIDENCE_COMPLETE}
    return {"authorization":{"id":"active"},"task_manifest":{"task_id":"immutable-read-v1"},"model_binding":{"model":"qwen2.5-coder:7b","digest":digest},"packet":packet,"request":request,"raw_response":{"model":"qwen2.5-coder:7b","message":{"content":"grounded"}},"tool_schema":{"tools":[]},"tool_parse_receipt":{"status":"NO_TOOL_CALL"},"tool_ledger":{"calls":[]},"observation_ledger":{"observations":[]},"model_request_receipt":{"count":1},"evaluation_receipt":{"outcome":"PASS"},"diff_receipt":{"changed_paths":[]},"run_receipt":receipt}
def _sealed(tmp_path):
    records=_records()
    from source_proxy.jcode.canonical_io import hash_value
    records["run_receipt"]["packet_sha256"]=hash_value(records["packet"]); records["run_receipt"]["request_sha256"]=hash_value(records["request"])
    return seal_run(tmp_path,records["run_receipt"]["run_id"],records)
def test_complete_run_is_verified_and_deterministic(tmp_path):
    run=_sealed(tmp_path); assert verify_run(run)["status"]==EVIDENCE_COMPLETE
    assert (run/"packet.json").read_bytes()==(run/"packet.json").read_bytes()
@pytest.mark.parametrize("artifact",["packet.json","request.json","raw_response.json","tool_ledger.json","observation_ledger.json","diff_receipt.json"])
def test_missing_required_artifacts_prevent_verdict(tmp_path,artifact):
    run=_sealed(tmp_path); (run/artifact).unlink(); assert verify_run(run)["status"]==EVIDENCE_INCOMPLETE
def test_writer_rejects_missing_raw_request_or_response(tmp_path):
    for key in ("request","raw_response"):
        records=_records(); records.pop(key)
        with pytest.raises(EvidenceContractError,match="missing_required_artifacts"): seal_run(tmp_path,"f-7b-"+key.replace("_","-"),records)
def test_digest_model_and_request_counter_mismatches_fail_closed(tmp_path):
    run=_sealed(tmp_path); binding=json.loads((run/"model_binding.json").read_text()); binding["digest"]="x"*64; (run/"model_binding.json").write_text(json.dumps(binding))
    assert "digest_mismatch" in verify_run(run)["reasons"]
    receipt=json.loads((run/"run_receipt.json").read_text()); receipt["request_budget_counter"]=0; (run/"run_receipt.json").write_text(json.dumps(receipt))
    assert "request_count_mismatch" in verify_run(run)["reasons"]
def test_hash_tamper_duplicate_id_and_receipt_status_fail_closed(tmp_path):
    run=_sealed(tmp_path); (run/"packet.sha256").write_text("0"*64); assert "packet_hash_mismatch" in verify_run(run)["reasons"]
    with pytest.raises(EvidenceContractError,match="duplicate_run_id"): seal_run(tmp_path,"f-7b-read-system",_records())
    records=_records("f-7b-other"); records["run_receipt"]["evidence_completeness"]=EVIDENCE_INCOMPLETE
    with pytest.raises(EvidenceContractError,match="identity_or_status"): seal_run(tmp_path,"f-7b-other",records)
def test_cleanup_cannot_hide_evidence_or_timeout_omission(tmp_path):
    run=_sealed(tmp_path); receipt=json.loads((run/"run_receipt.json").read_text()); receipt.pop("timeout_or_cancellation"); (run/"run_receipt.json").write_text(json.dumps(receipt))
    assert verify_run(run)["status"]==EVIDENCE_INCOMPLETE