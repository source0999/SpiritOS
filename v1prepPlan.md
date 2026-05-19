# Cartographer v1 Prep Plan

## Status Snapshot

Cartographer is v1 human-review ready, but it is not fully frozen yet.

The only remaining v1 closeout item is the freeze marker.

Authority remains locked.

Validation-only closeout completed. No apply, commit, push, delete, merge, or authority promotion occurred.

Current repository state recorded for this plan:
- HEAD: 683793732031b6d9471de7995931310065df84a5
- Branch: main
- Ahead/behind: 0 0

## Current Verdict

Cartographer has reached v1 readiness for human review. It is not fully finalized until the freeze marker is created, validated, reviewed, and then committed with explicit human approval.

## Authority Boundary

- passing tests do not grant authority
- proof artifacts do not grant authority
- freeze marker does not grant authority
- write_actions_enabled must remain false
- authority_granted must remain false
- actions_taken must remain false
- no apply, commit, push, merge, cleanup, autopilot, or authority promotion without separate approval

## Evidence Already Recorded

- data/cartographer-v1-diagnostics/proxy-closeout-2026-05-19T002129Z.json
- data/cartographer-v1-diagnostics/proxy-closeout-2026-05-19T002146Z.json
- data/cartographer-v1-diagnostics/scout-search-diagnostics-2026-05-19T002228Z.json
- data/cartographer-v1-diagnostics/phase-4f-closeout-2026-05-19T002237Z.json
- data/cartographer-v1-proof-gates/manual-proof-gates-20260519T002448Z.json
- scout/soak-logs/scout-soak-snapshot-2026-05-19T002317Z.json

## Evidence Summary

- proxy closeout passed under .venv
- Scout search diagnostics passed
- phase-4f closeout passed
- TypeScript passed
- lint warnings only
- blueprint validation passed
- diff check passed
- targeted Vitest passed
- v1 proof validation passed
- v1 readiness passed
- freeze marker missing

Additional validation details:
- `npm run typecheck` exited 0
- `npm run lint` exited 0 with 6 warnings and 0 errors
- `npm run validate:blueprints` passed
- `git diff --check` exited 0
- targeted Vitest passed: 3 files passed, 94 tests passed
- `v1-proof-validation` is valid
- `v1-combined-readiness-dry-run` has `remaining_missing_count: 0`
- `v1-readiness` says `v1_ready: true` and `readiness: ready_for_human_v1_review`
- `v1-closeout-dashboard` says `primary_status: ready_missing_freeze_marker`
- freeze marker validation is missing because `data/cartographer-v1-freeze/freeze-marker.json` does not exist
- authority stayed locked: `write_actions_enabled false`, `authority_granted false`, `actions_taken false`

## Known Non-Blocker

The first proxy-closeout attempt using system python failed because `pytest` was missing from `/usr/bin/python3`. The same closeout passed under `.venv`, so this is recorded as an environment/interpreter mismatch, not a failed v1 proof gate or Source Proxy logic failure.

## Remaining Work

### Phase 1: Review Current Evidence

#### Increment 1.1: Inspect proof validation

- Goal
  Confirm that the existing v1 proof and readiness endpoints still report human-review readiness with authority locked.
- Actions
  Run:
  ```bash
  curl -k -s https://localhost:3000/v1/cartographer/v1-proof-validation | jq .
  curl -k -s https://localhost:3000/v1/cartographer/v1-combined-readiness-dry-run | jq .
  curl -k -s https://localhost:3000/v1/cartographer/v1-readiness | jq .
  ```
- Manual checks
  Review the endpoint output for validation status, missing evidence count, readiness state, blockers, and authority flags.
- Expected output
  - `validation_status` is `valid`
  - `remaining_missing_count` is `0`
  - `v1_ready` is `true`
  - `blocker_count` is `0`
  - authority still locked
- Debug path
  If any endpoint reports a blocker or missing evidence, print the relevant response and stop for review before changing files.
- Rollback
  No rollback is needed because this phase is read-only.
- Permission gate
  Stop before creating the freeze marker.

### Phase 2: Prepare Freeze Marker

#### Increment 2.1: Inspect freeze marker proposal

- Goal
  Inspect the proposed freeze marker path and confirm that validation currently reports the marker as missing.
- Actions
  Run:
  ```bash
  curl -k -s https://localhost:3000/v1/cartographer/v1-freeze-marker-proposal | jq .
  curl -k -s https://localhost:3000/v1/cartographer/v1-freeze-marker-validation | jq .
  ```
- Manual checks
  Confirm the proposed marker path, current missing status, and that no write action occurred.
- Expected output
  - proposal points to `data/cartographer-v1-freeze/freeze-marker.json`
  - validation currently reports missing
  - no write action occurs
- Debug path
  If the proposal points somewhere unexpected, stop and review the endpoint output before creating any file.
- Rollback
  No rollback is needed because this phase is read-only.
- Permission gate
  Ask Britton before writing the freeze marker file.

### Phase 3: Create Freeze Marker After Approval

#### Increment 3.1: Create the freeze marker only after explicit approval

- Goal
  Create the v1 freeze marker after explicit approval, then validate it without committing or pushing.
- Actions
  - create `data/cartographer-v1-freeze/freeze-marker.json`
  - include current HEAD, branch, `v1_ready true`, readiness ready, missing evidence count 0, and locked authority boundary
  - do not commit or push
- Manual checks
  Run:
  ```bash
  curl -k -s https://localhost:3000/v1/cartographer/v1-freeze-marker-validation | jq .
  curl -k -s https://localhost:3000/v1/cartographer/v1-closeout-dashboard | jq .
  git diff --check
  git status --short data/cartographer-v1-freeze/freeze-marker.json
  ```
- Expected output
  - freeze marker validation valid
  - closeout dashboard no longer says `ready_missing_freeze_marker`
  - authority remains locked
  - no apply, commit, push, merge, or promotion happened
- Debug path
  If invalid, print the validation issues and do not edit anything else until reviewed.
- Rollback
  ```bash
  rm -f data/cartographer-v1-freeze/freeze-marker.json
  ```
- Permission gate
  Ask Britton before staging or committing.

### Phase 4: Final Human Review

#### Increment 4.1: Review dirty tree and group commit candidates

- Goal
  Review the dirty tree and group candidate files for explicit human staging decisions.
- Actions
  Run:
  ```bash
  git status --short
  git diff --check
  git diff --stat
  ```
- Manual checks
  Inspect whether proof artifacts, freeze marker, Scout soak evidence, planning docs, and any pre-existing source changes are separable for review.
- Expected output
  - proof artifacts are identifiable
  - freeze marker is identifiable
  - no unexpected source edits appear
  - dirty tree is reviewable by group
- Debug path
  If unexpected source edits appear, identify them without reverting or cleaning anything, then ask Britton how to proceed.
- Rollback
  No rollback should be performed during review. Any rollback requires explicit approval and should be scoped to the approved file or group.
- Permission gate
  Ask Britton which group to stage first.

Review groups:
1. v1 proof artifacts
2. freeze marker
3. Scout soak evidence
4. docs-only planning files
5. source changes, if any already existed before this plan

### Phase 5: Commit Strategy

#### Increment 5.1: Commit evidence only after approval

- Goal
  Commit v1 evidence and documentation only after explicit human approval for each staging and commit action.
- Actions
  Recommended commit grouping:
  - commit 1: Cartographer v1 proof evidence and freeze marker
  - commit 2: docs-only closeout/prep plan if desired
  - do not mix unrelated source hardening changes with evidence artifacts unless Britton explicitly approves
- Manual checks
  Review `git status --short`, staged files, and the exact commit message before each commit.
- Expected output
  Expected commit message examples:
  ```text
  chore(cartographer): record v1 proof evidence
  docs(cartographer): add v1 prep plan
  ```
- Debug path
  If the staged set includes unexpected files, unstage only with explicit approval or stop and ask Britton for the intended grouping.
- Rollback
  No commit rollback should occur without explicit approval.
- Permission gate
  Ask Britton before every commit and before every push.

### Phase 6: Post-v1 Direction

#### Increment 6.1: Stop and reassess after v1 freeze

- Goal
  Pause after v1 freeze and avoid starting a new Cartographer autonomy phase automatically.
- Actions
  Do not start a new Cartographer autonomy phase automatically.
- Manual checks
  After v1 is frozen, review whether a separate post-v1 plan is approved before writing one.
- Expected output
  After v1 is frozen, write a separate plan for:
  - safer autonomous docs-only mode
  - sub-cartographer specialization
  - multi-project tracking
  - project onboarding from scratch
  - UI polish for v1 dashboard
  - controlled branch/worktree strategy
- Debug path
  If post-v1 work is requested before freeze completion, restate the freeze dependency and ask Britton whether to defer or split the plan.
- Rollback
  No rollback is needed because this phase should not change files unless separately approved.
- Permission gate
  Ask Britton before writing any post-v1 master plan.

## Final Manual Check For This File

After writing `v1prepPlan.md`, run only:
```bash
sed -n '1,260p' v1prepPlan.md
git diff --check -- v1prepPlan.md
git status --short v1prepPlan.md
```

Expected:
- `v1prepPlan.md` exists
- the plan says Cartographer is v1 human-review ready but not frozen yet
- the freeze marker is listed as the only remaining finalization item
- authority remains locked
- no source code changed
- no evidence files changed
- no freeze marker created
- no commit or push occurred
