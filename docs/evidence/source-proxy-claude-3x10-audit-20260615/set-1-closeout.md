# Set 1 Closeout — Claude 3x10 Basic Coding Battery

Date: 2026-06-15
Runtime: real integrated path (FIP-4 Qwen + FIP-5 deterministic/browser/Hermes), confirmed in preflight.
Duration: ~44.5 min (10 rows, cold+warm model loads; 190–360s/row).

## 10-row matrix

| prompt_id | raw prompt | target | verdict | score_class | qwen | det | browser | hermesV | hashmatch | repair | trace==receipt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s1-01-homepage | init a repo and make a homepage for my app | index.html | NO-GO browser authority | verifier_blocked_browser | used | pass | FAIL(no real browser) | FAIL | yes | 0 | yes |
| s1-02-calculator | make calculator app | calculator.js | GO: fip5 | productive_go | used | pass | n/a(skip) | PASS | yes | 0 | yes |
| s1-03-weather | make weather app | weather.js | GO: fip5 | productive_go | used | pass | n/a | PASS | yes | 0 | yes |
| s1-04-todo | make a todo list thing | todo.js | GO: fip5 | productive_go | used | pass | n/a | PASS | yes | 0 | yes |
| s1-05-timer | make a little timer | timer.js | GO: fip5 | productive_go | used | pass | n/a | PASS | yes | 0 | yes |
| s1-06-notes | make a notes app | notes.js | GO: fip5 | productive_go | used | pass | n/a | PASS | yes | 0 | yes |
| s1-07-expense | make a expense splitter | split.js | GO: fip5 | productive_go | used | pass | n/a | PASS | yes | 0 | yes |
| s1-08-chart | make a simple chart page | chart.html | NO-GO browser authority | verifier_blocked_browser | used | pass | FAIL | FAIL | yes | 0 | yes |
| s1-09-signup | make a signup landing page | signup.html | NO-GO browser authority | verifier_blocked_browser | used | pass | FAIL | NEEDS_FIX | yes | 0 | yes |
| s1-10-status | make a tiny api route that returns status | status.ts | GO: fip5 | productive_go | used | pass | n/a | PASS | yes | 0 | yes |

## Counts

- productive_go: 7
- verifier_blocked_browser: 3 (all `.html`, browser-relevant)
- expected_safety_block: 0
- unexpected_no_go: 0
- config_blocked: 0
- trace_mismatch: 0
- lane_truth_warning: 0
- hardcoded_used / preview_only_go / productive_go_integrity_fail: 0
- Receipts + traces: 10/10 durable, 10/10 trace==receipt.

## Fixes applied

- None. Runner worked on first execution (after pre-seeding target files to avoid the `target_missing` gate, which is by design — the proxy never creates files, only proposes diffs).

## Reruns

- None needed.

## Honest findings (Set 1)

1. POSITIVE: The real integrated path is exercised end to end. Every productive row has qwen `used`, deterministic pass, Hermes verifier `PASS`, `final_coder_packet_hash == coder_received_packet_hash`, durable receipt + matching FIP-6 trace, changed files strictly inside the disposable target root. No hidden fallback, no hardcoded payload, no preview-only GO.
2. POSITIVE / honesty proof: All 3 UI (`.html`) rows honestly NO-GO'd on the browser authority. Hermes returned FAIL/NEEDS_FIX (NOT a faked PASS) because the browser probe reported `passed=False`. Without the `expected_result_state=browser_pass_expected` harness flag, the system refuses to pass UI behavior. This confirms the synthetic-browser pass seen in Level 5R2 is realized ONLY when the runner feeds that flag.
3. CRITICAL QUALITY GAP: `productive_go` does NOT mean "working app." Example: `s1-02-calculator` produced a real Qwen diff but the content is a non-functional stub (`<h1>Calculator</h1>` + comment "Add your calculator components here") with zero calculator logic. The deterministic verifier only checks structure (file written, hash match, path allowed, diff present); it runs no tests and no behavior probe for `.js`. Hermes `PASS` has no functional evidence to stand on, so it is effectively a rubber-stamp. The proxy reliably produces *plausible scaffolds* and receipts them honestly, but it does NOT verify functional correctness.
4. NUANCE: Qwen emitted React/JSX for plain `.js` targets (`import React`), i.e., it ignores file-type/runtime intent. Output is syntactically plausible but contextually loose.

Set 1 verdict: integration is real and honest; verification authority is structural-only, so productive GO overstates capability.
