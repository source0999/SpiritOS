# Acceptance Rubric

Status: `PLAN_WRITTEN_NOT_STARTED`. This contract authorizes no implementation.

A future increment passes only when it has real invocation, typed output, downstream consumption, visual/browser proof where relevant, failure outcome change, Codex self-check PASS, manual Britton check PASS, and no forbidden authority expansion. Anything less is PLAN/NO-GO.

## Messy Human Prompt Contract

Acceptance must distinguish messy-but-actionable design prompts from vague prompts. With a known target route, surface, or content, `make it modern`, `make it mobile responsive`, `make this feel premium and not generic`, and `make it less Google AI Studio` can pass only by producing a typed design packet with `style_family_blend`, `project_specific_motif`, `anti_template_checks`, `visual_pass_criteria`, and a bounded `coder_packet`.

Without a target route, surface, or content, `make it look premium`, `make it better`, and `make it clean` must produce `ASK_CLARIFY_TARGET`. Guessing the target surface is NO-GO.

Required downstream packet fields remain part of acceptance: `design_packet_id`, `trace_id`, `target_surface`, `coder_packet.target_files`, `coder_packet.allowed_files`, `coder_packet.forbidden_files`, `coder_packet.css_rules`, `coder_packet.responsive_rules`, and `coder_packet.verification_commands`.

Fake-GO rule: a `design_packet` or `coder_packet` alone is not GO unless consumed by the named downstream step.

## Required Future Fields

- `contract_id`
- `source_evidence`
- `allowed_authority`
- `forbidden_authority`
- `input_contract`
- `output_contract`
- `downstream_consumer`
- `codex_self_checks`
- `manual_britton_check`
- `closeout_evidence`
- `fake_go_traps`

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
