# Plan 5/8: UI Batch Trial Runner Evidence

## Scope

Plan 5 adds a CLI batch runner for preview-only UI agent trials. It stages prompts through `/coding`, records screenshots/traces/JSON, and does not grant apply, commit, push, provider, Cartographer, hidden-worker, or permanent mutation authority.

## Phase 5.1: Batch Runner

Implemented:

- `scripts/agent-trials/run-ui-agent-trials.mjs`

Supported filters:

- `--agent coding`
- `--agent design`
- `--agent combined`
- `--viewport desktop`
- `--viewport mobile`
- `--limit 10`
- `--profile britton-realistic`
- `--profile clean-control`

Evidence:

- `node scripts/agent-trials/run-ui-agent-trials.mjs --agent coding --viewport desktop --limit 5` passed 5/5 with 100% score and 0 hidden mutation failures.
- `node scripts/agent-trials/run-ui-agent-trials.mjs --agent design --viewport desktop --limit 5` passed 5/5 with 100% score and 0 hidden mutation failures.
- `node scripts/agent-trials/run-ui-agent-trials.mjs --agent combined --viewport desktop --limit 2 --profile clean-control` passed 2/2 with 100% score and 0 hidden mutation failures.

GO / NO-GO: GO.

## Phase 5.2: Human-Like Prompt Profiles

Implemented:

- `tests/ui-agent-trials/fixtures/prompt-profiles.json`

Profiles:

- `britton-realistic`: includes typos/frustration tone, audit/fluff rejection, long context, PIVOT instructions, safe execution, no permanent changes, manual checks, and exact next steps.
- `clean-control`: concise comparison profile with the same preview-only safety boundary.

Evidence:

- Britton-realistic profile was used in the required coding/design desktop and mobile smoke runs.
- Clean-control profile was used in an extra combined filter run and a coding control run.

GO / NO-GO: GO.

## Phase 5.3: Evidence Browser/Output

Implemented output files:

- `docs/evidence/agent-runtime-trial-harness/plan-5/summary.json`
- `docs/evidence/agent-runtime-trial-harness/plan-5/summary.md`
- organized artifacts under `docs/evidence/agent-runtime-trial-harness/plan-5/artifacts/<run-id>/<agent>/<trial-id>/`

Artifacts per trial:

- JSON result
- screenshot PNG
- Playwright trace ZIP
- design before-screenshot PNG for design trials

GO / NO-GO: GO.

## Phase 5.4: Batch Smoke

Checks run:

```bash
node scripts/agent-trials/run-ui-agent-trials.mjs --agent coding --viewport desktop --limit 5
node scripts/agent-trials/run-ui-agent-trials.mjs --agent design --viewport desktop --limit 5
node scripts/agent-trials/run-ui-agent-trials.mjs --agent coding --viewport mobile --limit 3
node scripts/agent-trials/run-ui-agent-trials.mjs --agent design --viewport mobile --limit 3
node scripts/agent-trials/run-ui-agent-trials.mjs --agent combined --viewport desktop --limit 2 --profile clean-control
npx --no-install tsc --noEmit --pretty false
git diff --check
git status --branch --short --untracked-files=normal
```

Smoke evidence:

- Coding desktop: 5/5 passed, 100% weighted score, 0 hidden mutation failures.
- Design desktop: 5/5 passed, 100% weighted score, 0 hidden mutation failures.
- Coding mobile: 3/3 passed, 100% weighted score, 0 hidden mutation failures.
- Design mobile: 3/3 passed, 100% weighted score, 0 hidden mutation failures.
- Combined clean-control desktop: 2/2 passed, 100% weighted score, 0 hidden mutation failures.

GO / NO-GO: GO.

## Plan 5 Result

GO.

The runner can execute multiple coding/design UI trials in one command, required filters work, both prompt profiles exist, summaries are readable, screenshots/traces are organized, and trial prompts produced no permanent mutation beyond Plan 5 evidence artifacts.
