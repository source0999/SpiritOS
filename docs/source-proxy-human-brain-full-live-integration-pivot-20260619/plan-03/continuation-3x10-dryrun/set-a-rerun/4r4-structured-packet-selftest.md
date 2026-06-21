# Stage 4R4 Structured Packet Self-Test

- invalid_json: PASS expected_valid=False valid=False errors=['no_json_object_found', 'packet_not_object']
- A2_positive_packet: PASS expected_valid=True valid=True errors=none
- A5_positive_packet: PASS expected_valid=True valid=True errors=none
- A9_positive_packet: PASS expected_valid=True valid=True errors=none
- empty_decisions: PASS expected_valid=False valid=False errors=['empty_decisions_changed_by_evidence', 'insufficient_source_refs:0']
- fabricated_host: PASS expected_valid=False valid=False errors=['fabricated_host:0:fabricated.example']
- garbled_fake_tool: PASS expected_valid=False valid=False errors=['garbled_or_fabricated_tokens_detected']
- a5_python_version_only: PASS expected_valid=False valid=False errors=['a5_mac_facts_listed_but_unused', 'a5_two_mac_signals', 'decision_invalid_evidence_id:0:mac:ram', 'decision_invalid_evidence_id:3:mac:cpu', 'decision_invalid_evidence_id:3:mac:gpu', 'evidence_invalid_id:10:mac:ram', 'evidence_invalid_id:11:mac:cpu', 'evidence_invalid_id:12:mac:gpu', 'evidence_invalid_id:13:mac:disk', 'evidence_invalid_id:14:mac:runtimes', 'evidence_invalid_id:15:mac:signals', 'insufficient_mac_refs:0']
- a2_missing_mv3_native_service_worker: PASS expected_valid=False valid=False errors=['a2_mv3', 'a2_service_worker_lifecycle', 'missing_contract_term:manifest v3', 'missing_contract_term:service worker']
- generic_decision_text: PASS expected_valid=False valid=False errors=['decision_no_action_verb:0', 'generic_materiality_phrase']

Overall: PASS
