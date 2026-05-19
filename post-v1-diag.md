# Post-v1 Diagnostic Plan

## Status

Cartographer v1 closeout is frozen, committed, and pushed through the approved v1 evidence and prep-plan commits.

The next work should be treated as post-v1 diagnostic planning, not as a continuation of the v1 freeze. No new autonomy phase, authority promotion, autopilot mode, apply action, cleanup, merge, commit, or push should happen without separate explicit approval.

Current local branch context when this plan was drafted:
- `main` is ahead of `origin/main` by 2 local checkpoint commits.
- The latest pushed v1 commits are:
  - `3868d4b chore(cartographer): record v1 proof evidence`
  - `c6b1522 docs(cartographer): add v1 prep plan`
- The latest local checkpoint commits are:
  - `ab7834b chore(cartographer): checkpoint remaining v1 worktree`
  - `03c6c53 docs(scout): checkpoint remaining planning notes`

## Purpose

This plan defines a careful post-v1 diagnostic pass for Cartographer, Scout, and related Source Proxy surfaces after the v1 readiness freeze. The goal is to learn what should be hardened next, not to immediately start building or granting new authority.

## Non-Goals

- Do not promote Cartographer authority.
- Do not enable autopilot.
- Do not merge automatically.
- Do not push without separate approval.
- Do not delete or clean up files without separate approval.
- Do not treat v1 readiness as approval for post-v1 implementation.
- Do not start broad refactors until diagnostics identify a narrow target.

## Authority Boundary

- `write_actions_enabled` must remain false unless explicitly changed by a separate approved design.
- `authority_granted` must remain false unless explicitly approved.
- `actions_taken` must remain false for Cartographer-owned automation.
- Passing tests do not grant authority.
- Freeze markers do not grant authority.
- Diagnostic plans do not grant authority.
- Commits and pushes require separate approval.

## Diagnostic Threads

### 1. V1 Freeze Integrity

Goal: Confirm the v1 freeze remains valid after the local checkpoint commits.

Manual checks:
```bash
curl -k -s https://localhost:3000/v1/cartographer/v1-freeze-marker-validation | jq .
curl -k -s https://localhost:3000/v1/cartographer/v1-closeout-dashboard | jq .
git status --branch --short
git log --oneline -5
```

Expected outcome:
- freeze marker validation remains valid
- closeout dashboard remains ready with valid freeze marker
- branch state is clearly understood
- no authority flags changed

### 2. Remaining Local Checkpoints

Goal: Decide whether to push the two local checkpoint commits or keep them local for review.

Manual checks:
```bash
git log --oneline origin/main..HEAD
git show --stat --oneline --name-status ab7834b
git show --stat --oneline --name-status 03c6c53
```

Expected outcome:
- the two unpushed commits are reviewable
- the broad Cartographer checkpoint and Scout planning checkpoint are understood separately
- push decision remains human-gated

### 3. Cartographer Post-v1 Surface Audit

Goal: Identify which v1-adjacent endpoints and services should be hardened before any new autonomy work.

Focus areas:
- v1 closeout endpoints
- proof validation endpoints
- freeze marker validation
- readiness dashboard
- trust score
- clutter inventory and proposal review
- docs autopilot dry-run and soak surfaces
- push queue and approval-gated git actions

Manual checks:
```bash
find src/app/v1/cartographer -maxdepth 3 -type f | sort
find source_proxy/cartographer -maxdepth 2 -type f | sort
```

Expected outcome:
- endpoint and service inventory is explicit
- post-v1 hardening targets are visible
- no implementation starts during the audit

### 4. Scout Diagnostic Surface

Goal: Review Scout planning and soak artifacts separately from Cartographer v1.

Focus areas:
- Scout soak snapshots
- Scout packet synthesis notes
- Scout polish closeout docs
- Scout configuration changes
- docker compose changes

Manual checks:
```bash
git status --short scout
find scout -maxdepth 3 -type f | sort
```

Expected outcome:
- Scout changes are separated from Cartographer v1 closeout
- dirty Scout files, if any, are identified before staging
- Scout diagnostics can be planned without disturbing v1 evidence

### 5. Safety and Approval Regression

Goal: Verify that post-v1 additions did not weaken approval gates.

Manual checks:
```bash
npm run typecheck
npm run lint
npm run validate:blueprints
git diff --check
```

Expected outcome:
- TypeScript passes
- lint has no errors
- blueprint validation passes
- diff check is clean
- any warnings are recorded before further work

### 6. Focused Test Selection

Goal: Choose a focused post-v1 test set before running broad validation.

Candidate suites:
- Cartographer API tests
- Source Proxy safety tests
- approval gate tests
- push queue tests
- Scout overview tests
- coding workflow tests touched by the checkpoint

Manual check:
```bash
git diff --name-only origin/main..HEAD
```

Expected outcome:
- test selection is based on changed files
- broad test runs are deliberate, not automatic
- failures are diagnosed before new implementation

## Proposed Post-v1 Increments

### Increment 1: Freeze Revalidation

- Goal: Confirm v1 remains frozen and valid after local checkpoint commits.
- Actions: run freeze marker validation and closeout dashboard checks.
- Manual checks: record endpoint output and branch state.
- Expected output: v1 remains valid and authority remains locked.
- Debug path: if invalid, stop and inspect only the validation issues.
- Permission gate: ask before editing any freeze or proof artifact.

### Increment 2: Commit Review and Push Decision

- Goal: Decide whether to push local checkpoint commits.
- Actions: review `origin/main..HEAD` and commit stats.
- Manual checks: inspect the two local checkpoint commits.
- Expected output: human-readable push recommendation.
- Debug path: if a commit is too broad, stop and decide whether to split in a follow-up branch.
- Permission gate: ask before push.

### Increment 3: Endpoint Inventory

- Goal: produce a concise map of post-v1 Cartographer routes and Source Proxy services.
- Actions: list route and service files, group them by responsibility.
- Manual checks: compare route inventory to docs and dashboard surfaces.
- Expected output: endpoint map with missing docs or test gaps.
- Debug path: if ownership is unclear, tag the file as `needs review`.
- Permission gate: ask before editing docs or tests.

### Increment 4: Safety Regression Pass

- Goal: confirm approval and authority boundaries still hold.
- Actions: run focused tests for approval gate, push queue, and Cartographer safety.
- Manual checks: record commands and results.
- Expected output: safety gates pass or produce actionable failures.
- Debug path: if a test fails, diagnose before broad changes.
- Permission gate: ask before patching source.

### Increment 5: Post-v1 Roadmap

- Goal: write a separate implementation roadmap only after diagnostics are complete.
- Actions: summarize findings and recommend next slices.
- Manual checks: confirm no diagnostic finding is silently promoted into implementation.
- Expected output: prioritized roadmap for docs-only autonomy, sub-cartographers, multi-project tracking, onboarding, dashboard polish, and branch/worktree strategy.
- Debug path: if priorities conflict, keep the roadmap as alternatives instead of forcing one path.
- Permission gate: ask before writing or committing the roadmap.

## Recommended First Manual Check

Run:
```bash
curl -k -s https://localhost:3000/v1/cartographer/v1-freeze-marker-validation | jq .
curl -k -s https://localhost:3000/v1/cartographer/v1-closeout-dashboard | jq .
git status --branch --short
git log --oneline -5
```

Expected:
- freeze marker validation is valid
- dashboard reports ready with valid freeze marker
- authority remains locked
- local branch state is clear
- no push happens during the diagnostic check

## Stop Conditions

Stop and ask before:
- editing source
- editing evidence artifacts
- changing authority or approval settings
- enabling autopilot
- staging files
- committing
- pushing
- deleting or cleaning files
- starting a new implementation phase
