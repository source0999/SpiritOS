# Set 2 Closeout — Claude 3x10 Basic Coding Battery

Date: 2026-06-16 (UTC)
Duration: ~47 min.

## 10-row matrix

| prompt_id | raw prompt | target | score_class | qwen | det | browser | hermesV | hashmatch | trace==receipt |
|---|---|---|---|---|---|---|---|---|---|
| s2-01-dashboard | lets start a repo and make a dashboard for my app | dashboard.html | verifier_blocked_browser | used | pass | FAIL | FAIL | yes | yes |
| s2-02-counter | make a time counter app | counter.js | productive_go | used | pass | n/a | PASS | yes | yes |
| s2-03-moon | make a moon phase app | moon.js | productive_go | used | pass | n/a | PASS | yes | yes |
| s2-04-checklist | make checklist thing i can add and clear | checklist.js | productive_go | used | pass | n/a | PASS | yes | yes |
| s2-05-stopwatch | make stopwatch card with start pause reset | stopwatch.js | productive_go | used | pass | n/a | PASS | yes | yes |
| s2-06-sticky | make a quick sticky notes board | sticky.js | productive_go | used | pass | n/a | PASS | yes | yes |
| s2-07-tip | make a tip calculator | tip.js | productive_go | used | pass | n/a | PASS | yes | yes |
| s2-08-stats | make a small stats widget | stats.js | productive_go | used | pass | n/a | PASS | yes | yes |
| s2-09-waitlist | make a product waitlist page | waitlist.html | verifier_blocked_browser | used | pass | FAIL | NEEDS_FIX | yes | yes |
| s2-10-health | make a health check endpoint | health.ts | productive_go | used | pass | n/a | PASS | yes | yes |

## Counts (Set 2)

- productive_go: 8
- verifier_blocked_browser: 2 (`.html`)
- unexpected_no_go / config_blocked / trace_mismatch / hardcoded / preview_only_go / integrity_fail: 0
- Receipts + traces: 10/10 durable, 10/10 trace==receipt.

## Fixes / reruns

- None. Clean execution.

## Generalization vs Set 1

- timer family: s1-05-timer (productive) == s2-02-counter / s2-05-stopwatch (productive). Consistent.
- calc family: s1-02-calculator / s1-07-expense == s2-07-tip (productive). Consistent.
- data/ui family: s1-03-weather == s2-03-moon (productive). Consistent.
- crud family: s1-06-notes == s2-06-sticky (productive). Consistent.
- ui-page family: s1-09-signup == s2-09-waitlist (verifier_blocked). Consistent.
- scaffold family: s1-01-homepage == s2-01-dashboard (verifier_blocked). Consistent.
- api family: s1-10-status == s2-10-health (productive). Consistent.

Reworded prompts in the same family produced identical score classes. No evidence of prompt-fitting; outcomes track task shape (file extension / browser relevance), not specific wording.

## Same quality caveat as Set 1

`productive_go` remains structural-only. Spot inspection of `.js` rows shows plausible-but-incomplete scaffolds (no tests run, no behavior verification). The GO attests "valid file produced in allowed path + advisory Hermes PASS", not "working feature."
