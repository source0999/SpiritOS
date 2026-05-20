# Source Proxy Closeout and Consolidation Plan

## Status Verdict

Proxy closeout status: PASS.

Global safety status: FAIL.

Main blockers:

- Cartographer safety failure.
- Test-created Scout soak logs caused the mutation boundary to fail.
- The dirty tree is not on a review branch.
- Latest manual project-health output reported 31 unsafe dirty files.

This is not a feature-build phase. The goal is to stabilize the current working tree, classify what belongs together, repair the safety gate, and prepare deliberate review groups. No new Source Proxy feature roadmap is opened here.

## Evidence Reviewed

Reviewed planning and reference documents:

- `docs/source-proxy-production-hardening-plan.md`
- `docs/source-proxy-hardening-closeout.md`
- `docs/source-proxy-regression-matrix.md`
- `docs/source-proxy-remote-manual-checks.md`
- `docs/codingUI.md`
- `docs/agent-wrapper-reference-study.md`
- `docs/aionui-reference-study.md`
- `docs/spirit-cowork-gap-report.md`
- `docs/plan-index.md`

Reviewed closeout and safety code:

- `source_proxy/testing/runner.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`
- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/api/cartographer.py`
- `source_proxy/cartographer/service.py`
- `source_proxy/cartographer/commit_proposals.py`
- `source_proxy/cartographer/level_2_readiness.py`

Reviewed adjacent Scout and dashboard work:

- `scout/src/scout/api/packets.py`
- `scout/src/scout/api/sources.py`
- `scout/src/scout/api/auto_rank.py`
- `src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`
- `src/components/dashboard/ScoutIntelligenceCenter.tsx`
- `src/lib/scout-overview.ts`

Live workspace evidence observed before writing this plan:

- Branch: `main`
- HEAD: `74dc4ba77ea274ebf6c804eb4e9aee9017cf718c`
- Current dirty tree includes additional Scout discovery-job files and later Scout Level 2 evidence logs beyond the pasted manual summary, including `scout/soak-logs/scout-level-2-evidence-2026-05-20T015518Z.json` and `scout/soak-logs/scout-level-2-evidence-2026-05-20T015829Z.json`.
- No implementation, apply, commit, push, cleanup, deletion, or approval bypass was performed while creating this plan.

## Non-Negotiable Safety Boundary

These boundaries apply until Britton explicitly approves a later implementation increment:

- No apply.
- No execute-approved.
- No commit.
- No push.
- No merge.
- No deletion.
- No cleanup.
- No approval bypass.
- No autonomy promotion.
- No mobile execution authority.
- No Codex worker promotion.
- No design-vault cleanup without human approval.
- No touching secrets, certificates, tokens, `.env` files, or protected paths.

Approval, apply, commit, push, merge, and cleanup remain separate actions. A green diagnostic command does not grant any of those authorities.

## Current Blockers

- `proxy-closeout` passed and recommended the next increment.
- `global-safety-regression` failed because Cartographer safety failed and the outer mutation check saw unexpected Scout Level 2 evidence logs.
- The global profile's outer mutation filter currently permits `scout/soak-logs/scout-soak-snapshot-*`, while the failing run created `scout/soak-logs/scout-level-2-evidence-*`.
- Cartographer project health blocks merge because the working tree has uncommitted changes and the work is not on a review branch.
- Evidence files are mixed with source, dashboard, Scout, and docs changes, so the dirty tree cannot be reviewed as one safe bundle.
- The current tree has unrelated or not-yet-classified design-vault and design-system work that must not be swept into Source Proxy closeout.

## Dirty Tree Classification

Source Proxy core:

- `source_proxy/safety/paths.py`
- `source_proxy/tasks/long_running.py`
- `source_proxy/testing/runner.py`
- `source_proxy/tests/test_verification_contracts.py`
- `source_proxy/verification/contracts.py`
- `source_proxy/verification/diff.py`

Cartographer safety and readiness:

- `source_proxy/api/cartographer.py`
- `source_proxy/cartographer/commit_proposals.py`
- `source_proxy/cartographer/level_2_readiness.py`
- `source_proxy/cartographer/service.py`
- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`
- `docs/cartographer-level-3-autonomy-plan.md`

Scout API and auto-rank:

- `scout/src/scout/api/auto_rank.py`
- `scout/src/scout/api/discovery_jobs.py`
- `scout/src/scout/api/packets.py`
- `scout/src/scout/api/sources.py`
- `scout/src/scout/tests/test_discovery_jobs.py`
- `scout/src/scout/tests/test_packets_api.py`
- `scout/src/scout/tests/test_sources_api.py`

Dashboard Scout UI:

- `src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`
- `src/components/dashboard/ScoutIntelligenceCenter.tsx`
- `src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx`
- `src/lib/scout-overview.ts`

Docs and plan index:

- `docs/plan-index.md`
- `docs/scout-v0-5-evidence-snapshot-review.md`
- `docs/scout-v0-5-scheduled-read-only-watch-design.md`
- `docs/source-proxy-closeout-consolidation-plan.md`

Evidence snapshots and generated soak logs:

- `scout/soak-logs/scout-level-2-evidence-2026-05-20T004503Z.json`
- `scout/soak-logs/scout-level-2-evidence-2026-05-20T004511Z.json`
- `scout/soak-logs/scout-level-2-evidence-2026-05-20T015131Z.json`
- `scout/soak-logs/scout-level-2-evidence-2026-05-20T015211Z.json`
- `scout/soak-logs/scout-level-2-evidence-2026-05-20T015518Z.json`
- `scout/soak-logs/scout-level-2-evidence-2026-05-20T015829Z.json`

Design vault or unrelated design-system work:

- `data/design-vault/`
- `docs/design-systems-master-v0.1.md`

## Phase 0: Freeze and Classify

### Increment 0.1

Goal:
Capture the exact repository state and classify the dirty tree without staging, committing, deleting, or cleaning anything.

Files to inspect:

- `git status --short` output
- `git status -sb` output
- `git branch --show-current`
- `git rev-parse HEAD`
- `docs/source-proxy-closeout-consolidation-plan.md`

Files allowed to change, if any:

- None.

Commands to run:

```bash
cd /home/source/SpiritOS
git status --short
git status -sb
git branch --show-current
git rev-parse HEAD
```

Manual check:
Confirm that all dirty files are assigned to one bucket: Source Proxy core, Cartographer safety and readiness, Scout API and auto-rank, Dashboard Scout UI, docs and plan index, evidence snapshots and generated soak logs, or design vault/unrelated design-system work.

Expected output:

- Branch and HEAD are recorded.
- Dirty files are listed exactly.
- No files are staged.
- No commit exists from this diagnostic pass.
- No cleanup was run.

Debug path if it fails:
If new files appear during the check, record them as a new observation and classify them before continuing. If HEAD changes, stop immediately and inspect `git reflog -5` and `git log --oneline -5` without reverting anything.

Stop condition:
Stop when the dirty tree is fully classified and unchanged by the diagnostic commands.

Next increment title:
Increment 1.1: Target the Cartographer safety failure.

## Phase 1: Diagnose Global Safety Regression Failure

### Increment 1.1

Goal:
Expose the exact Cartographer safety failure with the smallest targeted test command. Do not infer the cause only from the global summary.

Files to inspect:

- `source_proxy/testing/runner.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`
- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/api/cartographer.py`
- `source_proxy/cartographer/service.py`
- `source_proxy/cartographer/commit_proposals.py`
- `source_proxy/cartographer/level_2_readiness.py`

Files allowed to change, if any:

- None.

Commands to run:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py source_proxy/tests/test_cartographer_api.py -x
git status --short
```

Manual check:
Read the first failing test, the assertion, and the status delta printed after the run. Confirm whether the failure is from pytest itself, mutation detection, HEAD movement, or a mismatch between allowed generated evidence patterns.

Expected output:

- Either the targeted Cartographer tests pass and the failure is isolated to the runner mutation boundary, or the first failing test names the exact Cartographer contract that regressed.
- HEAD remains unchanged.
- No apply, execute-approved, commit, push, merge, cleanup, or deletion occurs.

Debug path if it fails:
If pytest fails, rerun only the named failing test with `-vv`. If pytest passes but status gains new soak logs, inspect the runner's status-delta filters and the Scout evidence profile that created the files. Do not patch yet.

Stop condition:
Stop when the exact failing assertion or mutation source is known.

Next increment title:
Increment 1.2: Identify why Scout Level 2 evidence logs appear during global safety.

### Increment 1.2

Goal:
Find why `global-safety-regression` creates or observes new `scout-level-2-evidence-*` files and decide the correct policy before implementation.

Files to inspect:

- `source_proxy/testing/runner.py`
- `scout/soak-logs/`
- `scout/src/scout/tests/test_v03_soak_safety.py`
- `scout/src/scout/tests/test_discovery_jobs.py`
- `scout/src/scout/tests/test_packets_api.py`
- `scout/src/scout/tests/test_sources_api.py`

Files allowed to change, if any:

- None.

Commands to run:

```bash
cd /home/source/SpiritOS
git status --short scout/soak-logs source_proxy/testing/runner.py scout/src/scout/tests
grep -n "scout-level-2-evidence\|scout-soak-snapshot\|global-safety-regression\|unexpected_status_delta" source_proxy/testing/runner.py
PYTHONPATH=. .venv/bin/python -m pytest scout/src/scout/tests/test_v03_soak_safety.py -q
git status --short scout/soak-logs
```

Manual check:
Confirm whether the logs are generated by a Scout test, by a runner profile called during global safety, by a live service side effect, or by a pre-existing background process.

Expected output:

- The source of `scout-level-2-evidence-*` writes is identified.
- The logs are classified as one of: temp test artifact, expected generated evidence, harness-cleaned artifact, or actual mutation bug.
- No cleanup is performed automatically.

Debug path if it fails:
If the source is not obvious, run the Scout backend safety tests one file at a time and inspect `git status --short scout/soak-logs` after each file. If logs appear without a test running, inspect running services and timestamps before changing code.

Stop condition:
Stop when the decision path below can be answered with evidence:

- Temp artifact path: use when the files are useful only during tests and should not persist in the repo.
- Allowlist as expected evidence: use when the logs are intentional review artifacts and should remain visible to project health.
- Harness cleanup after capture: use only if the logs are disposable and cleanup can be explicit, bounded, and reported.
- Actual mutation bug: use when a read-only safety regression should not write these files at all.

Next increment title:
Increment 2.1: Define evidence and generated-file policy.

## Phase 2: Evidence and Generated-File Policy

### Increment 2.1

Goal:
Define which evidence files are expected, where generated test artifacts belong, and how mutation checks distinguish acceptable evidence from unsafe repo mutation.

Files to inspect:

- `source_proxy/testing/runner.py`
- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/cartographer/service.py`
- `scout/soak-logs/`
- `docs/source-proxy-regression-matrix.md`

Files allowed to change, if any:

- None during this planning increment. A later approved implementation increment may touch only the files named by the chosen policy.

Commands to run:

```bash
cd /home/source/SpiritOS
grep -n "expected_evidence_files\|unsafe_dirty_files\|scout-soak-snapshot\|scout-level-2-evidence\|unexpected_status_delta" source_proxy/testing/runner.py source_proxy/tests/test_cartographer_api.py source_proxy/cartographer/service.py
git status --short scout/soak-logs
```

Manual check:
Write down the policy choice before editing code. Evidence that is part of human review should stay visible and be listed as expected evidence. Test-only artifacts should go to a temp path or be removed by a bounded harness step only after capture and only with explicit reporting.

Expected output:

- A named policy decision exists for `scout-level-2-evidence-*`.
- Mutation checks have a planned distinction between expected evidence and unsafe dirty files.
- Rollback and cleanup review are manual, not automatic.

Debug path if it fails:
If project health and runner profiles disagree about expected evidence, treat that disagreement as the blocker and do not proceed to consolidation. Choose one source of truth and update the other only in a later approved implementation increment.

Stop condition:
Stop when Britton can approve one policy path without ambiguity.

Next increment title:
Increment 3.1: Consolidate dirty tree into review groups.

## Phase 3: Dirty-Tree Consolidation Plan

### Increment 3.1

Goal:
Group the current dirty tree into logical commit candidates without staging or committing.

Files to inspect:

- All dirty files from `git status --short`.
- `source_proxy/cartographer/commit_proposals.py`
- `source_proxy/cartographer/level_2_readiness.py`
- `docs/plan-index.md`

Files allowed to change, if any:

- None.

Commands to run:

```bash
cd /home/source/SpiritOS
git status --short
git diff --name-status
```

Manual check:
Confirm that every dirty file belongs to exactly one candidate or is explicitly excluded/deferred.

Expected output:

- Commit candidate A through F are review groups only.
- No staging occurs.
- No commit occurs.
- Excluded design-vault/design-system work remains untouched unless Britton approves a separate path.

Debug path if it fails:
If a file spans two candidates, inspect its diff and choose the group that owns the behavioral contract. If the file is unrelated to Source Proxy closeout, move it to excluded/deferred rather than forcing it into a proxy bundle.

Stop condition:
Stop when the dirty tree can be reviewed one group at a time.

Next increment title:
Increment 4.1: Move to a review branch by human command.

Commit candidate A: Source Proxy safety and verification contracts.

Files:

- `source_proxy/safety/paths.py`
- `source_proxy/tasks/long_running.py`
- `source_proxy/testing/runner.py`
- `source_proxy/tests/test_verification_contracts.py`
- `source_proxy/verification/contracts.py`
- `source_proxy/verification/diff.py`

Why they belong together:
These files define the Source Proxy safety runner, long-running task authority, path safety, diff validation, and verification contracts that the closeout gates depend on.

Tests required before this group is allowed:

```bash
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_proxy_runner.py source_proxy/tests/test_verification_contracts.py source_proxy/tests/test_long_running_tasks.py source_proxy/tests/test_diff_verification.py
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Commit candidate B: Cartographer closeout, safety, and readiness.

Files:

- `source_proxy/api/cartographer.py`
- `source_proxy/cartographer/commit_proposals.py`
- `source_proxy/cartographer/level_2_readiness.py`
- `source_proxy/cartographer/service.py`
- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`
- `docs/cartographer-level-3-autonomy-plan.md`

Why they belong together:
These files own Cartographer project health, dirty-tree classification, Level 2/Level 3 readiness, commit proposal previews, and safety audit coverage.

Tests required before this group is allowed:

```bash
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py source_proxy/tests/test_cartographer_api.py
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile cartographer-safety
```

Commit candidate C: Scout API and auto-rank changes.

Files:

- `scout/src/scout/api/auto_rank.py`
- `scout/src/scout/api/discovery_jobs.py`
- `scout/src/scout/api/packets.py`
- `scout/src/scout/api/sources.py`
- `scout/src/scout/tests/test_discovery_jobs.py`
- `scout/src/scout/tests/test_packets_api.py`
- `scout/src/scout/tests/test_sources_api.py`

Why they belong together:
These files add or expose read-only Scout ranking, packet/source review metadata, and discovery gate behavior. They should be reviewed separately from Source Proxy authority code.

Tests required before this group is allowed:

```bash
PYTHONPATH=. .venv/bin/python -m pytest scout/src/scout/tests/test_discovery_jobs.py scout/src/scout/tests/test_packets_api.py scout/src/scout/tests/test_sources_api.py
PYTHONPATH=. .venv/bin/python -m pytest scout/src/scout/tests/test_source_registry.py scout/src/scout/tests/test_search_candidate_extraction.py scout/src/scout/tests/test_search_provider.py scout/src/scout/tests/test_v03_soak_safety.py
```

Commit candidate D: Scout dashboard UI changes.

Files:

- `src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`
- `src/components/dashboard/ScoutIntelligenceCenter.tsx`
- `src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx`
- `src/lib/scout-overview.ts`

Why they belong together:
These files surface Scout auto-rank, source review, packet review, and dashboard data contracts. They should follow the Scout API contract but remain a separate UI review group.

Tests required before this group is allowed:

```bash
npx vitest run src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx
npx vitest run src/components/coding/__tests__/coding-workflow-step.test.ts src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx
```

Commit candidate E: Docs and plan index.

Files:

- `docs/plan-index.md`
- `docs/scout-v0-5-evidence-snapshot-review.md`
- `docs/scout-v0-5-scheduled-read-only-watch-design.md`
- `docs/source-proxy-closeout-consolidation-plan.md`

Why they belong together:
These files document current plan state, Scout evidence review, scheduled read-only watch design, and this closeout/consolidation plan. They do not grant implementation authority.

Tests required before this group is allowed:

```bash
git diff --check
grep -n "status: active\|status: historical\|status: deferred" docs/plan-index.md
sed -n '1,260p' docs/source-proxy-closeout-consolidation-plan.md
```

Commit candidate F: Evidence snapshots, only if approved.

Files:

- `scout/soak-logs/scout-level-2-evidence-2026-05-20T004503Z.json`
- `scout/soak-logs/scout-level-2-evidence-2026-05-20T004511Z.json`
- `scout/soak-logs/scout-level-2-evidence-2026-05-20T015131Z.json`
- `scout/soak-logs/scout-level-2-evidence-2026-05-20T015211Z.json`
- `scout/soak-logs/scout-level-2-evidence-2026-05-20T015518Z.json`
- `scout/soak-logs/scout-level-2-evidence-2026-05-20T015829Z.json`

Why they belong together:
These are generated evidence snapshots. They should not be mixed with source changes. They belong in a commit only if Britton explicitly approves preserving them as review evidence.

Tests required before this group is allowed:

```bash
git status --short scout/soak-logs
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile global-safety-regression
```

Excluded or deferred:

- `data/design-vault/`
- `docs/design-systems-master-v0.1.md`

Why excluded:
These appear related to design-vault or design-system work, not Source Proxy closeout. Do not clean, delete, stage, or fold them into proxy consolidation without human approval.

## Phase 4: Review-Branch Strategy

### Increment 4.1

Goal:
Move the closeout work onto a review branch by human command so project health can stop blocking on "not on a review branch" after the dirty tree is intentionally organized.

Files to inspect:

- No files required.

Files allowed to change, if any:

- None by Codex in this planning pass.

Commands to run:

```bash
cd /home/source/SpiritOS
git status -sb
git switch -c review/source-proxy-closeout-consolidation
git status -sb
```

Manual check:
Britton should run these commands only after approving the branch move. Confirm the branch name is `review/source-proxy-closeout-consolidation` and that no files were staged or committed by the switch.

Expected output:

- Current branch becomes `review/source-proxy-closeout-consolidation`.
- Dirty files remain dirty.
- HEAD stays `74dc4ba77ea274ebf6c804eb4e9aee9017cf718c` unless a human has explicitly committed later.

Debug path if it fails:
If the branch already exists, inspect it with `git branch --list review/source-proxy-closeout-consolidation` and `git status -sb`. Do not delete or reset the branch without explicit approval.

Stop condition:
Stop when the work is on a review branch and the dirty tree is unchanged except for branch metadata.

Next increment title:
Increment 5.1: Run the final closeout gate.

Why project health blocks merge while not on a review branch:
Project health treats dirty work on `main` as not merge-ready because it lacks the review isolation needed for grouped staging, explicit checks, and separate commit/push approvals. A review branch makes the consolidation reviewable without granting commit or push authority.

## Phase 5: Final Closeout Gate

### Increment 5.1

Goal:
Run the exact final closeout sequence before any implementation or commit work proceeds.

Files to inspect:

- `docs/source-proxy-closeout-consolidation-plan.md`
- `source_proxy/testing/runner.py`
- Current `git status --short`

Files allowed to change, if any:

- None.

Commands to run:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py source_proxy/tests/test_cartographer_api.py -x
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile global-safety-regression
git status --short
```

Manual check:
Confirm that the output shows proxy closeout PASS, global safety PASS, no unexpected mutation, no approval/apply/commit/push bypass, and only intentional dirty review groups.

Expected output:

- `git diff --check` has no output.
- Targeted Cartographer safety tests pass.
- `proxy-closeout` PASS.
- `global-safety-regression` PASS.
- No unexpected mutation.
- No approve/apply/commit/push bypass.
- Dirty tree only contains the intentional plan doc or approved review groups.
- HEAD is unchanged unless Britton explicitly commits later.

Debug path if it fails:
If `git diff --check` fails, fix whitespace only in a later approved implementation increment. If Cartographer safety fails, return to Increment 1.1. If global safety fails only on Scout evidence logs, return to Increment 1.2 and Phase 2 policy. If HEAD changes, stop and inspect the commit history without reverting.

Stop condition:
Stop when the full sequence is green or when the first blocker is identified.

Next increment title:
Increment 6.1: Begin Codex-like `/coding` polish only after green closeout.

## Phase 6: Only After Green Closeout, Codex-Like /coding Polish Track

### Increment 6.1

Goal:
Define future `/coding` polish only after global safety is green. Do not implement UI polish now.

Files to inspect:

- `docs/codingUI.md`
- `docs/agent-wrapper-reference-study.md`
- `docs/aionui-reference-study.md`
- `docs/spirit-cowork-gap-report.md`
- Current dashboard and `/coding` UI files, only after the final closeout gate passes.

Files allowed to change, if any:

- None during this closeout plan.

Commands to run:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile global-safety-regression
git status --short
```

Manual check:
Confirm global safety is PASS before opening any UI polish increment.

Expected output:

- `global-safety-regression` PASS.
- No unexpected mutation.
- No authority boundary regression.
- `/coding` polish remains deferred until the closeout gate is green.

Debug path if it fails:
Return to the failing closeout phase. Do not start UI polish while safety is red.

Stop condition:
Stop until Britton approves a separate `/coding` polish implementation increment.

Next increment title:
Future Increment: Codex-like `/coding` cockpit polish.

Future track, gated by green global safety:

- Project/thread sidebar.
- Active task timeline.
- Terminal evidence panel.
- Diff/review pane.
- Artifact shelf.
- Browser preview lane.
- Mobile-first review cards.
- Clearer blocked, ready, applied, and verify states.

This track must borrow Codex-like review ergonomics without promoting Codex to default worker, adding mobile execution authority, or bypassing Source Proxy gates.

## Final Green Gate

The final green gate is:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py source_proxy/tests/test_cartographer_api.py -x
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile global-safety-regression
git status --short
```

Expected final state:

- `proxy-closeout` PASS.
- `global-safety-regression` PASS.
- No unexpected mutation.
- No approve/apply/commit/push bypass.
- Dirty tree only contains intentional plan docs or approved review groups.
- HEAD unchanged unless Britton explicitly commits later.

## Rollback and Recovery

This plan does not authorize automatic rollback or cleanup.

Increment 2.1 result note:

- `scout-level-2-evidence-*` is expected generated evidence only inside the explicit `scout-level-2-evidence-snapshot` runner profile.
- `global-safety-regression` remains strict: it still allows the existing `scout-soak-snapshot-*` background evidence pattern, but it does not globally allowlist `scout-level-2-evidence-*`.
- If `scout-level-2-evidence-*` appears during `global-safety-regression`, the runner now reports it as unexpected and explains the likely causes: a concurrent/manual Level 2 evidence snapshot run, another wrapper invoking that profile nearby, or a real unexpected mutation.
- No automatic cleanup or deletion is part of this policy.

Manual rollback review procedure:

1. Capture `git status --short` and `git diff --name-status`.
2. Identify the exact file or evidence artifact under review.
3. Confirm whether it is source work, docs work, expected evidence, temp test output, or unrelated design work.
4. Ask Britton before any restore, deletion, cleanup, or branch operation.
5. If rollback is approved later, run only the exact command Britton approved and record the before/after status.

Do not delete generated soak logs automatically. Do not clean `data/design-vault/`. Do not restore or discard unrelated dirty files. Do not touch secrets, certificates, tokens, `.env` files, or protected paths.

## Deferred Codex-Like /coding Polish Track

The Codex-like `/coding` polish track is explicitly deferred until the closeout gate is green.

Allowed future ideas after green closeout:

- Project/thread sidebar for active and past tasks.
- Active task timeline with states from draft through verification.
- Terminal evidence panel for command receipts.
- Diff/review pane with allowed-file and protected-path status.
- Artifact shelf for logs, screenshots, receipts, and generated evidence.
- Browser preview lane for UI work.
- Mobile-first review cards for blocked, ready, applied, and verify states.
- Clearer state language around blocked, ready, approved, applied, and verified work.

Forbidden in that future track unless separately approved:

- New apply authority.
- Commit or push controls.
- Mobile execution authority.
- Codex worker promotion.
- Autonomy promotion.
- Approval bypass.
- Design-vault cleanup.

## Permission Gate

Stop here. Do not implement this plan until Britton approves the first implementation increment.
