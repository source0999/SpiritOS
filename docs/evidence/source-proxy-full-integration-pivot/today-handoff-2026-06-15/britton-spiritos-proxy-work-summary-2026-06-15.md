# Britton SpiritOS Source Proxy Work Summary

Date prepared: 2026-06-15

Purpose: portable handoff for Britton, group review, GPT grading, and future Codex threads.

## Executive Summary

This work took Source Proxy from the post-FIP-7 uncertainty point through FIP-7R, Integrated Levels 3, 4, 5, 5R, 5R2, and post-Level-5 stabilization. The accepted current state is **Integrated Level 5R2 GO**.

No post-Level-5 expansion has started. TinyFish was not added. xersearch was not created. Cartographer was not promoted to route ownership. No commit or push was performed.

## Timeline

1. Reconciled the repo after a duplicate/stale FIP-4 chat and confirmed the accepted FIP-5/FIP-6/FIP-7 work was still present.
2. Ran FIP-7R remediation only. Fixed slow/local Qwen timeout behavior, Scout overlong-query/no-allowed-packet truth handling, and gauntlet runner timeout issues. FIP-7R closed as GO.
3. Ran Integrated Level 3 against the live Source Proxy stack. Level 3 closed as GO with durable receipts and FIP-6 traces.
4. Ran Integrated Level 4 with a stricter 12-prompt stability/behavior matrix. Level 4 closed as GO.
5. Ran Integrated Level 5 with a 20-prompt full-stack matrix. Level 5 was CONFIG-BLOCKED by two Hermes verifier no-op output-contract failures.
6. Ran Integrated Level 5R. It fixed the no-op Hermes output-contract issue but exposed three unexpected NO-GO rows: two browser/Hermes evidence mismatch rows and one malformed Qwen action output row.
7. Ran Integrated Level 5R2. It remediated the accepted 5R blockers and closed as GO.
8. Wrote post-Level-5 stabilization and active-context handoff docs.
9. Prepared a commit/stage planning recommendation without staging, committing, pushing, deleting, or reverting anything.

## Accepted Final Proof

Integrated Level 5R2 full matrix counts:

```json
{
  "config_blocked": 0,
  "expected_safety_block": 2,
  "go": 18,
  "lane_truth_warning": 0,
  "no_go": 2,
  "posted": 20,
  "productive_go": 18,
  "receipt_and_trace": 20,
  "total": 20,
  "trace_matches_receipt": 20,
  "trace_mismatch": 0,
  "unexpected_no_go": 0
}
```

Latest accepted Level 5R2 run:

- Run ID: `fip0-2aa8cc99f2fc1657`
- Verdict: `GO: fip5_required_verifier_and_repair_complete`
- Trace version: `fip6.operator_trace.v1`

## What Changed In Source Proxy

- Durable FIP-0 receipts became the universal truth record for runtime lane state.
- FIP-1 context lanes were wired as advisory context: Obsidian, Cartographer, Design, Mac advisory status.
- FIP-2 local research truth was wired with honest Scout/SearXNG attribution and no false `used` marking.
- FIP-3 local Gemma/Hermes pre-coder lanes were added while keeping Qwen coding-only.
- FIP-4 final coder packet and Qwen action-output contract were enforced.
- FIP-5 deterministic/browser/Hermes verifier and bounded Qwen repair loop were added.
- FIP-6 operator trace endpoints projected receipt truth without private reasoning.
- FIP-7R made local Qwen slow-output behavior and Scout no-allowed-packet truth durable enough for gauntlet proof.
- Integrated Levels 3, 4, 5, 5R, and 5R2 proved the full stack with receipts and traces.

## Current Runtime Runbook

- Authoritative runtime checkout: Linux `source-server`, `/home/source/SpiritOS`
- Launch command: `npm run proxy:https:lan`
- Source Proxy URL: `https://127.0.0.1:8787`
- Latest receipt: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest`
- Latest trace: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest/trace`
- By-run trace: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/<run_id>/trace`

## Important Boundaries

- TinyFish remains deferred and requires Britton approval.
- xersearch remains missing and must not be created without approval.
- Cartographer remains advisory/preview context, not route owner.
- No post-Level-5 expansion has started.
- Old artifact-only ladders are not scoring authority.
- Safety blocks are scored separately from productive GO.

## Dirty Tree State

The worktree is intentionally broad and dirty. Accepted Source Proxy/FIP work sits beside unrelated SpiritFlix/media work and duplicate/stale FIP-4 artifacts. Do not bulk-stage or bulk-commit.

Recommended next gate: commit/stage preparation approval, with reviewable slices:

1. Source Proxy runtime/code/tests.
2. FIP/integrated runners and evidence, with duplicate/stale FIP-4 exclusions.
3. Stabilization/active-context docs.

## Bundle Contents

This directory contains:

- `britton-spiritos-proxy-work-summary-2026-06-15.md`: this human summary.
- `pack-00-index.xml`: index and grading map.
- `pack-01-governance-closeouts.xml`: closeouts and active context.
- `pack-02-runtime-source.xml`: Source Proxy runtime source and tests.
- `pack-03-runners.xml`: FIP and integrated runner scripts.
- `pack-04-results-matrices.xml`: accepted result matrices and key evidence JSON.
- `pack-05-level5r2-receipts.xml`: Level 5R2 durable receipt set.

## How To Grade

Read the packs in order:

1. `pack-00-index.xml`
2. `pack-01-governance-closeouts.xml`
3. `pack-02-runtime-source.xml`
4. `pack-03-runners.xml`
5. `pack-04-results-matrices.xml`
6. `pack-05-level5r2-receipts.xml`

The shortest review path is summary + Level 5R2 closeout + Level 5R2 results JSON + representative receipts.
