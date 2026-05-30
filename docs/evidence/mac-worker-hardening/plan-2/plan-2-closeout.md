# Plan 2 Closeout

Date: 2026-05-28

## Starting grade

B+/A-

Starting state from Plan 1:

- Repo/check integration was working.
- Mac was a real checkout on `main`.
- `system_status`, `run_safe_check`, `trial_context_assist`, `repo_context_search`, and `source_proxy_context_discovery` were proven.
- `scout_research_packet` was not proven.
- `browser_design_check` was not proven.
- `scripts/mac-worker/` was still an untracked overlay.
- Proxy smoothness and web/search proof were incomplete.

## Ending grade

A-

Breakdown:

- Repo/check integration: A+
- Proxy advisory smoothness: B
- Job status truth: A
- Web/search proof: A+
- Browser/design proof: B

## What changed

- Formalized the Mac worker entry files as tracked Linux repo content.
- Added a Mac worker operator contract.
- Hardened `scout_research_packet` result shape.
- Added local-only Scout advisory packet proof.
- Added bounded local-first SearXNG `web_search_packet` mode.
- Proved web search packet end-to-end through SpiritOS API, Mac worker, and local SearXNG.
- Hardened `browser_design_check` result shape so it is honest about missing screenshot proof.
- Added an explicit Mac advisory opt-in bridge to `CodingCommandCenterShell`.
- Added/updated tests for Mac packet contracts and the explicit opt-in bridge.
- Wrote Plan 2 evidence and closeouts.

## Files changed

Implementation and contract files changed by Plan 2:

- `docs/mac-worker-operator-contract.md`
- `scripts/mac-worker/spirit-mac-worker.mjs`
- `scripts/mac-worker/spirit_mac_worker.py`
- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
- `src/lib/mac-worker/__tests__/contract.test.ts`
- `src/lib/mac-worker/types.ts`

Evidence files created:

- `docs/evidence/mac-worker-hardening/plan-2/increment-2.1.1-current-baseline.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.1.2-a-plus-gap-list.md`
- `docs/evidence/mac-worker-hardening/plan-2/phase-2.1-closeout.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.2.1-overlay-decision.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.2.2-worker-overlay-formalized.md`
- `docs/evidence/mac-worker-hardening/plan-2/phase-2.2-closeout.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.3.1-scout-research-packet-inspection.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.3.2-scout-research-local-smoke.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.3.3-scout-research-result-shape.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.3.4-scout-research-api-proof.md`
- `docs/evidence/mac-worker-hardening/plan-2/phase-2.3-closeout.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.4.1-search-provider-boundary.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.4.2-safe-search-packet-mode.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.4.3-web-search-packet-proof.md`
- `docs/evidence/mac-worker-hardening/plan-2/phase-2.4-closeout.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.5.1-browser-design-boundary.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.5.2-browser-design-smoke.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.5.3-browser-design-result-packet.md`
- `docs/evidence/mac-worker-hardening/plan-2/phase-2.5-closeout.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.6.1-proxy-flow-map.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.6.2-explicit-mac-advisory-opt-in.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.6.3-realistic-proxy-mac-flow-proof.md`
- `docs/evidence/mac-worker-hardening/plan-2/phase-2.6-closeout.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.7.1-a-plus-acceptance-matrix.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.7.2-full-verification.md`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.7.3-final-mac-smoke-proof.md`
- `docs/evidence/mac-worker-hardening/plan-2/phase-2.7-closeout.md`
- `docs/evidence/mac-worker-hardening/plan-2/plan-2-closeout.md`

Pre-existing unrelated dirty files remain in the repo and were not reverted.

## Mac worker overlay decision

Decision: `scripts/mac-worker/` should be tracked repo content.

Linux now stages:

- `scripts/mac-worker/spirit-mac-worker.mjs`
- `scripts/mac-worker/spirit_mac_worker.py`

The Mac checkout still shows:

```text
## main...origin/main
?? scripts/mac-worker/
```

Reason: Plan 2 refreshed the approved worker overlay on the Mac, but no commit/push/pull was performed. Once the staged Linux files are committed and the Mac checkout updates from git, the Mac overlay should stop being untracked.

## Mac behavior before and after

Before Plan 2:

- Mac repo existed at `/Users/spiritmac/spiritos-worker/SpiritOS`.
- Mac repo was a real checkout at `ac1c6ddf7cf2d71739801a13c46a3f1f3426ea26`.
- `scripts/mac-worker/` existed as untracked overlay.
- `scout_research_packet` was not proven.
- `browser_design_check` was not proven.

After Plan 2:

- Mac worker still executes from `/Users/spiritmac/spiritos-worker/SpiritOS`.
- `system_status` passes with `repo_present:true`.
- `run_safe_check` git status passes.
- `trial_context_assist` passes.
- `scout_research_packet` local-only passes.
- `scout_research_packet` web-search packet passes through local SearXNG.
- `browser_design_check` passes as an honest blocked-screenshot packet.
- Mac still has no autonomous write authority.
- Mac still has no daemon, launch agent, hidden worker, or persistent browser process.

## API/UI behavior before and after

Before Plan 2:

- API could call proven Plan 1 jobs when the app server was running.
- UI showed Mac worker status truth.
- `scout_research_packet` and `browser_design_check` were unproven.
- No A+ web/search proof existed.
- No routed active `/coding` opt-in proof existed.

After Plan 2:

- API proves local-only Scout packet.
- API proves web-search Scout packet through Mac and local SearXNG.
- API proves browser-design packet is callable and honest about missing screenshot proof.
- Component-level UI has an explicit Mac advisory opt-in bridge in `CodingCommandCenterShell`.
- Active routed `/coding` still renders `CodingCockpitShell`, so A+ active UI smoothness is not proven.

## Jobs proven

- `system_status`
- `run_safe_check`
- `trial_context_assist`
- `repo_context_search`
- `source_proxy_context_discovery`
- `scout_research_packet` local-only
- `scout_research_packet` web-search packet
- `browser_design_check` callable blocked-screenshot packet

## Jobs blocked or still partial

- `browser_design_check` screenshot-backed proof is blocked because Mac lacks Node/npm/npx/Playwright or another approved browser artifact path.
- Proxy active `/coding` UI smoothness is partial because the opt-in bridge is not in the routed shell.

## Web/search proof status

A+

End-to-end proof:

- SpiritOS API request
- Mac worker execution
- local SearXNG at `source-server.local:8080`
- structured packet with sources, provider status, limitations, and untrusted-content warning
- no paid provider
- no Scout production write

## Browser/design proof status

B

Callable and honest, but no screenshot proof:

- no browser launched
- no screenshot captured
- no layout pixels inspected
- no CSS/design mutation
- no fake visual proof

## Proxy smoothness proof status

B

- Raw API and component-level opt-in proof exist.
- Harness has a Mac integration path.
- Plan 2 realistic harness run failed before Mac use because the app server was unavailable.
- Active `/coding` does not expose the new opt-in bridge because it renders `CodingCockpitShell`.

## Advisory-only status

Mac remains advisory/check support only.

No Mac job may:

- apply fixes
- commit
- push
- mutate Cartographer
- mutate Scout production storage
- change provider routing
- read/write secrets
- start hidden workers
- install daemons or launch agents
- gain autonomous write authority

## Hidden workers and persistent processes

Hidden workers started: none.

Daemons or launch agents created: none.

Persistent processes left running: none.

The explicit temporary Next dev server used for proof was stopped before closeout. Port 3000 was no longer listening after shutdown.

## Checks run and results

- `npx --no-install vitest run src/lib/mac-worker/__tests__/contract.test.ts src/app/api/coding/mac-worker/__tests__/route.test.ts src/lib/coding/__tests__/agent-trials-ui.test.ts --reporter=dot`: passed, 23 tests.
- `npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx --reporter=dot`: passed, 75 tests, with existing React `act(...)` warnings.
- `npx --no-install tsc --noEmit --pretty false`: passed.
- `git diff --check`: passed.
- `python3 -m py_compile scripts/mac-worker/spirit_mac_worker.py`: passed.
- `node --check scripts/mac-worker/spirit-mac-worker.mjs`: passed.
- `node --check scripts/agent-trials/run-ui-agent-trials.mjs`: passed.
- Final API GET: passed.
- Final API `system_status`: passed.
- Final API `run_safe_check`: passed.
- Final API `trial_context_assist`: passed.
- Final API `scout_research_packet` local-only: passed.
- Final API `browser_design_check`: passed as blocked-screenshot packet.

## GO / NO-GO

GO for Plan 2 complete.

NO-GO for claiming full A+ proxy smoothness or screenshot-backed browser proof.

## Recommended next plan

Plan 3 should move the explicit Mac advisory opt-in bridge into the active routed `/coding` shell or switch `/coding` routing intentionally, then re-run a realistic harness/UI proof that records Mac use end-to-end.

Do not start Plan 3 without Britton approval.

## Copy-paste status block for Britton

```text
MAC INTEGRATION A+ HARDENING RESULT:
Plan: Plan 2 - Mac Worker A+ Proxy, Search, Browser, and Overlay Proof
Status: GO / complete with proxy/browser caveats
Starting grade: B+/A-
Ending grade: A-
Files changed: docs/mac-worker-operator-contract.md; scripts/mac-worker/spirit-mac-worker.mjs; scripts/mac-worker/spirit_mac_worker.py; src/components/coding/CodingCommandCenterShell.tsx; src/components/coding/__tests__/coding-command-center-shell.test.tsx; src/lib/mac-worker/__tests__/contract.test.ts; src/lib/mac-worker/types.ts; docs/evidence/mac-worker-hardening/plan-2/*
Mac worker overlay: Linux worker files formalized as tracked content; Mac checkout still shows untracked scripts/mac-worker/ until commit/pull updates it
Repo/check integration: A+
Proxy smoothness: B; raw API and component opt-in proof exist, but routed /coding active shell does not expose the bridge yet
Web/search proof: A+; API to Mac to local SearXNG web_search_packet proven with structured untrusted sources and no Scout writes
Browser/design proof: B; callable structured packet, but screenshot proof blocked because Mac lacks approved browser automation
Jobs proven: system_status, run_safe_check, trial_context_assist, repo_context_search, source_proxy_context_discovery, scout_research_packet local_only, scout_research_packet web_search_packet, browser_design_check callable blocked-screenshot packet
Jobs partial/blocked: browser_design_check screenshot proof; active /coding smooth opt-in proof
Safety boundary preserved: yes, advisory/check support only
Hidden workers started: none
Persistent processes left running: none
Checks run: vitest mac/API/coding 23 passed; vitest command center 75 passed; tsc passed; git diff --check passed; py_compile passed; node --check worker passed; node --check agent trial runner passed; final API smoke passed
Final grade: A-
Recommended next step: Approve Plan 3 to move/verify the Mac opt-in bridge in the active routed /coding shell and add approved Mac browser screenshot capability if A+ browser proof is required
Copy-paste verification block: see docs/evidence/mac-worker-hardening/plan-2/plan-2-closeout.md
```
