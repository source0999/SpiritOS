# Coding E2E Loop

Global setup is documented in [global-test-tooling.md](./global-test-tooling.md).

One-shot managed Prompt 1 lifecycle proof:

```bash
node scripts/run-coding-e2e-loop.mjs --fixture-state=missing
```

Bookmark loop:

```bash
node scripts/run-coding-e2e-loop.mjs --fixture-state=missing --watch
```

Fixture states:

- `missing`: requires the product reset route to return `status=reset_verified` and `clean_verified=true`. The harness also confirms all six fixture files are absent. Direct filesystem deletion never counts as reset proof.
- `bare`: first requires the same verified product reset, then seeds six test-precondition files with a non-rendering `src/main.js`. The seed is recorded separately and is not reset proof. Prompt 1 must not short-circuit to `already_satisfied`.
- `rendering`: first requires the verified product reset, then seeds a rendering storefront test precondition. Prompt 1 may short-circuit only with storefront/runtime proof.

The authoritative v3 lifecycle uses `--fixture-state=missing`. `bare` and `rendering` remain useful with focused anti-cheat specs, but those focused runs are non-authoritative unless they also emit the complete v3 lifecycle packet.

The loop loads `.env.local` before probing the proxy, frontend, or Playwright. It logs the loaded `SPIRIT_CODING_USE_PROXY` and `SOURCE_PROXY_*` keys, masking keys/tokens/secrets. It does not start fallback services.

Health checks:

- Requires Source Proxy at exactly `https://127.0.0.1:8787`.
- Requires the frontend at `https://localhost:3000` or `https://127.0.0.1:3000`.
- Requires `/v1/self/status` to identify `source-proxy` and list this exact checkout root in `configured_roots`.
- Requires the frontend workspace-read response to report this exact checkout root.
- Hard-fails without fixture mutation when either managed service is unhealthy, stale, or serving another checkout. Ports `8877` and `3100` are recorded only as forbidden historical fallbacks.
- Requires `POST /v1/coding/dummy-product-site-preview/reset` before Playwright. A missing route, non-200 response, unverified response, or residual fixture file is a hard failure.

Evidence lands under `docs/evidence/e2e-loop/<timestamp>/`:

- `result.json`: `coding-e2e-loop/v3` summary with managed identity, pre-run product-reset proof, Playwright status, ordered HTTP events, lifecycle receipts, required stage verdicts, and one authoritative final truth.
- `diagnostics.txt`: diagnostics for both the initial Prompt 1 run and the clean Prompt 1 rerun, copied from the real `/coding` UI state.
- `playwright-report.json`: raw Playwright JSON reporter output.
- `playwright-stderr.txt`: stderr from the Playwright process.

The authoritative lifecycle is fixed and ordered:

1. Verify the product-reset-established missing fixture, then run Prompt 1 through a real six-file apply, post-apply verification, browser verification, anti-cheat, and a commit-safe final receipt.
2. Click the selected-prompt Undo control in the real Trial Runner UI. The test requires the task-bound `/undo` request to carry the initial run's exact backup-manifest path and requires the request, response, and durable task readback to agree on that manifest, the Undo receipt, the exact six restored files, untouched scope, and `fixture_missing` state. A legacy reverse diff does not qualify.
3. Require the UI's missing-preview response and clean-baseline response body to prove a clean state after Undo and before its product reset call, so the reset cannot mask an incomplete Undo. The reset response must contain `status=reset_verified`, `reset_verified=true`, `clean_verified=true`, and a receipt id.
4. Independently recheck the clean baseline, all six absent fixture files, and the missing browser preview.
5. Reload `/coding` and run Prompt 1 again from that clean state. The rerun must start after the recorded clean probe, use a new task id, perform the same exact six-file apply (never `already_satisfied`), and independently pass the same canonical stages.

Overall PASS requires every infrastructure step plus `context`, `post_apply_verification`, `browser_verification`, `anti_cheat`, `final_receipt`, `diagnostic_consistency`, `prompt1_initial_run`, `manifest_backed_undo`, `product_reset_after_undo`, `clean_baseline_after_undo`, and `prompt1_clean_rerun` to report `GO` with complete evidence fields. The final rerun receipt must also say `commit_safe=true`. Missing, `not graded`, blocked, failed, contradictory, out-of-order, GO-labeled-but-incomplete, or legacy one-pass evidence is `NO_GO`.

The default spec is the authoritative lifecycle. A focused smoke spec supplied with `--spec` cannot produce a v3 GO unless it emits the complete lifecycle packet.

Focused contract check (does not start services or touch the fixture):

```bash
node --test tests/e2e-loop/coding-e2e-loop-contract.test.mjs
```
