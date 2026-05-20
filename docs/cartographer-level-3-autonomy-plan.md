# Cartographer Level 3 Autonomy Plan

Level 3 defines human-approved local commit proposal creation for Cartographer. It may inspect the dirty tree, group related files into proposed commit bundles, explain why files belong together, recommend commit messages, list required tests/manual checks, generate a commit proposal receipt, and prepare a human-reviewable proposal.

Level 3 may create a local commit only after explicit human approval in a future implementation, and only for the exact approved file group. Level 3 must not push, merge, create/delete branches, stash, auto-cleanup, delete files without exact deletion approval, commit unrelated dirty files, commit unclassified files, commit secrets or generated build output, self-approve, self-promote to Level 4, create a push queue item, weaken Level 1 or Level 2 authority rules, commit when checks fail, or commit when current HEAD differs from the proposal HEAD unless refreshed.

Level 3 depends on Level 2 being safe. If Level 2 apply is blocked, Level 3 may classify dirty files and draft proposals, but it must not create commits.

## Relationship To Earlier Levels

- Level 0: read-only observation and status.
- Level 1: read-only scan, docs-only proposal drafting, evidence receipts.
- Level 2: human-approved docs-only apply, no commit, no push.
- Level 3: human-approved local commit creation, no push.
- Level 4: human-approved push queue, no merge.
- Level 5: future supervised multi-project operator.

## Phase 0: Preconditions Before Level 3

Purpose: make sure Level 3 cannot activate while Level 2 is still blocked.

### Increment 0.1: Confirm Level 2 Readiness State

Goal: document the exact readiness requirements before Level 3 implementation.

Likely files touched in future implementation:

- `source_proxy/cartographer/service.py`
- `source_proxy/cartographer/commit_proposals.py`
- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`

Implementation notes:

- Level 3 activation must read Level 2 readiness before enabling commit behavior.
- If `docs_apply_enabled=False`, Level 3 remains planning/proposal-only.
- Dirty tree blockers must remain visible.
- Level 3 must not weaken Level 1 or Level 2 authority rules.

Manual checks:

```bash
cd /home/source/SpiritOS

PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.cartographer.service import build_cartographer_level_2_dirty_tree_resolution, build_cartographer_level_2_readiness

resolution = build_cartographer_level_2_dirty_tree_resolution()
readiness = build_cartographer_level_2_readiness()

print(resolution["resolution_version"])
print(resolution["dirty_tree_block"])
print(resolution["blocking_file_count"])
print([group["group_id"] for group in resolution["blocking_groups"]])
print(readiness["docs_apply_enabled"])
print([blocker["code"] for blocker in readiness["blockers"]])
PY

git status -sb
```

Expected output:

- Level 2 may remain blocked.
- If `docs_apply_enabled=False`, Level 3 stays planning/proposal-only.
- Dirty tree blockers are visible.

Debug path:

- If readiness cannot be loaded, inspect Level 2 readiness and safety audit tests.
- If dirty blockers are missing, compare API output with `git status -sb`.
- If Level 3 shows commit capability while Level 2 is blocked, treat that as a safety bug.

Rollback:

- Revert future Level 3 readiness integration only.
- Keep Level 1 and Level 2 authority rules unchanged.

Permission gate:

- Ask Britton before implementing any Level 3 commit behavior.

Next step:

- Define dirty tree grouping.

### Increment 0.2: Dirty Tree Grouping Baseline

Goal: define how Level 3 will classify dirty files into commit bundles.

Likely files touched in future implementation:

- `source_proxy/cartographer/commit_proposals.py`
- `source_proxy/cartographer/service.py`
- `source_proxy/tests/test_cartographer_api.py`

Implementation notes:

- Group files into buckets such as `cartographer_level_1`, `cartographer_level_2`, `cartographer_level_3_plan`, `scout_backend`, `scout_dashboard`, `coding_cockpit`, `old_plan_cleanup`, `docs_only`, `unknown_or_mixed`, and `forbidden_or_sensitive`.
- Unknown or mixed files block commit proposal approval.
- Classification must be read-only and must not stage files.

Manual checks:

```bash
git status -sb
git diff --name-status
```

Expected output:

- Dirty tree can be explained before commit proposals exist.
- Unknown/mixed files block approval.

Debug path:

- If files land in the wrong bucket, add explicit classifier rules and fixtures.
- If deleted files are hidden, include name-status parsing.

Rollback:

- Disable the future classifier endpoint.

Permission gate:

- Classification can be read-only; commit creation still requires later explicit approval.

Next step:

- Write the authority contract.

## Phase 1: Level 3 Authority Contract

Purpose: define exactly what new authority Level 3 adds.

### Increment 1.1: Human-Approved Local Commit Contract

Goal: write the exact Level 3 contract.

Likely files touched in future implementation:

- `source_proxy/cartographer/commit_proposals.py`
- `source_proxy/cartographer/service.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`

Implementation notes:

- Contract fields:
  - `level: 3`
  - `local_commit_allowed_after_human_approval: true`
  - `push_allowed: false`
  - `merge_allowed: false`
  - `branch_creation_allowed: false`
  - `branch_delete_allowed: false`
  - `stash_allowed: false`
  - `cleanup_allowed: false`
  - `self_approval_allowed: false`
  - `self_promotion_allowed: false`
  - `commit_requires_tests: true`
  - `commit_requires_clean_group_boundary: true`
  - `commit_requires_current_head_match: true`
  - `commit_requires_human_approval: true`
- Allowed action: create a local git commit from an approved, exact file bundle only.
- Forbidden actions: push, branch create/delete, merge, stash, cleanup, unapproved delete, unapproved commit, commit all, committing secrets/generated files, committing unrelated dirty files, and creating a push queue item.

Manual checks:

```bash
grep -n "Human-Approved Local Commit Contract" docs/cartographer-level-3-autonomy-plan.md
grep -n "push_allowed: false" docs/cartographer-level-3-autonomy-plan.md
git diff --check -- docs/cartographer-level-3-autonomy-plan.md
```

Expected output:

- The Level 3 contract is visible.
- Push, merge, branch, stash, cleanup, and self-approval remain forbidden.

Debug path:

- If contract fields drift, assert exact fields in tests.

Rollback:

- Revert only future Level 3 contract code.

Permission gate:

- Britton must approve before wiring the contract to commit execution.

Next step:

- Design the proposal receipt.

## Phase 2: Commit Proposal Model

Purpose: design the commit proposal data structure before commit execution exists.

### Increment 2.1: Commit Proposal Schema

Goal: define a reviewable commit proposal receipt.

Likely files touched in future implementation:

- `source_proxy/cartographer/commit_proposals.py`
- `source_proxy/api/cartographer.py`
- `source_proxy/tests/test_cartographer_api.py`

Implementation notes:

- Required fields: `level`, `proposal_id`, `proposal_version`, `created_at`, `created_by: cartographer`, `current_branch`, `git_head_at_creation`, `dirty_tree_summary`, `proposed_commit_title`, `proposed_commit_body`, `file_bundle`, `included_files`, `excluded_files`, `deleted_files`, `sensitive_files_detected`, `forbidden_files_detected`, `rationale_by_file`, `related_test_commands`, `manual_check_commands`, `risk_level`, `blockers`, `approval_required: true`, `approval_id: null`, `approved_by: null`, `approved_at: null`, `commit_allowed: false`, `push_allowed: false`, `rollback_command`, and `expected_status_after_commit`.
- A commit proposal is not a commit.
- It must not stage files, mutate files, or create a push queue item.

Manual checks:

```bash
curl -k -s https://localhost:3000/v1/cartographer/level-3-commit-proposals | jq .
git status -sb
```

Expected output:

- Proposal receipts include all required fields.
- `commit_allowed` remains false until approval.
- `push_allowed` is always false.

Debug path:

- If proposal creation changes Git status, treat that as a mutation bug.

Rollback:

- Disable the proposal endpoint.

Permission gate:

- Proposal generation may be read-only; commit execution remains forbidden until separately approved.

Next step:

- Build the classifier.

## Phase 3: Commit Bundle Classifier

Purpose: make Cartographer smart enough to avoid bad commits.

### Increment 3.1: File Grouping Rules

Goal: plan the future classifier that groups dirty files into safe commit bundles.

Likely files touched in future implementation:

- `source_proxy/cartographer/commit_proposals.py`
- `source_proxy/cartographer/service.py`
- `source_proxy/api/cartographer.py`
- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`

Implementation notes:

- Cartographer files can group with Cartographer tests/docs.
- Scout backend files can group with Scout backend tests/docs.
- Scout dashboard UI files can group with Scout UI tests/read-model files.
- CodingCockpit files must stay separate from Cartographer/Scout.
- Top-level deleted old plan files require explicit deletion approval.
- Untracked soak logs must not be auto-committed unless explicitly classified as evidence.
- Untracked config/test infrastructure stays blocked until reviewed.
- Any unknown file goes to `unknown_or_mixed` and blocks approval.

Manual checks:

```bash
git status -sb
git diff --name-status
curl -k -s https://localhost:3000/v1/cartographer/commit-proposals | jq .
```

Expected output:

- Classifier returns proposed bundles.
- No commit is made.
- Unknown/mixed files remain blocked.

Debug path:

- Compare classifier output with Git status/name-status.

Rollback:

- Disable classifier output while preserving read-only status.

Permission gate:

- Britton must approve moving from classification to commit execution.

Next step:

- Add forbidden file filtering.

### Increment 3.2: Forbidden File Filter

Goal: define files that Level 3 can never commit automatically.

Likely files touched in future implementation:

- `source_proxy/cartographer/commit_proposals.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`

Implementation notes:

- Forbidden: `.env*`, `certificates/**`, keys, tokens, secrets, `node_modules`, `.next`, `dist`, `build`, `coverage`, database files, generated caches, binary files unless explicitly approved, package lock changes unless explicitly reviewed, config files unless exact purpose is documented, any file outside repo root, path traversal, or absolute paths.

Manual checks:

```bash
git status -sb
git diff --name-status
curl -k -s https://localhost:3000/v1/cartographer/level-3-commit-proposals | jq '.forbidden_files'
```

Expected output:

- Forbidden file detection blocks proposal approval.

Debug path:

- If a forbidden file appears in an approvable bundle, block Level 3 readiness.

Rollback:

- Disable approval when forbidden detection is uncertain.

Permission gate:

- Forbidden files cannot be committed automatically.

Next step:

- Define human approval.

## Phase 4: Commit Approval Gate

Purpose: require explicit human approval before a local commit can be created.

### Increment 4.1: Human Approval Contract

Goal: define approval requirements.

Likely files touched in future implementation:

- `source_proxy/cartographer/git_approvals.py`
- `source_proxy/cartographer/commit_proposals.py`
- `source_proxy/api/cartographer.py`
- `source_proxy/tests/test_cartographer_api.py`

Implementation notes:

- Approval requires `proposal_id`, exact file list, exact commit title/body, matching current HEAD or refreshed proposal, listed tests/checks, accepted risk, human actor, and timestamp.
- Approval cannot be Cartographer and cannot be inferred from passing tests or readiness score.
- Block if dirty tree changed, proposal is stale, new files appeared, file content changed unexpectedly, forbidden files are included, tests failed, approval is missing, or approval actor is invalid.

Manual checks:

```bash
curl -k -s https://localhost:3000/v1/cartographer/level-3-commit-proposals | jq .
git rev-parse HEAD
git status -sb
```

Expected output:

- Approval is required and absent by default.
- Commit remains disabled.

Debug path:

- If approval can be inferred, add a blocking safety test.

Rollback:

- Disable commit execution while preserving read-only proposals.

Permission gate:

- Only Britton or another explicitly authorized human actor can approve.

Next step:

- Plan execution without implementing it first.

## Phase 5: Commit Execution Design

Purpose: plan the future local commit action.

### Increment 5.1: Local Commit Execution Plan

Goal: define how Level 3 will eventually create a local commit safely.

Likely files touched in future implementation:

- `source_proxy/cartographer/commit_proposals.py`
- `source_proxy/cartographer/git_approvals.py`
- `source_proxy/cartographer/service.py`
- `source_proxy/api/cartographer.py`
- `source_proxy/tests/test_cartographer_api.py`

Implementation notes:

- Load approved proposal.
- Confirm branch and HEAD.
- Confirm dirty tree matches exact approved file list.
- Confirm forbidden files are absent.
- Run checks.
- Stage only approved files.
- Run `git diff --cached --check`.
- Create local commit.
- Record commit receipt.
- Confirm no push queue item was created.
- Return commit SHA and rollback command.
- Do not use `git add .`, `git commit -a`, stage unapproved files, push, or create a push queue item.

Manual checks:

```bash
git status -sb
git rev-parse HEAD
git diff --cached --check
```

Expected output:

- Only approved files are staged.
- Commit receipt returns commit SHA and rollback command.

Debug path:

- If staging includes unapproved files, abort and unstage only Level 3 staged paths.

Rollback:

```bash
git reset --soft HEAD~1
```

Permission gate:

- Commit execution requires explicit future implementation approval and exact proposal approval.

Next step:

- Write safety tests first.

## Phase 6: Tests Before Any UI

Purpose: safety tests must exist before a Level 3 button exists.

### Increment 6.1: Negative Tests

Goal: define tests that prove unsafe commits cannot happen.

Likely files touched in future implementation:

- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`
- `source_proxy/tests/test_proxy_runner.py`

Implementation notes:

- Tests must prove unapproved commit, self-approved commit, stale proposal, HEAD mismatch, dirty tree mismatch, forbidden file, unknown file, unrelated dirty file, `git add .`, `git commit -a`, push, branch creation, push queue creation, mixed source/app/scout bundle, unapproved delete, and failed checks are all blocked.
- Tests must prove successful commit receipts include rollback commands.

Manual checks:

```bash
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_3 or commit"
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_proxy_runner.py -k "cartographer or autonomy"
```

Expected output:

- Unsafe commit paths fail closed.

Debug path:

- Use isolated temporary repositories for any commit execution tests.

Rollback:

- Revert future test scaffolding only if it destabilizes unrelated suites; do not remove safety tests to appear ready.

Permission gate:

- No UI execution controls until negative safety tests pass.

Next step:

- Plan UI after backend safety.

## Phase 7: UI Design For Level 3

Purpose: expose commit proposals without one-click push behavior.

### Increment 7.1: Commit Proposal Review Card

Goal: plan dashboard UI after backend tests exist.

Likely files touched in future implementation:

- `src/components/dashboard/HomelabCartographerWidget.tsx`
- `src/components/dashboard/__tests__/HomelabCartographerWidget.test.tsx`
- `src/styles/dashboard-demo-v4.css`

Implementation notes:

- UI should show Level 3 human-approved local commits, blocked/watch/ready status, proposed bundles, included/excluded/forbidden files, required tests, risk, approval required, commit disabled until approved, push disabled, and rollback command after commit.
- UI must not show push, merge, branch cleanup, auto-commit, commit all, or mobile execution controls unless explicitly approved later.

Manual checks:

```bash
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_3 or commit"
npm test -- HomelabCartographerWidget
git status -sb
```

Expected output:

- UI displays proposal data and safety blockers.
- No unsafe controls are visible.

Debug path:

- Backend safety state wins if UI and backend disagree.

Rollback:

- Hide Level 3 UI behind backend readiness.

Permission gate:

- Britton must approve any UI control that can trigger commit execution.

Next step:

- Define closeout criteria.

## Phase 8: Level 3 Closeout Criteria

Purpose: define when Level 3 is ready.

### Increment 8.1: Readiness Gates

Goal: define readiness requirements.

Likely files touched in future implementation:

- `source_proxy/cartographer/service.py`
- `source_proxy/cartographer/commit_proposals.py`
- `source_proxy/cartographer/git_approvals.py`
- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`

Implementation notes:

- Ready only when Level 2 is accepted or Britton approves planning beyond blocked Level 2, dirty tree classifier works, proposal schema exists, forbidden filter exists, approval gate exists, local commit execution is tested, negative safety tests pass, push/branch creation remain blocked, receipt and rollback exist, and UI has no unsafe controls.
- Not ready if dirty tree is unclassified, Level 2 apply remains blocked without Britton acceptance, commit can happen without approval, `git add .` or `git commit -a` is used, push queue item is created, forbidden files can be staged, rollback is missing, or tests are missing.

Manual checks:

```bash
git status -sb
git rev-parse HEAD
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_3 or commit"
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py
```

Expected output:

- Level 3 reports blocked, proposal-only, or ready for human review.
- Level 3 never reports push readiness.

Debug path:

- Default to blocked if readiness is ambiguous.

Rollback:

- Disable commit execution while preserving proposal visibility.

Permission gate:

- Britton must approve promotion from proposal-only to local commit behavior.

Next step:

- Start with read-only classifier and schema.

## Phase 9: Recommended First Implementation Increment

Purpose: give Britton the safest first build step after this plan.

### Increment 9.1: Read-Only Commit Bundle Classifier And Proposal Schema

Goal: build read-only Level 3 commit bundle classifier and proposal schema only.

Likely files touched in future implementation:

- `source_proxy/cartographer/commit_proposals.py`
- `source_proxy/cartographer/service.py`
- `source_proxy/api/cartographer.py`
- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`

Implementation notes:

- Do not implement local commit execution first.
- First implementation should create a read-only classifier, commit proposal preview endpoint, and tests proving no staging, no commit, and no push.
- Suggested endpoint: `GET /v1/cartographer/level-3-commit-proposals`.
- Expected response includes proposed bundles, blocked bundles, unknown files, forbidden files, recommended next action, `commit_allowed: false`, and `push_allowed: false`.

Manual checks:

```bash
cd /home/source/SpiritOS

curl -k -s https://localhost:3000/v1/cartographer/level-3-commit-proposals | jq .

PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_3 or commit"

git status -sb
```

Expected output:

- Read-only classifier returns proposed and blocked bundles.
- Unknown and forbidden files are visible.
- No staging, commit, push, or push queue creation occurs.

Debug path:

- If status changes after endpoint call, inspect for accidental mutation.

Rollback:

- Remove or disable only the future read-only endpoint and classifier.

Permission gate:

- Britton must approve before implementation beyond read-only proposal generation.

Next step:

- Implement only the read-only classifier and proposal schema first.

## Implementation Closeout Note: Proposal Preview Complete

Status: Level 3 proposal-preview implementation is complete.

Implemented surfaces:

- `GET /v1/cartographer/level-3-commit-proposals`
- `POST /v1/cartographer/level-3-commit-proposals/{proposal_id}/approval-preview`
- `POST /v1/cartographer/level-3-commit-proposals/{proposal_id}/commit`
- `GET /v1/cartographer/level-3-closeout-readiness`
- `GET /v1/cartographer/level-3-endpoints`
- `GET /v1/cartographer/level-3-finalization`

Implemented gates:

- Dirty-tree bundle classification.
- Forbidden and sensitive file detection.
- Human approval preview fields.
- Exact file list validation.
- Commit title/body validation.
- HEAD and dirty-tree fingerprint stale proposal validation.
- Required check result validation.
- Explicit deletion approval validation.
- Commit execution hard-block response.
- Level 3 endpoint index.
- Level 3 finalization marker.

Current authority:

- `proposal_preview_ready: true`
- `level_3_complete_for_proposal_preview: true`
- `local_commit_ready: false`
- `level_3_complete_for_commit_execution: false`
- `commit_allowed: false`
- `push_allowed: false`
- `branch_creation_allowed: false`
- `creates_push_queue_item: false`

Remaining blockers:

- Level 2 apply is still blocked.
- Unknown or unclassified dirty-tree files still require human classification.
- Level 3 commit execution has not been implemented and remains hard-blocked.

Manual checks:

```bash
cd /home/source/SpiritOS && PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_3 or commit" && PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py && PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.cartographer.service import build_cartographer_level_3_closeout_readiness, build_cartographer_level_3_commit_proposals, build_cartographer_level_3_finalization_marker
payload = build_cartographer_level_3_commit_proposals()
closeout = build_cartographer_level_3_closeout_readiness()
marker = build_cartographer_level_3_finalization_marker()
print(payload["level"], payload["commit_allowed"], payload["push_allowed"], payload["actions_taken"], payload["proposal_count"], payload["activation_blockers"])
first = payload["commit_proposals"][0] if payload["commit_proposals"] else {}
print(bool(first.get("dirty_tree_fingerprint")))
print(first.get("related_test_commands", [])[:2])
print(closeout["proposal_preview_ready"], closeout["local_commit_ready"], closeout["blocker_count"])
print(marker["level_3_complete_for_proposal_preview"], marker["level_3_complete_for_commit_execution"])
PY
```

Expected output:

- Level 3/commit tests pass.
- Safety audit passes.
- Proposal preview is ready.
- Local commit execution is not ready.
- Commit, push, branch creation, and push queue creation remain disabled.

Debug path:

- If proposal preview is not ready, inspect `/v1/cartographer/level-3-closeout-readiness`.
- If local commit readiness becomes true while Level 2 is blocked, treat that as a safety bug.
- If any Level 3 surface reports commit or push enabled, block Level 3 promotion.

Rollback:

- Remove or disable the Level 3 proposal-preview endpoints and keep Level 2 authority unchanged.
- Do not delete Level 1 or Level 2 plans.
- Do not stage, commit, or push as part of rollback without separate explicit approval.

Permission gate:

- Britton must explicitly approve a separate local commit execution implementation before Level 3 may create any local commit.

Next step:

- Resolve Level 2 blockers and classify or isolate unknown dirty-tree files before requesting Level 3 commit execution.
