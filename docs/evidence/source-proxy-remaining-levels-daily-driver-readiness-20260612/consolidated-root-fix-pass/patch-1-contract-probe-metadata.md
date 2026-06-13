# Patch 1: Contract And Probe Metadata Plumbing

Status: PASS_SUBCHECK

## Changed Files

- `source_proxy/decision/artifact_repair_contract.py`
- `source_proxy/tests/test_artifact_repair_loop.py`

## What Changed

- `build_behavior_failure_packet` can now derive repair-ready expected behavior from executed browser probe evidence when the original behavior contract is partial.
- True missing metadata still produces `HANDOFF` with `missing_probe_metadata` and `repair_metadata_incomplete`.
- Behavior failure packets now preserve `repair_attempt_count`, `expected_observable_behavior`, before/after values, click/fill/canvas probe evidence, selected preview path, generated file list, console/open summary, and stale-unverified reason cleanup.

## Before / After Example Packet

Before:

```json
{
  "status": "HANDOFF",
  "handoff_reasons": ["behavior_contract_probe_missing"],
  "behavior_contract": {"probe_targets": []},
  "behavior_probe": {
    "verdict": "FAIL",
    "actual": {"before": "0", "after": "0", "clicked": ["button"]}
  }
}
```

After:

```json
{
  "status": "READY_FOR_LOCAL_REPAIR",
  "handoff_reasons": [],
  "probe_id": "counter-visible-increment",
  "expected_behavior": {
    "acceptance_criterion": "Clicking the primary button visibly changes the counter.",
    "expected_observation": "Counter text increments after click."
  },
  "observed_behavior": {"before": "0", "after": "0"},
  "behavior_probe_evidence": {"clicked": ["button"]},
  "reason_codes": ["behavior_failed_verified", "behavior_probe_failed:counter-visible-increment"]
}
```

Truly missing expected/actual semantics still remains:

```json
{
  "status": "HANDOFF",
  "handoff_reasons": ["missing_probe_metadata"],
  "reason_codes": ["behavior_failed_verified", "repair_metadata_incomplete"]
}
```

## Tests Run

```text
python -m pytest source_proxy/tests/test_artifact_behavior_contract.py source_proxy/tests/test_artifact_repair_contract.py source_proxy/tests/test_artifact_repair_loop.py source_proxy/tests/test_artifact_retest_result.py source_proxy/tests/test_artifact_final_verdict.py
34 passed

python -m py_compile source_proxy/decision/artifact_repair_contract.py source_proxy/tests/test_artifact_repair_loop.py
PASS

git diff --check -- source_proxy/decision/artifact_repair_contract.py source_proxy/tests/test_artifact_repair_loop.py
PASS
```

## Remaining Risks

- This subcheck proves packet plumbing and focused repair-loop behavior. It does not yet prove end-to-end random 10/10b/10c/10d behavior reliability.
- Evidence report generators still need the later patches before the trace is fully auditable.
