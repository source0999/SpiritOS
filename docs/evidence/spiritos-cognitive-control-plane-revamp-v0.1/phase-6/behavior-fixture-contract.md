# Behavior Fixture Contract

## Product PASS Rule

A product PASS requires direct behavior proof against the acceptance criteria for the requested product. Supporting signals are not enough.

The following are not product PASS evidence by themselves:

- artifact existence
- preview opens
- route returns 200
- generated markdown
- static hard-coded content
- body class toggles without computed visual change
- clean diff preview
- passing unit tests that do not exercise the requested behavior

## Proof Tiers

| Tier | Name | Product PASS Eligible | Description |
| --- | --- | --- | --- |
| 0 | Artifact readiness | No | Artifact exists, file type is plausible, preview file path is present. |
| 1 | Static or DOM contract | No | Expected elements, labels, or CSS classes exist without interaction proof. |
| 2 | Behavior interaction and computed state | Yes | Interaction is executed and observed result matches acceptance criteria. |
| 3 | Route, browser, screenshot, or manual proof | Yes | End-to-end proof covers the requested user behavior and records receipts. |
| 4 | Regression suite or repeatability | Yes | Behavior proof is repeatable and tied to tests or durable evidence. |

## June 12 Required Fixtures

### Calculator False Positive

- Fixture id: `calculator-false-positive`
- Previous result: PASS
- Corrected result: FAIL
- Required behavior test: click or type `2 + 3 =`
- Observed failure: display returned `0` instead of `5`
- PASS only if: display returns `5`
- Future required use: Phase 1.3 and Phase 6.2

### Dark Theme False Positive

- Fixture id: `dark-theme-false-positive`
- Previous result: PASS
- Corrected result: FAIL
- Required behavior test: capture computed body colors, click toggle, capture computed colors again
- Observed failure: class changed but background and text colors stayed the same
- PASS only if: computed background or text colors visibly change in the expected direction
- Future required use: Phase 1.3 and Phase 6.2

### Habit Tracker False Positive

- Fixture id: `habit-tracker-false-positive`
- Previous result: PASS
- Corrected result: FAIL
- Required behavior test: inspect for input, buttons, and state-changing controls
- Observed failure: static hard-coded habits with no controls
- PASS only if: user can add, complete, edit, remove, or otherwise change habit state according to the prompt
- Future required use: Phase 1.3 and Phase 6.2

### Timer False Negative

- Fixture id: `timer-false-negative`
- Previous result: FAIL
- Corrected result: PASS
- Required behavior test: start timer, wait, stop, verify time freezes
- Observed pass: timer changed from `00:00` to `00:02` and stayed after Stop
- PASS preservation rule: keep this PASS when start, count, stop, and freeze behavior works
- Future required use: Phase 6.2 pass-preservation fixture

### Non-App and Missing Artifact Failures

- Fixture id: `notes-markdown-only`
- Corrected result: FAIL
- Required behavior test: verify an app exists, not just markdown content
- Observed failure: notes app generated markdown only instead of an app

- Fixture ids: `password-checker-missing-preview`, `drawing-pad-missing-preview`, `music-player-mockup-missing-preview`
- Corrected result: FAIL
- Required behavior test: preview artifact must exist before behavior can be evaluated
- Observed failure: no preview files

## Required Future Use

Phase 6 implementation must preserve corrected behavior diagnostics as proof inputs. It must never rediscover these fixtures from scratch or let raw artifact availability override the corrected verdict.
