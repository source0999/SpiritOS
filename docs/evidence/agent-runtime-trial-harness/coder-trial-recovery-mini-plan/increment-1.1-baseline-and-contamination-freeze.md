# Increment 1.1 - Baseline and Contamination Freeze

## Plan file read

Read `docs/evidence/agent-runtime-trial-harness/coder-trial-recovery-mini-plan.md`.

## Baseline commands

Ran from `Z:\` and verified later from Dell host `/home/source/SpiritOS`:

```text
git status --short
git diff --stat
git branch --show-current
```

Branch: `lane/coding-human-trial-runner-polish-20260530-112512`

Dirty tracked work was already present in coding/source-proxy files before this increment. No reset, stash, clean, delete, or unrelated overwrite was performed.

## Contaminated suite marker

`suite-mq4in5v9` is contaminated and invalid as benchmark evidence.

Frozen facts:

- Proven model-generated rows: 0
- Proven known-scaffold rows: 5
- Contamination-risk rows: 5
- `provider_call_made=true` does not prove model-authored code.
- Successful rows lacked generation provenance.
- Known scaffold/fallback behavior existed for exact Coder 10 Agent Lab paths.

## Self-check

- Dirty tree listed: yes.
- Existing work identified: coding cockpit, durable trial rows, source proxy bounded create/long-running, source proxy tests, frontend tests.
- No destructive cleanup: yes.
- Contaminated suite facts recorded: yes.
