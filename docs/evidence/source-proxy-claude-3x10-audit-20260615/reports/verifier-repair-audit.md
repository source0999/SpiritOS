# Verifier & Repair Audit (evidence-based)

Date: 2026-06-16 (UTC). Basis: 30-row battery receipts + source inspection.

## Deterministic verifier

- Ran 30/30, `passed` 30/30 for the structural contract.
- What it ACTUALLY checks (`_fip5_deterministic_verifier`): fip4 status used, final==received
  hash, output parsed, changed files inside allowed_files, protected files not changed, and
  (only when the prompt contains an "exactly this content:" marker) required-text presence.
- What it does NOT check: that the code compiles, runs, has no errors, or fulfills the request.
  No tests are executed. So `deterministic passed` = "structurally valid replace_file in scope".
- Harness coupling (source): `expected_result_state in {repair_expected, max_repair_expected}`
  forces synthetic failures. The battery did NOT send these, so all deterministic passes were
  organic-structural (good), but the forced-failure path remains in production code.

## Browser behavior verifier

- THERE IS NO REAL BROWSER. `_fip5_browser_probe` returns synthetic `passed=True` only when fed
  `expected_result_state=browser_pass_expected`; otherwise, for browser-relevant targets
  (`.tsx/.jsx/.html`, `src/app`, `src/components`) it returns `passed=False`.
- Battery proof: 8/8 `.html` rows -> `browser passed=False`, verdict
  `NO-GO: fip5_browser_behavior_authority_blocks_pass`, `probes_run=["fip5_runtime_browser_relevance_probe"]`
  (a label, not a DOM/navigation check). No screenshot, no console, no assertions.
- Honesty note: because the battery did NOT feed the flag, the system honestly refused to pass
  UI. The OVERCLAIM is realized only when a runner feeds `browser_pass_expected` (as Level 5R2 did).

## Hermes post-code verifier

- Cannot manufacture PASS over evidence: `_fip5_normalize_hermes_verifier_output` downgrades
  PASS->NEEDS_FIX on deterministic failure and PASS->FAIL on browser failure. Proven: every
  `.html` row returned FAIL/NEEDS_FIX, never PASS.
- Evidence mismatch re-ask exists and is bounded (max 2 attempts).
- Weakness: for non-UI rows there is no functional/browser evidence, so PASS is a low-evidence
  rubber-stamp on a structurally valid file. Model is `hermes3:8b-abliterated`.

## Repair loop

- 0 repair attempts across ALL 30 rows (`repair_attempt_count=0`, `repair_max_attempts=2`).
- Why: the loop condition is `not deterministic.passed and browser.passed is not False`.
  Productive rows passed deterministic immediately (no repair); `.html` rows failed on BROWSER
  (browser.passed=False short-circuits the loop, no repair). So honest prompts never triggered
  repair.
- Consequence: the bounded repair behavior is UNPROVEN outside the harness-forced
  `repair_expected` flag. Its real-world reliability remains untested by honest input.
- Bounding is enforced in source (max attempts 0-5, default 2) and verdict
  `NO-GO: fip5_repair_attempts_exhausted...` exists, but was not reached here.

## No-op / already-satisfied behavior

- Not exercised honestly here (all targets were fresh placeholders -> real edits). The hardcoded
  already-satisfied path (`_product_trial_feature_already_satisfied_payload`) was NOT triggered.

## Authority chain verdict

The verifier authority chain is structurally SOUND (verifier cannot override deterministic or
browser) but EVIDENTIALLY HOLLOW for the two cases that matter:
1. UI behavior: no real browser -> cannot verify, honestly blocks.
2. Non-UI correctness: no tests/execution -> PASS attests structure only.
Plus the repair loop is effectively dead code under honest input. Fixing verification quality
(real browser + functional execution + organic repair) is the top engineering priority.
