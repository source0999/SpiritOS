# Full Integration Pivot Active Context

Date: 2026-06-15

Current accepted state: Integrated Level 5R2 GO.

No post-Level-5 expansion has started.

## Accepted Timeline

- FIP-0 GO
- FIP-1 GO
- FIP-2 GO
- FIP-3 GO
- FIP-4 GO
- FIP-5 GO
- FIP-6 GO
- FIP-7R GO
- Integrated Level 3 GO
- Integrated Level 4 GO
- Integrated Level 5 CONFIG-BLOCKED
- Integrated Level 5R NO-GO
- Integrated Level 5R2 GO

Current authority:

- `docs/evidence/source-proxy-full-integration-pivot/integrated-level-5R2-closeout.md`
- `docs/evidence/source-proxy-full-integration-pivot/post-level-5-stabilization-closeout.md`

## Runtime Runbook

- Authoritative runtime checkout: Linux `source-server`, `/home/source/SpiritOS`.
- Launch command: `npm run proxy:https:lan`.
- Source Proxy URL: `https://127.0.0.1:8787`.
- Restart target: tmux session `source-proxy-lan`.
- Receipt endpoint: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest`.
- Latest trace endpoint: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest/trace`.
- By-run trace endpoint: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/<run_id>/trace`.

Do not assume Windows `Z:\` edits are live until the Linux runtime has been restarted.

## Current Proof Summary

Integrated Level 5R2 full matrix:

- Total prompts: 20
- Posted: 20
- Durable receipts and traces: 20
- Trace verdicts matched receipts: 20
- Productive GO: 18
- Expected safety block: 2
- Unexpected NO-GO: 0
- CONFIG-BLOCKED: 0
- Lane truth warnings: 0

Latest accepted run from the Level 5R2 full matrix:

- Run ID: `fip0-2aa8cc99f2fc1657`
- Verdict: `GO: fip5_required_verifier_and_repair_complete`
- Trace version: `fip6.operator_trace.v1`

## Boundaries

Do not start post-Level-5 expansion from this context without Britton approval.

Do not:

- add TinyFish;
- create xersearch;
- start new model lanes;
- promote Cartographer route ownership;
- resume or invent another ladder;
- use old artifact-only scoring authority;
- commit or push without explicit approval.

## Next Approved Options

These are options only. Do not execute any option until Britton explicitly approves it.

Option A: commit/stage preparation only.

```text
BRITTON GO COMMIT/STAGE PREPARATION ONLY

Purpose:
Prepare a reviewable staging plan for the accepted Source Proxy/FIP/Integrated Level work after Integrated Level 5R2 GO.

Do not commit.
Do not push.
Do not start post-Level-5 expansion.
Do not delete or revert unrelated dirty work.

Use docs/evidence/source-proxy-full-integration-pivot/post-level-5-stabilization-closeout.md as the resume authority.

Return:
- exact staging groups
- files included and excluded
- risk notes
- proposed commit messages
- checks to rerun before Britton approves commit

Stop after staging plan.
```

Option B: post-Level-5 expansion planning only.

```text
BRITTON GO POST-LEVEL-5 EXPANSION PLANNING ONLY

Purpose:
Plan the next Source Proxy expansion after Integrated Level 5R2 GO without implementing it.

Do not code.
Do not start new model lanes.
Do not add TinyFish.
Do not create xersearch.
Do not promote Cartographer route ownership.
Do not commit or push.

Use docs/evidence/source-proxy-full-integration-pivot/post-level-5-stabilization-closeout.md as the resume authority.

Return:
- candidate expansion goals
- risks and prerequisites
- proposed acceptance gates
- required evidence artifacts
- exact next implementation prompt

Stop after plan.
```

Option C: Cartographer route-ownership promotion plan.

```text
BRITTON GO CARTOGRAPHER ROUTE-OWNERSHIP PROMOTION PLAN ONLY

Purpose:
Plan what would be required to promote Cartographer from advisory context to route ownership after Integrated Level 5R2 GO.

Do not implement.
Do not promote Cartographer.
Do not change routing.
Do not start new model lanes.
Do not add TinyFish or create xersearch.
Do not commit or push.

Use docs/evidence/source-proxy-full-integration-pivot/post-level-5-stabilization-closeout.md as the resume authority.

Return:
- proposed ownership contract
- risk analysis
- migration steps
- tests and receipts required
- GO/NO-GO gate for actual implementation

Stop after plan.
```

Option D: TinyFish/cloud search evaluation plan.

```text
BRITTON GO TINYFISH/CLOUD SEARCH EVALUATION PLAN ONLY

Purpose:
Plan a TinyFish/cloud-search evaluation after Integrated Level 5R2 GO.

This requires Britton approval before any provider call, credential use, cloud search, or implementation.

Do not add TinyFish.
Do not create xersearch.
Do not call cloud providers.
Do not change Source Proxy code.
Do not commit or push.

Use docs/evidence/source-proxy-full-integration-pivot/post-level-5-stabilization-closeout.md as the resume authority.

Return:
- evaluation questions
- approval requirements
- secret-safety plan
- receipt and attribution requirements
- exact implementation-gate prompt

Stop after plan.
```

Option E: Integrated Level 6 stress/soak plan.

```text
BRITTON GO INTEGRATED LEVEL 6 STRESS/SOAK PLAN ONLY

Purpose:
Plan an Integrated Level 6 stress/soak gate after Integrated Level 5R2 GO.

Do not run Level 6.
Do not start post-Level-5 expansion implementation.
Do not add TinyFish.
Do not create xersearch.
Do not start new model lanes.
Do not commit or push.

Use docs/evidence/source-proxy-full-integration-pivot/post-level-5-stabilization-closeout.md as the resume authority.

Return:
- stress/soak matrix proposal
- runtime duration and prompt categories
- failure buckets
- receipt/trace requirements
- readiness criteria
- exact run prompt for Britton approval

Stop after plan.
```

## Recommended Next Gate

Recommended next gate: Option A, commit/stage preparation only.

Reason: the accepted Source Proxy/FIP/integrated work is now broad and proven; preparing a reviewable staging plan reduces risk before any expansion planning or implementation.
