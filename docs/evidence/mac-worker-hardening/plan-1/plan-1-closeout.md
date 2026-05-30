# Plan 1 Closeout

Date: 2026-05-28

## Original Mac worker state

Before Plan 1 changes:

- Mac SSH was reachable as `spirit-mac-mini`.
- Hostname was `spirit-mac-mini.local`.
- Mac worker path existed at `/Users/spiritmac/spiritos-worker/SpiritOS`.
- Worker script existed.
- The path was not a git checkout.
- `.git` was missing.
- API `system_status` reported `repo_present:false`.
- `run_safe_check` could not be trusted against that path because git commands failed with the known non-repo failure mode.

## What changed

The old targeted synced Mac worker tree was moved aside as a timestamped backup:

```text
/Users/spiritmac/spiritos-worker/SpiritOS.pre-git-backup-20260528-150109
```

A fresh real git checkout was created at:

```text
/Users/spiritmac/spiritos-worker/SpiritOS
```

The checkout is on:

```text
main
```

The checkout HEAD is:

```text
ac1c6ddf7cf2d71739801a13c46a3f1f3426ea26
```

The Mac checkout status is:

```text
## main...origin/main
?? scripts/mac-worker/
```

`scripts/mac-worker/` is a documented untracked advisory worker overlay copied from the Linux working tree because it is not present in `origin/main` but is required by the current Mac worker command path.

## Files changed

Implementation files changed by this plan:

- `scripts/mac-worker/spirit_mac_worker.py`
- `scripts/mac-worker/spirit-mac-worker.mjs`
- `src/lib/mac-worker/client.ts`
- `src/lib/mac-worker/contract.ts` was inspected but not changed.
- `src/lib/mac-worker/types.ts`
- `src/lib/mac-worker/registry.ts`
- `src/lib/mac-worker/__tests__/contract.test.ts`
- `src/app/api/coding/mac-worker/route.ts` was inspected but not changed.
- `src/app/api/coding/mac-worker/__tests__/route.test.ts`
- `src/components/coding/CodingCommandCenterShell.tsx`

Evidence files created:

- `docs/evidence/mac-worker-hardening/plan-1/increment-1.1.1-linux-baseline.md`
- `docs/evidence/mac-worker-hardening/plan-1/increment-1.1.2-mac-baseline.md`
- `docs/evidence/mac-worker-hardening/plan-1/phase-1.1-closeout.md`
- `docs/evidence/mac-worker-hardening/plan-1/increment-1.2.1-checkout-strategy.md`
- `docs/evidence/mac-worker-hardening/plan-1/increment-1.2.2-real-git-checkout.md`
- `docs/evidence/mac-worker-hardening/plan-1/phase-1.2-closeout.md`
- `docs/evidence/mac-worker-hardening/plan-1/increment-1.3.1-direct-worker-system-status.md`
- `docs/evidence/mac-worker-hardening/plan-1/increment-1.3.2-api-system-status.md`
- `docs/evidence/mac-worker-hardening/plan-1/phase-1.3-closeout.md`
- `docs/evidence/mac-worker-hardening/plan-1/increment-1.4.1-run-safe-check-git-status.md`
- `docs/evidence/mac-worker-hardening/plan-1/increment-1.4.2-run-safe-check-diff-check.md`
- `docs/evidence/mac-worker-hardening/plan-1/increment-1.4.3-safe-command-allowlist.md`
- `docs/evidence/mac-worker-hardening/plan-1/phase-1.4-closeout.md`
- `docs/evidence/mac-worker-hardening/plan-1/increment-1.5.1-job-acceptance-matrix.md`
- `docs/evidence/mac-worker-hardening/plan-1/increment-1.5.2-context-jobs-post-checkout.md`
- `docs/evidence/mac-worker-hardening/plan-1/phase-1.5-closeout.md`
- `docs/evidence/mac-worker-hardening/plan-1/increment-1.6.1-api-status-truth.md`
- `docs/evidence/mac-worker-hardening/plan-1/increment-1.6.2-coding-ui-truth.md`
- `docs/evidence/mac-worker-hardening/plan-1/phase-1.6-closeout.md`
- `docs/evidence/mac-worker-hardening/plan-1/increment-1.7.1-repo-checks.md`
- `docs/evidence/mac-worker-hardening/plan-1/increment-1.7.2-final-mac-smoke.md`
- `docs/evidence/mac-worker-hardening/plan-1/phase-1.7-closeout.md`
- `docs/evidence/mac-worker-hardening/plan-1/plan-1-closeout.md`

The repository had unrelated dirty files before this plan started; they were not reverted.

## Mac behavior before and after

Before:

- `system_status` worked but reported `repo_present:false`.
- Mac path existed but was a targeted synced copy.
- Git commands were not trustworthy because `.git` was missing.

After:

- `system_status` reports `repo_present:true`.
- Mac path is a real git checkout at the same HEAD as Linux baseline.
- `run_safe_check` runs `git status --branch --short --untracked-files=normal`.
- `run_safe_check` runs `git diff --check`.
- Unsafe commands such as `rm -rf .` and `git pull` are blocked with structured `success:false` results.
- API/UI status exposes repo presence, blocked safe checks, last job success, last job type, result summary, and error.

## Jobs proven

- `system_status`
- `run_safe_check`
- `trial_context_assist`
- `repo_context_search`
- `source_proxy_context_discovery`

## Jobs blocked or not tested

- `scout_research_packet`: not tested in Plan 1.
- `browser_design_check`: not tested in Plan 1.

No untested job is marked production-ready.

## Checks run and results

- `npx --no-install vitest run src/lib/mac-worker/__tests__/contract.test.ts src/app/api/coding/mac-worker/__tests__/route.test.ts src/lib/coding/__tests__/agent-trials-ui.test.ts --reporter=dot`: passed.
- `npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx --reporter=dot`: passed with existing React `act(...)` warnings.
- `npx --no-install tsc --noEmit --pretty false`: passed.
- `git diff --check`: passed.
- `python3 -m py_compile scripts/mac-worker/spirit_mac_worker.py`: passed.
- `node --check scripts/mac-worker/spirit-mac-worker.mjs`: passed.
- `node --check scripts/agent-trials/run-ui-agent-trials.mjs`: passed.
- Final API GET: passed.
- Final API `system_status`: passed with `repo_present:true`.
- Final API `run_safe_check` git status: passed.
- Final API `run_safe_check` git diff check: passed.
- Final SSH git status and HEAD: passed.

## Safety boundary

- The Mac Mini remains a support/check/advisory node only.
- No autonomous write authority was added.
- No hidden workers were created.
- No daemon was created.
- No launch agent was created.
- No persistent process was left running.
- No Mac repo write authority was granted beyond the explicit checkout/worker-overlay setup required by this plan.
- No secrets were read, copied, edited, or hardcoded.
- `.env.local` was not touched.
- Cartographer was not mutated.
- Scout production workflows were not mutated.
- Production routing, model routing, and provider authority were not changed.

## GO / NO-GO

GO for Plan 1 complete.

NO-GO to Plan 2 unless Britton explicitly approves it.

## Copy-paste verification block for Britton

```text
MAC WORKER HARDENING RESULT:
Plan: Plan 1 - Mac Worker Repo Checkout Hardening
Status: GO / complete
Mac path: /Users/spiritmac/spiritos-worker/SpiritOS
Old Mac tree backup: /Users/spiritmac/spiritos-worker/SpiritOS.pre-git-backup-20260528-150109
Repo checkout: real git checkout on main at ac1c6ddf7cf2d71739801a13c46a3f1f3426ea26
Mac status: ## main...origin/main plus untracked scripts/mac-worker/ advisory overlay
system_status: passed; repo_present:true
run_safe_check git status: passed
run_safe_check git diff --check: passed
Jobs proven: system_status, run_safe_check, trial_context_assist, repo_context_search, source_proxy_context_discovery
Jobs not tested: scout_research_packet, browser_design_check
Unsafe commands: blocked with success:false, reason_code, blocked_command, recommended_checks
Safety boundary: advisory/check support only; no autonomous write authority
Hidden workers started: none
Persistent processes left running: none
Recommended next increment: explicitly approve a follow-up to track scripts/mac-worker/ in the repository or otherwise formalize the worker overlay
```
