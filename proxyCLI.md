# SpiritOS Source Proxy Master Plan
## Phase 10.7 to Phase 11
## Codex CLI Adapter First, AionUI Wrapper Later

Status date: 2026-05-17
Owner: Britton
Branch: cartographer/next-increment
Current HEAD: d7d38aa

## Executive verdict

Current status:
GO for Phase 10.7 package review.
GO for writing the next master plan.
HOLD final pull or merge until package evidence selection is complete.

The system is now in production-hardening beta.

Do not build the AionUI custom wrapper yet.
Do build the Codex CLI adapter under Source Proxy.
Use AionUI, Continue, Cline, Goose, and OpenCode as references, not as the source of truth.

## Current confirmed baseline

Confirmed from latest diagnostics:

- TypeScript: PASS
- git diff --check: PASS
- source_proxy/tests/test_proxy_runner.py: 40 passed
- Phase 4F closeout: PASS
- phase-4e-safety-seed: 3 passed, applied_anything false
- Cartographer soak snapshot: PASS
- Cartographer reliability: score 100, grade boring
- HEAD unchanged
- dirty tree expected

Current expected dirty files:

- source_proxy/testing/runner.py
- source_proxy/tests/test_proxy_runner.py
- selected Scout soak snapshot evidence
- selected Cartographer soak snapshot evidence

Current Phase 10.7 patch purpose:

- Scout soak snapshot uses docker logs --since snapshot start
- warning parsing scopes to latest scout_starting session
- list-shaped errors and dict-shaped errors are handled correctly
- stale pre-startup log errors no longer poison fresh soak evidence
- regression tests cover those cases

## Non-negotiable rules

1. Source Proxy remains the boss.
2. Codex CLI is a worker, not the system of record.
3. AionUI is reference material for now, not the core wrapper.
4. Passing tests never equal approval.
5. Approval does not equal apply.
6. Apply does not equal commit.
7. Commit does not equal push.
8. Push requires separate explicit approval.
9. Scout cannot bypass coding safety.
10. Cartographer cannot bypass Source Proxy approval.
11. No final pull or merge without a fresh clean diagnostic.
12. Every phase must have manual checks, expected outputs, debug steps, rollback, and next step.

## High-level sequence

Phase 10.7: Finish package and commit review.
Phase 10.8: Add Codex CLI adapter under Source Proxy.
Phase 10.9: Add Codex task packets and evidence capture.
Phase 10.10: Run 5 to 10 real coding tasks through the adapter.
Phase 10.11: Promote real-task results into Cartographer and Blueprinter.
Phase 11.0: Research AionUI and adjacent tools as references.
Phase 11.1: Build Spirit Cowork Console only after gaps are proven.
Phase 11.2: Decide whether AionUI should be ignored, borrowed from, integrated with, or wrapped.

# Phase 10.7: Package and Commit Review

Goal:
Close the production-hardening baseline cleanly before adding Codex CLI.

Do not add new features in this phase.

## Increment 10.7.1: Package evidence selection

Goal:
Decide exactly what belongs in the Phase 10.7 package.

Files likely touched:
- source_proxy/testing/runner.py
- source_proxy/tests/test_proxy_runner.py
- selected scout/soak-logs/*.json
- selected source_proxy/cartographer/soak-logs/*.json
- optional docs release note only if needed

Implementation notes:
Include the two code files.
Include only passing soak evidence unless forensic history is intentionally desired.
Do not include failed stale-warning Scout snapshots unless the commit message clearly labels them as diagnostic history.

Recommended passing evidence to include:
- scout/soak-logs/scout-soak-snapshot-2026-05-17T023515Z.json
- scout/soak-logs/scout-soak-snapshot-2026-05-17T023549Z.json
- scout/soak-logs/scout-soak-snapshot-2026-05-17T024001Z.json
- scout/soak-logs/scout-soak-snapshot-2026-05-17T030240Z.json
- source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-17T030304Z.json

Recommended evidence to exclude unless you want forensic history:
- scout/soak-logs/scout-soak-snapshot-2026-05-17T022415Z.json
- scout/soak-logs/scout-soak-snapshot-2026-05-17T022449Z.json
- scout/soak-logs/scout-soak-snapshot-2026-05-17T022846Z.json

Manual checks:
cd ~/SpiritOS

git --no-pager diff --stat
git --no-pager diff --name-status
git diff --check

GIT_PAGER=cat git diff -- source_proxy/testing/runner.py source_proxy/tests/test_proxy_runner.py

Expected outputs:
- only the two code files are modified
- no whitespace errors
- Scout soak hardening is visible
- test coverage for list-shaped errors and stale pre-startup logs is visible

Debug if failed:
- If extra source files appear, stop and classify them.
- If diff check prints whitespace errors, fix whitespace before package.
- If soak logs are noisy, include only the latest passing evidence.
- If the diff is larger than expected, do not commit until reviewed.

Rollback:
git restore source_proxy/testing/runner.py source_proxy/tests/test_proxy_runner.py

For evidence only:
rm scout/soak-logs/<unwanted-file>.json
rm source_proxy/cartographer/soak-logs/<unwanted-file>.json

Next step:
Proceed to Increment 10.7.2 after evidence selection is clear.

Permission gate:
Ask Britton before deleting or excluding any evidence files permanently.

## Increment 10.7.2: Final package diagnostic

Goal:
Run one clean final diagnostic after evidence selection.

Files likely touched:
None expected, except allowed soak snapshot logs if those profiles are run.

Manual checks:
cd ~/SpiritOS

npm run typecheck 2>/dev/null || npx tsc --noEmit

PYTHONPATH=. python3 -m pytest source_proxy/tests/test_proxy_runner.py

PYTHONPATH=. python3 -m source_proxy.testing.runner --profile phase-4f-closeout

PYTHONPATH=. python3 -m source_proxy.testing.self_tests --suite phase-4e-safety-seed

PYTHONPATH=. python3 -m source_proxy.testing.runner --profile cartographer-soak-snapshot

git diff --check
git status --short
git rev-parse --short HEAD

Expected outputs:
- typecheck passes
- test_proxy_runner.py passes
- Phase 4F closeout passes
- safety seed passes
- Cartographer soak snapshot passes
- HEAD remains d7d38aa until commit
- dirty tree remains explainable
- no approve, apply, execute-approved, commit, push, or cleanup occurs

Debug if failed:
- If typecheck fails, stop and inspect TypeScript output.
- If proxy runner tests fail, inspect the new 10.7 tests first.
- If Phase 4F fails due Scout logs, confirm docker --since and scout_starting session logic.
- If safety seed fails, stop all Codex adapter work.
- If HEAD changes, stop and inspect git reflog.

Rollback:
No code rollback unless tests reveal a bad patch.
Use git restore only after reviewing the failing diff.

Next step:
Proceed to Increment 10.7.3.

Permission gate:
Ask Britton before committing.

## Increment 10.7.3: Commit Phase 10.7 package

Goal:
Create a clean commit for the production hardening baseline.

Files likely touched:
Git index only.

Implementation notes:
Use a specific commit message.
Do not push in this increment unless separately approved.

Suggested commit message:
test(proxy): harden scout soak snapshot evidence parsing

Manual checks:
cd ~/SpiritOS

git status --short

git add source_proxy/testing/runner.py source_proxy/tests/test_proxy_runner.py

# Add only selected passing evidence if approved:
git add scout/soak-logs/<selected-passing-scout-snapshot>.json
git add source_proxy/cartographer/soak-logs/<selected-passing-cartographer-snapshot>.json

git diff --cached --stat
git diff --cached --check
git status --short

Expected outputs:
- staged files match package decision
- no unexpected files staged
- diff check clean
- no push happens

Debug if failed:
- If bad files are staged, run git restore --staged <file>.
- If failed evidence files are staged accidentally, unstage them.
- If staged diff is too broad, stop and split commit.

Rollback:
git restore --staged .
No working tree changes are lost.

Next step:
Commit only after staged package is reviewed.

Permission gate:
Ask Britton before running git commit.

## Increment 10.7.4: Post-commit verification

Goal:
Prove commit did not break the baseline.

Files likely touched:
None expected, except optional soak logs.

Manual checks:
cd ~/SpiritOS

git log -1 --oneline
git status --short
npm run typecheck 2>/dev/null || npx tsc --noEmit
PYTHONPATH=. python3 -m pytest source_proxy/tests/test_proxy_runner.py
PYTHONPATH=. python3 -m source_proxy.testing.self_tests --suite phase-4e-safety-seed

Expected outputs:
- latest commit is the 10.7 package commit
- status is clean or only expected untracked evidence
- typecheck passes
- proxy runner tests pass
- safety seed passes
- no push happens

Debug if failed:
- If tests fail after commit, inspect whether evidence files affected tests.
- If status has unexpected files, classify before moving on.
- If commit message is wrong, amend only with approval.

Rollback:
For a bad commit on local branch:
git reset --soft HEAD~1

Do not reset after push without explicit approval.

Next step:
Proceed to Phase 10.8.

Permission gate:
Ask Britton before pushing.

# Phase 10.8: Codex CLI Adapter Under Source Proxy

Goal:
Make Codex CLI a worker that Source Proxy can invoke, observe, and judge.

Codex must not become the approval system.
Codex must not apply, commit, or push through its own authority.
Codex output becomes a proposal packet.

## Increment 10.8.1: Codex CLI capability probe

Goal:
Detect whether Codex CLI is installed, authenticated, and able to run safely.

Files likely touched:
- source_proxy/tools/codex_cli.py or source_proxy/codex/adapter.py
- source_proxy/tests/test_codex_cli_adapter.py
- source_proxy/api/tools_manifest.py or source_proxy/api/self_status.py
- docs/codex-cli-adapter-plan.md

Implementation notes:
Create a read-only probe first.
The probe should report:
- codex binary found
- codex version
- auth likely available or unavailable
- supports exec
- supports JSON mode
- supports sandbox options
- supports output-last-message
- supports output-schema
- default sandbox recommendation
- dangerous flags blocked by policy

Do not run repo-changing Codex tasks yet.

Manual checks:
cd ~/SpiritOS

which codex || true
codex --version || true

PYTHONPATH=. python3 -m pytest source_proxy/tests/test_codex_cli_adapter.py
curl -s http://localhost:3000/v1/self/status | jq '.codex // .tools.codex // .capabilities.codex'

git status --short

Expected outputs:
- capability probe returns installed true or installed false cleanly
- missing Codex is a config-blocked state, not a crash
- no files are changed by probing
- no approval/apply/commit/push happens

Debug if failed:
- If codex command not found, install or add PATH.
- If auth fails, run Codex manually and sign in.
- If status endpoint crashes, isolate adapter import from runtime errors.
- If the probe mutates files, block the phase.

Rollback:
git restore source_proxy src docs/codex-cli-adapter-plan.md

Next step:
Proceed to Increment 10.8.2 after the probe reports cleanly.

Permission gate:
Ask Britton before adding any endpoint that can run Codex.

## Increment 10.8.2: Codex execution envelope

Goal:
Define a safe envelope for running Codex.

Files likely touched:
- source_proxy/codex/adapter.py
- source_proxy/codex/models.py
- source_proxy/safety/paths.py
- source_proxy/tests/test_codex_cli_adapter.py
- docs/codex-cli-adapter-plan.md

Implementation notes:
The envelope should define:
- workspace root
- task ID
- allowed files
- blocked files
- sandbox mode
- timeout
- model mode
- output directory
- max output size
- command allowlist
- environment allowlist
- dangerous flag denylist

Default command shape:
codex exec --cd <workspace> --json --output-last-message <path> --sandbox workspace-write <prompt-file>

Allowed first sandbox:
workspace-write only for a throwaway test branch or docs-only task.

Blocked flags:
- --dangerously-bypass-approvals-and-sandbox
- --yolo
- --sandbox danger-full-access
- any flag that grants outside-root write access without explicit approval

Manual checks:
cd ~/SpiritOS

PYTHONPATH=. python3 -m pytest source_proxy/tests/test_codex_cli_adapter.py

python - <<'PY'
from source_proxy.codex.adapter import build_codex_command
print(build_codex_command(
    workspace="/home/source/SpiritOS",
    prompt_file="/tmp/task.md",
    output_file="/tmp/final.md",
    sandbox="workspace-write",
))
PY

git status --short

Expected outputs:
- command builder emits safe defaults
- dangerous flags are rejected
- allowed_files are preserved
- no files are changed by command building
- tests cover unsafe sandbox rejection

Debug if failed:
- If dangerous flags pass through, add explicit denylist tests.
- If command allows outside workspace, block add-dir support for now.
- If timeout is missing, add hard timeout before live runs.
- If env leaks secrets, replace env with a minimal allowlist.

Rollback:
git restore source_proxy/codex source_proxy/tests/test_codex_cli_adapter.py docs/codex-cli-adapter-plan.md

Next step:
Proceed to Increment 10.8.3.

Permission gate:
Ask Britton before the first live Codex run.

## Increment 10.8.3: First live Codex dry run

Goal:
Run Codex on a harmless read-only task and capture evidence.

Files likely touched:
- source_proxy/codex/adapter.py
- source_proxy/tasks/long_running.py, only if needed for task capture
- source_proxy/tests/test_codex_cli_adapter.py
- tmp/artifacts or source_proxy/data-like ignored output path, if already safe

Implementation notes:
First live task should ask Codex to summarize the repo or explain a test file.
It should not request file edits.
Capture:
- command
- start time
- end time
- exit code
- stdout excerpt
- stderr excerpt
- JSON event count
- final message path
- changed files before and after
- HEAD before and after
- result: pass, fail, timeout, blocked_by_config

Manual checks:
cd ~/SpiritOS

git status --short
git rev-parse --short HEAD

# Run through your adapter, not raw Codex if the route exists:
PYTHONPATH=. python3 -m source_proxy.codex.adapter --dry-run-readonly "Summarize source_proxy/testing/runner.py without editing files."

git status --short
git rev-parse --short HEAD

Expected outputs:
- Codex runs or returns config-blocked cleanly
- final message is captured
- changed files delta is none
- HEAD unchanged
- no approval/apply/commit/push happens

Debug if failed:
- If Codex waits interactively, adjust exec flags.
- If output is huge, truncate and save artifact.
- If Codex edits files during read-only task, block live runs and enforce read-only sandbox.
- If adapter cannot parse JSON events, capture raw stdout and degrade gracefully.

Rollback:
Delete generated adapter artifacts only.
Do not reset repo unless actual files changed.

Next step:
Proceed to Increment 10.8.4.

Permission gate:
Ask Britton before allowing docs-only edits.

## Increment 10.8.4: Docs-only Codex proposal run

Goal:
Let Codex attempt a tiny docs-only edit, but do not auto-apply through Source Proxy.

Files likely touched:
- source_proxy/codex/adapter.py
- source_proxy/verification/diff.py
- source_proxy/api/diff_verification.py
- source_proxy/tests/test_codex_cli_adapter.py
- source_proxy/tests/test_diff_verification.py
- docs/codex-cli-adapter-plan.md

Implementation notes:
Codex may modify a docs-only target in a controlled branch/worktree.
Source Proxy must capture:
- changed files
- unified diff
- allowed file match
- target match
- diff check result
- tests requested by Codex
- tests actually run
- final message
- recommendation

Do not treat Codex’s edit as approved.
Do not commit.
Do not push.

Manual check task:
Target file:
docs/phase-8-manual-check.md

Task:
Append one sentence saying Phase 10.8 Codex adapter dry-run docs proposal was captured safely.

Manual checks:
cd ~/SpiritOS

git status --short
git rev-parse --short HEAD

# Through adapter:
PYTHONPATH=. python3 -m source_proxy.codex.adapter --proposal-task docs/phase-8-manual-check.md

git diff -- docs/phase-8-manual-check.md
git diff --check
git status --short
git rev-parse --short HEAD

Expected outputs:
- only docs/phase-8-manual-check.md changes
- diff captured
- approval remains required
- commit not created
- push not created
- HEAD unchanged
- Source Proxy report says proposal_ready or preview_ready, not applied

Debug if failed:
- If Codex changes extra files, block and restore.
- If approval becomes available without verifier pass, block.
- If apply happens automatically, stop Codex adapter work.
- If output lacks diff, improve git diff capture.

Rollback:
git restore docs/phase-8-manual-check.md

Next step:
Proceed to Increment 10.8.5.

Permission gate:
Ask Britton before wiring Codex into dashboard or /coding.

## Increment 10.8.5: Source Proxy API route for Codex adapter

Goal:
Expose Codex worker runs through Source Proxy in a controlled dry-run/proposal route.

Files likely touched:
- source_proxy/api/codex_adapter.py or source_proxy/api/workspace_tools.py
- source_proxy/main.py
- src/app/v1/coding/codex/route.ts or equivalent Next bridge
- source_proxy/tests/test_codex_cli_adapter.py
- source_proxy/tests/test_source_proxy_end_to_end.py
- src/components/coding/CodingAgentInterface.tsx, only if minimal status display needed

Implementation notes:
Route should accept:
- task
- target_file
- allowed_files
- mode: readonly or proposal
- sandbox_policy
- timeout_seconds

Route must reject:
- mode apply
- mode commit
- mode push
- missing allowed_files for proposal mode
- dangerous sandbox
- outside-root target
- secret-shaped path
- protected path

Manual checks:
cd ~/SpiritOS

PYTHONPATH=. python3 -m pytest \
  source_proxy/tests/test_codex_cli_adapter.py \
  source_proxy/tests/test_source_proxy_end_to_end.py

curl -s -X POST http://localhost:3000/v1/coding/codex \
  -H 'Content-Type: application/json' \
  -d '{
    "mode": "readonly",
    "task": "Summarize the proxy runner safety contract.",
    "allowed_files": [],
    "target_file": null
  }' | jq .

git status --short

Expected outputs:
- readonly request returns captured evidence or config-blocked
- proposal request requires allowed_files
- unsafe targets are rejected
- no apply/commit/push
- git status has no surprise changes

Debug if failed:
- If 500 error, inspect bridge route and Python API route.
- If target validation missing, reuse TaskSpec/path safety.
- If unsafe mode is accepted, add route-level enum validation.
- If response too large, add truncation.

Rollback:
git restore source_proxy/api source_proxy/main.py src/app/v1/coding source_proxy/tests src/components/coding

Next step:
Proceed to Phase 10.9.

Permission gate:
Ask Britton before UI controls are enabled.

# Phase 10.9: Codex Task Packet and Evidence Capture

Goal:
Make every Codex run produce a structured task packet that Cartographer and Source Proxy can understand.

## Increment 10.9.1: Codex TaskSpec packet

Goal:
Standardize what Codex receives.

Files likely touched:
- source_proxy/codex/task_packet.py
- source_proxy/planning/plan.py
- source_proxy/decision/prompt_packet.py
- source_proxy/tests/test_prompt_packet_context_metadata.py
- source_proxy/tests/test_codex_cli_adapter.py
- docs/codex-cli-adapter-plan.md

Implementation notes:
Task packet fields:
- task_id
- task_summary
- target_file
- allowed_files
- forbidden_files
- current_branch
- current_head
- relevant_files
- manual checks required
- expected output format
- no approve/apply/commit/push rule
- rollback instruction
- max scope

The packet should explicitly tell Codex:
- produce changes only inside allowed files
- do not commit
- do not push
- do not touch secrets
- report tests run
- report files changed
- stop if target is ambiguous

Manual checks:
cd ~/SpiritOS

PYTHONPATH=. python3 -m pytest \
  source_proxy/tests/test_prompt_packet_context_metadata.py \
  source_proxy/tests/test_codex_cli_adapter.py

python - <<'PY'
from source_proxy.codex.task_packet import build_codex_task_packet
print(build_codex_task_packet(
    task="Append one docs sentence",
    target_file="docs/phase-8-manual-check.md",
    allowed_files=["docs/phase-8-manual-check.md"],
))
PY

Expected outputs:
- packet includes target and allowed_files
- packet includes safety boundaries
- packet includes manual checks
- packet does not include secret contents
- packet is deterministic enough for tests

Debug if failed:
- If packet misses allowed_files, block.
- If packet includes too much repo context, trim.
- If packet changes between runs for no reason, stabilize ordering.
- If old UI memory contaminates packet, clear stale focus.

Rollback:
git restore source_proxy/codex source_proxy/planning source_proxy/decision source_proxy/tests docs/codex-cli-adapter-plan.md

Next step:
Proceed to Increment 10.9.2.

Permission gate:
Ask Britton before sending full repo context to Codex.

## Increment 10.9.2: Evidence artifact model

Goal:
Save what Codex did in a way the dashboard can replay.

Files likely touched:
- source_proxy/codex/evidence.py
- source_proxy/tasks/long_running.py
- source_proxy/tests/test_codex_cli_adapter.py
- src/components/coding/CodingAgentInterface.tsx
- docs/codex-cli-adapter-plan.md

Implementation notes:
Evidence artifact fields:
- task_id
- worker: codex_cli
- command
- sandbox
- started_at
- finished_at
- exit_code
- final_message_excerpt
- stdout_excerpt
- stderr_excerpt
- json_event_count
- changed_files_before
- changed_files_after
- diff_stat
- diff_excerpt
- head_before
- head_after
- safety_verdict
- recommendation
- rollback_hint

Manual checks:
cd ~/SpiritOS

PYTHONPATH=. python3 -m pytest source_proxy/tests/test_codex_cli_adapter.py

# Run one readonly task and inspect artifact:
PYTHONPATH=. python3 -m source_proxy.codex.adapter --dry-run-readonly "List the safety boundaries in docs/proxy-test-runner-plan.md."

find source_proxy -path '*codex*' -o -path '*artifacts*' | head

git status --short

Expected outputs:
- artifact is created only in approved artifact location
- artifact does not contain full secrets
- HEAD unchanged
- changed files are none for readonly task
- dashboard or CLI can print the evidence summary

Debug if failed:
- If artifact path is not ignored or approved, choose a better evidence location.
- If artifact includes too much output, truncate and store references.
- If changed files are wrong, inspect git status parser.
- If HEAD changed, block.

Rollback:
Delete test artifacts only after review.
Revert code files if needed.

Next step:
Proceed to Increment 10.9.3.

Permission gate:
Ask Britton before dashboard replay UI is patched.

## Increment 10.9.3: Dashboard evidence view

Goal:
Show Codex worker activity without turning it into an apply button.

Files likely touched:
- src/components/coding/CodingAgentInterface.tsx
- src/components/coding/SpiritToolActivityCards.tsx or equivalent
- src/app/v1/coding/codex/route.ts
- src/components/coding/__tests__/*
- source_proxy/tests/test_codex_cli_adapter.py

Implementation notes:
Display:
- worker
- task ID
- status
- target file
- changed files
- safety verdict
- diff available
- tests run
- recommendation
- approval state

Do not add apply control in this increment.
Do not add commit or push controls.

Manual checks:
cd ~/SpiritOS

npx vitest run src/components/coding/__tests__/coding-workflow-step.test.ts
PYTHONPATH=. python3 -m pytest source_proxy/tests/test_codex_cli_adapter.py
git diff --check

Open /coding:
- run or load a Codex readonly evidence packet
- confirm evidence appears
- confirm no apply button appears from Codex evidence alone

Expected outputs:
- UI shows Codex evidence
- approval remains separate
- no accidental action buttons
- tests pass
- no horizontal layout break

Debug if failed:
- If UI confuses proposal with approval, fix labels.
- If evidence is too noisy, collapse stdout/stderr under advanced.
- If mobile layout breaks, reduce card width.
- If test warnings appear but tests pass, classify separately.

Rollback:
git restore src/components/coding src/app/v1/coding source_proxy/tests

Next step:
Proceed to Phase 10.10.

Permission gate:
Ask Britton before adding any apply path to Codex-created proposals.

# Phase 10.10: Real Task Trial

Goal:
Run 5 to 10 real coding tasks through Codex under Source Proxy and measure reliability.

Do not start with high-risk files.
Do not touch approval, apply, commit, push, secrets, sandbox, or path safety code until the trial is proven.

## Increment 10.10.1: Trial task list

Goal:
Choose safe tasks before running Codex.

Files likely touched:
- docs/codex-cli-adapter-plan.md
- docs/codex-real-task-trial.md
- optional _blueprints/runbooks/codex_adapter_manual_checks.md

Implementation notes:
Create a task list with risk levels.

Suggested first 10 tasks:

1. Docs-only wording fix in docs/phase-8-manual-check.md
2. Add one runner doc note to docs/proxy-test-runner-plan.md
3. Add one test for Codex command denylist
4. Add one test for missing Codex binary config-blocked state
5. Add one UI test for Codex evidence card labels
6. Add one dashboard copy fix, no logic change
7. Add one README run command section for Codex adapter
8. Add one adapter artifact truncation test
9. Add one safe no-op route validation test
10. Add one docs-only rollback runbook note

Manual checks:
Review each task and classify:
- target file
- allowed files
- risk
- expected tests
- rollback command

Expected outputs:
- 5 to 10 tasks listed
- each task has allowed_files
- each task has rollback
- no high-risk files included at first

Debug if failed:
- If a task touches too many areas, split it.
- If allowed files are vague, rewrite task.
- If rollback is unclear, do not run it.
- If tests are unclear, add a manual check first.

Rollback:
Docs-only rollback:
git restore docs/codex-real-task-trial.md docs/codex-cli-adapter-plan.md

Next step:
Proceed to Increment 10.10.2.

Permission gate:
Ask Britton before running Task 1.

## Increment 10.10.2: Run first 3 safe tasks

Goal:
Prove Codex can complete small tasks without safety drift.

Files likely touched:
Varies by approved task, but docs/tests only.

Implementation notes:
For each task:
- capture before git status
- run Codex through adapter
- inspect changed files
- run required tests
- capture evidence artifact
- review Source Proxy recommendation
- do not commit until all 3 are reviewed

Manual checks for each task:
cd ~/SpiritOS

git status --short
git rev-parse --short HEAD

# Run task through Source Proxy Codex adapter.

git diff --stat
git diff --check
git status --short

# Run task-specific tests.

Expected outputs:
- task changes only allowed files
- tests pass
- no approval/apply/commit/push bypass
- evidence artifact created
- rollback hint present
- HEAD unchanged until commit approval

Debug if failed:
- If extra files changed, restore and tighten packet.
- If Codex ignores target, improve TaskSpec.
- If tests fail, ask Codex for fix only inside allowed files.
- If Codex times out, reduce task size.

Rollback:
git restore <changed-files>

Next step:
Proceed to Increment 10.10.3 after 3 clean tasks.

Permission gate:
Ask Britton before committing the first 3-task batch.

## Increment 10.10.3: Run tasks 4 to 7

Goal:
Test slightly broader tasks while staying out of high-risk code.

Files likely touched:
- docs/*
- source_proxy/tests/*
- src/components/coding/__tests__/*
- maybe source_proxy/codex/* if adapter tests require small fixes

Implementation notes:
Keep each task small.
One task per run.
No high-risk files yet.

Manual checks:
Same as Increment 10.10.2, plus:
PYTHONPATH=. python3 -m pytest source_proxy/tests/test_codex_cli_adapter.py
npx vitest run src/components/coding/__tests__/coding-workflow-step.test.ts
git diff --check

Expected outputs:
- 4 more tasks completed or intentionally rejected
- at least 5 total successful real tasks
- failure modes are understandable
- no safety boundary violation

Debug if failed:
- If multiple tasks fail from same reason, stop and patch adapter.
- If failures are mostly prompt quality, refine TaskSpec packet.
- If failures are runtime, improve timeout/output capture.
- If UI tests flake, isolate UI changes from adapter work.

Rollback:
git restore <changed-files>
Delete only test evidence artifacts after review.

Next step:
Proceed to Increment 10.10.4.

Permission gate:
Ask Britton before task 8 or any adapter code refactor.

## Increment 10.10.4: Trial closeout report

Goal:
Decide whether Codex adapter is stable enough to become the default coding worker.

Files likely touched:
- docs/codex-real-task-trial.md
- docs/codex-cli-adapter-plan.md
- optional _blueprints/runbooks/codex_adapter_manual_checks.md

Implementation notes:
Report:
- task count
- success count
- failure count
- timeout count
- extra-file violations
- tests run
- average run time
- common failure reasons
- recommended defaults
- blocked modes
- next phase recommendation

Manual checks:
cd ~/SpiritOS

git status --short
git diff --stat
git diff --check

PYTHONPATH=. python3 -m pytest source_proxy/tests/test_codex_cli_adapter.py
PYTHONPATH=. python3 -m source_proxy.testing.self_tests --suite phase-4e-safety-seed

Expected outputs:
- trial report exists
- no safety regression
- no unapproved apply/commit/push
- recommendation says promote, continue trial, or block

Debug if failed:
- If report is vague, add table with task-by-task evidence.
- If safety seed fails, block promotion.
- If too many tasks failed, keep Codex as experimental.
- If Codex created clutter, add cleanup classification before proceeding.

Rollback:
git restore docs/codex-real-task-trial.md docs/codex-cli-adapter-plan.md _blueprints/runbooks/codex_adapter_manual_checks.md

Next step:
Proceed to Phase 10.11 only if at least 5 real tasks are clean.

Permission gate:
Ask Britton before promoting Codex to default worker.

# Phase 10.11: Cartographer and Blueprinter Integration

Goal:
Make Cartographer understand Codex-created work as tracked project progress.

Codex does work.
Source Proxy verifies work.
Cartographer records work.
Blueprinter updates system memory.
Britton approves authority changes.

## Increment 10.11.1: Cartographer sees Codex task evidence

Goal:
Cartographer should display Codex task results without gaining apply/commit/push authority.

Files likely touched:
- source_proxy/cartographer/change_scribe.py
- source_proxy/cartographer/audit_trail.py
- source_proxy/cartographer/project_health.py
- source_proxy/api/cartographer.py
- src/components/dashboard/HomelabCartographerWidget.tsx
- source_proxy/tests/test_cartographer_api.py

Implementation notes:
Cartographer summary should include:
- latest Codex task IDs
- changed files
- component mapping
- risk labels
- tests run
- whether proposal is pending review
- whether commit proposal is needed

Manual checks:
cd ~/SpiritOS

curl -s http://localhost:3000/v1/cartographer/project-health | jq .
curl -s http://localhost:3000/v1/cartographer/audit-trail | jq .
git status --short

Expected outputs:
- Codex-created dirty files are visible
- risk labels appear
- commit proposal may be suggested
- no commit created
- no push created

Debug if failed:
- If Codex evidence missing, inspect artifact indexing.
- If risk label wrong, patch component mapper.
- If commit proposal appears too soon, require stable checks first.
- If dashboard says applied incorrectly, fix labels.

Rollback:
git restore source_proxy/cartographer source_proxy/api/cartographer.py src/components/dashboard source_proxy/tests

Next step:
Proceed to Increment 10.11.2.

Permission gate:
Ask Britton before enabling any Cartographer action based on Codex evidence.

## Increment 10.11.2: Blueprinter receives trial summary

Goal:
Update blueprints only through proposal flow.

Files likely touched:
- _blueprints/current/*
- _blueprints/components/*
- _blueprints/runbooks/*
- source_proxy/cartographer/blueprint_scribe.py
- source_proxy/cartographer/proposals.py
- source_proxy/tests/test_cartographer_api.py

Implementation notes:
Blueprinter should propose updates like:
- Codex adapter added
- evidence capture added
- known limitations
- runbook commands
- manual checks

Proposal-only.
No direct write unless approved.

Manual checks:
cd ~/SpiritOS

curl -s http://localhost:3000/v1/cartographer/blueprint-scribe | jq .
curl -s http://localhost:3000/v1/cartographer/proposals | jq .
git status --short

Expected outputs:
- blueprint update proposal created or previewed
- status is pending_review
- no files applied
- no commit
- no push

Debug if failed:
- If it writes directly, block and revert.
- If proposal lacks changed files, patch preview.
- If proposal targets wrong blueprint, improve component mapping.
- If proposal repeats duplicate, improve dedupe.

Rollback:
git restore _blueprints source_proxy/cartographer source_proxy/tests

Next step:
Proceed to Increment 10.11.3.

Permission gate:
Ask Britton before applying any blueprint proposal.

## Increment 10.11.3: Commit readiness gate

Goal:
Prepare a clean commit group after Codex adapter trial.

Files likely touched:
Git index only after approval.

Implementation notes:
Commit group should separate:
- adapter code
- tests
- docs
- evidence logs

Do not mix high-risk future AionUI work into this commit.

Manual checks:
cd ~/SpiritOS

git status --short
git diff --stat
git diff --check
PYTHONPATH=. python3 -m source_proxy.testing.self_tests --suite phase-4e-safety-seed
PYTHONPATH=. python3 -m pytest source_proxy/tests/test_codex_cli_adapter.py

Expected outputs:
- clear commit proposal
- no safety failures
- no whitespace errors
- no unreviewed files

Debug if failed:
- If commit group too broad, split it.
- If tests fail, stop and fix before staging.
- If dirty evidence is noisy, decide include/exclude.
- If status includes generated artifacts, add ignore or cleanup.

Rollback:
git restore --staged .
Do not delete evidence until reviewed.

Next step:
Commit only after approval.

Permission gate:
Ask Britton before commit and again before push.

# Phase 11.0: Open-Source Reference Study

Goal:
Study AionUI and adjacent tools after Codex adapter is real, not before.

This phase is research and comparison only.
No production integration yet.

## Increment 11.0.1: AionUI local evaluation spike

Goal:
Understand what AionUI does better than SpiritOS without handing it your repo authority.

Files likely touched:
- docs/aionui-reference-study.md
- optional screenshots or notes outside repo
- no source code expected

Implementation notes:
Install AionUI separately.
Do not point it at SpiritOS with write authority first.
Test with a toy repo.
Observe:
- multi-agent workspace
- Codex detection
- Claude Code detection
- Goose/OpenCode detection
- task queue
- scheduled tasks
- file write flow
- approval flow
- logs/events
- remote access
- phone notifications
- whether actions are replayable
- whether diffs are reviewable

Manual checks:
Create a toy repo:

mkdir -p ~/aionui-toy-repo
cd ~/aionui-toy-repo
git init
echo "# Toy" > README.md
git add README.md
git commit -m "init toy repo"

In AionUI:
- open toy repo
- run one docs edit task
- inspect whether diff is shown
- inspect whether approval is required
- inspect logs
- inspect changed files

Terminal:
cd ~/aionui-toy-repo
git status --short
git diff --stat
git log --oneline -3

Expected outputs:
- AionUI behavior documented
- no SpiritOS repo changes
- strengths and gaps listed
- no conclusion to integrate yet

Debug if failed:
- If AionUI requires more setup, document setup friction.
- If it writes without clear approval, mark as unsafe for direct SpiritOS use.
- If logs are not extractable, mark as UI inspiration only.
- If it handles multi-agent queues well, mark for Spirit Cowork Console reference.

Rollback:
Delete toy repo if needed:
rm -rf ~/aionui-toy-repo

Next step:
Proceed to Increment 11.0.2.

Permission gate:
Ask Britton before opening SpiritOS inside AionUI.

## Increment 11.0.2: Compare AionUI, Codex App, Continue, Cline, Goose, OpenCode

Goal:
Decide what SpiritOS should borrow.

Files likely touched:
- docs/agent-wrapper-reference-study.md
- _blueprints/proposals/spirit-cowork-console.md, proposal only

Implementation notes:
Comparison categories:
- multi-agent support
- repo context
- task queue
- approval UX
- sandbox model
- diff review
- test running
- logs and replay
- branch/worktree support
- commit/push governance
- mobile or remote controls
- scheduled tasks
- local model support
- MCP or tool protocol support
- integration complexity
- risk level

Manual checks:
Create a table:

Tool | Best idea to borrow | Risk | SpiritOS equivalent | Decision

Expected outputs:
- AionUI: reference for multi-agent cowork workspace
- Codex App: reference for parallel threads, worktrees, review pane
- Continue: reference for repo-defined checks
- Cline: reference for Plan/Act and JSON/headless workflows
- Goose: reference for permission modes and skills
- OpenCode: reference for provider-agnostic terminal agent behavior
- SpiritOS: remains system of record

Debug if failed:
- If research becomes too broad, limit to 6 tools.
- If feature claims are unclear, cite official docs only.
- If tool is unstable, mark as watchlist.
- If two tools solve same problem, pick one reference pattern.

Rollback:
git restore docs/agent-wrapper-reference-study.md _blueprints/proposals/spirit-cowork-console.md

Next step:
Proceed to Increment 11.0.3.

Permission gate:
Ask Britton before proposing Spirit Cowork Console.

## Increment 11.0.3: Gap report

Goal:
Identify what SpiritOS still lacks after Codex adapter trial.

Files likely touched:
- docs/spirit-cowork-gap-report.md
- _blueprints/proposals/spirit-cowork-console.md

Implementation notes:
Gap categories:
- worker orchestration
- task queue
- multi-agent UI
- agent comparison
- live logs
- replay
- artifact shelf
- mobile controls
- notifications
- scheduling
- model fallback
- cost tracking
- rollback UX
- cross-project onboarding

Manual checks:
Review actual Codex adapter trial results.
Review AionUI reference notes.
Review dashboard/coding UI.

Expected outputs:
- clear list of missing SpiritOS capabilities
- clear list of things SpiritOS already does better
- recommendation: build, borrow, integrate, or wait

Debug if failed:
- If recommendations are vague, add scoring.
- If gap is not backed by trial evidence, mark as speculative.
- If everything looks urgent, split by risk and value.
- If UI gaps dominate, avoid backend changes.

Rollback:
git restore docs/spirit-cowork-gap-report.md _blueprints/proposals/spirit-cowork-console.md

Next step:
Proceed to Phase 11.1 only if gaps justify it.

Permission gate:
Ask Britton before any AionUI wrapper or Spirit Cowork Console build.

# Phase 11.1: Spirit Cowork Console MVP

Goal:
Build your own AionUI-inspired multi-agent workspace only after Codex adapter and gap report prove the need.

This is not an AionUI clone.
This is the SpiritOS command center for safe workers.

## Increment 11.1.1: Cowork Console read-only shell

Goal:
Create a read-only workspace that shows agents and tasks.

Files likely touched:
- src/app/cowork/page.tsx
- src/components/cowork/SpiritCoworkConsole.tsx
- src/components/cowork/AgentWorkerCard.tsx
- src/components/cowork/TaskQueuePanel.tsx
- src/app/v1/cowork/status/route.ts
- source_proxy/api/agent_workers.py
- source_proxy/tests/test_agent_registry.py
- src/components/cowork/__tests__/*

Implementation notes:
Show:
- Codex CLI worker
- local model worker
- Scout
- Cartographer
- Blueprinter
- Runner
- status
- capability
- last task
- current authority level
- allowed actions
- forbidden actions

Read-only only.

Manual checks:
cd ~/SpiritOS

npm run typecheck 2>/dev/null || npx tsc --noEmit
npx vitest run src/components/cowork
PYTHONPATH=. python3 -m pytest source_proxy/tests/test_agent_registry.py
git diff --check

Open:
https://localhost:3000/cowork

Expected outputs:
- cowork page loads
- workers visible
- authority levels visible
- no run button yet
- no apply/commit/push controls

Debug if failed:
- If route breaks app shell, isolate page.
- If mobile layout breaks, stack cards.
- If worker status is stale, show last_checked_at.
- If authority labels are confusing, copy from agent registry.

Rollback:
git restore src/app/cowork src/components/cowork src/app/v1/cowork source_proxy/api/agent_workers.py source_proxy/tests/test_agent_registry.py

Next step:
Proceed to Increment 11.1.2.

Permission gate:
Ask Britton before adding task start controls.

## Increment 11.1.2: Task start proposal only

Goal:
Let Cowork Console create a task proposal, not run it automatically.

Files likely touched:
- src/components/cowork/TaskComposer.tsx
- src/app/v1/cowork/tasks/route.ts
- source_proxy/tasks/long_running.py
- source_proxy/planning/architect.py
- source_proxy/tests/test_long_running_tasks.py
- src/components/cowork/__tests__/*

Implementation notes:
Task composer creates:
- draft task
- suggested worker
- target file
- allowed files
- manual checks
- risk label

It does not run Codex until Britton approves.

Manual checks:
Open /cowork:
- enter a docs-only task
- choose Codex worker
- submit as draft
- confirm task appears as pending approval
- confirm no files changed

Terminal:
git status --short
curl -s http://localhost:3000/v1/cowork/tasks | jq .

Expected outputs:
- draft task exists
- no Codex run yet
- no file changes
- no approval bypass

Debug if failed:
- If task starts immediately, block.
- If allowed_files missing, require target resolution first.
- If risk label missing, reuse component mapper.
- If draft disappears on refresh, persist through existing task memory.

Rollback:
git restore src/components/cowork src/app/v1/cowork source_proxy/tasks source_proxy/planning source_proxy/tests

Next step:
Proceed to Increment 11.1.3.

Permission gate:
Ask Britton before enabling run-approved-task.

## Increment 11.1.3: Run approved Codex worker from Cowork Console

Goal:
Trigger Codex adapter from UI only after explicit approval.

Files likely touched:
- src/components/cowork/TaskQueuePanel.tsx
- src/app/v1/cowork/tasks/[taskId]/run-approved/route.ts
- source_proxy/api/long_running_tasks.py
- source_proxy/codex/adapter.py
- source_proxy/tests/test_long_running_tasks.py
- src/components/cowork/__tests__/*

Implementation notes:
Run button appears only when:
- task has target
- allowed_files set
- risk acceptable
- approval explicitly recorded
- worker is available
- sandbox policy safe

Manual checks:
Open /cowork:
- create docs-only task
- approve run
- click run
- watch task status
- inspect evidence

Terminal:
git status --short
git diff --stat
git diff --check
git rev-parse --short HEAD

Expected outputs:
- Codex runs only after approval
- evidence appears
- changed files match allowed_files
- HEAD unchanged
- no commit
- no push

Debug if failed:
- If run starts before approval, block.
- If changed files exceed allowed_files, restore and tighten adapter.
- If task status gets stuck, inspect long-running stream.
- If UI hides failure, patch error display.

Rollback:
git restore <changed-files>
git restore src/components/cowork src/app/v1/cowork source_proxy/api source_proxy/codex source_proxy/tests

Next step:
Proceed to Increment 11.1.4.

Permission gate:
Ask Britton before adding multi-worker team tasks.

## Increment 11.1.4: Multi-worker reference mode

Goal:
Show how multiple workers could collaborate without letting them all write.

Files likely touched:
- src/components/cowork/MultiWorkerPlanPanel.tsx
- source_proxy/agents/registry.py
- source_proxy/planning/reviewer.py
- source_proxy/tests/test_agent_registry.py
- src/components/cowork/__tests__/*

Implementation notes:
Initial roles:
- Architect: plan only
- Codex: propose code changes
- Reviewer: inspect diff
- Tester: recommend tests
- Cartographer: record project state
- Scout: external research only
- Blueprinter: propose doc updates

Only Codex may produce a file-change proposal.
No worker may approve, apply, commit, or push.

Manual checks:
Create a multi-worker task:
- ask Architect to plan
- ask Codex to propose
- ask Reviewer to review
- ask Tester to suggest checks
- confirm only one proposal exists
- confirm no automatic apply

Expected outputs:
- timeline shows each worker action
- only approved worker produces diff
- no authority escalation
- no duplicated proposals

Debug if failed:
- If multiple workers edit, restrict write-capable roles.
- If Scout writes, block Scout write path.
- If Reviewer edits, force reviewer to verdict-only.
- If timeline confusing, simplify labels.

Rollback:
git restore src/components/cowork source_proxy/agents source_proxy/planning source_proxy/tests

Next step:
Proceed to Phase 11.2.

Permission gate:
Ask Britton before any autonomous multi-agent work.

# Phase 11.2: AionUI Decision Gate

Goal:
Make a real decision about AionUI after SpiritOS has its own Codex worker and Cowork Console baseline.

## Increment 11.2.1: Decide integration posture

Goal:
Choose one of four paths.

Options:
1. Ignore AionUI for now.
2. Borrow UX ideas only.
3. Use AionUI as an external launcher for non-SpiritOS toy tasks.
4. Build a controlled integration bridge later.

Do not choose option 4 unless AionUI exposes logs/events/control points that Source Proxy can verify.

Files likely touched:
- docs/aionui-decision.md
- _blueprints/proposals/aionui-integration-posture.md

Manual checks:
Review:
- Codex adapter trial report
- AionUI spike notes
- Cowork Console MVP
- gap report

Expected outputs:
- one option chosen
- reason documented
- risks listed
- no code integration yet

Debug if failed:
- If decision is emotional, return to evidence table.
- If AionUI has no clean event API, choose UX-only.
- If SpiritOS already covers the needed feature, skip integration.
- If AionUI’s write model is too broad, do not connect real repos.

Rollback:
git restore docs/aionui-decision.md _blueprints/proposals/aionui-integration-posture.md

Next step:
Proceed only if integration is justified.

Permission gate:
Ask Britton before any AionUI bridge.

## Increment 11.2.2: Optional AionUI bridge research only

Goal:
Determine whether AionUI can be observed safely by SpiritOS.

Files likely touched:
- docs/aionui-bridge-research.md
- no production code expected

Implementation notes:
Look for:
- CLI invocation support
- task event logs
- file change logs
- MCP/ACP compatibility
- local database
- exported conversation history
- approval events
- safe external API

No credentials.
No real repo writes.
No bridge code yet.

Manual checks:
Use toy repo only.
Run one AionUI task.
Inspect whether there are logs or events.
Confirm changed files via git.

Expected outputs:
- bridge possible, bridge not possible, or not worth it
- no SpiritOS changes
- no real repo risk

Debug if failed:
- If logs unavailable, classify as UI-only reference.
- If data format unstable, do not build bridge.
- If it requires broad permissions, stop.
- If it duplicates SpiritOS, skip.

Rollback:
Delete research notes only if needed.

Next step:
Either stop AionUI work or draft a later bridge plan.

Permission gate:
Ask Britton before any production integration.

# Release gates

## Gate A: Phase 10.7 package ready

Required:
- typecheck pass
- diff check pass
- test_proxy_runner.py pass
- Phase 4F closeout pass
- safety seed pass
- Cartographer soak pass
- expected dirty tree only
- evidence selected
- no final pull without clean diag

## Gate B: Codex adapter ready

Required:
- Codex capability probe works
- safe command envelope tests pass
- readonly live run works
- docs-only proposal works
- dangerous flags blocked
- output captured
- changed files captured
- HEAD unchanged unless explicitly expected
- no apply/commit/push

## Gate C: Real-task trial ready

Required:
- at least 5 real tasks attempted
- at least 5 clean successes or documented failures
- no safety boundary breach
- no extra-file edits accepted
- failures are actionable
- trial report exists

## Gate D: Cowork Console ready

Required:
- read-only worker dashboard exists
- task proposal flow exists
- approved run flow exists
- evidence visible
- no multi-worker automatic writes
- no apply/commit/push controls added accidentally

## Gate E: AionUI decision ready

Required:
- AionUI tested on toy repo
- reference comparison complete
- SpiritOS gap report complete
- decision documented
- no wrapper built before evidence

# Immediate next action

Do not start AionUI wrapper.

Next immediate engineering move:

Phase 10.7.1:
Select package evidence.

Then:
Phase 10.7.2:
Run final package diagnostic.

Then:
Phase 10.7.3:
Commit 10.7 package after approval.

Then:
Phase 10.8.1:
Codex CLI capability probe.

# First prompt to Codex after package commit

Use this only after Phase 10.7 commit is complete:

Work in ARPA mode:
Analyze the current repo and Phase 10.7 package state first.
Research the existing Source Proxy runner, safety path validation, long-running task system, and tool manifest.
Plan the change.
Ask permission before patching.
Do not commit.
Do not push.
Do not approve, apply, or execute any workflow.

Task:
Prepare Phase 10.8.1 only: Codex CLI capability probe.

Goal:
Add a read-only capability probe that tells Source Proxy whether Codex CLI is available and what safe execution features appear usable.

Strict boundaries:
- Do not run a live Codex task yet.
- Do not edit files outside the planned probe/test/docs files.
- Do not add apply, commit, push, or approval authority.
- Do not use dangerous Codex flags.
- Do not touch Scout, Cartographer apply, commit, push, approval gate, secrets, or sandbox authority.

Files to inspect:
- source_proxy/testing/runner.py
- source_proxy/api/self_status.py
- source_proxy/api/tools_manifest.py
- source_proxy/agents/registry.py
- source_proxy/tests/test_self_status.py
- source_proxy/tests/test_workspace_tools.py
- source_proxy/tests/test_agent_registry.py
- docs/proxy-test-runner-plan.md

Files likely touched:
- source_proxy/codex/adapter.py or source_proxy/codex_cli/adapter.py
- source_proxy/codex/__init__.py if needed
- source_proxy/tests/test_codex_cli_adapter.py
- source_proxy/api/tools_manifest.py or source_proxy/api/self_status.py
- docs/codex-cli-adapter-plan.md

Required behavior:
- Detect whether codex binary exists.
- Detect codex version if available.
- Return config_blocked instead of crashing when codex is missing.
- Report safe supported/expected features:
  - exec
  - json events
  - output-last-message
  - output-schema
  - profile
  - sandbox read-only
  - sandbox workspace-write
- Report dangerous modes as blocked:
  - danger-full-access
  - yolo
  - dangerously-bypass-approvals-and-sandbox
- Do not run a Codex task.
- Do not mutate repo files except the intentional patch files.
- Do not approve, apply, commit, or push.

Manual checks after patch:
cd ~/SpiritOS

which codex || true
codex --version || true

PYTHONPATH=. python3 -m pytest source_proxy/tests/test_codex_cli_adapter.py

PYTHONPATH=. python3 -m pytest \
  source_proxy/tests/test_self_status.py \
  source_proxy/tests/test_workspace_tools.py \
  source_proxy/tests/test_agent_registry.py

npm run typecheck 2>/dev/null || npx tsc --noEmit

git diff --check
git status --short

Expected outputs:
- tests pass
- missing codex returns config_blocked, not crash
- installed codex returns detected true and version
- dangerous flags are blocked in tests
- no Codex live task runs
- no approve/apply/commit/push happens
- only intended files change

Debug if failed:
- If import fails, isolate Codex adapter from optional runtime dependencies.
- If codex not found crashes the API, catch FileNotFoundError.
- If version parsing is brittle, return raw_version plus parsed_version optional.
- If dangerous flags pass through, add denylist tests before implementation.
- If tests mutate repo state, move to temp dirs.

Rollback:
git restore source_proxy/codex source_proxy/api/tools_manifest.py source_proxy/api/self_status.py source_proxy/tests/test_codex_cli_adapter.py docs/codex-cli-adapter-plan.md

Before patching, return:
- Current diagnosis
- Exact files proposed
- Implementation plan
- Manual checks
- Expected outputs
- Risks
- Rollback
- Ask: "Do you want me to implement Phase 10.8.1 now?"