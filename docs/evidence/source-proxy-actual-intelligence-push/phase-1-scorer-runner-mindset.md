# Phase 1 Scorer Runner Mindset

Status: passed for implemented scorer/runner scope.

Files changed:
- `src/lib/coding/actual-intelligence-outcome.ts`
- `src/lib/coding/agent-trials-ui.ts`
- `tests/ui-agent-trials/trial-result-schema.ts`
- `tests/ui-agent-trials/trial-result-schema.test.ts`
- `tests/ui-agent-trials/run-ui-agent-trials.test.ts`
- `scripts/agent-trials/run-ui-agent-trials.mjs`
- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Checks run:
- `npm run typecheck` - pass
- `npx --no-install vitest run src/lib/coding/__tests__/agent-trials-ui.test.ts tests/ui-agent-trials/run-ui-agent-trials.test.ts tests/ui-agent-trials/trial-result-schema.test.ts tests/ui-agent-trials/realistic-prompt-remediation.test.ts src/components/coding/__tests__/coding-cockpit-shell.test.tsx --testTimeout=20000` - pass, 73 tests
- `git diff --check` - pass

Before:
- Trial UI defaults displayed `S+` for Coder, Designer, Combined.
- Runner summaries counted safe blocks alongside success-like trial status.
- Diagnostic reports lacked an explicit actual-intelligence category.

After:
- Outcome taxonomy separates `pass_productive`, `already_satisfied_noop_useful`, `blocked_safety`, `blocked_missing_scope`, `route_gap_not_ready`, visual gaps, verification failures, unsafe failures, and environment gaps.
- `blocked_safety` increments safety-only counters and `counts_for_coding_usefulness=false`.
- `already_satisfied_noop_useful` requires positive target evidence and zero changed files.
- `provider_call_made=false` with a live claim sets `disqualifies_live_claim=true` and `s_plus_eligible=false`.
- `/coding` runner badge now says `Live usefulness pending`, not `S+`.

Proof:
- `tests/ui-agent-trials/run-ui-agent-trials.test.ts` includes a blocker-heavy run that has `useful_actual_intelligence_outcomes=0` and `live_actual_intelligence_s_plus_eligible=false`.
- `src/lib/coding/__tests__/agent-trials-ui.test.ts` covers safety-only blocks, useful no-op proof, and provider false live-claim disqualification.
