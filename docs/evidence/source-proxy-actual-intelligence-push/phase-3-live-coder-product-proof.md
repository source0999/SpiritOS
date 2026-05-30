# Phase 3 Live Coder Product Proof

Status: partial, not S+.

Implemented useful coder work:
- Added actual-intelligence scoring taxonomy and UI diagnostics.
- Added 50-prompt actual-intelligence bank.
- Added Scout stored-only design inspiration intake in `source_proxy/proxy_memory/scout_intake.py`.
- Added backend test proving stored-only Scout design intake does not crawl, start scheduler/worker, write proxy memory, promote memory, or inject coding context.
- Fixed `/coding` repeated prompt preview keys so browser evidence has no duplicate-key warnings.
- Replaced default runner `S+` badge with `Live usefulness pending`.
- Updated trial diagnostic reports to show useful outcomes, safety-only blockers, changed files, checks, provider truth, and live-claim disqualification.

Live provider evidence:
- Command: `curl -ksS -X POST https://localhost:3000/v1/coding/hermes-stress-smoke`
- Result: `pass=true`, `provider=local`, `routed_model=ollama_chat/hermes4`, `response_content=HERMES4_STRESS_OK`, `zero_cost_local_route=true`.
- This proves the local provider path is callable, but it is one smoke call, not 7 live coding tasks.

Checks run:
- `npm run typecheck` - pass
- `npx --no-install vitest run src/lib/coding/__tests__/agent-trials-ui.test.ts tests/ui-agent-trials/run-ui-agent-trials.test.ts tests/ui-agent-trials/trial-result-schema.test.ts tests/ui-agent-trials/realistic-prompt-remediation.test.ts src/components/coding/__tests__/coding-cockpit-shell.test.tsx --testTimeout=20000` - pass, 73 tests
- `./.venv/bin/pytest -q source_proxy/tests/test_scout_intake.py` - pass, 3 tests
- `git diff --check` - pass

Coder S+ gate:
- Unsafe failures: 0 found in implemented checks.
- Hidden mutation outside scope: none from my changes; pre-existing dirty tree remains.
- Provider call made: true for Hermes stress-smoke only.
- 10 productive live coding tasks with 7 provider calls: not completed in this turn.
- Verdict: useful product progress, but not honest S+.
