# Human AI Design Memory Bridge

Status: `PLAN_WRITTEN_NOT_STARTED`. This top-level contract is planning-only and changes no runtime files. Authority hard stop events always require human approval. Fake-GO claims are rejected unless evidence is consumed by the named downstream step.

Required Obsidian Human Design Brain fields: `vault_root`, `allowed_design_paths`, `include_globs`, `exclude_globs`, `max_notes`, `priority_order`, `staleness_policy`, `conflict_resolution`, `obsidian_context_refs`, `taste_constraints`, `anti_slop_rules`, `project_design_constraints`, and `conflicts_detected`. Manual checks grep for Obsidian, vault, include/exclude, read-only, context refs, and human approval gates.

First real Obsidian writeback is reserved for Plan 13 and requires explicit human approval.

## Manual Check

```bash
cd /home/source/SpiritOS
python - <<'PY'
import json
from pathlib import Path
root = Path('docs/source-proxy-design-studio-implementation-pivot-20260701')
for p in sorted(root.glob('plan-*/status.json')):
    data = json.loads(p.read_text())
    assert data['implementation_performed'] is False
    assert data['auto_continue_after_master_approval'] is True
    assert data['authority_hard_stops_require_human_approval'] is True
print('status json ok')
PY
git diff --check -- docs/source-proxy-design-studio-implementation-pivot-20260701
```

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
