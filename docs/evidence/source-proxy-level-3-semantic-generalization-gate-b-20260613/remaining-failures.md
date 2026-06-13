# Remaining Failures

## Summary

One final clean similar 10 prompt remains failing after Gate B:

- `make a dusk dawn palette switch`

## Failure Details

- route: GO
- normalized intent: `disposable_small_file_bundle`
- preview: selected and opened
- behavior contract probe: `theme-computed-color-change`
- repair attempts: 1
- final bucket: `theme_no_computed_state_change`
- final verdict: FAIL

## Interpretation

The route/intake part of this failure is fixed. The prior `route_blocked_no_preview` failure no longer occurs.

The remaining issue is behavior/probe alignment for dusk/dawn/palette theme prompts. The browser probe selected the generic visible text-change path for this prompt, recorded unchanged body text after click, and the strict final classifier reported a theme computed-state failure.

## Why This Does Not Block Gate B GO

Gate B success target was at least 8/10 behavior PASS with clean integrity. The rerun reached 9/10 behavior PASS with zero score warnings, zero false-positive corrections, zero false-negative corrections, and clean anti-cheat status.

Do not proceed to Level 4 automatically. The next reviewed improvement should target theme probe dispatch/generation robustness if Britton wants to chase 10/10.
