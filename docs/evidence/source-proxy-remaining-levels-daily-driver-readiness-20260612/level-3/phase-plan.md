# Level 3 Phase Plan

## Phase 3A: Approval Boundary And Harness Preflight

Purpose: confirm task boundaries and prove the harness can produce approval and diff packets without applying real repo mutations.

Allowed changes after manual GO:

- Evidence files under this Level 3 folder.
- Test-only harness calls that do not mutate product files.

Forbidden changes:

- Product code mutation.
- Provider/model fallback.
- Sidecar activation.
- Obsidian writes.
- Git stage, commit, push, stash, reset, checkout, clean, or branch creation.

Expected tests:

- Focused unit tests for task spec intake and tool action contracts.
- `git diff --check`.

Evidence files:

- `phase-3a-preflight.md`
- `phase-3a-checks.txt`
- `phase-3a-closeout.md`

Stop condition:

- Stop if approval boundary is ambiguous, if dirty baseline cannot be separated from Level 3 changes, or if any command would require a forbidden git operation.

## Phase 3B: Bounded Real Repo Diff Preview

Purpose: prove Source Proxy can identify a safe real repo target and produce a visible diff preview before apply.

Allowed changes after manual GO:

- One tiny approved docs-or-test target at a time.
- Evidence files for the increment.

Forbidden changes:

- Applying a diff without an explicit approval receipt.
- Touching files outside approved paths.
- Hidden prompt-specific templates.
- Scorer weakening.

Expected tests:

- Targeted unit test for touched area.
- `git diff --check`.
- Diff preview parsing check.

Evidence files:

- `phase-3b-task-spec.json`
- `phase-3b-context-packet.json`
- `phase-3b-proposed-diff.patch`
- `phase-3b-closeout.md`

Stop condition:

- Stop if Source Proxy targets an unapproved file, produces no diff while claiming success, or cannot explain the target selection through visible reason codes.

## Phase 3C: Approved Apply And Revert Proof

Purpose: prove an approved Level 3 mutation can be applied, tested, and reverted without damaging unrelated dirty work.

Allowed changes after manual GO:

- The specific approved file mutation.
- Revert of that same mutation only.
- Evidence files.

Forbidden changes:

- Broad revert of the working tree.
- Reverting pre-existing dirty files.
- Committing or staging.

Expected tests:

- Focused tests for the touched file.
- Touched-area regression tests.
- `git diff --check`.
- Post-revert status comparison against baseline.

Evidence files:

- `phase-3c-apply-receipt.json`
- `phase-3c-test-output.txt`
- `phase-3c-revert-proof.patch`
- `phase-3c-post-revert-status.txt`
- `phase-3c-closeout.md`

Stop condition:

- Stop if tests fail, revert is not clean, unrelated files change, or the evidence cannot separate Level 3 changes from pre-existing dirty state.
