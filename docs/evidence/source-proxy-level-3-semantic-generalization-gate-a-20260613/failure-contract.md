# Failure Contract

Date: 2026-06-13

Verdict: NO-GO

Grade recommendation: keep Level 3 as NEEDS-FIX/NO-GO. Do not accept Level 3 as GO until a fresh similar holdout clears at least 8/10 browser-verified behavior PASS without scorer padding or prompt-specific branches.

## Final Clean Similar 10 Result

- Final result: 5/10 behavior PASS, 5 FAIL.
- Threshold: 8/10 behavior PASS.
- Qwen status: qwen2.5-coder:7b invoked for all 10 prompts.
- Gemma/Hermes status: preview-only or not invoked; no verifier transcript proves active use.
- Cartographer status: preview-only metadata/status only; no live route ownership invocation.
- Anti-cheat status: clean. No fallback, deterministic scaffold, backend-authored rescue content, cloud fallback, real app mutation, score-integrity failure, report mismatch, missing behavior evidence, or missing transcript.
- Anti-tailoring status: clean in searched source/runtime scopes. New prompt strings exist only as evidence artifacts.

## Passes

| id | prompt | family | route | behavior |
| --- | --- | --- | --- | --- |
| final-l3-clean-01 | make a laundry flip countdown | timer/countdown | GO | PASS |
| final-l3-clean-04 | make a beach bag checklist app | checklist/list | GO | PASS |
| final-l3-clean-06 | make a campfire podcast mini player | player/radio/audio | GO | PASS |
| final-l3-clean-07 | make a stair step tally counter | counter/tracker | GO | PASS |
| final-l3-clean-08 | make a sticky thought memo board | notes/memo | GO | PASS |

## Failures

| id | prompt | family | normalized_intent | route | failure |
| --- | --- | --- | --- | --- | --- |
| final-l3-clean-02 | make a parking garage cost sharer | calculator/splitter | clarification_required_real_repo_implementation | EXPECTED-BLOCKED | route_blocked_no_preview |
| final-l3-clean-03 | make a dusk dawn palette switch | theme/mode toggle | clarification_required_real_repo_implementation | EXPECTED-BLOCKED | route_blocked_no_preview |
| final-l3-clean-05 | make a pretend balcony forecast tile | weather/forecast/tile | disposable_small_file_bundle | GO | weather_static_when_update_expected |
| final-l3-clean-09 | make a secret phrase strength gauge | password/passphrase strength | clarification_required_real_repo_implementation | EXPECTED-BLOCKED | route_blocked_no_preview |
| final-l3-clean-10 | make a finger paint doodle pad | drawing/canvas/sketch | disposable_small_file_bundle | GO | drawing_canvas_no_pixel_change |

## Route And Intake Failures

final-l3-clean-02, final-l3-clean-03, and final-l3-clean-09 had behavior family/contract evidence, but normalized_intent fell to `clarification_required_real_repo_implementation`. That put them on the expected-blocked/no-preview path. The model still attempted file actions, but they were not allowed to create a disposable preview artifact.

This proves family inference and behavior contract inference can succeed while routing still blocks.

## Behavior And Repair Failures

final-l3-clean-05 and final-l3-clean-10 routed correctly to disposable artifacts and opened previews. They failed because the browser-observed behavior did not change after interaction. One repair attempt ran for each and produced path-bound writes, but the next behavior probe still failed.

Weather: the probe clicked a weather control. City/temp/condition text stayed unchanged.

Drawing: the probe performed mouse drawing on a canvas. Canvas pixels stayed unchanged.

## Why Level 3 Is Still NO-GO

Level 3 is not only about passing older locked wording. The fresh similar 10 exposed two generalization gaps:

- Semantic route boundary is brittle: nearby standalone mini-app wording can be interpreted as unresolved real-repo work.
- Browser behavior remains brittle for weather and drawing even after one local repair attempt.

A 5/10 behavior PASS result is below the 8/10 threshold. This cannot be accepted as Level 3 GO.

## Why Level 4 Or Bigger Batch Should Not Start

Starting Level 4 or a larger batch now would measure known Level 3 defects at greater cost. The next pass should first repair generic semantic routing and repair prompt/generation behavior, then rerun the existing final clean similar 10 as the bounded holdout.
