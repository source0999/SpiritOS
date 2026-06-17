# Full Proxy Audit — SpiritOS Source Proxy (evidence-based)

Date: 2026-06-16 (UTC). Basis: live 3x10 battery (30 rows) on the real integrated path
(FIP-1..5 enabled), durable receipts, FIP-6 traces, source inspection, runtime proof.

## 1. Executive verdict

Grade: C (confidence: high).

The integrated pipeline is REAL, SAFE, and HONESTLY RECEIPTED, but it does not verify
functional correctness and overstates capability with `productive_go`. Proven strengths:
the real `/coding -> /v1/decisions/prompt-packet` hot path executed all 30 rows; Qwen coded
with perfect packet-hash discipline (final==received 30/30); durable receipts + matching
FIP-6 traces 30/30; perfect target-scope containment 30/30; Scout/SearXNG honestly skipped
30/30; the synthetic browser verifier honestly REFUSED to pass UI when not fed the harness
flag (8/8 `.html` rows NO-GO, no fake PASS). Proven weaknesses: `productive_go` is structural
only (a non-functional calculator stub passed); no real browser verification exists; advisory
lanes (Gemma/Hermes-critic) timed out on several rows yet did not gate GO; FIP-6 traces embed
raw Qwen output; the bounded repair loop was never organically exercised.

## 2. Can SpiritOS handle the 3x10 basic coding battery?

Partially, and honestly. It PRODUCED code and honestly receipted 22/30 rows, and honestly
blocked 8/30 UI rows it cannot verify. But NONE of the 22 productive rows were verified to
actually work, and inspection shows non-functional scaffolds. As a "coding system that easily
handles basic tasks", it is a reliable, safe, well-instrumented PIPELINE wrapped around a weak
7B coder whose output is not functionally checked. It does not yet deliver working apps.

## 3. Prompt-by-prompt results

22 productive_go (all non-`.html`): s1-02,03,04,05,06,07,10; s2-02,03,04,05,06,07,08,10;
s3-02,03,04,05,06,07,10. 8 verifier_blocked_browser (all `.html`): s1-01,08,09; s2-01,09;
s3-01,08,09. Every productive row: GO: fip5, qwen used, hash match, deterministic pass,
Hermes PASS, repair 0, trace==receipt. Every blocked row: NO-GO browser authority, Hermes
FAIL/NEEDS_FIX (no fake PASS). Full matrix in `../battery-results.json`.

## 4. Set-by-set generalization

Sets 1/2/3 reword the same families. Score class was identical within each family across all
three sets (e.g., calculator==tip==budget==number-cruncher all productive; signup==waitlist==
coming-soon all verifier_blocked). Outcome tracks task shape, not wording.

## 5. Similar prompts -> similar correct outcomes without prompt-fitting?

Yes. No hardcoded/trial/dummy path was triggered for any of the 30 rows (verified: 0
`hardcoded_used`, no benchmark-fitted reason codes, no scaffold bundles). The behavior is
shape-driven and consistent, which is the anti-prompt-fitting evidence Britton asked for.

## 6. Failures and buckets

- verifier_blocked_browser: 8 (expected; UI cannot be verified without a real browser).
- coding_failure / output_contract: 0. repair_failure: 0. config_blocked: 0.
- unexpected_no_go: 0. trace_mismatch: 0. hardcoded_used: 0. preview_only_go: 0.
- Degraded advisory lanes (non-fatal, non-gating): Gemma failed ~6 rows, Hermes-critic 1 row.

## 7. Hardcoded/scaffolded behavior evidence

In the BATTERY: none triggered. In the CODEBASE (source inspection): present and dormant.
`source_proxy/api/decision.py` contains prompt-fitted builders
(`_product_trial_feature_already_satisfied_payload`, `_agent_trials_ui_test_coder_diff_payload`)
that match exact target paths/phrases/file-content to emit no-ops or a literal hardcoded diff
"without model execution". They are reachable on the legacy path (FIP-4 disabled) and via
`trial_recover_already_satisfied`. The battery avoided them (disposable targets, no flags), so
they did not fire — but they remain a live liability. See `anti-cheat-security-audit.md`.

## 8. Preview-only/read-only lane counted as integrated?

No false counting observed in the battery. Context lanes (Cartographer/Obsidian/Design/Mac
worker) are READ_ONLY by contract and were not counted as coder success. However, advisory
lane FAILURE (Gemma timeout) did not change the GO, so those lanes are effectively decorative
for acceptance — integrated in plumbing, not in authority.

## 9. Hidden fallback evidence

None. No qwen-precoder fallback, no cloud fallback, no TinyFish, no xersearch. The proxy never
applied a diff. `anti_tailoring_status` recorded hidden_apply/commit/push/worker = false 30/30.

## 10. Fake PASS evidence

None hidden. For UI rows the system refused to pass (Hermes FAIL/NEEDS_FIX). For non-UI rows
Hermes PASS is a low-evidence rubber-stamp (no functional check), but it is not a hidden fake —
the receipt shows exactly what was (not) checked.

## 11. Synthetic browser verifier overclaim evidence

Confirmed at the source and at runtime. There is NO browser automation in the repo. The probe
returns synthetic `passed=True` only when fed `expected_result_state=browser_pass_expected`.
The battery did not feed it, so all 8 UI rows correctly failed. The OVERCLAIM lives in the
Level 5R2 closeout prose ("browser behavior passed"), which describes a fabricated probe.

## 12. Protected-path weakness evidence

None found; strong. `source_proxy/safety/paths.py` blocks `..`, absolute/drive/UNC paths,
`%`-encoding, dotfiles, and secret markers. The exact-match allowlist (`_fip4_path_allowed`)
further constrains. All 30 battery changed-files were inside the disposable root.

## 13. Receipt/trace mismatch evidence

None. 30/30 trace verdict == receipt verdict. (Leakage is a separate issue, item 14 /
`receipt-trace-audit.md`.)

## 14. Lane truth overclaim evidence

No false `used`. Scout/SearXNG honestly `skipped` 30/30. The real lane-truth gap is the
opposite: advisory lane FAILURES (Gemma/Hermes-critic) are recorded but do NOT gate GO, so a
degraded context lane disappears behind a productive verdict.

## 15. Model-role audit

See `model-lane-audit.md`. Roles are correctly separated (Qwen code-only; Gemma/Hermes-critic
pre-coder advisory; Hermes verifier post-code). Qwen never planned/verified; verifier never
acted as critic. Gemma/critic instability under VRAM contention is the main issue.

## 16. Subagent/node audit

See `search-context-audit.md`. Cartographer advisory (read-only, real repo map). Obsidian/
Design present but typically skipped. Mac worker is a hardcoded `skipped` stub. Scout/SearXNG
honest but unexercised (no current-info prompts).

## 17. Security/vulnerability audit

See `anti-cheat-security-audit.md`. Strong path safety, no hidden apply, local-only providers.
Main risks: unauthenticated receipt/trace endpoints (publicly linked from `/coding`) that
expose raw prompts + raw model output excerpts; prompt-fitted code in production.

## 18. Bottlenecks

- Model reliability: 190-360s/row; Gemma ReadTimeouts under 3-model VRAM contention.
- Verifier quality: structural-only; no real browser; no functional/test execution.
- Coder quality: 7B emits plausible non-functional scaffolds; ignores file-type intent (JSX in .js).
- Trace hygiene: raw model output embedded in operator_trace.
- Runtime/staging: live source edited mid-run without proxy restart (on-disk/in-memory drift).

## 19. What must be fixed before "Level 10"

1. Real headless-browser behavior verification (replace the synthetic probe).
2. Functional verification for non-UI code (run generated tests / behavior probes) so
   `productive_go` means "works", not "file written".
3. Make advisory-lane degradation gate or explicitly downgrade the verdict (no silent
   decorative lanes).
4. Quarantine prompt-fitted/dummy/trial code out of the production hot path.
5. Strip raw model output from FIP-6 operator traces; enforce the "no private reasoning" claim
   with a content scanner, not a constant boolean.

## 20. What must be fixed before daily-driver use

1. Coder quality/capability (stronger or better-prompted coder; output that fulfills intent).
2. Throughput (sub-60s rows; resolve VRAM contention / model warm-keeping).
3. Auth on receipt/trace endpoints; stop leaking raw prompts/outputs to a public link.
4. Runtime discipline: never serve a proxy whose on-disk source has drifted; auto-restart or
   refuse with a staleness banner.
5. Stronger scoring that distinguishes "produced" from "verified working", surfaced in the UI.
