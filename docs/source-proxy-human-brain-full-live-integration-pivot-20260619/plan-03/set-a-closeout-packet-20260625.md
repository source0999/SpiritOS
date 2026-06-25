# Plan 3 Set A Closeout Packet - 2026-06-25

## Executive verdict

`SET_A_CONFIRMED_READY_FOR_HUMAN_APPROVAL`

Plan 3 Set A is stable and ready for Britton human approval. This packet summarizes
the final Set A evidence only. Set B/C not run. Plan 4 not started.

## What passed

- Direct SearXNG 10x: 10/10 HTTP 200, 20 results each.
- A3 3x: PASS / PASS / PASS with 6 sources and no failed gates.
- Full Set A 2x: 10/10 PASS twice, 0 failed, 0 blocked.
- Codex audit: confirmed Set A stability for human review.
- GLM audit: confirmed Set A ready for human approval and audited lane/functionality.
- durable provider proof: direct SearXNG proof captured in the Plan 3 docs tree.

## Evidence index

| Path | What it proves | Verdict |
| --- | --- | --- |
| `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/codex-set-a-stability-audit-20260625.md` | Codex reviewed branch/head, SearXNG, A3 3x, full Set A 2x, and anti-cheat evidence. | `SET_A_STABILITY_CONFIRMED_FOR_HUMAN_REVIEW` |
| `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/glm-set-a-stability-and-lane-audit-20260625.md` | GLM independently audited Set A stability, lanes, context, packet evidence, caveats, and Set B risk. | `SET_A_CONFIRMED_READY_FOR_HUMAN_APPROVAL` |
| `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/final-set-a-stability-readback-20260625.md` | Readback of final verification scope, SearXNG config state, prior A3 instability, and forbidden scope. | final verification authorized for Set A only |
| `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/final-set-a-stability-rerun-20260625.md` | Direct SearXNG 10x, A3 3x, full Set A 2x, and no Set B/C or Plan 4. | `PLAN3_SET_A_STABLE_GO_READY_FOR_HUMAN_DECISION` |
| `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/provider-evidence-20260625/direct-searxng-a3-query-10x-20260625.md` | Durable direct provider proof replacing the prior `/tmp` direct-provider caveat. | `DURABLE_SEARXNG_PROOF_CAPTURED` |
| `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/provider-evidence-20260625/direct-searxng-a3-query-10x-20260625-summary.json` | Machine-readable direct provider summary. | 10/10 HTTP 200, 0 zero-result runs |
| `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/provider-evidence-20260625/direct-searxng-a3-query-10x-20260625.jsonl` | Raw 10-attempt direct SearXNG JSONL proof. | all 10 attempts OK |
| `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/runs/run-20260625T121016Z/` | A3 append-only receipt run 1. | PASS |
| `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/runs/run-20260625T121558Z/` | A3 append-only receipt run 2. | PASS |
| `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/runs/run-20260625T121858Z/` | A3 append-only receipt run 3. | PASS |
| `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/runs/run-20260625T122144Z/` | Full Set A append-only run 1. | 10/10 PASS |
| `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/runs/run-20260625T124450Z/` | Full Set A append-only run 2. | 10/10 PASS |

## Prompt results

Final prompt status is taken from the two full Set A append-only runs, which matched.

| Prompt | Final status | Sources | Internet required | Lane | Notes |
| --- | --- | ---: | --- | --- | --- |
| A1 | PASS | 6 | true | `generic_stabilized_research` | research lane used; `SOURCES_AVAILABLE` |
| A2 | PASS | 6 | true | `validated_decision_packet` | structured packet lane; code-owned source URLs |
| A3 | PASS | 6 | true | `generic_stabilized_research` | A3 also passed three standalone reruns |
| A4 | PASS | 6 | true | `generic_stabilized_research` | research and repo context accepted |
| A5 | PASS | 6 | true | `validated_decision_packet` | structured packet and Mac-worker signals audited |
| A6 | PASS | 6 | true | `generic_stabilized_research` | policy/media research only; no media mutation |
| A7 | PASS | 0 | false | `generic_local_work_product` | repo-context prompt; zero live sources acceptable |
| A8 | PASS | 0 | false | `generic_local_work_product` | repo-context prompt; zero live sources acceptable |
| A9 | PASS | 6 | true | `validated_decision_packet` | structured packet lane and sources available |
| A10 | PASS | 0 | false | `generic_local_work_product` | repo-context prompt; zero live sources acceptable |

## Lane coverage

| Lane | Set A coverage | Closeout note |
| --- | --- | --- |
| research lane | Used by A1-A6 and A9. | SearXNG returned 6 receipt sources for internet-required prompts; durable direct 10x proof captured. |
| repo/context lane | Used by A2-A10. | Receipts and GLM audit confirm real repo files/context were consumed. |
| model lane | Used by Set A receipts. | Live model lane participated; no local fallback was accepted as PASS. |
| structured packet lane | Used by A2, A5, and A9. | Code-owned source registry and model-provenance stripping were audited. |
| generic stabilized lane | Used by A1, A3, A4, and A6. | Generic lane changes stabilized A3 without an A3-specific branch. |
| verifier/grader | Grader used for Set A status; browser/verifier lane was not required. | Patch/verifier behavior remains unproven for Set B. |
| anti-cheat | Audited by Codex and GLM. | No hardcoded PASS/GO, fake source acceptance, or zero-source internet-required PASS found. |
| durable task/task spec | Present in receipt lane evidence. | Task IDs, durable task lanes, and consumer events were represented in receipts. |
| Mac worker | Required only by A5 signals. | GLM classified A5 Mac evidence as real for Set A scope. |
| skipped/degraded lanes | Browser/verifier, repair, recovery, and some side lanes were honestly not required. | These lanes must not be treated as proven for Set B/C. |

## Anti-cheat / no-fake-GO findings

- no hardcoded PASS/GO
- no A3 hack
- no fake source acceptance
- no model-owned provenance accepted
- no zero-source internet-required PASS
- skipped lanes honestly reported

## Caveats

- Set A only.
- Set B/C not run.
- Plan 4 not started.
- Set B has medium generalization risk.
- Set B patch/verifier lane not proven by Set A.
- Set B needs declared rubric before execution.
- A3-only summary carry-forward was noisy but not a cheat.
- append-only run dirs must be preserved.

## Human decision needed

Britton must explicitly approve Set A closeout before Set B readback/execution.

## Recommended next step

Create Set B rubric/readback packet. Do not execute Set B yet.
