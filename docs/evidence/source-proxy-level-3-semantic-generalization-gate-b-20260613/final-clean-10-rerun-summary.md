# Final Clean Similar 10 Rerun Summary

## Command

```powershell
python Z:/docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_run_batch.py --prompt-file Z:/docs/evidence/source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613/final-proof-prompt-set.json --run-root Z:/docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/final-clean-10-gate-b-runs --title "Source Proxy Level 3 semantic generalization Gate B final clean similar 10 rerun" --results Z:/docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/final-clean-10-gate-b-results.json --html Z:/docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/final-clean-10-gate-b.html --run-receipt Z:/docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/final-clean-10-gate-b-run-receipt.json --browser-results Z:/docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/final-clean-10-gate-b-browser-behavior-results.json --repair-summary Z:/docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/final-clean-10-gate-b-post-behavior-repair-summary.json --model-id qwen2.5-coder:7b
```

Note: an earlier relative-path invocation failed before prompt execution because the runner resolves relative paths from its own script directory. The successful rerun used absolute `Z:/...` paths.

## Result

- Pass/fail count: 9 PASS, 1 FAIL.
- Threshold: 8/10 behavior PASS.
- Verdict: GO.
- Overall verdict from runner: `GREEN_READY_FOR_BRITTON_REVIEW`.
- Repair attempts: 2.
- Repair handoffs: 0.
- Score warnings: 0.
- False-positive corrections: 0.
- False-negative corrections: 0.
- Report verdict mismatches: 0.
- Anti-cheat status: clean.

## Per-Prompt Results

| prompt | route | final | repair attempts | failure |
| --- | --- | --- | ---: | --- |
| make a laundry flip countdown | GO | PASS | 0 |  |
| make a parking garage cost sharer | GO | PASS | 0 |  |
| make a dusk dawn palette switch | GO | FAIL | 1 | theme_no_computed_state_change |
| make a beach bag checklist app | GO | PASS | 0 |  |
| make a pretend balcony forecast tile | GO | PASS | 0 |  |
| make a campfire podcast mini player | GO | PASS | 0 |  |
| make a stair step tally counter | GO | PASS | 0 |  |
| make a sticky thought memo board | GO | PASS | 0 |  |
| make a secret phrase strength gauge | GO | PASS | 0 |  |
| make a finger paint doodle pad | GO | PASS | 1 |  |

## Remaining Failure

The only remaining failure is `make a dusk dawn palette switch`.

The route and preview issue is fixed: route GO, disposable intent, preview selected, and behavior contract probe id `theme-computed-color-change` recorded.

The browser probe used the generic visible text-change path for dusk/dawn/palette wording, and visible text did not change after click. The strict final classifier reports `theme_no_computed_state_change`.

No scorer changes were made after the rerun.
