# Operator Runbook - v0.1 Control Plane Foundation

## Purpose

Use this runbook when preparing the next approved SpiritOS Cognitive Control Plane increment.

The default posture is preview-gated, evidence-backed, and reuse-first.

## Startup Checklist

1. Confirm explicit Britton approval for the next phase or increment.
2. Run `git status --short`.
3. Classify dirty files before editing.
4. Confirm allowed paths for the approved phase.
5. Read the relevant prior phase closeout and adapter map.
6. Inspect existing SpiritOS/Source Proxy systems before creating any new module.
7. Create an increment receipt skeleton before edits.

## Required PIVOT Flow

P - Preflight:

- Record repo path.
- Run `git status --short`.
- Identify allowed files.
- Identify forbidden files/actions.
- Inspect existing code/docs before editing.
- Create increment receipt skeleton.

I - Implement:

- Make the smallest scoped change for the current increment.
- Do not touch unrelated files.
- Do not refactor broadly.
- Do not start the next increment early.

V - Verify:

- Run focused safe checks.
- Run `git diff --check` for changed surfaces.
- Validate JSON/docs.
- Mark unavailable checks as UNVERIFIED, not PASS.

O - Observe:

- Record changed files.
- Record commands run.
- Record pass/fail output.
- Record skipped/unverified checks.
- Preserve prior evidence.

T - Triage:

- Decide GO, NO-GO, or PARTIAL.
- Write increment receipt.
- Name next authorized increment only.
- Stop on NO-GO or PARTIAL.

## Reuse-First Rule

Before adding future cognitive modules, inspect and decide whether to wrap, adapt, or reuse existing:

- Source Proxy API/routes.
- Context and Obsidian readers.
- Decision and prompt packet builders.
- Verifier, diff, and approval logic.
- `/coding` frontend/backend runner surfaces.
- Durable run store.
- Evidence docs.
- Cartographer/repo-map/context systems.
- Worker/model routing systems.
- Test utilities.

## Truth Rules

- Artifact existence does not imply product PASS.
- Preview opens does not imply behavior PASS.
- Static content does not imply app behavior.
- PASS requires observed behavior satisfying the contract.
- FAIL must name the broken behavior.
- UNVERIFIED is required when evidence is missing, unavailable, unsafe, or out of scope.

## Forbidden Without Separate Approval

- Provider/model calls.
- Worker starts.
- Obsidian writes.
- Git mutation.
- Generated diagnostic artifact mutation.
- `apply` route calls.
- `execute-approved` route calls.
- Safe-write/workflow-runner execution.
- Production UI rewrites.
- Autonomous execution beyond preview-gated flow.
- Multi-lane benchmark execution.
- Automatic learning or memory write-back.

## Phase 10 Handoff Boundary

v0.1 is complete when this runbook and closeout are verified.

Any next work must be separately approved and should begin from the v0.1 evidence root, especially:

- `revamp-v0.1-scope.md`
- `allowed-paths.json`
- `anti-scaffold-rules.md`
- `phase-0/existing-system-reuse-inventory.json`
- `phase-1/canonical-truth-contract.json`
- `phase-2/read-only-memory-contract.json`
- `phase-6/behavior-fixture-contract.json`
- `phase-8/integrated-dry-run-loop-contract.json`
- `phase-9/timer-controlled-live-proof.json`
