# Increment 0.5 - June 12 False-Positive Fixture Carry-Forward Packet

## Preflight

- Repo path: `Z:\`
- Allowed files: evidence docs only.
- Source code, generated benchmark artifacts, and preview artifacts were not changed.

## Implement

Created:

- `phase-0/increment-0.5-june-12-false-positive-fixtures.md`
- `phase-0/june-12-false-positive-fixtures.json`

## Fixture Requirements

These fixtures must be carried into Phase 1.3 and Phase 6.2.

1. Calculator false positive
   - Previous result: PASS
   - Corrected result: FAIL
   - Behavior test: click/type `2 + 3 =`
   - Observed: display returned `0` instead of `5`

2. Dark theme false positive
   - Previous result: PASS
   - Corrected result: FAIL
   - Behavior test: capture computed body colors, click toggle, capture again
   - Observed: class changed but background/text colors stayed the same

3. Habit tracker false positive
   - Previous result: PASS
   - Corrected result: FAIL
   - Behavior test: inspect for input/buttons/state-changing controls
   - Observed: static hard-coded habits, no controls

4. Timer false negative
   - Previous result: FAIL
   - Corrected result: PASS
   - Behavior test: start timer, wait, stop, verify time freezes
   - Observed: timer changed from `00:00` to `00:02` and stayed after Stop

5. Non-app / missing artifact failures
   - Notes app: markdown only, not app
   - Password checker: no preview files
   - Drawing pad: no preview files
   - Music player mockup: no preview files

## Required Truth Rules

- Artifact existence does not imply product PASS.
- Preview opens does not imply behavior PASS.
- Static content does not imply app behavior.
- Corrected behavior diagnostics are proof inputs for future phases.

## Verify

- All requested fixture classes recorded: PASS
- Phase 1.3 and Phase 6.2 future use recorded: PASS
- Pass-preservation fixture for timer recorded: PASS
- Negative cases for missing/non-app artifacts recorded: PASS

## Triage

Verdict: GO

Next authorized increment: Increment 0.6 - Existing-system reuse inventory.

