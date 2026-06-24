# Full Set A Remaining Fix Final Report - 2026-06-24

## Verdict

`PLAN3_NEEDS_FIX_WITH_GOOD_DEBUGGERS`

## Failure Groups

- A1: `RESEARCH_MATERIALITY` improved to `DECISION_BODY_TOO_THIN`; still `NEEDS_FIX`
- A3: `RESEARCH_SOURCE_LINKAGE`, `RESEARCH_MATERIALITY`; fixed
- A4: `RESEARCH_MATERIALITY`; fixed
- A6: `RESEARCH_MATERIALITY`; fixed
- A7: `VERIFIER_EXPECTATION_MISMATCH`; fixed
- A8: `VERIFIER_EXPECTATION_MISMATCH`; fixed
- A10: `VERIFIER_EXPECTATION_MISMATCH`; fixed

## Root Causes Fixed

- Raw source matching was too narrow: title-only source lines and minor model typos could fail despite mapping back to a raw source object.
- Research parser errors were applied to non-internet repo-only prompts even when no live research was required.
- The specific-decision checker did not recognize concrete planning verbs that still represent decisions.
- Retry prompt wording did not explicitly require decision lines to start with concrete action verbs.

## Files Changed

- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py`
- `source_proxy/tests/test_plan3_stage4r_packet_runner.py`
- Set A rerun public receipts under `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/`
- Remaining-failure analysis/rerun/final-report docs

## Tests Added

- raw source line can match exact raw source title
- raw source line can match raw title tokens despite minor model typo
- fake model source still fails
- repo-only prompt does not require research source materiality

## Rerun Results

- Remaining Set A slice: A3/A4/A6/A7/A8/A10 PASS; A1 NEEDS_FIX
- Full Set A: not rerun because the remaining slice did not reach GO after the allowed loop
- A2/A5/A9 regression status: public receipts remained PASS from prior full/slice evidence; not rerun in this task except shared-helper tests
- Set B/C: not run

## Remaining Failure

- A1: `research_materially_changed_output`, `research_change_fields_too_thin`

## Validation

- `git diff --check`: pass after trimming generated A1 receipt whitespace
- `.venv/bin/python -m pytest source_proxy/tests/test_plan3_stage4r_packet_runner.py -q`: 19 passed
- `.venv/bin/python -m pytest source_proxy/tests/test_plan3_packet_assembler.py -q`: skipped because the file does not exist
- `.venv/bin/python -m pytest source_proxy/tests/test_status_codes.py source_proxy/tests/test_anticheat_registry.py source_proxy/tests/test_brain_switch_contract.py source_proxy/tests/test_packet_decomposition.py source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_model_lane_observability.py source_proxy/tests/test_model_lanes.py source_proxy/tests/test_verifier_lane.py -q`: 133 passed on rerun; first attempt had one transient browser-verifier timeout that passed on immediate single-test rerun
- Frontend/typecheck: skipped, no frontend changed
- Context verify: skipped, no context scripts changed

## Safety

- Contract weakened: no
- API/frontier added: no
- Hardcoded prompt tailoring: no
- Plan 4 started: no
- Set B/C run: no
- SpiritFlix/media/Jellyfin touched: no

## Human Decision Needed

Britton should decide whether to authorize a separate A1-only bounded fix for thin research-change fields. Set B/C must remain gated until full Set A is honestly GO.
