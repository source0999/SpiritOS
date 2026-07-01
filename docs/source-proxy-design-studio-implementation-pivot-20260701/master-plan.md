# Design Studio Implementation Master Plan v1

Status: `PLAN_WRITTEN_NOT_STARTED`. This is a docs-only consolidated implementation pivot. It authorizes no code implementation, runtime patch, external tool install, website fetch, raw CSS ingest, Obsidian write, Prompt 4/5 run, model routing change, SpiritFlix/media touch, Mac worker change, staging, commit, push, reset, clean, rebase, or stash.

A-grade success: The system is A-grade only when a messy design prompt plus optional Obsidian/reference/site/CSS input can produce a typed design_packet, a bounded coder_packet, an original sandbox implementation, desktop/mobile screenshot proof, anti-template/originality pass, critic/repair pass, and gated Obsidian writeback, all with consumed evidence and no fake-GO traps.

## Operating Philosophy

- Obsidian is the Obsidian Human Design Brain.
- Proxy packets are the AI Design Brain.
- Visual index/reference library is reference memory.
- Coder is the implementation hand.
- Browser verifier is the eyes.
- Critic/repair loop is taste and refinement.
- Obsidian reads come early.
- Obsidian writes come very late and require explicit human approval.

## Five Stages

- Stage 1 - Foundation: Plan 00, Plan 01
- Stage 2 - Preview and Packet Runtime: Plan 02, Plan 03
- Stage 3 - References, DesignDNA, and Memory Bridge: Plan 04, Plan 05, Plan 06, Plan 07
- Stage 4 - Coder, Proof, and Repair: Plan 08, Plan 09, Plan 10, Plan 11, Plan 12
- Stage 5 - Writeback and Acceptance: Plan 13, Plan 14

## Autopivot Execution Model

After Britton approves the whole implementation pivot, Codex may execute sequentially: increment -> run increment manual check -> update increment evidence -> continue to next increment. At phase end it runs the phase rollup, updates `phase-rollup.md`, and continues. At plan end it runs the plan rollup, updates `plan-rollup.md`, and continues to the next plan. Codex must not stop at normal phase or plan boundaries. Codex stops only for hard blocker, failed check it cannot safely fix inside allowed scope, protected path conflict, missing required repo files, ambiguous dirty-tree conflict in target files, need for Britton decision, or any authority hard stop.

## Authority Hard Stops

- first real Obsidian writeback: requires explicit human approval.
- first sandbox apply: requires explicit human approval.
- first external tool install: requires explicit human approval.
- first external website/network scrape: requires explicit human approval.
- first raw CSS ingestion: requires explicit human approval.
- first real app screen apply: requires explicit human approval.
- first model routing change: requires explicit human approval.
- first Mac worker change: requires explicit human approval.
- first SpiritFlix/media touch: requires explicit human approval.
- any approval/safe-write/execute-approved bypass proposal: requires explicit human approval.
- any uncertainty over license/copyright/source use: requires explicit human approval.

## Global Fake-GO Blockers

- docs exist
- route exists
- preview opens
- design_packet exists
- coder_packet exists
- Obsidian note exists
- visual index exists
- reference uploaded
- CSS parsed
- website screenshot captured
- desktop screenshot only
- HTTP 200 only
- critic says looks good
- model says fixed
- memory row exists
- external tool installed
- unconsumed packet
- unconsumed screenshot
- unconsumed Obsidian context
- unconsumed DesignDNA
- unconsumed critic
- unverified verifier output
- direct CSS/classname copy
- generic Google AI Studio-looking output

## Repo References Inspected

- `docs/source-proxy-design-studio-pivot-20260630/master-plan.md:1-32` anchors the predecessor docs-only Design Studio pivot, fake-GO rules, phase/increment shape, and reuse of existing Source Proxy methodology.
- `docs/source-proxy-design-studio-pivot-20260630/design-packet-contract.md:11-44` anchors messy-prompt examples, `ASK_CLARIFY_TARGET`, `style_family_blend`, and the rule that a `design_packet` or `coder_packet` alone is fake-GO unless consumed downstream.
- `docs/source-proxy-design-studio-pivot-20260630/acceptance-rubric.md:9-15` anchors the messy-prompt acceptance terms and downstream packet requirements.
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/master-plan.md:1-15` anchors gated whole-brain planning and no preview/schema/fallback-only GO.
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/execution-handoff.md:1-9` anchors explicit approval before execution.
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/canonical-state-and-event-contract.md:1-5` anchors canonical state/event fields including `consumer_event_id` and downstream consumption.
- `src/app/coding/design-demo/page.tsx:3-16` anchors the existing sandbox route component.
- `src/app/v1/coding/design-vault/preview/route.ts:1-37` anchors the older preview-only design packet seam.
- `source_proxy/context/obsidian.py:19-239` anchors read-only Obsidian context config, candidate-note filtering, scoring, and excerpts.
- `source_proxy/api/obsidian_context.py:13-18` anchors the Obsidian context query API wrapper.
- `source_proxy/vector/visual_index.py:18-194` anchors visual reference ingest/query and optional OpenCLIP/LanceDB adapters.
- `source_proxy/tests/test_visual_index.py:32-75` anchors visual index batch, discovery, ingest, and empty-query tests.
- `source_proxy/decision/human_messy_homepage.py:47-383` anchors messy-prompt generation, workspace constraints, behavior contracts, and scoring.
- `source_proxy/decision/task_spec_intake.py:38-80,211-282,361-485` anchors target intake, artifact classification, and manual-apply policy.
- `source_proxy/decision/packet_decomposition.py:19-198` anchors task shape, sub-packets, and decomposition validation.
- `source_proxy/decision/artifact_behavior_contract.py:10-394` anchors behavior probe contracts and preview requirements.
- `source_proxy/decision/verifier_lane.py:15-188` anchors verifier packets, normalization, preview, and live functional verifier seams.
- `source_proxy/decision/artifact_repair_contract.py:22-223` anchors failure packets and repair prompts.
- `source_proxy/decision/artifact_repair_loop.py:16-259` anchors limited repair loop, allowed files, changed files, and model-authored targets.
- `source_proxy/verification/diff.py:1123-1438` anchors diff preview, browser-proof requirement, and changed-file parsing.
- `src/app/v1/actions/execute-approved/route.ts:13-253,794-812` anchors approved execution, allowed-file checks, protected path checks, and approval id hashing.
- `src/components/coding/CodingCommandCenterShell.tsx:2970-3423` anchors existing design packet UI copy and rollback signal vocabulary.
- `src/lib/coding/proxy-route-payload.ts` and `src/lib/coding/preview-only-request.ts` anchor existing coding route payload and preview-only request helpers.
