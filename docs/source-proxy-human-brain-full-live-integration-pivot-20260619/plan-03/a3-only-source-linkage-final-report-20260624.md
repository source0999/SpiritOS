# A3-Only Source Linkage Final Report - 2026-06-24

## Verdict

`PLAN3_NEEDS_FIX_WITH_GOOD_DEBUGGERS`

## A3 Root Cause

`MODEL_SOURCE_LEAKED_INTO_PACKET`

The model placed repo evidence inside the `Research-to-decision changes` section and also emitted model-owned/misspelled source text for Android research sources. Repo evidence is valid context, but it is not raw research provenance and must not satisfy research-change source refs.

## Fix Strategy

- Canonicalize matched research-change source refs to the raw research source registry.
- Drop research-change blocks whose source cannot be proven from raw collected research sources.
- Keep the grader strict so missing or insufficient raw research source evidence still fails honestly.
- Do not add prompt-ID-specific A3 logic.

## Files Changed

- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py`
- `source_proxy/tests/test_plan3_stage4r_packet_runner.py`
- Set A rerun public receipts under `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/`
- A3 source-linkage analysis, rerun, full-rerun, and final-report docs.

## Tests Added

- A3-like source refs are canonicalized to raw research sources.
- Repo evidence in the research-change section is dropped rather than treated as research provenance.
- Model-authored fake sources are dropped by the repair helper and still fail under direct parser validation.
- Missing raw research sources still fail honestly.
- The repair helper has no prompt-ID-specific A3 branch.

## Validation

- `git diff --check`: passed after trimming generated Markdown receipt whitespace.
- `.venv/bin/python -m pytest source_proxy/tests/test_plan3_stage4r_packet_runner.py -q`: passed, 25 tests.
- `.venv/bin/python -m pytest source_proxy/tests/test_status_codes.py source_proxy/tests/test_anticheat_registry.py source_proxy/tests/test_brain_switch_contract.py source_proxy/tests/test_packet_decomposition.py source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_model_lane_observability.py source_proxy/tests/test_model_lanes.py source_proxy/tests/test_verifier_lane.py -q`: passed, 133 tests.
- Frontend/typecheck: skipped; no frontend files changed.
- Context verify: skipped; no context scripts changed.

## Rerun Results

- A3-only rerun: `PASS`
- Full Set A rerun: `NEEDS_FIX`
- A1 stayed PASS in the full rerun: yes
- A2/A5/A9 stayed PASS in the full rerun: yes
- A4/A6/A7/A8/A10 stayed PASS in the full rerun: yes
- Remaining failure: A3 `research_change_no_specific_decision`

## Safety

- Contract weakened: no
- API/frontier added: no
- Hardcoded prompt tailoring: no
- Plan 4 started: no
- Set B/C run: no
- SpiritFlix/media/Jellyfin touched: no
- Protected paths touched: no

## Human Decision Needed

Britton should decide whether to authorize a separate bounded A3 decision-specificity fix. Set B/C must remain gated until full Set A is honestly GO.
