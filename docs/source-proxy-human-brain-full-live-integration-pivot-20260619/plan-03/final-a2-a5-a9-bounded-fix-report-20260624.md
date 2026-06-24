# Final A2/A5/A9 Bounded Fix Report - 2026-06-24

## Verdict

`PLAN3_NEEDS_FIX_WITH_GOOD_DEBUGGERS`

## Root Cause

- A2/A5: research block parsing continued into the repo/Mac evidence section, where repo snippets containing `Source:` could overwrite the final research block source. The packet provenance was code-owned, but the grader parser still treated later repo text as research provenance.
- A9: local model output used semantically valid planning phrases, `test later` and later `skip`, as `action_intent` values even though the controlled enum already represents those as `defer` and `reject`.

## Source-Linkage Fix

- `research_change_blocks()` now stops parsing research-change blocks when the `Repo/Mac evidence that changed the plan` section begins.
- Rendered research source lines include code-owned raw source IDs.
- The packet shell records a `raw_source_registry` with evidence ID, host, and URL for research evidence.
- Model-authored source URLs/hosts remain stripped from model-owned prose and are not used as provenance.

## Action-Intent Fix

- Exact `test later` maps to existing controlled intent `defer`.
- Exact `skip` maps to existing controlled intent `reject`.
- Each normalization records original value, normalized value, and reason in `code_owned_packet_shell_status.action_intent_normalizations`.
- Unrelated invalid action intents still fail.

## Files Changed

- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py`
- `source_proxy/tests/test_plan3_stage4r_packet_runner.py`
- Plan 3 rerun evidence receipts under `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/`
- This analysis/rerun/report doc set.

## Tests Added

- Parser ignores repo `Source:` lines after the research section.
- `test later` normalizes to `defer`.
- `skip` normalizes to `reject`.
- Raw source registry is present in shell status.

## Rerun Result

- A2: `PASS`
- A5: `PASS`
- A9: `PASS`
- Full Set A: `NEEDS_FIX`

## Remaining Failures

Full Set A still has unrelated failures in A1, A3, A4, A6, A7, A8, and A10. Those were not chased because this task was bounded to A2/A5/A9 plus a full Set A check only if the slice passed.

## Validation

- `git diff --check`: pass after trimming generated receipt whitespace
- `.venv/bin/python -m pytest source_proxy/tests/test_plan3_stage4r_packet_runner.py -q`: 15 passed
- `.venv/bin/python -m pytest source_proxy/tests/test_status_codes.py source_proxy/tests/test_anticheat_registry.py source_proxy/tests/test_brain_switch_contract.py source_proxy/tests/test_packet_decomposition.py source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_model_lane_observability.py source_proxy/tests/test_model_lanes.py source_proxy/tests/test_verifier_lane.py -q`: 133 passed
- Frontend/typecheck: skipped, no frontend changed
- Context verify: skipped, no context scripts changed

## Safety

- Contract weakened: no
- API/frontier call added: no
- Hardcoded prompt tailoring: no
- Set B/C run: no
- Plan 4 started: no
- SpiritFlix/media/Jellyfin touched: no

## Human Decision Needed

Britton should decide whether to authorize a separate full Set A cleanup for the non-A2/A5/A9 failures. Set B/C must not start until full Set A is honestly GO.
