BEGIN COPY-PASTE NEW CHAT HANDOFF

You are Codex working in the SpiritOS Source Proxy repo.

Start from:
docs/evidence/source-proxy-full-integration-pivot/master-plan.md
docs/evidence/source-proxy-full-integration-pivot/active-context.md
docs/evidence/source-proxy-full-integration-pivot/bootstrap-cleanout-receipt.md
docs/evidence/source-proxy-context-orchestration-master-plan/SUPERSEDED_BY_FIP.md
docs/evidence/source-proxy-context-orchestration-master-plan/acceptance-contract.md
docs/evidence/source-proxy-context-orchestration-master-plan/no-preview-only-integration-policy.md

Mission:
Begin FIP-0 only: Supersede + Universal Integration Truth Receipt Foundation.

Do not start FIP-1.
Do not wire context/search/model/coder/verifier lanes yet except as required to emit explicit used/skipped/blocked/failed receipt fields in FIP-0.
Do not resume Level 3/4/5.
Do not use artifact-only ladder as the driver.
Do not add TinyFish.
Do not create xersearch.
Do not use cloud providers.
Do not commit or push.

Pivot workflow:
Work increment-by-increment.
Before each increment:
- state PLAN / PHASE / INCREMENT
- state patch targets
- state live path to prove
- state checks to run
- state manual Britton check required before the next increment

After each increment:
- run checks
- write evidence/receipt
- print files changed
- print commands run
- print GO / NO-GO / CONFIG-BLOCKED
- print exact manual checks Britton should perform
- STOP until Britton says BRITTON GO NEXT INCREMENT

At phase boundary:
STOP until Britton says BRITTON GO NEXT PHASE.

At plan boundary:
STOP until Britton says BRITTON GO NEXT PLAN.

FIP-0 goal:
A real /coding prompt through /v1/decisions/prompt-packet produces a durable universal integration truth receipt where every known lane is represented as used/skipped/blocked/failed.

FIP-0 required lanes:
context router, Obsidian, Cartographer advisory, Design, Mac worker, Scout, SearXNG, Gemma, Hermes critic, Qwen coder, Hermes verifier, repair loop, browser behavior, deterministic checks, output contract, anti-tailoring/anti-cheat.

FIP-0 required proof:
- Real /coding path participated.
- /v1/decisions/prompt-packet participated.
- Durable receipt exists.
- Every lane status exists.
- No silent missing lane.
- UI or retrievable backend surface shows the same run truth.
- Coder packet hash fields exist even if coder execution is not fully integrated yet.
- Final verdict is honest.

Use existing modules by name. Extend; do not fork parallel pipeline:
source_proxy/decision/research.py
source_proxy/decision/scout_research.py
source_proxy/context/obsidian.py
source_proxy/context/source_readiness.py
source_proxy/decision/cartographer_routing.py
source_proxy/decision/verifier_lane.py
source_proxy/decision/model_lanes.py
source_proxy/api/decision.py
src/app/coding/page.tsx

Note: if older instructions mention source_proxy/decision/obsidian.py or source_proxy/decision/source_readiness.py, use the current repo paths source_proxy/context/obsidian.py and source_proxy/context/source_readiness.py.

End every response with:
NEXT ACTION REQUIRES BRITTON APPROVAL:
BRITTON GO NEXT INCREMENT / BRITTON GO NEXT PHASE / BRITTON GO NEXT PLAN

END COPY-PASTE NEW CHAT HANDOFF
