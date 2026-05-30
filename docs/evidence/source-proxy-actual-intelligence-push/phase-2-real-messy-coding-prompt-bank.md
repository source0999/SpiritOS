# Phase 2 Real Messy Coding Prompt Bank

Status: passed.

File:
- `tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json`

Distribution:
- 30 productive coding prompts
- 6 already-satisfied/no-op prompts
- 5 designer visual/product prompts
- 5 combined designer -> coder -> designer-recheck prompts
- 4 adversarial safety prompts

Validation:
- `tests/ui-agent-trials/realistic-prompt-remediation.test.ts` checks schema fields, exact distribution, productive dominance, required Britton messy examples, and adversarial cap.

Checks:
- `npx --no-install vitest run tests/ui-agent-trials/realistic-prompt-remediation.test.ts` - pass as part of the 73-test focused run.

Proof blockers cannot dominate:
- Productive coding prompts are 30/50.
- Adversarial safety prompts are 4/50.
- The schema requires `expected_useful_result`, `checks`, `scorer_dimensions`, provider-call requirement, apply policy, and frontend/manual proof for every prompt.
