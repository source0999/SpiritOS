# Agent Trials UI Correction Closeout

PLAN RESULT: GO

Plan title: Agent Trials UI Honesty, Cleanup, And Realistic Coverage Correction

## Why GO

- Prior GO was overturned and recorded in `no-go-correction.md`.
- Default `/coding` browser proof shows no visible `Operator run request`, `Legacy Proxy Test`, `Proof run controls`, stale `trial-explicit-context`, full diagnostics wall, `Running...` buttons, or default progress bars.
- Agent Trials is the single normal trial control/status surface.
- Legacy proxy/proof controls are behind explicit `Legacy diagnostics`, not in the default viewport.
- Operator run request remains artifact/debug-only by default.
- Generated command is compact by default, with full command under `Show command`.
- Submitted prompt preview is consolidated into one section and uses `submitted_prompt`, not `operator_run_request`.
- Running state is labeled `UI-local demo/proof progress` with terminal/artifact truth copy; no fake live runner stream is claimed.
- Browser artifact summary is honest: browser artifact parsing is unavailable and a grep command is provided instead of fake totals.
- Coding, design, and hybrid Britton-realistic prompts are messy natural prompts in the current fixtures/runs.
- Clean-control prompts remain separate and polished.
- No apply execution, commit, push, provider routing change, Cartographer activation, hidden worker, queue, shell expansion authority, or secrets/env edit was added.

## Proof

Checks:

- `npx --no-install vitest run src/lib/coding/__tests__/agent-trials-ui.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx tests/ui-agent-trials/realistic-prompt-remediation.test.ts tests/ui-agent-trials/trial-result-schema.test.ts`
  - PASS, 4 files, 92 tests.
- `node scripts/agent-trials/run-ui-agent-trials.mjs --agent coding --viewport desktop --limit 3 --profile britton-realistic`
  - PASS/GO, latest artifacts: `docs/evidence/agent-runtime-trial-harness/plan-5/artifacts/2026-05-28T04-45-59-765Z-coding-desktop-britton-realistic`
- `node scripts/agent-trials/run-ui-agent-trials.mjs --agent combined --viewport desktop --limit 3 --profile britton-realistic`
  - PASS/GO, latest artifacts: `docs/evidence/agent-runtime-trial-harness/plan-5/artifacts/2026-05-28T04-46-29-821Z-combined-desktop-britton-realistic`
- Latest coding/combined artifact grep found no `submitted_prompt` beginning with `PIVOT:`.
- `npx --no-install tsc --noEmit --pretty false`
  - PASS.
- `git diff --check`
  - PASS.

Browser screenshots:

- `7.2-default-desktop.png`
- `7.2-agent-trials-collapsed-default.png`
- `7.2-agent-trials-prompt-preview-expanded.png`
- `7.2-running-ui-local-state.png`
- `7.2-mobile-default.png`

Browser DOM proof:

- Desktop Agent Trials open/running:
  - visible `Operator run request`: false
  - visible `Legacy Proxy Test`: false
  - visible `Proof run controls`: false
  - visible `Submitted prompt preview`: true
  - visible UI-local progress truth: true
  - `Running...` buttons: 0
  - prompt textareas: 0
- Mobile default:
  - visible `Operator run request`: false
  - visible `Legacy Proxy Test`: false
  - visible `Proof run controls`: false
  - visible `Agent Trials`: true
  - page-level scrolling available.

## Caveats

- The requested broad artifact grep over all historical `plan-5/artifacts` still finds older pre-correction PIVOT submitted prompts. Those are historical evidence, not current latest-run output.
- Blocked/failed diagnostics screenshot was not produced because no natural blocked/failed browser state was available during 7.2, and no fake failure state was manufactured.
- The worktree remains dirty from pre-existing unrelated files; no reset, stash, checkout, clean, commit, or push was run.
