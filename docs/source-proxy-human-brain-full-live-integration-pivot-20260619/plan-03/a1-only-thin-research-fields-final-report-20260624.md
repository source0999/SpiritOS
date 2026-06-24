# A1-Only Thin Research Fields Final Report - 2026-06-24

## Verdict

`PLAN3_NEEDS_FIX_WITH_GOOD_DEBUGGERS`

## A1 Result

- Before: `NEEDS_FIX` with `research_materially_changed_output` and `research_change_fields_too_thin`.
- Root cause: `ASSEMBLER_CAN_DERIVE_FIELDS_FROM_RAW_EVIDENCE`.
- Fix strategy: parse inline research-change labels and add a bounded code-owned repair helper that can derive a missing `Why` only from raw-source-backed model findings and concrete decisions.
- After: A1 `PASS` in A1-only rerun and A1 `PASS` in the final full Set A rerun.

## Research-Change Fields

- Before: the validator saw `Finding`/`Source` but no separate sufficient `Decision changed`/`Why` fields.
- After: A1 produced three accepted research-change blocks and `research_materially_changed_output=true`.
- Raw evidence grounding: accepted blocks must still match raw source title, host, URL, or strong raw-title token overlap.
- Validator result: A1 passed; fake-source tests still fail.

## Full Set A Result

- A1: `PASS`
- A2: `PASS`
- A3: `NEEDS_FIX` with `research_change_source_not_from_raw_sources`
- A4: `PASS`
- A5: `PASS`
- A6: `PASS`
- A7: `PASS`
- A8: `PASS`
- A9: `PASS`
- A10: `PASS`

Full Set A remains `NEEDS_FIX` because A3 failed in the final full rerun. This task was A1-only, so A3 was not patched.

## Files Changed

- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py`
- `source_proxy/tests/test_plan3_stage4r_packet_runner.py`
- Set A rerun public receipts under `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/`
- A1-only analysis, rerun, full-rerun, and final-report docs.

## Tests

- `.venv/bin/python -m pytest source_proxy/tests/test_plan3_stage4r_packet_runner.py -q`: passed, 22 tests.
- `git diff --check`: passed after trimming generated Markdown receipt whitespace.
- `.venv/bin/python -m pytest source_proxy/tests/test_status_codes.py source_proxy/tests/test_anticheat_registry.py source_proxy/tests/test_brain_switch_contract.py source_proxy/tests/test_packet_decomposition.py source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_model_lane_observability.py source_proxy/tests/test_model_lanes.py source_proxy/tests/test_verifier_lane.py -q`: passed, 133 tests.
- Frontend/typecheck: skipped; no frontend files changed.
- Context verify: skipped; no context scripts changed.

## Safety

- Pushed: no
- Remote merge: no
- Plan 4 started: no
- Set B/C run: no
- SpiritFlix/media/Jellyfin touched: no
- Protected paths touched: no
- Contract weakened: no
- Hardcoded A1 tailoring: no
- API/frontier call added: no

## Human Direction Needed

Britton should review the A1 fix and decide whether to authorize a separate A3-only bounded source-linkage fix. Set B/C must remain gated until full Set A is honestly GO.
