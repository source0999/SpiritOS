# Level 4 Contract

Level 4 disposable artifact PASS requires more than a static UI, preview open, or one shallow state change.

Each prompt should verify at least two meaningful behavior observations where possible, such as add plus toggle, calculate plus reset, play/pause plus next, draw plus clear, theme switch plus secondary control, input feedback plus show/hide, update weather plus unit/city switch, or start/pause/reset/log history.

## Non-Pass Signals

- Route GO alone.
- Preview opens.
- Static DOM presence.
- Model says it works.
- One button label exists but does not change state.
- One behavior works but the second requested behavior is absent.
- Repair writes files but behavior stays static.

## Final Verdict Rules

- GO: at least 8/10 Level 4 behavior PASS, clean anti-cheat, clean anti-tailoring, no score warnings, no false-positive/false-negative corrections.
- PARTIAL-GO: 6/10 or 7/10 Level 4 behavior PASS with clean integrity and useful diagnostics.
- NO-GO: 5/10 or less Level 4 behavior PASS, or major generalization failure, with intact evidence.
- NEEDS-INSTRUMENTATION: existing probes cannot fairly evaluate Level 4 complexity.
- NEEDS-FIX: runner/evidence/test pipeline breaks or integrity contamination appears.

## Scoring Boundary

The Level 4 behavior verdict is based on the locked prompt set and the evidence-only Level 4 probe wrapper written before the run. Existing Source Proxy runtime, route code, scorer code, final verdict logic, generated artifacts, and repair logic are not patched in this proof.
