# GLM vs Claude: Source Proxy Audit Comparison

**GLM audit**: 2026-06-17 (this audit)
**Claude audit**: 2026-06-15 (prior, pre-PR2)
**Claude grade**: C
**GLM grade**: B+

---

## Side-by-Side Comparison

| Dimension | Claude (2026-06-15) | GLM (2026-06-17) | Changed? |
|---|---|---|---|
| **Overall grade** | C | B+ | ⬆️ Yes (source improved; runtime stale) |
| **`productive:true` honesty** | `productive:true` could come from static/deterministic paths only | Requires `fip4_real` + `verification_real.behavior` + no degraded lanes | ✅ Fixed |
| **`coder_path` field** | Not present or not gated | Present; `fip4_real` vs `legacy_stub` tracked | ✅ Added |
| **`verification_real.behavior`** | Not present | Requires `browser_passed OR functional_passed` | ✅ Added |
| **`verification_real.functional`** | Could be true from deterministic-only | Requires `functional_verifier_used AND functional_verifier_passed` | ✅ Fixed |
| **Functional verifier** | Not present | Real Node `vm` sandbox, 500ms timeout, module load + export verification | ✅ Added |
| **Browser verifier** | Synthetic `browser_pass_expected` | Real Playwright/Chromium, `chromium.launch({headless:true})`, file:// navigation | ✅ Replaced synthetic |
| **Browser ≠ functional** | Not tested | Proven: row 02 shows `behavior:true` via `functional` while `browser:skipped` | ✅ Independent |
| **Synthetic cheat** | `browser_pass_expected` could produce PASS | Quarantined behind `_trial_harness_only_enabled()`, returns `rejected_default` when flag OFF | ✅ Quarantined |
| **Hardcoded payloads** | Live and reachable | All gated behind `_trial_harness_only_enabled()`, unreachable by default | ✅ Quarantined |
| **Trace hygiene scanner** | Not present | Real tree-walker (`fip6_trace_hygiene_v1`), flags leak keys + pattern markers | ✅ Added |
| **Public receipt redaction** | Raw Qwen output leaked in traces | `_sanitize_public_receipt()` strips `raw_prompt` + `raw_output_excerpt` recursively | ✅ Fixed |
| **Private receipt access** | Endpoints unauthenticated | Gated behind dev token (`_local_receipt_debug_authorized()`), OFF by default | ✅ Mitigated |
| **Lane degradation** | GO verdicts despite lane failure | `GO:` → `NO-GO: expected_degraded_lane` when `degraded_lanes` non-empty | ✅ Fixed |
| **Degraded lane hiding behind `productive:true`** | Possible | Impossible: degraded lanes block `productive:true` at line 1175-1182 | ✅ Fixed |
| **`SOURCE_PROXY_TRIAL_HARNESS_ONLY`** | Not assessed | Confirmed OFF (absent from env), defaults to `"0"` | ✅ Safe |
| **Runtime FIP flag persistence** | Not assessed | **FAIL**: watchdog restart lost FIP flags, proxy on `legacy_stub` | ⚠️ New finding |
| **Automated restart smoke** | Not assessed | **MISSING**: no health probe after watchdog restart | ⚠️ New finding |
| **Functional verifier depth** | N/A | Narrow (module load only, not value verification) | ⚠️ Still limited |
| **Browser verifier stability** | N/A | PR2 smoke showed `timed_out` for real HTML tasks | ⚠️ Unstable |
| **Protected path list** | Not assessed | Exists but could be more comprehensive | ⚠️ Could improve |

---

## What Improved (Source-Level)

1. **Structured truth model** — PR1 Phase A added `productive`, `coder_path`, `verification_real`, `degraded_lanes`. These fields are now the authoritative honesty layer.
2. **Productive gating** — `productive:true` is impossible without real FIP4 coding + real behavior verification. The gate is multi-factor and correct.
3. **Real verifiers** — Both functional (Node vm sandbox) and browser (Playwright/Chromium) are genuine execution-based verifiers, not synthetic stubs.
4. **Trace hygiene** — A real scanner walks the trace and flags leaks. Public receipts are recursively sanitized. Live verification shows zero leaks.
5. **Anti-cheat quarantine** — All hardcoded/dummy/trial payloads are gated behind a trial flag that's OFF by default.
6. **Lane degradation downgrade** — Required lane failures now properly downgrade GO verdicts to NO-GO.

## What Is Still Weak

1. **Runtime env persistence** — The FIP flags are not reliably inherited across watchdog restarts. This is the single biggest blocker.
2. **No restart health probe** — Nothing validates that FIP4 is actually live after a restart.
3. **Functional verifier depth** — Only verifies module load + export count. Doesn't verify that functions return correct values. A malicious or broken module that exports garbage would pass.
4. **Browser verifier stability** — Timed out on real HTML tasks in PR2 smoke. May need timeout tuning or Playwright warm-up.
5. **POST path hangs when FIP4 OFF** — The legacy stub path attempts Qwen codegen and hangs, making the proxy unresponsive to new requests. No graceful fallback.
6. **Receipt storage** — Old receipts with legacy-stub verdicts are not tagged or cleaned.

---

## GLM vs Claude Agreement Matrix

| Claude Finding | GLM Independent Verdict | Agree/Disagree |
|---|---|---|
| "structured truth fields missing" | Now present and correct in source | ✅ Agree (was true; now fixed) |
| "`productive:true` dishonest" | Now honest (multi-factor gate) | ✅ Agree (was true; now fixed) |
| "browser verifier synthetic" | Now real Playwright/Chromium | ✅ Agree (was true; now fixed) |
| "raw output leaks in traces" | Fixed — zero leaks in live scan | ✅ Agree (was true; now fixed) |
| "hardcoded payloads live liability" | Quarantined behind trial flag | ✅ Agree (was true; now fixed) |
| "GO verdicts despite lane failure" | Fixed — degraded lanes downgrade | ✅ Agree (was true; now fixed) |
| "runtime discipline needed" | **Still true** — worse than Claude found | ✅ Agree (still true) |
| "daily-driver ready?" | Claude said NO. GLM says: source yes, runtime NO | ✅ Agree |

**GLM agrees with all of Claude's prior findings.** Every issue Claude identified in the 2026-06-15 audit has been addressed in the source code. However, GLM adds one new finding Claude didn't assess: the runtime env staleness that silently degrades the proxy to legacy_stub.

---

## Grade Evolution

```
Claude (2026-06-15, pre-PR2):  C  (honest but fragile, multiple truth gaps)
Source code (2026-06-17):      A- (all controls present and correct)
Runtime (2026-06-17):          D  (FIP4 OFF, proxy on legacy_stub, POST hangs)
GLM overall (2026-06-17):      B+ (source A-, runtime D, weighted average)
```

The gap between source quality (A-) and runtime health (D) is the defining tension. The code is ready; the deployment is not.
