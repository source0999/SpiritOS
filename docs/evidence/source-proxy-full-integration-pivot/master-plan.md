# Source Proxy Full Integration Pivot Master Plan

Status:
- Active replacement master plan.
- Supersedes old source-proxy-context-orchestration-master-plan and artifact-only level ladder as the execution driver.
- Preserves reusable substrate from old GO work.

## Operating Laws

- Hot-path-or-it-did-not-happen.
- Every lane emits used/skipped/blocked/failed.
- No silent skips.
- No fake success.
- No hand-holding, scaffolding, prompt-tailoring, hidden apply, hidden commit, hidden push, hidden worker, or per-prompt special casing.
- Real target path: `/coding` -> `/v1/decisions/prompt-packet` -> context/model/search/coder/verifier/repair packet flow.
- Qwen coding-only.
- Gemma/Hermes local non-coding lanes.
- Hermes verifier necessary-not-sufficient.
- Deterministic/browser evidence authoritative.
- SearXNG in `source_proxy/decision/research.py` is the local search lane.
- TinyFish deferred.
- xersearch is missing alias/name only; do not build new xersearch module.
- Cartographer advisory only unless Britton explicitly promotes.
- Mandatory Britton approval at every Plan boundary.
- New-chat pivot workflow must stop after every increment/phase/plan for manual checks and Britton GO before continuing.

## Plans

### FIP-0 - Supersede + Universal Integration Truth Receipt Foundation

Purpose:
Build the universal per-prompt integration truth receipt before lane wiring.

Live path:
Real `/coding` prompt -> `/v1/decisions/prompt-packet` -> durable truth receipt created -> receipt includes every lane status even before live wiring.

Receipt fields:
`run_id`, `timestamp`, `raw_prompt`, `normalized_task`, `route_type`, `workspace_mode`, `dirty_tree_status`, `allowed_files`, `forbidden_files`, `protected_path_check`, `context_router_status`, `obsidian_status`, `cartographer_status`, `design_status`, `mac_worker_status`, `scout_status`, `searxng_status`, `gemma_status`, `hermes_critic_status`, `qwen_coder_status`, `hermes_verifier_status`, `repair_loop_status`, `browser_behavior_status`, `deterministic_check_status`, `output_contract_status`, `anti_tailoring_status`, `final_packet_hash`, `coder_received_packet_hash`, `used_sources`, `skipped_reasons`, `blocked_reasons`, `failed_reasons`, `provider_errors`, `model_errors`, `checks_run`, `diff_summary`, `final_verdict`.

GO:
A real `/coding` prompt produces a durable truth receipt with every lane represented.

STOP:
After FIP-0 GO, stop and ask Britton before FIP-1.

### FIP-1 - Live Context Lanes + Context/Research-Needed Router

Purpose:
Put context lanes and the router on `/coding` before search injection.

Lanes:
context router, Obsidian read-only selected-note/context injection, Cartographer advisory context, Design context, Mac worker advisory context, `source_proxy/context/source_readiness.py`.

Live path:
Real `/coding` messy prompt -> prompt-packet -> context/research-needed router -> context lane calls as applicable -> no search provider call -> packet includes context outputs and search_needed decision.

Required:
`search_provider_call_status = skipped_plan_boundary`.

GO:
Real `/coding` prompt shows context router output, per-lane statuses, and actual context packet inclusion.

STOP:
After FIP-1 GO, stop and ask Britton before FIP-2.

### FIP-2 - Local Search Injection: SearXNG + Scout

Purpose:
Wire local web/research search into the context packet after router is live.

Lanes:
`source_proxy/decision/research.py` SearXNG path, `source_proxy/decision/scout_research.py`, context router search_needed decision, `/coding`, prompt-packet, truth receipt.

Live path:
Real `/coding` prompt -> `search_needed=true` -> SearXNG through `SEARXNG_URL` `format=json` -> Scout when enabled/reachable -> cited research packet included in context.

Required:
`tinyfish_status = deferred_cloud_requires_britton_approval`.
`xersearch_status = missing_alias_to_existing_searxng_lane_only`.

GO:
One search-needed `/coding` prompt produces local SearXNG research packet included in final context; one no-search prompt shows skipped.

STOP:
After FIP-2 GO, stop and ask Britton before FIP-3.

### FIP-3 - Concurrent Local Non-Coding Model Lane Activation

Purpose:
Activate Gemma and Hermes as real non-coding model stages concurrently.

Lanes:
`source_proxy/decision/model_lanes.py`, Ollama model routing, Gemma intent/spec/context-needed lane, Hermes critique/risk lane, Hermes verifier role identity/schema reserved.

Live path:
Real `/coding` prompt -> context packet -> Gemma spec/intake -> Hermes critique/risk -> final pre-coder packet includes both.

Rules:
- No one-sidecar-at-a-time sequencing.
- Breakage acceptable if attributed.
- Qwen cannot do pre-coder reasoning.
- Gemma/Hermes must show model identity, prompt hash, output hash, schema validation status.

GO:
Real `/coding` prompt produces live Gemma output and live Hermes critique inside pre-coder packet.

STOP:
After FIP-3 GO, stop and ask Britton before FIP-4.

### FIP-4 - Final Coder Packet Assembly + Qwen Coding-Only Execution

Purpose:
Assemble the actual final coder packet and send it to Qwen only as coder.

Live path:
Real `/coding` prompt -> context router -> context lanes -> local search when needed -> Gemma spec -> Hermes critique -> final coder packet -> Qwen `qwen2.5-coder:7b` receives exact packet -> strict file/action blocks -> parser -> workspace write/diff/check -> receipt with packet hash and coder-received hash.

GO:
Qwen receives final assembled packet, authors valid file/action output, parser enforces contract, controlled diff/check receipt exists.

STOP:
After FIP-4 GO, stop and ask Britton before FIP-5.

### FIP-5 - Required Verifier + Bounded Repair Loop

Purpose:
Make deterministic/browser/Hermes verification and repair live against integrated runs.

Rules:
- Hermes verifier is required but necessary-not-sufficient.
- Deterministic/browser evidence authoritative.
- Preserve `source_proxy/decision/verifier_lane.py` guards.
- Hermes may force FAIL/repair.
- Hermes may not manufacture PASS or override browser behavior.
- Repair loop max attempts default N=2.
- Repair packets go to Qwen as coder-only.

GO:
System proves one PASS case, one FAIL/repair case, and one max-repair or clean NO-GO case with receipts.

STOP:
After FIP-5 GO, stop and ask Britton before FIP-6.

### FIP-6 - Operator-Visible Prompt Transaction Trace

Purpose:
Build the Codex-like operational transparency layer after lanes exist.

Display:
`raw_prompt`, `normalized_task`, context router decision, every lane status, SearXNG/Scout sources, Gemma transcript summary, Hermes critique summary, final Qwen packet, Qwen output summary, parser result, diff, checks, browser probe, Hermes verifier summary, repair attempts, final verdict, packet hash match, receipt path.

Rules:
This is not hidden chain-of-thought. It is operational evidence: prompts, packets, model calls, source calls, receipts, diffs, checks, and verifier outcomes.

GO:
UI trace and durable receipt match for the same real `/coding` run.

STOP:
After FIP-6 GO, stop and ask Britton before FIP-7.

### FIP-7 - Full-Integration Messy-Prompt Gauntlet + Resume Level Ladder

Purpose:
Run Britton-style messy prompts through the actual full integration, then resume Level 3/4/5 testing against integrated system.

Prompt categories:
1. repo context no web
2. Obsidian/design context
3. Cartographer advisory context
4. local SearXNG web search
5. Scout/research context
6. browser behavior verification
7. blocked lane with attribution
8. verifier repair
9. protected/wrong-file trap
10. already-satisfied/no-op

GO:
Integrated gauntlet passes approved threshold with durable receipts and no hidden/fallback success.

STOP:
After FIP-7 closeout, ask Britton which next ladder or expansion is approved.

## Required Per-Increment Template

```text
PLAN:
PHASE:
INCREMENT:
PURPOSE:
PATCH TARGETS:
MODULES TO REUSE BY NAME:
LIVE PATH TO PROVE:
LANES TO TOUCH:
LANES THAT MAY RUN CONCURRENTLY:
IMPLEMENTATION CHANGE:
RECEIPT FIELDS REQUIRED:
CHECKS CODEX MUST RUN BEFORE NEXT INCREMENT:
MANUAL CHECK BRITTON MUST PERFORM:
EXPECTED GO EVIDENCE:
NO-GO CONDITIONS:
CONFIG-BLOCKED CONDITIONS:
ANTI-CHEAT CHECKS:
HOT-PATH PROOF:
ROLLBACK:
EVIDENCE FILES / RECEIPT PATHS:
INCREMENT VERDICT: GO | NO-GO | CONFIG-BLOCKED
NEXT INCREMENT ONLY IF:
PHASE-CLOSEOUT REQUIREMENT:
PLAN-CLOSEOUT REQUIREMENT:
BRITTON STOP GATE:
```

## Manual Check Rule

After every increment, Codex must stop and present:
- files changed
- commands run
- receipts written
- GO/NO-GO/CONFIG-BLOCKED
- exact manual checks Britton should perform
- exact approval phrase needed to continue

No next increment starts until Britton says:

```text
BRITTON GO NEXT INCREMENT
```

No next phase starts until Britton says:

```text
BRITTON GO NEXT PHASE
```

No next plan starts until Britton says:

```text
BRITTON GO NEXT PLAN
```
