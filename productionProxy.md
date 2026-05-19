# Master Plan: Source Proxy Production Hardening and Remote-Usable Operator Console

Status date: 2026-05-17
Owner: Britton
Scope: Source Proxy, Codex CLI worker, Cartographer, Blueprinter, /coding UI, remote manual-check workflow
Current grade: 7/10
Current label: working beta
Target label: production-hardening beta, then internal daily-use alpha

## Executive Verdict

Source Proxy is not broken. It is in working beta.

The core safety model is strong:
- approval, apply, commit, and push are separated
- Codex evidence is proposal-only
- protected paths and traversal are blocked
- Python safety suites pass
- Codex CLI adapter tests pass
- Cartographer is working beta
- Blueprinter remains proposal-only

The blockers are mostly polish, operator clarity, stale-plan cleanup, live route validation, and UI readiness.

Codex CLI status:
Codex CLI is integrated as an experimental Source Proxy worker.
It is not default-promoted.
It must not get approve, apply, commit, or push authority.

Codex mobile status:
Codex mobile is now part of the remote workflow.
Use it to monitor, steer, answer questions, review diffs, and approve Codex-side actions when safe.
Do not treat Codex mobile as the SpiritOS trust boundary.
SpiritOS approval gates remain the authority.

## Non-negotiable Rules

1. Source Proxy remains the boss.
2. Codex CLI is a worker, not the system of record.
3. Codex mobile is a remote review/control surface, not the system of record.
4. Cartographer tracks and explains project state, but cannot bypass approval.
5. Blueprinter drafts proposals only.
6. Scout cannot trigger coding writes.
7. Approval does not equal apply.
8. Apply does not equal commit.
9. Commit does not equal push.
10. Push requires separate explicit approval.
11. No AionUi bridge now.
12. No Cowork Console now.
13. No autonomous multi-agent writes now.
14. No default Codex promotion until route validation, evidence replay, UI clarity, and governance checks pass.
15. Every increment must end with manual checks, expected outputs, debug path, rollback, and a permission gate.

## Deferred Until Later

Do not build these during this plan:
- AionUi bridge
- Spirit Cowork Console
- scheduled provider tasks
- native SpiritOS mobile execution
- multi-agent autonomous writes
- automatic commit/push
- provider marketplace
- broad MCP/plugin system
- default Codex promotion

These can return later after daily-use Source Proxy is boring and reliable.

---

# Release Gates

## Gate A: Baseline Reset Clean

Required:
- `proxyCLI.md` deletion is accepted or intentionally replaced by a new source-of-truth plan
- stale Phase 11 language is archived or clearly labeled historical
- `git diff --check` passes
- `npm run typecheck` passes
- safety suite passes
- dashboard failures are either fixed or documented as unrelated
- no fake continuation increments remain active

## Gate B: P0 Reliability Clean

Required:
- dashboard Vitest failures fixed
- live port 3000 route checks reliable
- `phase-4f-closeout` behavior clarified
- snapshot-writing diagnostics do not create confusing FAIL states
- fresh closeout report is readable and honest

## Gate C: Codex Worker Hardened

Required:
- Codex route validation tests pass
- evidence capture and replay are stable
- dangerous flags blocked
- protected/secret paths blocked
- `allowed_files` and `target_file` preserved
- live route is either safely enabled or cleanly config-blocked
- no approve/apply/commit/push authority

## Gate D: Remote Manual Checks Usable

Required:
- Codex mobile workflow documented
- remote manual checks can be done without RustDesk for common cases
- Termius/SSH fallback is documented
- mobile cannot bypass Source Proxy approval gates
- manual check packets are small enough to review on phone

## Gate E: Operator Console Usable

Required:
- task queue visible
- task state visible
- blockers visible
- evidence visible
- diff status visible
- tests visible
- approval state visible
- no accidental apply/commit/push controls

## Gate F: Daily-Use Alpha

Required:
- one-command closeout works
- happy path works end-to-end
- failed path is understandable
- rollback hints visible
- Cartographer explains repo state
- Codex can propose safely
- Britton can use desktop or mobile to review work confidently

---

# Phase 0: Baseline Reset After proxyCLI.md Deletion

Purpose:
Stop stale plans from confusing Codex. Establish the current repo and this new master plan as the working truth.

## Increment 0.1: Confirm proxyCLI.md Reset

Goal:
Make the repo explicitly recognize that `proxyCLI.md` was intentionally removed or retired.

Files likely touched:
- none for diagnostic
- later maybe `docs/source-proxy-current-plan.md`
- later maybe `README.md`
- later maybe `docs/plan-index.md`

Allowed actions:
- inspect repo
- inspect git status
- inspect stale references
- report findings

Forbidden actions:
- no patch
- no recreate `proxyCLI.md`
- no commit
- no push
- no cleanup yet

Manual checks:
```bash
cd ~/SpiritOS
git status --short
test -f proxyCLI.md && echo "proxyCLI exists" || echo "proxyCLI missing by reset"
grep -RIn "11.0.4\|Phase 11.1\|Phase 11.2\|Cowork Console\|AionUi bridge\|provider-layer implementation" docs *.md source_proxy src 2>/dev/null || trues

Expected outputs:

proxyCLI.md is missing or clearly retired
stale planning references are identified
no repo changes happen

Debug path:

If Codex treats missing proxyCLI.md as an error, tell it: "proxyCLI.md missing by user reset. Use current repo and docs as source of truth."
If stale docs look active, list them for Phase 0.2.

Rollback:

none, diagnostic only

Next step:
Proceed to Increment 0.2.

Permission gate:
Ask Britton before writing any replacement plan file.

Increment 0.2: Classify Stale Planning Docs

Goal:
Separate historical/reference docs from active plan docs.

Files likely touched:

docs/agent-wrapper-reference-study.md
docs/aionui-reference-study.md
docs/spirit-cowork-gap-report.md
cartographerBeta.md
maybe README or docs index later

Allowed actions:

read docs
classify each stale reference as historical, deferred, dangerous, or active
propose cleanup wording

Forbidden actions:

no cleanup patch yet
no deleting docs
no new roadmap
no AionUi or Cowork work

Manual checks:

cd ~/SpiritOS
grep -RIn "Next action\|Next step\|Phase 11\|Cowork Console\|AionUi bridge\|provider layer\|provider-layer" docs *.md source_proxy/testing/runner.py 2>/dev/null || true

Expected outputs:

a list of stale references
each reference classified
active-plan confusion identified

Debug path:

If a doc says "do not build," keep it but label it historical if Codex keeps misreading it.
If a doc says "next step: build," treat it as dangerous stale planning text.

Rollback:

none, diagnostic only

Next step:
Proceed to Increment 0.3.

Permission gate:
Ask Britton before rewriting or archiving any docs.

Increment 0.3: Establish New Plan Source of Truth

Goal:
Create one replacement master-plan document after Britton approves.

Files likely touched:

docs/source-proxy-production-hardening-plan.md
maybe README.md or docs/plan-index.md

Implementation notes:
The new doc should say:

proxyCLI.md is retired
this new plan is the active Source Proxy plan
Phase 11/Cowork/AionUi are deferred
Codex CLI is experimental worker only
Codex mobile is remote review/control only
approval/apply/commit/push remain separated

Manual checks:

cd ~/SpiritOS
grep -RIn "active Source Proxy plan" docs README.md 2>/dev/null || true
git diff -- docs/source-proxy-production-hardening-plan.md README.md docs/plan-index.md
git diff --check

Expected outputs:

one clear source-of-truth doc exists
old fake continuation path is not revived
no code changes

Debug path:

If Codex tries to recreate proxyCLI.md, stop.
If the doc includes new provider build work, remove it.
If it blurs deferred and active work, split those sections.

Rollback:

git restore docs/source-proxy-production-hardening-plan.md README.md docs/plan-index.md 2>/dev/null || true

Next step:
Proceed to Phase 1 after this doc is accepted.

Permission gate:
Ask Britton before writing the file.

Phase 1: P0 Reliability Cleanup

Purpose:
Clear current blockers before building UI polish.

Increment 1.1: Fix Dashboard Vitest Failures

Goal:
Resolve the two failing dashboard tests without changing product behavior unnecessarily.

Files likely touched:

src/components/dashboard/SpiritDashboardHome.tsx
src/components/dashboard/tests/SpiritDashboardHome.test.tsx
related dashboard components only if required

Allowed actions:

inspect test failures
patch component or test if expectation drift is real
run targeted tests

Forbidden actions:

no redesign
no unrelated dashboard styling
no Scout or Proxy behavior changes
no commit

Manual checks:

cd ~/SpiritOS
npx vitest run src/components/dashboard/__tests__/SpiritDashboardHome.test.tsx
npm run typecheck
git diff --check
git status --short

Expected outputs:

dashboard test passes
typecheck passes
diff is limited to dashboard files
no proxy safety files touched

Debug path:

If expectations are stale, update the test.
If UI behavior regressed, patch component.
If failures are from async/mock data, stabilize fixture.
If broad failures appear, stop and report.

Rollback:

git restore src/components/dashboard

Next step:
Proceed to Increment 1.2.

Permission gate:
Ask Britton before patching.

Increment 1.2: Make Port 3000 Route Checks Reliable

Goal:
Make live Next route checks useful instead of timing out or returning empty replies.

Files likely touched:

scripts/source-proxy-dev.mjs
src/app/v1/cartographer/_proxy.ts
src/app/v1/cartographer/status/route.ts
src/app/v1/cartographer/project-health/route.ts
docs/runbooks/source-proxy-dev.md, if created

Allowed actions:

inspect dev server logs
test HTTP and HTTPS route behavior
document correct startup command
patch only if route/proxy bug is found

Forbidden actions:

no broad route rewrite
no auth bypass
no disabling TLS safety permanently
no unrelated dashboard work

Manual checks:

cd ~/SpiritOS

npm run typecheck

curl -k -sS --max-time 15 https://localhost:3000/v1/cartographer/status | jq '.'
curl -k -sS --max-time 15 https://localhost:3000/v1/cartographer/project-health | jq '.'
curl -k -sS --max-time 15 https://localhost:3000/v1/self/status | jq '.'

git status --short

Expected outputs:

routes return JSON or a clear service-unavailable/config-blocked response
no empty reply
no hang
no misleading success

Debug path:

If Next is not running, document correct command.
If HTTPS cert issue, document HTTPS startup.
If Python proxy not running, return clean upstream error.
If route crashes, isolate route handler.

Rollback:

git restore scripts src/app/v1 docs

Next step:
Proceed to Increment 1.3.

Permission gate:
Ask Britton before patching route behavior.

Increment 1.3: Fix phase-4f-closeout Snapshot Confusion

Goal:
Stop expected snapshot writes from making closeout look like a real failure.

Files likely touched:

source_proxy/testing/runner.py
source_proxy/tests/test_proxy_runner.py
docs/proxy-test-runner-plan.md

Implementation notes:
The runner should distinguish:

true dirty unexpected changes
expected snapshot-only writes
generated evidence that needs review
real failure

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_proxy_runner.py
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile phase-4f-closeout
git status --short

Expected outputs:

runner reports expected snapshot writes clearly
no fake FAIL for expected evidence
real dirty tree still blocks
test_proxy_runner.py passes

Debug path:

If snapshot writes are expected but dirty, label as evidence_review_needed.
If runner hides real dirty files, revert.
If Scout logs cause unrelated failure, keep Scout failure separate from proxy failure.

Rollback:

git restore source_proxy/testing/runner.py source_proxy/tests/test_proxy_runner.py docs/proxy-test-runner-plan.md

Next step:
Proceed to Phase 2.

Permission gate:
Ask Britton before patching runner behavior.

Phase 2: Codex Experimental Worker Hardening

Purpose:
Make Codex CLI safer and clearer as a Source Proxy worker before any default promotion.

Increment 2.1: Codex Route Live-Execution Contract

Goal:
Define exactly when /v1/coding/codex should return config-blocked versus run a safe readonly/proposal task.

Files likely touched:

source_proxy/api/codex_adapter.py
src/app/v1/coding/codex/route.ts
source_proxy/tests/test_codex_cli_adapter.py
source_proxy/tests/test_source_proxy_end_to_end.py

Implementation notes:
The route must support:

config-blocked
readonly evidence run
proposal evidence run with allowed files
explicit blocked state for apply/commit/push

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest \
  source_proxy/tests/test_codex_cli_adapter.py \
  source_proxy/tests/test_source_proxy_end_to_end.py

curl -k -sS --max-time 20 https://localhost:3000/v1/coding/codex \
  -H 'Content-Type: application/json' \
  -d '{"mode":"readonly","task":"Summarize Source Proxy safety boundaries.","allowed_files":[],"target_file":null}' | jq '.'

git status --short

Expected outputs:

route returns evidence or config-blocked
no crash
no apply/commit/push
no changed files for readonly

Debug path:

If env flag missing, return config-blocked with exact reason.
If route accepts unsafe modes, add enum validation.
If response is too large, add truncation.

Rollback:

git restore source_proxy/api/codex_adapter.py src/app/v1/coding/codex/route.ts source_proxy/tests

Next step:
Proceed to Increment 2.2.

Permission gate:
Ask Britton before enabling live route execution.

Increment 2.2: Route-Level Safety Regression Pack

Goal:
Add route-level tests for unsafe targets and action bypass.

Files likely touched:

source_proxy/tests/test_codex_cli_adapter.py
source_proxy/tests/test_source_proxy_end_to_end.py
source_proxy/safety/paths.py only if a real gap appears
source_proxy/api/codex_adapter.py only if validation gap appears

Test cases:

.env
.env.local
certificates
path traversal
target mismatch
missing allowed_files
protected path inside allowed_files
apply mode rejected
commit mode rejected
push mode rejected
dangerous Codex flags rejected

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest \
  source_proxy/tests/test_codex_cli_adapter.py \
  source_proxy/tests/test_source_proxy_end_to_end.py \
  source_proxy/tests/test_diff_verification.py \
  source_proxy/tests/test_verification_contracts.py

git diff --check
git status --short

Expected outputs:

unsafe route inputs blocked
missing allowed_files blocked for proposal mode
no apply/commit/push path through Codex
tests pass

Debug path:

If safety function already exists, reuse it.
If route duplicates safety badly, centralize through existing path safety.
If test must be skipped due server env, add pure Python route unit coverage.

Rollback:

git restore source_proxy/tests source_proxy/api/codex_adapter.py source_proxy/safety/paths.py

Next step:
Proceed to Increment 2.3.

Permission gate:
Ask Britton before patching safety behavior.

Increment 2.3: Evidence Replay and Truncation

Goal:
Make Codex evidence readable, replayable, and safe to show in UI.

Files likely touched:

source_proxy/codex/evidence.py
source_proxy/codex/adapter.py
source_proxy/cartographer/codex_evidence.py
source_proxy/tests/test_codex_cli_adapter.py
src/components/coding/CodingAgentInterface.tsx, only if needed for display

Evidence fields:

task_id
worker
mode
command summary
sandbox
started_at
finished_at
exit_code
stdout excerpt
stderr excerpt
final message excerpt
changed files before
changed files after
diff stat
head before
head after
safety verdict
recommendation
rollback hint
truncation markers

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_codex_cli_adapter.py

PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.codex.evidence import summarize_codex_evidence
print("evidence summary import ok")
PY

git diff --check
git status --short

Expected outputs:

evidence can be summarized without giant logs
secrets are not exposed
truncation is explicit
HEAD and changed files are captured
no UI action authority added

Debug path:

If output is too large, reduce excerpts.
If evidence lacks rollback hint, derive from target files.
If secrets appear, add redaction tests.

Rollback:

git restore source_proxy/codex source_proxy/cartographer/codex_evidence.py source_proxy/tests src/components/coding

Next step:
Proceed to Increment 2.4.

Permission gate:
Ask Britton before adding UI replay.

Increment 2.4: Finish Remaining Codex Trial Tasks

Goal:
Run the remaining safe Codex hardening tasks without promoting Codex.

Likely tasks:

denylist regression
evidence artifact truncation regression
safe no-op route validation regression
rollback runbook note

Files likely touched:

source_proxy/tests/test_codex_cli_adapter.py
source_proxy/tests/test_source_proxy_end_to_end.py
docs/codex-real-task-trial.md
docs/proxy-test-runner-plan.md

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest \
  source_proxy/tests/test_codex_cli_adapter.py \
  source_proxy/tests/test_source_proxy_end_to_end.py

git diff --check
git status --short

Expected outputs:

at least one new hardening regression added
no promotion
no apply/commit/push
Codex remains experimental

Debug path:

If Codex changes extra files, block and restore.
If route validation exposes a real gap, patch only that gap.
If docs drift into new roadmap, remove roadmap language.

Rollback:

git restore source_proxy/tests docs/codex-real-task-trial.md docs/proxy-test-runner-plan.md

Next step:
Proceed to Phase 3.

Permission gate:
Ask Britton before running each real Codex task.

Phase 3: Remote Manual-Check Workflow With Codex Mobile

Purpose:
Use Codex mobile to reduce RustDesk/Termius juggling while keeping SpiritOS safety gates intact.

Increment 3.1: Define Remote Authority Rules

Goal:
Document what Codex mobile can and cannot do for SpiritOS.

Files likely touched:

docs/source-proxy-remote-manual-checks.md
docs/source-proxy-production-hardening-plan.md

Allowed through Codex mobile:

monitor Codex task status
answer Codex questions
review terminal output
review diffs
review test output
approve Codex-side safe commands when they are diagnostic or scoped
request Codex to run read-only checks

Forbidden through Codex mobile:

bypass Source Proxy
directly approve SpiritOS apply/commit/push outside gates
merge/push from Codex app as default workflow
broad file cleanup
secret edits
provider-layer implementation
Cowork/AionUi work

Manual checks:

cd ~/SpiritOS
git diff -- docs/source-proxy-remote-manual-checks.md docs/source-proxy-production-hardening-plan.md
git diff --check

Expected outputs:

remote authority rules are clear
Codex mobile is review/control only
Source Proxy remains authority

Debug path:

If wording sounds like Codex mobile owns approvals, rewrite.
If it includes "remote execution is safe by default," rewrite.

Rollback:

git restore docs/source-proxy-remote-manual-checks.md docs/source-proxy-production-hardening-plan.md

Next step:
Proceed to Increment 3.2.

Permission gate:
Ask Britton before writing docs.

Increment 3.2: Mobile Manual-Check Packet Format

Goal:
Create a compact manual-check format that works on a phone screen.

Files likely touched:

docs/source-proxy-remote-manual-checks.md
source_proxy/testing/runner.py only if output format is added later

Packet fields:

check name
purpose
command
expected pass signal
expected dirty files
blocked warning signs
what to screenshot or copy
next action
rollback

Manual checks:

cd ~/SpiritOS
sed -n '1,260p' docs/source-proxy-remote-manual-checks.md
git diff --check

Expected outputs:

manual checks are phone-readable
commands are copy-pasteable
pass/fail criteria are not vague

Debug path:

If too long, make a short mobile card plus expanded details.
If command depends on GUI, add SSH fallback.

Rollback:

git restore docs/source-proxy-remote-manual-checks.md source_proxy/testing/runner.py

Next step:
Proceed to Increment 3.3.

Permission gate:
Ask Britton before changing runner output.

Increment 3.3: Remote Check Evidence Receipt

Goal:
Make each remote manual check produce a small receipt Britton can paste back into ChatGPT or Codex.

Files likely touched:

source_proxy/testing/runner.py
source_proxy/tests/test_proxy_runner.py
docs/source-proxy-remote-manual-checks.md

Receipt format:

CHECK:
RESULT:
COMMAND:
HEAD_BEFORE:
HEAD_AFTER:
DIRTY_FILES:
EXPECTED_DIRTY:
BLOCKERS:
NEXT_ACTION:

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_proxy_runner.py
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile phase-4f-closeout

git status --short

Expected outputs:

runner can print a compact receipt
no hidden failure
expected dirty files are labeled
remote review is easier

Debug path:

If receipt hides detail, include a path to full log.
If runner mutates unexpectedly, classify output as blocked.

Rollback:

git restore source_proxy/testing/runner.py source_proxy/tests/test_proxy_runner.py docs/source-proxy-remote-manual-checks.md

Next step:
Proceed to Increment 3.4.

Permission gate:
Ask Britton before patching runner output.

Increment 3.4: Remote Workflow Smoke Test

Goal:
Prove Britton can do one Source Proxy check remotely using Codex mobile plus SSH fallback if needed.

Allowed flow:

Codex mobile for active Codex thread review
SSH/Termius only if raw terminal command is needed
no RustDesk required for this check
no SpiritOS apply/commit/push

Manual checks:

cd ~/SpiritOS

git status --short
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.self_tests --suite phase-4e-safety-seed
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile phase-4f-closeout
git status --short

Expected outputs:

Britton can see pass/fail remotely
output is understandable on phone
no GUI required
no unreviewed repo mutations

Debug path:

If mobile output is too large, shorten receipt.
If terminal is still required too often, add runner commands.
If Codex mobile cannot reach host, use SSH fallback and document setup gap.

Rollback:

none, diagnostic only

Next step:
Proceed to Phase 4.

Permission gate:
Ask Britton before changing any app/mobile-specific behavior.

Phase 4: Read-Only Operator Console

Purpose:
Make /coding show the truth before it can do more.

Increment 4.1: Unified Task Queue Read Model

Goal:
Show all relevant Source Proxy tasks in one read-only queue.

Files likely touched:

source_proxy/tasks/long_running.py
source_proxy/api/long_running_tasks.py
src/app/v1/tasks/long-running/route.ts
src/components/coding/CodingAgentInterface.tsx
src/components/coding/tests/*

Queue fields:

task_id
title
worker
mode
status
target_file
allowed_files
created_at
updated_at
blocker
next_safe_action

Manual checks:

cd ~/SpiritOS

npm run typecheck
npx vitest run src/components/coding
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_long_running_tasks.py

git diff --check

Expected outputs:

task queue visible
no action buttons required
no apply/commit/push added
tests pass

Debug path:

If tasks vanish on refresh, persist minimal task state.
If UI gets noisy, group by active, blocked, completed.

Rollback:

git restore source_proxy/tasks source_proxy/api src/app/v1/tasks src/components/coding

Next step:
Proceed to Increment 4.2.

Permission gate:
Ask Britton before patching UI.

Increment 4.2: Evidence and Artifact Shelf

Goal:
Show Codex evidence, diffs, test output, and rollback hints as artifacts.

Files likely touched:

src/components/coding/CodingAgentInterface.tsx
src/components/coding/SpiritToolActivityCards.tsx, if present
source_proxy/codex/evidence.py
source_proxy/cartographer/codex_evidence.py
src/components/coding/tests/*

Artifact types:

evidence packet
diff preview
test report
stdout/stderr excerpt
final message
rollback hint

Manual checks:

cd ~/SpiritOS

npm run typecheck
npx vitest run src/components/coding
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_codex_cli_adapter.py

git diff --check

Expected outputs:

artifacts visible
long output collapsed
safety verdict visible
no apply button from evidence alone

Debug path:

If UI confuses evidence with approval, relabel.
If artifact data is missing, show "not captured" honestly.
If output overflows mobile, collapse sections.

Rollback:

git restore src/components/coding source_proxy/codex source_proxy/cartographer/codex_evidence.py

Next step:
Proceed to Increment 4.3.

Permission gate:
Ask Britton before patching UI.

Increment 4.3: Blocker and Next Safe Action Panel

Goal:
Make blocked tasks explain what to do next.

Files likely touched:

source_proxy/tasks/long_running.py
source_proxy/testing/runner.py
src/components/coding/CodingAgentInterface.tsx
src/components/coding/tests/*

Blocker examples:

config_blocked
missing_allowed_files
protected_path
target_mismatch
route_unavailable
tests_failed
evidence_review_needed
approval_required
apply_required
commit_required
push_approval_required

Manual checks:

cd ~/SpiritOS

npm run typecheck
npx vitest run src/components/coding
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_long_running_tasks.py source_proxy/tests/test_proxy_runner.py

git diff --check

Expected outputs:

blocked tasks say why
next action is concrete
no vague "failed"
no hidden dangerous action

Debug path:

If blocker reason is missing, add reason code.
If next action says "continue" vaguely, replace with command or route.
If UI implies auto-fix, relabel.

Rollback:

git restore source_proxy/tasks source_proxy/testing/runner.py source_proxy/tests src/components/coding

Next step:
Proceed to Increment 4.4.

Permission gate:
Ask Britton before patching runner or UI.

Increment 4.4: Persist Read-Only Task Story Across Refresh

Goal:
A browser refresh should not erase the task story.

Files likely touched:

source_proxy/tasks/long_running.py
source_proxy/api/long_running_tasks.py
src/hooks or local persistence files
src/components/coding/CodingAgentInterface.tsx

Persist:

task IDs
last known status
blockers
artifact IDs
test reports
approval state
rejection state

Manual checks:

cd ~/SpiritOS

npm run typecheck
npx vitest run src/components/coding
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_long_running_tasks.py

git diff --check

Expected outputs:

refresh keeps task summary
no fake active task if backend says done
no approval state invented client-side

Debug path:

If client and server disagree, server wins.
If local persistence creates stale actions, clear action state on refresh.

Rollback:

git restore source_proxy/tasks source_proxy/api src/hooks src/components/coding

Next step:
Proceed to Phase 5.

Permission gate:
Ask Britton before patching persistence.

Phase 5: Safe Proposal Flow

Purpose:
Make proposal creation and diff review usable without weakening gates.

Increment 5.1: Proposal Creation UI

Goal:
Let Britton create a bounded proposal task from /coding.

Files likely touched:

src/components/coding/CodingAgentInterface.tsx
src/lib/coding/explicit-task-target.ts
src/lib/coding/proxy-route-payload.ts
src/app/v1/actions/preview/route.ts
source_proxy/api/action_preview.py

Required fields:

task
target_file
allowed_files
forbidden_files optional
mode: readonly or proposal
expected checks
rollback hint

Manual checks:

cd ~/SpiritOS

npm run typecheck
npx vitest run src/components/coding
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_source_proxy_end_to_end.py

git diff --check

Expected outputs:

UI requires target and allowed files for proposal
missing target is blocked
protected target is blocked
no apply button yet

Debug path:

If target inference is weak, force manual target selection.
If UI makes allowed_files optional in proposal mode, block.

Rollback:

git restore src/components/coding src/lib/coding src/app/v1/actions source_proxy/api/action_preview.py

Next step:
Proceed to Increment 5.2.

Permission gate:
Ask Britton before patching UI.

Increment 5.2: Diff Preview Integration

Goal:
Show a verified diff preview before any approval appears.

Files likely touched:

source_proxy/api/diff_verification.py
source_proxy/verification/diff.py
src/app/v1/verification/diff-preview/route.ts
src/components/coding/CodingAgentInterface.tsx
source_proxy/tests/test_diff_verification.py

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_diff_verification.py
npm run typecheck
npx vitest run src/components/coding

git diff --check

Expected outputs:

diff paths visible
target match visible
allowed files match visible
protected path status visible
approval unavailable if diff fails

Debug path:

If diff path parsing fails, add regression.
If approval appears before diff pass, block.
If diff display hides path mismatch, fix UI.

Rollback:

git restore source_proxy/api/diff_verification.py source_proxy/verification/diff.py src/app/v1/verification src/components/coding source_proxy/tests

Next step:
Proceed to Increment 5.3.

Permission gate:
Ask Britton before patching diff flow.

Increment 5.3: Verifier and Reviewer Result Cards

Goal:
Show deterministic verifier and reviewer output clearly.

Files likely touched:

source_proxy/verification/deterministic.py
source_proxy/planning/reviewer.py
source_proxy/api/action_preview.py
src/components/coding/CodingAgentInterface.tsx
source_proxy/tests/test_reviewer_deterministic.py
source_proxy/tests/test_verification_contracts.py

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest \
  source_proxy/tests/test_reviewer_deterministic.py \
  source_proxy/tests/test_verification_contracts.py

npm run typecheck
npx vitest run src/components/coding
git diff --check

Expected outputs:

deterministic pass/fail visible
reviewer advisory status visible
unavailable LLM reviewer is not treated as strong pass
approval requires required checks only

Debug path:

If advisory reviewer blocks too much, label advisory.
If unavailable reviewer passes silently, add warning state.
If deterministic verifier lacks reason codes, add them.

Rollback:

git restore source_proxy/verification source_proxy/planning source_proxy/api src/components/coding source_proxy/tests

Next step:
Proceed to Increment 5.4.

Permission gate:
Ask Britton before patching verifier/reviewer behavior.

Increment 5.4: Approval Button Guard

Goal:
Only show approval when all required gates pass.

Files likely touched:

source_proxy/approval/gate.py
source_proxy/api/action_preview.py
src/components/coding/approval-gate-binding.ts
src/components/coding/CodingAgentInterface.tsx
source_proxy/tests/test_source_proxy_end_to_end.py
src/components/coding/tests/*

Required approval conditions:

target known
allowed files known
protected paths pass
diff applies cleanly
verifier passes
reviewer state is acceptable
no secret paths
no action mode escalation
human explicitly clicks approve

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest \
  source_proxy/tests/test_source_proxy_end_to_end.py \
  source_proxy/tests/test_coding_regression_pack.py

npm run typecheck
npx vitest run src/components/coding
git diff --check

Expected outputs:

approval unavailable when blocked
approval available only when preview is clean
no apply happens from approval alone
tests pass

Debug path:

If approval and apply are conflated, split state.
If UI enables button from stale state, force revalidation.
If backend accepts stale approval, block.

Rollback:

git restore source_proxy/approval source_proxy/api src/components/coding source_proxy/tests

Next step:
Proceed to Phase 6.

Permission gate:
Ask Britton before patching approval controls.

Phase 6: Apply, Commit, and Push Governance

Purpose:
Make the full path usable while preserving separate approvals.

Increment 6.1: Approved Apply Lane

Goal:
Apply only an already-approved proposal.

Files likely touched:

src/app/v1/actions/execute-approved/route.ts
source_proxy/tasks/long_running.py
source_proxy/api/action_preview.py
source_proxy/approval/gate.py
source_proxy/tests/test_source_proxy_end_to_end.py

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest \
  source_proxy/tests/test_source_proxy_end_to_end.py \
  source_proxy/tests/test_long_running_tasks.py

git diff --check
git status --short

Expected outputs:

apply requires approval ID
apply cannot use stale preview
apply changes only expected files
apply does not commit
apply does not push

Debug path:

If apply changes extra files, block and restore.
If approval ID can be reused unsafely, expire after use.
If apply creates commit, stop.

Rollback:

git restore src/app/v1/actions source_proxy/tasks source_proxy/api source_proxy/approval source_proxy/tests

Next step:
Proceed to Increment 6.2.

Permission gate:
Ask Britton before enabling apply flow.

Increment 6.2: Post-Apply Verification

Goal:
After apply, run expected checks and produce evidence.

Files likely touched:

source_proxy/tasks/long_running.py
source_proxy/testing/runner.py
source_proxy/verification/contracts.py
src/components/coding/CodingAgentInterface.tsx

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_long_running_tasks.py source_proxy/tests/test_verification_contracts.py
npm run typecheck
git diff --check

Expected outputs:

post-apply checks run or are listed as not run
result is visible
failed checks block commit proposal
no push path

Debug path:

If checks are too slow, make profiles.
If checks are missing, show missing checks honestly.
If failure still allows commit proposal, block.

Rollback:

git restore source_proxy/tasks source_proxy/testing source_proxy/verification src/components/coding

Next step:
Proceed to Increment 6.3.

Permission gate:
Ask Britton before patching post-apply flow.

Increment 6.3: Commit Proposal Lane

Goal:
Create commit proposals only after apply and verification.

Files likely touched:

source_proxy/cartographer/commit_proposals.py
source_proxy/cartographer/git_approvals.py
source_proxy/cartographer/project_health.py
src/app/v1/cartographer/commit-proposals/route.ts
src/components/dashboard/HomelabCartographerWidget.tsx

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py source_proxy/tests/test_cartographer_safety_audit.py

curl -k -sS --max-time 15 https://localhost:3000/v1/cartographer/commit-proposals | jq '.'

git status --short
git diff --check

Expected outputs:

commit proposal shows files, tests, message, risk
commit requires explicit approval
no push happens
failed verification blocks commit proposal

Debug path:

If proposal appears before verification, block.
If commit proposal lacks file list, add it.
If widget implies push, relabel.

Rollback:

git restore source_proxy/cartographer src/app/v1/cartographer src/components/dashboard

Next step:
Proceed to Increment 6.4.

Permission gate:
Ask Britton before enabling commit approval.

Increment 6.4: Push Queue Lane

Goal:
Keep push as a separate final approval with clear risk and remote status.

Files likely touched:

source_proxy/cartographer/push_queue.py
source_proxy/cartographer/project_health.py
src/app/v1/cartographer/push-queue/route.ts
src/components/dashboard/HomelabCartographerWidget.tsx

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py source_proxy/tests/test_cartographer_safety_audit.py

curl -k -sS --max-time 15 https://localhost:3000/v1/cartographer/push-queue | jq '.'
curl -k -sS --max-time 15 https://localhost:3000/v1/cartographer/project-health | jq '.'

git status -sb
git diff --check

Expected outputs:

push queue visible
ahead/behind visible
push requires separate approval
no push by default
branch protection warnings visible

Debug path:

If push queue appears for dirty uncommitted files, fix state logic.
If push approval can happen without commit evidence, block.
If push status is stale, refresh git state before display.

Rollback:

git restore source_proxy/cartographer src/app/v1/cartographer src/components/dashboard

Next step:
Proceed to Phase 7.

Permission gate:
Ask Britton before any real push.

Phase 7: Cartographer and Blueprinter Governance Cleanup

Purpose:
Make project memory and planning reliable after the proxyCLI.md reset.

Increment 7.1: Active Plan Index

Goal:
Make Cartographer/Blueprinter know which docs are active, historical, deferred, or archived.

Files likely touched:

docs/plan-index.md
docs/source-proxy-production-hardening-plan.md
source_proxy/cartographer/blueprint_registry.py
source_proxy/cartographer/project_health.py

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py
grep -RIn "status: active\|status: historical\|status: deferred" docs _blueprints 2>/dev/null || true
git diff --check

Expected outputs:

active plan is clear
old docs are not treated as next actions
deferred items remain visible but inactive

Debug path:

If index is too manual, add metadata later.
If docs lack frontmatter, start with simple table.

Rollback:

git restore docs/plan-index.md docs/source-proxy-production-hardening-plan.md source_proxy/cartographer

Next step:
Proceed to Increment 7.2.

Permission gate:
Ask Britton before patching registry behavior.

Increment 7.2: Cartographer Project Health Truth

Goal:
Make project-health explain exact current state without scary false blockers.

Files likely touched:

source_proxy/cartographer/project_health.py
source_proxy/cartographer/git_status.py
source_proxy/cartographer/models.py
source_proxy/tests/test_cartographer_api.py

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py

curl -k -sS --max-time 15 https://localhost:3000/v1/cartographer/project-health | jq '.'

git status -sb
git diff --check

Expected outputs:

dirty files listed
ahead/behind clear
merge/push readiness honest
snapshot evidence not confused with unsafe changes
next recommended action is concrete

Debug path:

If route unavailable, fix Phase 1.2 first.
If project-health says "ready" while dirty, block.
If it says "blocked" for expected evidence only, refine reason code.

Rollback:

git restore source_proxy/cartographer source_proxy/tests/test_cartographer_api.py

Next step:
Proceed to Increment 7.3.

Permission gate:
Ask Britton before patching project-health.

Increment 7.3: Blueprinter Proposal-Only Discipline

Goal:
Keep Blueprinter useful without letting it write directly.

Files likely touched:

source_proxy/cartographer/blueprint_scribe.py
source_proxy/cartographer/proposals.py
source_proxy/cartographer/proposal_reviews.py
source_proxy/tests/test_cartographer_api.py

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py source_proxy/tests/test_cartographer_safety_audit.py

curl -k -sS --max-time 15 https://localhost:3000/v1/cartographer/proposals | jq '.'

git status --short
git diff --check

Expected outputs:

Blueprinter creates proposals only
proposals require review
apply requires approval
no direct writes to source-of-truth docs

Debug path:

If Blueprinter writes files directly, block.
If proposals lack target files, add them.
If proposal diff is vague, require explicit diff preview.

Rollback:

git restore source_proxy/cartographer source_proxy/tests

Next step:
Proceed to Increment 7.4.

Permission gate:
Ask Britton before enabling proposal generation.

Increment 7.4: No Autonomy Escalation Check

Goal:
Add a recurring check that confirms no autonomous write settings were enabled accidentally.

Files likely touched:

source_proxy/testing/runner.py
source_proxy/tests/test_proxy_runner.py
docs/cartographer-trust-source-plan.md

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_proxy_runner.py
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile cartographer-soak-snapshot

git status --short
git diff --check

Expected outputs:

autonomous apply disabled
autonomous commit disabled
autonomous push disabled
docs-only autopilot disabled unless explicitly configured
snapshot writes expected and labeled

Debug path:

If any autonomous flag is true, block the plan.
If check cannot find flags, add explicit manifest.

Rollback:

git restore source_proxy/testing/runner.py source_proxy/tests/test_proxy_runner.py docs/cartographer-trust-source-plan.md

Next step:
Proceed to Phase 8.

Permission gate:
Ask Britton before adding or changing runner profiles.

Phase 8: Daily-Use Alpha Readiness

Purpose:
Turn Source Proxy into something Britton can actually use without feeling lost.

Increment 8.1: One-Command Proxy Closeout

Goal:
One command should answer whether the proxy is safe to continue.

Files likely touched:

source_proxy/testing/runner.py
source_proxy/tests/test_proxy_runner.py
docs/proxy-test-runner-plan.md

Command:

PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout

Closeout must include:

git state
safety seed
Codex adapter tests
route validation status
dashboard test status
Cartographer project health
expected dirty files
blockers
next safe action

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_proxy_runner.py
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout

git status --short
git diff --check

Expected outputs:

one readable PASS/WARN/BLOCKED report
exact blockers
exact next command
no vague success

Debug path:

If report too long, add summary plus detail sections.
If it runs too many expensive tests, split quick and full profiles.

Rollback:

git restore source_proxy/testing/runner.py source_proxy/tests/test_proxy_runner.py docs/proxy-test-runner-plan.md

Next step:
Proceed to Increment 8.2.

Permission gate:
Ask Britton before adding closeout profile.

Increment 8.2: Regression Matrix

Goal:
Make it obvious which test suite proves which safety guarantee.

Files likely touched:

docs/source-proxy-regression-matrix.md
source_proxy/testing/runner.py

Matrix columns:

guarantee
command
expected pass signal
failure meaning
debug command
owner area

Manual checks:

cd ~/SpiritOS
sed -n '1,260p' docs/source-proxy-regression-matrix.md
git diff --check

Expected outputs:

every critical safety guarantee has a test command
no mystery about which suite to run
docs do not invent passing tests

Debug path:

If a guarantee has no test, mark "missing test."
If a test is slow/flaky, label it.

Rollback:

git restore docs/source-proxy-regression-matrix.md source_proxy/testing/runner.py

Next step:
Proceed to Increment 8.3.

Permission gate:
Ask Britton before writing docs.

Increment 8.3: Manual Check 9

Goal:
Add a harder path-normalization and target-mismatch manual check.

Files likely touched:

source_proxy/testing/self_tests.py
source_proxy/tests/test_coding_self_tests.py
source_proxy/tests/test_coding_regression_pack.py
docs/proxy-test-runner-plan.md

Manual Check 9 examples:

b/./source_proxy/api/decision.py
symlink-like path patterns if relevant
encoded traversal if route accepts URL paths
target file differs from diff file

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest \
  source_proxy/tests/test_coding_self_tests.py \
  source_proxy/tests/test_coding_regression_pack.py

PYTHONPATH=. .venv/bin/python -m source_proxy.testing.self_tests --suite phase-4e-safety-seed

git diff --check

Expected outputs:

new check blocks unsafe normalized path
approval unavailable
would_change_files false
applied_anything false

Debug path:

If existing path safety already blocks it, add regression only.
If it passes, patch path normalization before continuing.

Rollback:

git restore source_proxy/testing/self_tests.py source_proxy/tests docs/proxy-test-runner-plan.md

Next step:
Proceed to Increment 8.4.

Permission gate:
Ask Britton before patching self-tests.

Increment 8.4: Desktop Plus Mobile Runbook

Goal:
Document how Britton should actually use the proxy from desktop, Codex mobile, and SSH fallback.

Files likely touched:

docs/source-proxy-remote-manual-checks.md
docs/source-proxy-daily-use-runbook.md

Runbook sections:

local desktop flow
Codex mobile review flow
SSH fallback flow
RustDesk only when GUI is required
what to paste back to ChatGPT
when to stop and ask for help
what never to approve remotely

Manual checks:

cd ~/SpiritOS
sed -n '1,320p' docs/source-proxy-daily-use-runbook.md
git diff --check

Expected outputs:

Britton knows which app to use for which job
Codex mobile reduces app juggling
Source Proxy approval still final
no remote bypass

Debug path:

If the runbook is too long, add a quick-start card.
If it depends on unbuilt UI, mark future-only.

Rollback:

git restore docs/source-proxy-remote-manual-checks.md docs/source-proxy-daily-use-runbook.md

Next step:
Proceed to Phase 9 after daily-use alpha is comfortable.

Permission gate:
Ask Britton before writing docs.

Phase 9: Provider Routing and Multi-Worker Prep

Purpose:
Prepare future provider flexibility without weakening safety.

Do not start until Phases 0 through 8 are stable.

Increment 9.1: Provider Capability Registry

Goal:
Represent providers by observed capability, not hype.

Providers:

Codex CLI
local Ollama
Gemini CLI later
optional API adapter later

Files likely touched:

source_proxy/agents/registry.py
source_proxy/decision/recommendation.py
source_proxy/api/tools_manifest.py
source_proxy/tests/test_agent_registry.py

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest \
  source_proxy/tests/test_agent_registry.py \
  source_proxy/tests/test_self_status.py \
  source_proxy/tests/test_proxy_agent_routing.py

git diff --check

Expected outputs:

providers show capability states
missing provider is config-blocked
no provider gets apply/commit/push authority
routing is recommendation only

Debug path:

If registry assumes capability, replace with probe result.
If routing silently picks provider, require explanation.

Rollback:

git restore source_proxy/agents source_proxy/decision source_proxy/api/tools_manifest.py source_proxy/tests

Next step:
Proceed to Increment 9.2.

Permission gate:
Ask Britton before patching provider registry.

Increment 9.2: Local Ollama Proposal-Only Adapter Study

Goal:
Test whether local Ollama can help with planning/review without file authority.

Files likely touched:

docs/local-ollama-provider-study.md
source_proxy/agents/registry.py only if read-only probe is added
source_proxy/tests/test_agent_registry.py

Manual checks:

cd ~/SpiritOS
curl -s http://localhost:11434/api/tags | jq '.models[]?.name' || true
git diff -- docs/local-ollama-provider-study.md
git diff --check

Expected outputs:

Ollama capability documented
no file writes from Ollama
no tool authority assumed
model limitations documented

Debug path:

If model lacks tool support, classify as planning/review only.
If output unreliable, keep it out of coding path.

Rollback:

git restore docs/local-ollama-provider-study.md source_proxy/agents source_proxy/tests

Next step:
Proceed to Increment 9.3.

Permission gate:
Ask Britton before adding adapter code.

Increment 9.3: Multi-Worker Read-Only Lanes

Goal:
Show multiple workers as lanes without allowing automatic writes.

Files likely touched:

source_proxy/tasks/long_running.py
src/components/coding/CodingAgentInterface.tsx
source_proxy/tests/test_long_running_tasks.py
src/components/coding/tests/*

Worker lanes:

Codex CLI
deterministic verifier
reviewer
Cartographer
Scout intake, read-only
local model reviewer later

Manual checks:

cd ~/SpiritOS

PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_long_running_tasks.py
npm run typecheck
npx vitest run src/components/coding
git diff --check

Expected outputs:

lanes are read-only
worker outputs are evidence
no automatic apply
no worker can push

Debug path:

If UI implies agents are autonomous, relabel.
If actions appear per worker, hide until governance phase.

Rollback:

git restore source_proxy/tasks src/components/coding source_proxy/tests

Next step:
Proceed to Increment 9.4.

Permission gate:
Ask Britton before patching worker lane UI.

Increment 9.4: Worktree and Branch Prep Study

Goal:
Study Codex-style worktrees without adding them yet.

Files likely touched:

docs/source-proxy-worktree-study.md
source_proxy/cartographer/branch_recommendations.py only if read-only probe is added

Manual checks:

cd ~/SpiritOS
git worktree list
git branch --show-current
git status -sb
git diff -- docs/source-proxy-worktree-study.md
git diff --check

Expected outputs:

risks documented
cleanup rules documented
no new worktree created unless separately approved
no branch changes

Debug path:

If branch state is dirty, do not start worktree experiments.
If cleanup policy is unclear, defer.

Rollback:

git restore docs/source-proxy-worktree-study.md source_proxy/cartographer/branch_recommendations.py

Next step:
Proceed to Phase 10 only after daily-use alpha is stable.

Permission gate:
Ask Britton before creating any worktree.

Phase 10: Deferred Advanced Features

Purpose:
Only after daily-use alpha is stable, decide what advanced layer is actually worth building.

Increment 10.1: Cowork Console Reassessment

Goal:
Decide whether Spirit Cowork Console is still needed after /coding operator console matures.

Do not build it yet.

Manual checks:

compare /coding operator console against original Cowork goals
list missing features
decide: merge into /coding, build separate console, or drop

Expected outputs:

decision document only
no code

Permission gate:
Ask Britton before any Cowork build.

Increment 10.2: AionUi Bridge Reassessment

Goal:
Decide whether AionUi bridge is useful after Source Proxy has its own console.

Do not build it yet.

Manual checks:

use toy repo only
do not open SpiritOS in AionUi
inspect whether AionUi has stable logs/events
decide: no bridge, UX reference only, or future bridge

Expected outputs:

decision document only
no production code

Permission gate:
Ask Britton before any AionUi integration.

Increment 10.3: Native SpiritOS Mobile Surface

Goal:
Decide what SpiritOS mobile should do now that Codex mobile exists.

Likely decision:

near term: Codex mobile + SSH fallback
mid term: SpiritOS responsive operator console
later: native mobile app only if web console is not enough

Expected outputs:

mobile feature decision
no native app yet

Permission gate:
Ask Britton before starting native mobile work.

Increment 10.4: Scheduled Provider Tasks

Goal:
Explore scheduled checks only after scoped TaskSpec and approval rules are boring.

Hard requirements:

allowed files
max runtime
no apply/commit/push
budget limits
notification only by default
approval before write

Expected outputs:

design only
no scheduler yet

Permission gate:
Ask Britton before adding scheduled tasks.

Increment 10.5: Limited Autopilot

Goal:
Only consider docs-only autopilot after long proof.

Hard requirements:

many clean soak runs
no secret edits
no source edits
no commit
no push
rollback evidence
clear kill switch

Expected outputs:

future design only

Permission gate:
Ask Britton before enabling any autopilot.

Immediate Next Move

Start with Phase 0.1 and Phase 0.2 as diagnostics only.

Recommended first Codex task:

"Do not patch. Confirm proxyCLI.md is retired, scan stale plan references, classify active vs historical docs, and report exactly what should become the new source-of-truth plan file."

Do not let Codex patch yet.

After that:

write the new plan file
fix dashboard Vitest failures
fix live route checks
clean runner closeout behavior
then harden Codex route/evidence
then build read-only operator console
then add safe proposal/apply/commit/push lanes
then use Codex mobile as the remote review workflow
Current Grade Targets

Current:
7/10, working beta

After Phase 1:
7.8/10, production-hardening beta

After Phase 3:
8.2/10, remote-usable beta

After Phase 5:
8.6/10, internal operator alpha

After Phase 8:
9/10, daily-use alpha

After Phase 9:
9.2/10, provider-ready beta

Production-ready requires:

stable daily use
repeatable closeout
no stale plan confusion
reliable route checks
clear UI
safe remote review
no bypasses
boring commit/push governance

Next step I recommend: have me write the **Codex prompt for Phase 0.1 and 0.2 only**, diagnostic-only, no patching yet.
::contentReference[oaicite:2]{index=2}