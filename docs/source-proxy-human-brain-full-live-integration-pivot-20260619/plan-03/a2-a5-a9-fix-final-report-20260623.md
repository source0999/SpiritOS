# A2/A5/A9 Fix Final Report - 2026-06-23

## Failure Analysis Summary

A2, A5, and A9 entered this task as `MODEL_PACKET_VALIDATION_FAILURE` on `ollama_hermes4_latest`. Raw packet attempts showed malformed/wrapped JSON, invented or invalid evidence references, fabricated hosts/URLs, missing contract terms, and weak decision fields.

Initial root cause selected: `LANE_SELECTION_WRONG`.

Second bounded root cause observed after qwen-first rerun: `PROMPT_TEMPLATE_UNCLEAR` / `LOCAL_MODEL_PACKET_AUTHOR_WEAK`. The model prompt exposed internal evidence digest fields and a sample evidence schema, but did not give the model packet-ready evidence objects to copy exactly.

## Files Changed

- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py`
- `source_proxy/tests/test_plan3_stage4r_packet_runner.py`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/a2-a5-a9-packet-failure-analysis-20260623.md`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/a2-a5-a9-fix-rerun-20260623.md`
- this final report

## Why This Is Not Acceptance Weakening

- The packet validator was not loosened.
- Required truth fields still fail when missing.
- Invalid packets still fail.
- No prompt-specific hardcoded answer was added.
- No API/frontier call was added.
- No malformed packet is accepted as a pass.

## A2/A5/A9 Rerun Result

- A2: `NEEDS_FIX`; selected best failed lane `ollama_hermes4_latest`; current errors include fabricated host, missing `local api`, non-JSON wrapping, invalid source URLs, and action-verb issue.
- A5: `NEEDS_FIX`; selected best failed lane `ollama_hermes4_latest`; current errors include thin decision fields, fabricated `ollama.ai`, insufficient source refs, non-JSON wrapping, and invalid source URL.
- A9: `NEEDS_FIX`; selected best failed lane `ollama_qwen2.5-coder_7b`; current errors include thin `default_without_evidence` fields and action-verb issues.

## Full Set A Rerun

Not run. The A2/A5/A9 slice did not pass, so full Set A is still gated.

## Tests Run

Focused tests before rerun:

```bash
python3 -m py_compile docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py
.venv/bin/python -m pytest source_proxy/tests/test_plan3_stage4r_packet_runner.py source_proxy/tests/test_model_lanes.py -q
git diff --check
```

Results: PASS; 9 focused tests passed.

Final validation:

```bash
git diff --check
.venv/bin/python -m pytest source_proxy/tests/test_status_codes.py source_proxy/tests/test_anticheat_registry.py source_proxy/tests/test_brain_switch_contract.py source_proxy/tests/test_packet_decomposition.py source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_model_lane_observability.py source_proxy/tests/test_model_lanes.py source_proxy/tests/test_verifier_lane.py source_proxy/tests/test_plan3_stage4r_packet_runner.py -q
```

Results: PASS; 137 tests passed.

## Skipped Checks

- Full Set A rerun: skipped because A2/A5/A9 slice remained `NEEDS_FIX`.
- Set B/C: skipped by gate.
- Plan 4: not started.

## Remaining Blockers

- Local models still fail structured packet validation for A2/A5/A9 under the current contract.
- A2/A5 best failed attempts fell back to Hermes after qwen failed; A9 best failed attempt remained qwen.
- The next fix likely needs Britton direction on whether to use a stronger approved structured-output provider, change the contract shape, or redesign packet assembly so the model authors only decisions while code owns evidence serialization.

## Human Decision Needed

Choose the next bounded path:

1. approve a stronger structured-output lane/provider for packet authoring,
2. redesign packet assembly so evidence serialization is code-owned and the model only fills decision fields, or
3. revise the contract shape while preserving all truth requirements.

## Verdict

`PLAN3_NEEDS_FIX_WITH_GOOD_DEBUGGERS`
