# GLM Independent Source Proxy Audit — Closeout

**Auditor**: GLM (ZCode builtin:zai-start-plan/GLM-5-Turbo)
**Date**: 2026-06-17
**Scope**: Source Proxy system — source-level code audit, live runtime probe, prior-evidence review, reduced battery
**Baseline**: Claude Opus 3×10 audit (2026-06-15, grade C)

---

## TL;DR

The PR1/PR2 codebase is **genuinely well-built**: structured truth fields, real functional/browser verifiers, honest `productive` gating, trace hygiene, anti-cheat quarantine, lane-degradation downgrade — all present and correct in source, and all proven in prior smoke receipts from 2026-06-15.

**However, the live proxy is silently running the legacy stub path.** FIP4 (and FIP1-FIP3, FIP5) environment flags were lost when the watchdog restarted uvicorn on Jun 16 19:49 from a shell context that did not inherit the tmux-exported FIP vars. My controlled live preflight post returned `coder_path: legacy_stub` with no verification, confirming FIP4 is OFF at runtime.

**This is a runtime-hygiene defect, not a code defect.** The code is ready; the deployment is stale.

---

## Grade: B+

**Rationale**: Code quality is A-level (all PR1/PR2 controls verified). Grade is pulled down to B+ because:
1. The live proxy is not exercising the real hot path (FIP4 OFF at runtime).
2. No automated smoke harness runs on watchdog restart to catch this.
3. Claude's prior C grade was pre-PR2; the source has improved dramatically since then.

Compared to Claude's C, the source-level improvements are substantial. The only reason this isn't an A is the runtime staleness.

---

## What Worked (Source-Level — Verified Correct)

### PR1 Phase A: Structured Truth Fields
- `productive` is gated on ALL of: GO verdict, `coder_path == fip4_real`, `verification_real.deterministic`, `verification_real.behavior`, no protected-path block, no degraded lanes. (decision.py:1175-1182)
- `coder_path` is set by the actual routing dispatch: `fip4_real`, `fip3_local_model`, `legacy_stub`, etc. Not a constant.
- `verification_real.behavior` requires `browser_passed OR functional_passed`. Not set by static analysis alone.
- `verification_real.functional` requires `functional_verifier_used AND functional_verifier_passed`. (decision.py:1172)
- `verification_real.browser` requires `browser_verifier_used AND browser_verifier_passed`. (decision.py:1170)
- **Independently confirmed**: PR2 browser smoke row 02 shows `verification_real.behavior:true` via `functional` while browser correctly `skipped` — the two paths are independent.

### PR1 Phase B: Public Receipt/Trace Redaction
- `_sanitize_public_receipt()` recursively strips `raw_prompt` and `raw_output_excerpt` from public responses. (decision.py:653-663)
- `_trace_hygiene_scan()` is a real tree-walking scanner that flags any private key name or reasoning-shaped pattern marker. (decision.py:683-711)
- All 4 receipt/trace endpoints gate `include_private` behind `_local_receipt_debug_authorized()`, which requires a configured dev token (OFF by default). (decision.py:5747-5820)
- **Live-verified**: Both `/fip0-receipts/latest` and `/latest/trace` return `private_access: false`, `private_fields_removed: 2`, zero leak keywords.
- **Leak scan**: 0 occurrences of `raw_prompt`, `raw_output_excerpt`, `raw_model_output`, `chain_of_thought`, `hidden_reasoning`, `private_reasoning` in 85KB receipt + 125KB trace.

### Verification Truth Cleanup
- `verification_real.functional` cannot be true unless the functional verifier was actually used AND passed. (decision.py:1172)
- Deterministic/static analysis alone cannot produce `productive:true`.

### PR2 Functional Verifier v0
- Real Node.js `vm` sandbox (decision.py:1795-1829): strips ESM exports, disables timers and eval/wasm (`codeGeneration: { strings: false, wasm: false }`), runs generated code with 500ms timeout, confirms module loads and exports functions.
- Not synthetic — actual code execution in a sandboxed context.

### PR2 Browser Verifier v0
- Real Playwright/Chromium inline Node harness (decision.py:1470-1530): `chromium.launch({headless: true})`, navigates to generated `.html` via `file://`, captures console errors, page errors, and visible text.
- Requires `loaded && visible_text_length > 0 && no_page_errors` for pass. (decision.py:1527-1560)
- Honest failure modes: `config_blocked` if Playwright unavailable, `timed_out` on timeout, `failed` on runtime error.
- Synthetic `browser_pass_expected` cheat is quarantined behind `_trial_harness_only_enabled()`. (decision.py:1418-1441) Returns `passed:False` with reason `browser_behavior_synthetic_pass_rejected_default` when trial flag is OFF.

### Anti-Cheat Hardcoded Payload Quarantine
- Every hardcoded/dummy/trial builder (`_product_trial_feature_already_satisfied_payload`, `_dummy_reversible_live_trial_coder_diff_payload`, `_expected_no_edit_trial_payload`, `_realistic_reversible_trial_coder_diff_payload`, `_dummy_trial_coder_diff_payload`) is gated behind `_trial_harness_only_enabled()`. (decision.py:4187-4208)
- `SOURCE_PROXY_TRIAL_HARNESS_ONLY` defaults to `"0"` and is absent from the live env.
- These paths are unreachable by default.

### Lane Degradation Downgrade
- If `degraded_lanes` is non-empty AND verdict starts with `"GO:"`, the verdict is rewritten to `NO-GO: expected_degraded_lane`. (decision.py:4132-4134)
- Proven in PR2 browser smoke row 04: `verification_real.behavior:true` + `coder_path:fip4_real` → still `NO-GO` because hermes_critic timed out.

---

## What Failed (Runtime — Not Source)

### Live Proxy FIP4 OFF (Critical Runtime Defect)
- **Observed**: Controlled preflight POST returned `coder_path: legacy_stub`, `productive: false`, verdict `NO-GO: fip3_local_model_lane_failed`.
- **Root cause**: The tmux shell (pid 14286) launched `tmux new -d -s ... 'cd ... && export FIP1=1 ... && npm run proxy:https:lan'`. The `export` statements run inside a transient subshell within tmux, not in the tmux client process. The watchdog (pid 275170) and uvicorn (pid 275224) were spawned from contexts that never inherited these exports.
- **When**: uvicorn started at Jun 16 19:49:40 (watchdog restart). The FIP flags were already gone.
- **Impact**: The live proxy falls through to the legacy stub coder path. No FIP4 Qwen coding, no functional/browser verification, no `productive:true` possible.
- **Proof**: pid 275224 `/proc/environ` has 0 occurrences of `SOURCE_PROXY_FIP4_QWEN_CODER_ENABLED=1`. My preflight post confirmed `coder_path: legacy_stub`.
- **Note**: Prior smoke evidence (2026-06-15) shows FIP4 was working before the watchdog restart. The code is correct; the deployment is stale.

### No Automated Runtime Health Smoke
- There is no mechanism that runs a FIP4 health smoke after each watchdog restart to detect that the real hot path is live.
- A watchdog restart that silently degrades the proxy to legacy_stub is invisible without manual inspection.

---

## What Remains Before Daily-Driver Use

1. **Runtime env persistence**: FIP flags must survive watchdog restarts. Either:
   - Write FIP flags to `.env.local` or `config/source-proxy.env` (loaded by `source-proxy-dev.mjs`).
   - Or ensure the tmux shell's exports propagate correctly (e.g., use `set -a; source fip-flags.sh; npm run ...` pattern).
2. **Watchdog restart smoke**: After each restart, run a lightweight FIP4 health probe. If `coder_path` returns `legacy_stub`, alert or auto-restart with correct env.
3. **Functional verifier coverage**: Currently only verifies module load + export count. Should also verify that exported functions return correct values for known inputs (actual behavioral verification, not just "module loaded without error").
4. **Browser verifier stability**: PR2 smoke showed `timed_out` for real HTML tasks. Playwright/Chromium startup may need optimization or a longer timeout for cold-start.
5. **Protected path coverage**: The `protected_blocked` gate exists but the protected-path list could be more comprehensive.
6. **Receipt storage hygiene**: Old receipts with legacy-stub verdicts should be cleaned or tagged so they don't pollute analytics.

---

## Battery Results

See `glm-battery-results.json` for machine-readable data. Summary:
- Reduced 6-row battery run against live proxy (FIP4 OFF → legacy stub path).
- All rows returned `coder_path: legacy_stub` as expected given runtime state.
- Trace hygiene passed on all rows (leak_count: 0).
- No `productive:true` possible without FIP4.
- Battery validates structural integrity of the legacy stub path but cannot measure FIP4 behavior.

---

## Comparison to Claude Prior Audit

| Dimension | Claude (2026-06-15) | GLM (2026-06-17) |
|---|---|---|
| Grade | C | B+ |
| Productive truth | NO — `productive:true` could come from static-only paths | YES — requires `fip4_real` + `verification_real.behavior` |
| Verification realness | NO — deterministic-only counts | YES — real functional (vm sandbox) + browser (Playwright/Chromium) |
| Browser proof independence | Not tested | YES — browser proof does not set `functional:true` |
| Synthetic cheat | `browser_pass_expected` could produce PASS | Quarantined behind trial flag, rejected by default |
| Trace hygiene | Raw Qwen output leaked in traces | Fixed — zero leaks in live scan |
| Hardcoded payloads | Live and reachable | Quarantined behind `_trial_harness_only_enabled()` |
| Lane degradation | GO verdicts despite lane failure | Fixed — `GO:` → `NO-GO: expected_degraded_lane` |
| Runtime health | Not assessed | FAIL — FIP4 OFF, proxy silently on legacy stub |
| Overall code quality | Fragile, honest but incomplete | Robust, honest, well-gated — but not being exercised live |

GLM **agrees with Claude's C grade for the codebase as it was on 2026-06-15**. The improvements since then (PR1 Phase B, verification truth cleanup, PR2 functional/browser verifiers, lane-degradation downgrade, anti-cheat quarantine) are genuine and substantial. The source-level grade is now A. The overall B+ reflects the runtime staleness.

---

## Evidence

All evidence in `docs/evidence/source-proxy-glm-3x10-audit-20260617/`.
Prior evidence referenced from `docs/evidence/source-proxy-claude-3x10-audit-20260615/`.
