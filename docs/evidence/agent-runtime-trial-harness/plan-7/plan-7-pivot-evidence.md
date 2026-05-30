# Plan 7/8: S+ Repeatability Gate Evidence

## Scope

Plan 7 grades coding, design, and combined trial readiness using repeatable UI batch artifacts. It does not implement Codex-like features.

## Phase 7.1: Full Batch Run

Checks run:

```bash
node scripts/agent-trials/run-ui-agent-trials.mjs --agent coding --viewport desktop --limit 30
node scripts/agent-trials/run-ui-agent-trials.mjs --agent design --viewport desktop --limit 30
node scripts/agent-trials/run-ui-agent-trials.mjs --agent combined --viewport desktop --limit 10
```

Evidence:

- Coding desktop: 30/30 passed, 100% weighted score, 0 hidden mutation failures.
- Design desktop: 30/30 passed, 100% weighted score, 0 hidden mutation failures.
- Combined desktop: 10/10 passed, 100% weighted score, 0 hidden mutation failures.

GO / NO-GO: GO.

## Phase 7.2: Mobile and Desktop Comparison

Checks run:

```bash
node scripts/agent-trials/run-ui-agent-trials.mjs --agent coding --viewport mobile --limit 10
node scripts/agent-trials/run-ui-agent-trials.mjs --agent design --viewport mobile --limit 10
```

Evidence:

- Coding mobile: 10/10 passed, 100% weighted score, 0 hidden mutation failures.
- Design mobile: 10/10 passed, 100% weighted score, 0 hidden mutation failures.
- `final-grade-report.json` records desktop/mobile comparison with 0% score delta.

GO / NO-GO: GO.

## Phase 7.3: Repeatability Rerun

The 30-trial coding and design batches cycle the 12 prompt fixtures with unique repeat ids. Repeatability is measured by score variance across repeated source fixture ids.

Evidence:

- Coding repeatability max score delta: 0%.
- Design repeatability max score delta: 0%.
- Combined repeatability has no repeated fixture groups in the 10-trial run and passes with 0% variance.

GO / NO-GO: GO.

## Phase 7.4: Hidden Mutation and Safety Audit

Evidence:

- `critical_safety_failures`: 0
- `hidden_mutation_failures`: 0
- `protected_path_attempts`: 0
- `fake_authority_failures`: 0
- `wrong_file_apply_failures`: 0
- `cleanup_proven`: true

No apply, commit, push, Cartographer, provider, hidden-worker, final CSS, protected-path, or permanent mutation authority was observed.

GO / NO-GO: GO.

## Phase 7.5: Grade Decision

Implemented:

- `scripts/agent-trials/summarize-all-trials.mjs`
- `docs/evidence/agent-runtime-trial-harness/plan-7/final-grade-report.json`
- `docs/evidence/agent-runtime-trial-harness/plan-7/final-grade-report.md`

Grade evidence:

- `coding_grade`: `S+`
- `design_grade`: `S+`
- `combined_grade`: `S+`
- `harness_grade`: `S+`
- `real_frontend_use_grade`: `REMEDIATION REQUIRED`
- `final_grade`: `S+ harness; real frontend UX remediation required`
- total reviewed trials: 90
- remediation includes `Natural prompt to bounded TaskSpec intake parser + scope clarification UI`

GO / NO-GO: GO.

## Plan 7 Result

GO.

The S+ harness decision is evidence-based, separated by coding/design/combined grade, compares desktop and mobile results, includes repeatability variance, and records zero hidden mutation, fake authority, or protected-path attempts. It is not an S+ claim for real frontend use until natural prompt to bounded TaskSpec intake and scope clarification UX are complete.
