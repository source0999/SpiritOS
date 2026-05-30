# Phase 6 Frontend Manual Verification Packet

Routes to open:
1. `https://localhost:3000/coding`
2. `https://localhost:3000/v1/coding/hermes-stress-smoke` with POST for provider smoke

What should be visible on `/coding`:
- Runner badge: `Live usefulness pending`
- No default `S+` runner claim.
- Result/report copy includes actual-intelligence category, useful vs safety-only counters, changed files, checks, provider/model truth, and live-claim disqualification.
- Trial score reads as useful outcomes, not total safety/blocker score.

Screenshots/artifacts:
- `.codex-smoke/phase-proof-coding-desktop-final.png`
- `.codex-smoke/phase-proof-coding-mobile-final.png`

Expected proof:
- PASS: desktop `/coding` loads.
- PASS: mobile `/coding` loads.
- PASS: browser console duplicate-key warnings were 0 during final captures.
- PASS: runner label does not say S+.
- PASS: targeted tests and typecheck pass.
- PASS: Hermes stress-smoke returns `HERMES4_STRESS_OK`.

Known caveats:
- The live provider proof is a smoke call, not 7 live coding tasks.
- Full designer and combined live loops remain pending.
- The worktree had many unrelated dirty files before this mission; do not treat `git status` as only this change set.
