# Code-Owned Packet Assembler Final Report - 2026-06-23

## Verdict

`PLAN3_NEEDS_FIX_WITH_GOOD_DEBUGGERS`

## Root Cause

- Before: A2/A5/A9 trusted the model to author final packet provenance, source URLs, local/API truth, JSON envelope, and final validation fields. Failures mixed fake hosts, invalid source URLs, non-JSON wrapping, and thin action semantics.
- After: code owns packet shell, evidence objects, source URLs, lane/provider/model truth, local/API distinction, JSON envelope, receipt/debugger status, and validation surface. The model owns only bounded decision-body text.

## Assembler

- Code-owned fields: `prompt_id`, `user_goal`, `evidence_items`, `final_recommendation`, `safe_mvp`, `handoff_packet`, `quality_self_check`, source refs, repo refs, Mac refs, lane truth, shell status.
- Model-owned fields: `decision_summary`, `reasoning_summary`, `risk_notes`, `ambiguity_notes`, `proposed_next_action`, `action_intent`, `confidence_reason`.
- Source URL handling: final packet source URLs come only from in-run source facts; model-authored URLs/hosts are stripped from model-owned prose.
- Local/API handling: packet receipts record local/API truth from selected lane metadata.
- JSON wrapping handling: unambiguous wrapped JSON is recorded as `wrapped_json_extracted`; it is not a validation blocker by itself.
- Action intent handling: invalid model action intents remain validation blockers unless they map to the controlled enum.

## Reruns

- A2: `NEEDS_FIX`; decision packet valid; remaining failure `research_change_source_not_from_raw_sources`.
- A5: `NEEDS_FIX`; decision packet valid; remaining failures `research_materially_changed_output`, `research_change_source_not_from_raw_sources`.
- A9: `NEEDS_FIX`; decision packet invalid; remaining failure is invalid model action intent `test later`.
- Full Set A: not rerun as a fresh full set because the required A2/A5/A9 slice did not reach GO.
- Set B/C: not run.

## Debugger Adequacy

- Adequate for current stop point.
- Receipts expose prompt/task ID, selected lane, provider/model, local/API truth, provider availability, model-body parse/action status, code-owned shell status, validation errors, receipt path, trace path, and next recommended action.
- Remaining debug gap: none blocking. The remaining failures are behavioral/semantic, not hidden diagnostics.

## Safety

- Pushed: no
- Remote merge: no
- Plan 4 started: no
- Set B/C run: no
- SpiritFlix/media/Jellyfin touched: no
- Protected paths touched: no
- Contract weakened: no
- Hardcoded A2/A5/A9 answer tailoring: no
- API/frontier call added: no

## Recommended Next Step

Britton should decide whether A9 should accept a controlled `test later` action intent mapping or require the model to emit `defer`, and whether A2/A5 should get one more renderer-only research-source linkage fix. Do not start Set B/C until Set A is honestly GO.
