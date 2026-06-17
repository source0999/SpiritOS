# Set 3 Closeout — Claude 3x10 Basic Coding Battery

Date: 2026-06-16 (UTC)
Duration: ~40 min.

## 10-row matrix

| prompt_id | raw prompt | target | score_class | qwen | det | browser | hermesV | trace==receipt |
|---|---|---|---|---|---|---|---|---|
| s3-01-shell | spin up a tiny app shell with a home screen | shell.html | verifier_blocked_browser | used | pass | FAIL | NEEDS_FIX | yes |
| s3-02-cruncher | build a basic number cruncher | cruncher.js | productive_go | used | pass | n/a | PASS | yes |
| s3-03-forecast | make a simple forecast-ish demo with fake data if needed | forecast.js | productive_go | used | pass | n/a | PASS | yes |
| s3-04-tasks | make a task tracker | tasks.js | productive_go | used | pass | n/a | PASS | yes |
| s3-05-countdown | make a countdown thing | countdown.js | productive_go | used | pass | n/a | PASS | yes |
| s3-06-journal | make a mini journal page | journal.js | productive_go | used | pass | n/a | PASS | yes |
| s3-07-budget | make a budget split helper | budget.js | productive_go | used | pass | n/a | PASS | yes |
| s3-08-progress | make a simple progress graph | progress.html | verifier_blocked_browser | used | pass | FAIL | FAIL | yes |
| s3-09-coming-soon | make a coming soon page | coming-soon.html | verifier_blocked_browser | used | pass | FAIL | FAIL | yes |
| s3-10-alive | make an endpoint that says the service is alive | alive.ts | productive_go | used | pass | n/a | PASS | yes |

## Counts (Set 3)

- productive_go: 7
- verifier_blocked_browser: 3 (`.html`)
- unexpected_no_go / config_blocked / trace_mismatch / hardcoded / preview_only_go / integrity_fail: 0
- Receipts + traces: 10/10 durable, 10/10 trace==receipt.

## Notable lane truth (Set 3)

- `s3-04-tasks`: hermes_critic_status = `failed`, yet final verdict GO: fip5 (advisory critic failure non-blocking; recorded in model_errors but does not gate GO).

## Fixes / reruns

- None.

## Generalization vs Set 1 and Set 2

- scaffold/home: s1-01, s2-01, s3-01 -> all verifier_blocked. Consistent.
- calc/logic: s1-02, s1-07, s2-07, s3-02, s3-07 -> all productive. Consistent.
- data/ui: s1-03, s2-03, s3-03 -> all productive. Consistent.
- state/crud: s1-04, s2-04, s3-04, s1-06, s2-06, s3-06 -> all productive. Consistent.
- timer: s1-05, s2-02, s2-05, s3-05 -> all productive. Consistent.
- ui/page: s1-08, s1-09, s2-09, s3-08, s3-09 -> all verifier_blocked. Consistent.
- api: s1-10, s2-10, s3-10 -> all productive. Consistent.

Outcome is fully determined by task shape (target extension / browser relevance), not by wording. Zero evidence of prompt-fitting across reworded sets.
