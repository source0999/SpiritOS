# Design Studio Pivot Master Plan

Status: `PLAN_WRITTEN_NOT_STARTED`. This packet is docs-only and authorizes no implementation, route change, model routing change, Prompt 4/5 run, runtime mutation, apply action, worker action, Obsidian write, media work, commit, push, reset, clean, rebase, or stash.

This is a master plan of plans for a future Claude-design-like SpiritOS Design Studio lane. It must extend the existing Source Proxy methodology instead of creating a parallel apply path. The first safe sandbox target is `src/app/coding/design-demo/page.tsx`; the first packet preview seam is `src/app/v1/coding/design-vault/preview/route.ts`; visual references must reuse `source_proxy/vector/visual_index.py`; verifier and repair behavior must consume existing browser/verifier/apply contracts.

## Non-Negotiables

- No fake GO: route exists, packet exists, preview works, screenshot exists, or design looks nice are never sufficient.
- No skipped lanes: intake, decomposition, design packet, critic, visual verification, repair, coder handoff, approval, and post-apply verification must be explicitly accounted for.
- No unconsumed packet laundering: every design packet must have a named downstream consumer and a causal trace showing consumption.
- No parallel apply path: coder handoff may draft bounded tasks, but only existing approved-action/safe-write contracts may apply.
- No authority expansion: any new write authority, model lane, Obsidian path, Mac worker path, or production route requires future explicit Britton approval.
- No Plan 7 replacement fantasy: this packet has `plan-07` because the user required the directory, but it is a Design Studio hardening plan, not a claim that prior Plan 7 work is authorized or complete.

## Plan Sequence

- Plan 0/8 - Truth Freeze, Sandbox Inventory, and Compression Gate. Status: `ELIGIBLE_FOR_FUTURE_BRITTON_APPROVAL`.
- Plan 1/8 - Design Lane Intake and Authority Boundary.
- Plan 2/8 - Design DNA and Token Extraction.
- Plan 3/8 - Design Packet and Coder Handoff Contract.
- Plan 4/8 - Visual Verification and Browser Evidence.
- Plan 5/8 - Critic, Anti-Template, and Uniqueness Gates.
- Plan 6/8 - Bounded Repair Loop and Failure Taxonomy.
- Plan 7/8 - Approval Reuse, Apply Isolation, and Post-Apply Verification.
- Plan 8/8 - Memory, Regression Pack, and Operator Handoff.

Only Plan 0 is eligible for a future Britton approval prompt. Plans 1-8 remain unauthorized until the previous plan has closeout evidence, Codex review, manual Britton check PASS, and explicit next-plan approval.

## Universal Phase Shape

Each plan has phases. Each phase has increments. Each increment must list scope, allowed files for future implementation, forbidden paths, input contract, output contract, downstream consumer, focused checks, Codex self-checks, manual Britton check block, rollback, GO criteria, and fake-GO traps. Each phase must close with evidence that every increment output was consumed or explicitly failed closed.

## Repo References Inspected

- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/master-plan.md:5` lists Plan 0 as the first eligible plan and later plans as gated.
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/master-plan.md:13-15` requires Britton decisions plus real invocation, downstream consumption, causal trace, and no preview-only GO.
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/execution-handoff.md:5-9` requires exact future approval text and blocks next-plan work without review and Britton approval.
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/canonical-state-and-event-contract.md:3-5` anchors reuse of existing state/event machinery and minimum task state fields.
- `src/app/coding/design-demo/page.tsx:9-26` exposes the existing Design Demo sandbox target.
- `src/app/v1/coding/design-vault/preview/route.ts:1-37` exposes the existing design-vault preview seam and packet shape.
- `source_proxy/vector/visual_index.py:11-18,33-79` exposes visual reference storage and query functions for future design memory.
- `source_proxy/tests/test_visual_index.py:32-75` covers visual index batch, discovery, ingest, and empty-query behavior.
- `source_proxy/decision/human_messy_homepage.py:47-109,204-217,227-383` anchors artifact generation, behavior contracts, workspace constraints, and scoring.
- `source_proxy/decision/task_spec_intake.py:38-80,211-282,361-485` anchors task intake, static UI artifact classification, and manual apply policy.
- `source_proxy/decision/packet_decomposition.py:19-49` anchors task shape and sub-packet decomposition concepts.
- `source_proxy/decision/artifact_behavior_contract.py` anchors behavior contracts that must be extended, not replaced.
- `source_proxy/decision/artifact_repair_contract.py` and `source_proxy/decision/artifact_repair_loop.py` anchor bounded repair concepts.
- `source_proxy/decision/verifier_lane.py` anchors verifier-lane reuse.
- `src/app/v1/actions/execute-approved/route.ts` anchors approved-action execution and must not be bypassed.
- `source_proxy/tests/test_verification_contracts.py` and `source_proxy/tests/test_coding_regression_pack.py:4523-4575` anchor verification and approved-apply expectations.
