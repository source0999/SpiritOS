# Codex Set A Stability Audit - 2026-06-25

## Executive Verdict

`SET_A_STABILITY_CONFIRMED_FOR_HUMAN_REVIEW`

Plan 3 Set A is genuinely ready for Britton human review. I found a clean branch/head match, no staged files, no unexpected dirty Source Proxy source files, stable direct SearXNG evidence, three passing A3 append-only receipts, and two full Set A append-only receipts with 10/10 PASS, zero failures, zero blocked prompts, and explicit `no_set_b_run`, `no_set_c_run`, and `no_plan4_work` summary flags.

Set B/C were not run. Plan 4 was not started. No source files were edited. This report is the only file intentionally added by this audit and is left uncommitted.

## Current HEAD

- branch: `integration/cleanup-plan3-debug-20260623`
- HEAD: `9be0ec8911b9d94f487b6b9e4aaea917240ebbac`
- HEAD subject: `Record Plan 3 Set A stability verification`
- staged files: none
- working tree: untracked append-only Plan 3 run directories only in the audited evidence root; no unexpected dirty Source Proxy source files observed

## Evidence Inspected

- `final-set-a-stability-readback-20260625.md`
- `final-set-a-stability-rerun-20260625.md`
- `research-provider-stability-rerun-20260625.md`
- `generic-model-contract-stability-rerun-20260625.md`
- `glm-set-a-stability-hardline-audit-20260625.md`
- `debugger-diagnostic-standard-20260623.md`
- `backend/searxng.yml`
- `/tmp/spiritos-final-set-a-stability/direct-searxng-10x.jsonl`
- append-only receipts for:
  - `run-20260625T121016Z`
  - `run-20260625T121558Z`
  - `run-20260625T121858Z`
  - `run-20260625T122144Z`
  - `run-20260625T124450Z`

## Direct SearXNG Proof

The direct provider file exists at `/tmp/spiritos-final-set-a-stability/direct-searxng-10x.jsonl`.

- line count: 10
- `ok=true`: 10/10
- HTTP status 200: 10/10
- `result_count=20`: 10/10
- errors/timeouts: none

This confirms the claimed direct provider proof. Because it is under `/tmp`, it remains ephemeral provider evidence, but it was present during this audit.

## A3 3x Proof

The three claimed A3-only append-only runs all have `A3.json` and `summary.json`.

| Run | Status | Source count | Provider classification | Failed gates |
| --- | --- | ---: | --- | --- |
| `run-20260625T121016Z` | `PASS` | 6 | `SOURCES_AVAILABLE` | none |
| `run-20260625T121558Z` | `PASS` | 6 | `SOURCES_AVAILABLE` | none |
| `run-20260625T121858Z` | `PASS` | 6 | `SOURCES_AVAILABLE` | none |

Verdict: A3 stability is confirmed as `PASS / PASS / PASS`.

## Full Set A 2x Proof

Both full Set A runs contain `A1.json` through `A10.json` plus `summary.json`.

| Run | Pass | Failed | Blocked | Set B | Set C | Plan 4 |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `run-20260625T122144Z` | 10 | 0 | 0 | not run | not run | not started |
| `run-20260625T124450Z` | 10 | 0 | 0 | not run | not run | not started |

Summary fields also record:

- `final_status_derived_by_grader: true`
- `fake_go_detected_computed: true`
- `hardcoded_sources_used: false`
- `hardcoded_plans_used: false`
- `old_generator_disqualified: true`
- `receipt_layout: canonical_latest_plus_append_only_per_run_id_copies`

Verdict: full Set A stability is confirmed twice.

## A7/A8/A10 Zero-Source PASS

The zero-source PASS cases are acceptable for Set A stability.

In both full Set A runs, A7, A8, and A10 record:

- `internet_required: false`
- `live_search_used: false`
- `source_count: 0`
- `source_facts_len: 0`
- `sources_len: 0`
- provider attempts: 0
- `local_fallback_used: false`
- `fake_go_detected: false`
- `failed_gates: []`
- selected model lane: `ollama_default`
- required lanes: route decision, task spec, durable task, live model, consumer, repo context

These prompts were not treated as internet-research prompts, so zero live sources are not suspicious here. The provider classification remains `UNKNOWN_NEEDS_HUMAN`, but the receipts show no provider attempt was required.

## Cheat / Overfit Scan

Prompt-specific A3 scan results were not evidence of an A3 implementation cheat. Hits were receipts, reports, test fixtures, anti-branch assertions, and a runner comment forbidding `pid == "A3"` branches.

The fake/fallback/source scan found:

- report text documenting fake-source rejection and stale-source guardrails
- tests covering fake-source rejection
- runner self-check text rejecting PASS with local fallback for internet-required work
- no discovered hardcoded PASS/GO path
- no discovered fake-source acceptance path
- no discovered stale-source-as-live-proof path

Classification:

- A3 prompt-specific branches: `BENIGN_TEST_GUARD` / report and receipt mentions only
- fake GO/fallback PASS: `BENIGN_TEST_GUARD`
- source fabrication: `BENIGN_TEST_GUARD`
- overall: no real cheat found in the targeted scan

## Validation

- `git diff --check`: PASS
- `source_proxy/tests/test_plan3_stage4r_packet_runner.py -q`: PASS, 39 passed
- `source_proxy/tests/test_research_preview.py -q`: PASS, 10 passed
- `source_proxy/tests/test_scout_research_bridge.py -q`: PASS, 8 passed
- backend slice: PASS, 133 passed

The first Scout bridge invocation through an SSH stdin script produced `unrecognized arguments: -`; rerunning the exact pytest command directly in the checkout passed 8/8, so I classified the first result as an invocation artifact rather than a product failure.

## Caveats

- The append-only run directories are still untracked, matching the claimed evidence handling. They should remain preserved for human review.
- The direct provider proof is in `/tmp`; it existed and was valid during this audit, but it is not durable like the Plan 3 docs tree.
- The older GLM hardline audit was accurate for the earlier unstable state, but the latest HEAD and append-only receipts show the later Set A stabilization claim has superseded that older verdict for Set A readiness.
- This audit confirms Set A stability only. It does not prove Set B/C generalization.

## Recommendation

GLM review is not required to accept Set A as ready for human review. It may still be useful before Set B/C if Britton wants independent scrutiny of the generalization risk, but this audit found enough evidence to move Set A to human decision.

Set B can be considered next only after Britton reviews and approves this Set A closeout. This audit did not run Set B/C.

## Safety

- source edited: no
- committed: no
- pushed: no
- Set B/C run: no
- Plan 4 started: no
- SpiritFlix/media/Jellyfin touched: no
