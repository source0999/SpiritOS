# Source Proxy Agent Integration Preflight New Chat Handoff v0.1

Status: historical handoff; superseded after Plan 12/12 closeout.

This handoff was used to start the build-first preflight roadmap. The roadmap is now closed through Plan 12/12. Do not use this prompt to restart Plan 0 or replay the completed roadmap.

Current closeout:

- `docs/source-proxy-agent-integration-preflight-plan-12-closeout-v0.1.md`

Next roadmap title only:

- `Cartographer Limited Daily-Driver Auto v1`

Historical prompt:

```text
You are Codex inside the SpiritOS repository at /home/source/SpiritOS.

MISSION:
Start the build-first Source Proxy Agent Integration Preflight roadmap by executing Plan 0 only from:

docs/source-proxy-agent-integration-preflight-build-roadmap-v0.1.md

Plan 0 title:
Roadmap Reset And Active Plan Cleanup

TARGET:
Prepare the repo for the new build-first roadmap that supersedes the failed docs-heavy 24-plan chain. Do not start implementation Plan 1. Do not continue old Plan 23. Do not start or schedule a soak. Do not re-soak. Do not run Cartographer activation. Do not run workers. Do not run provider/model calls.

CORRECT PIVOT WORKFLOW:
One Codex chat works on ONE WHOLE PLAN at a time. Plan 0 contains phases, and each phase contains increments. Work increment by increment inside Plan 0.

After each increment:
- make the scoped change,
- run that increment's terminal/manual checks yourself,
- inspect the output,
- fix safe failures inside Plan 0 scope,
- record GO / NO-GO for that increment,
- then continue to the next increment automatically if GO.

At the END of each phase, before moving to the next phase, run a phase-level terminal/manual check covering ALL increments completed in that phase.

At the END of Plan 0, give Britton one copy-paste terminal block to verify all phases and increments completed in Plan 0.

Do not stop after one increment unless a stop condition triggers. Do not interpret PIVOT as "do one increment only and stop." Do not ask Britton for permission between every increment unless:
- the next action can mutate outside Plan 0 docs cleanup scope,
- repo state is unsafe,
- expected proof cannot be produced honestly,
- a command may affect runtime/Cart/workers/git state beyond allowed scope,
- or Plan 0 explicitly requires human approval.

PLAN 0 PURPOSE:
Supersede failed 24-plan chain, stop Plan 23/soak, install correct PIVOT, classify old docs for archive/delete, and create clean active source of truth.

PLAN 0 PHASES AND INCREMENTS:

Phase 0.1: Old roadmap freeze
- Increment 0.1.1: Confirm Plan 23 and soak are not authorized.
- Increment 0.1.2: Locate active failed roadmap docs.
- Increment 0.1.3: Classify keep/archive/delete candidates.

Phase 0.2: PIVOT contract installation
- Increment 0.2.1: Add correct PIVOT workflow contract.
- Increment 0.2.2: Define implementation-plan standard.
- Increment 0.2.3: Define docs limit and no-packet rule.

Phase 0.3: Active roadmap switch
- Increment 0.3.1: Supersede old active roadmap pointers.
- Increment 0.3.2: Verify new roadmap is active source of truth.
- Increment 0.3.3: Produce Britton final Plan 0 terminal check block.

ALLOWED PLAN 0 FILES:
- docs/source-proxy-agent-integration-preflight-build-roadmap-v0.1.md
- docs/source-proxy-agent-integration-preflight-new-chat-handoff-v0.1.md
- docs/masterKeyProxyProduction.md
- docs/plan-index.md
- A new docs-only Plan 0 closeout/classification file only if needed and clearly named before editing.

FORBIDDEN:
- Do not edit src/**.
- Do not edit source_proxy/**.
- Do not edit scout/**.
- Do not edit backend/**.
- Do not edit scripts/**.
- Do not edit config/**.
- Do not edit tests.
- Do not edit CSS files.
- Do not edit package files.
- Do not edit runtime files.
- Do not edit Cartographer runtime/evidence/receipt files.
- Do not edit .env files.
- Do not mutate git metadata.
- Do not start Plan 1.
- Do not start implementation.
- Do not run Cartographer activation.
- Do not run queue/workers.
- Do not run provider/model calls.
- Do not run apply/execute-approved.
- Do not commit, push, branch, worktree, reset, stash, clean, checkout, or stage.
- Do not run npm install.
- Do not start runtime servers.
- Do not run browser automation.
- Do not capture screenshots.
- Do not run broad test suites.

PLAN 0 DOC QUALITY:
- Be specific.
- Keep docs readable.
- Do not create huge evidence packets.
- Do not write GO for work not done.
- Do not claim readiness from contracts.
- Do not delete historical evidence.
- Classify old roadmap docs as keep/archive/delete candidates, then require future verification before archive/delete.
- Preserve useful facts by moving them into the new active source of truth or classification table.
- Distinguish preview, approval, apply, commit, push, and auto.

SUGGESTED FINAL PLAN 0 VERIFICATION BLOCK:

cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
test -f docs/source-proxy-agent-integration-preflight-build-roadmap-v0.1.md
test -f docs/source-proxy-agent-integration-preflight-new-chat-handoff-v0.1.md
grep -nE "Preflight Final CSS Stage|Correct PIVOT|Plan 0:|Plan 1:|Plan 2:|Plan 3:|Plan 4:|Plan 5:|Plan 6:|Plan 7:|Plan 8:|Plan 9:|Plan 10:|Plan 11:|Plan 12:|Cartographer Limited Daily-Driver Auto v1|not daily-driver auto|do not stop after one increment|phase-level|final.*terminal" docs/source-proxy-agent-integration-preflight-build-roadmap-v0.1.md docs/source-proxy-agent-integration-preflight-new-chat-handoff-v0.1.md
git diff --check -- docs/source-proxy-agent-integration-preflight-build-roadmap-v0.1.md docs/source-proxy-agent-integration-preflight-new-chat-handoff-v0.1.md docs/masterKeyProxyProduction.md docs/plan-index.md

EXPECTED FINAL RESULT:
- Plan 0 all increments complete unless a stop condition triggers.
- Old roadmap active direction is superseded.
- Plan 23 and soak are explicitly not authorized.
- Correct PIVOT workflow is installed.
- Old roadmap docs are classified as keep/archive/delete candidates, with verification required before archive/delete.
- New roadmap is active source of truth.
- Plan 1 is not started.
- No source/runtime/CSS/Cart/provider/worker/git mutation occurred beyond Plan 0 docs cleanup scope.
- Final answer includes GO / NO-GO and the final full-plan terminal verification block.
```
