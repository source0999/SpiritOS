# Increment 1.5 - No Scaffold PASS Tests

## Tests added/changed

- `source_proxy/tests/test_coding_regression_pack.py`
  - `test_prompt_packet_agent_lab_create_blocks_known_scaffold_in_live_trial_mode`
  - `test_prompt_packet_calculator_create_blocks_fallback_after_invalid_model_tsx_in_live_trial`
  - `test_prompt_packet_agent_lab_known_apps_cannot_fall_back_to_pass_in_live_trial`
  - `test_prompt_packet_agent_lab_known_scaffold_remains_available_outside_live_trial`

- `src/lib/coding/__tests__/reversible-trial-runner.test.ts`
  - No-diff/provider-200 classification tests.
  - Baseline diagnostic formatting test.

- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`
  - Provenance/display/copy/stale cleanup related coverage in dirty tree.

- `src/lib/coding/__tests__/durable-run-store.test.ts`
  - Durable row persistence coverage in existing suite.

## Focused test results

Passed on Dell host `/home/source/SpiritOS`:

```text
.venv-source-proxy/bin/python -m unittest \
  source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_agent_lab_create_blocks_known_scaffold_in_live_trial_mode \
  source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_calculator_create_blocks_fallback_after_invalid_model_tsx_in_live_trial \
  source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_agent_lab_known_apps_cannot_fall_back_to_pass_in_live_trial \
  source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_agent_lab_known_scaffold_remains_available_outside_live_trial
```

Result: `Ran 4 tests ... OK`.

Also passed:

```text
npm run test -- src/lib/coding/__tests__/reversible-trial-runner.test.ts src/lib/coding/__tests__/durable-run-store.test.ts src/components/coding/__tests__/coding-cockpit-shell.test.tsx
```

Result: 3 files, 59 tests passed. React `act(...)` warnings appeared in existing cockpit tests.

## Self-check

- Known scaffold cannot PASS: covered.
- Generic/app-page scaffold cannot PASS: covered through bounded-create/fallback provenance and trial ban.
- Deterministic stub cannot PASS: covered by ban contract and diagnostics.
- Fallback after model failure cannot PASS: covered.
- `provider_call_made=true` does not prove model ability: covered.
- Missing provenance cannot silently PASS: durable defaults to `missing_provenance`.
- Valid model-authored diff can still PASS: source-proxy path only blocks scaffold/fallback provenance, not model-authored diff.
- Coder 10 was not rerun.
