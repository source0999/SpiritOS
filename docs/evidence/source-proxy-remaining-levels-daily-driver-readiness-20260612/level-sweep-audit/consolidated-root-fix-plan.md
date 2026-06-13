# Consolidated Root Fix Plan

This is a proposal only. No patches were implemented in this sweep.

Do not fix one failed prompt at a time. Do not add deterministic templates. Do not lower thresholds. Do not weaken probes.

## Patch 1: Contract And Probe Metadata Plumbing

Problem: some failed behavior rows cannot enter repair because behavior contract/probe metadata is missing even though browser behavior evidence exists.

Likely files:

- `source_proxy/decision/artifact_behavior_contract.py`
- `source_proxy/decision/artifact_repair_contract.py`
- `source_proxy/decision/artifact_repair_loop.py`
- evidence probe/report scripts under the blunt diagnostics evidence folder

Why this is not prompt tailoring: the patch would move generic behavior contract/probe IDs and observed browser evidence through the existing packet, not add prompt-specific answers or UI code.

Anti-cheat constraints:

- Preserve failed browser behavior as FAIL.
- Do not inject solution code.
- Do not add exact prompt branches.
- Keep missing metadata as HANDOFF if it still cannot be proven.

Tests needed:

- Contract metadata survives score -> behavior probe -> failure packet -> repair prompt.
- Missing metadata remains HANDOFF.
- Real failed probe uses `behavior_failed_verified`, not stale unverified wording.

Evidence needed:

- Before/after packet examples for a prior handoff row.
- Focused tests.
- One local-only disposable rerun after approval.

Promotion gate unblocked: Level 3 disposable behavior reliability and future Level 4 planner traceability.

## Patch 2: Path-Bound Repair Output Contract Hardening

Problem: repair model calls often return free-floating code without Source Proxy action JSON or path-bound file blocks.

Likely files:

- `source_proxy/decision/tool_actions.py`
- `source_proxy/decision/artifact_repair_contract.py`
- `source_proxy/decision/artifact_repair_loop.py`
- `source_proxy/tests/test_artifact_repair_loop.py`
- `source_proxy/tests/test_coding_regression_pack.py`

Why this is not prompt tailoring: it strengthens the generic action contract and diagnostics for all repair attempts rather than teaching any prompt answer.

Anti-cheat constraints:

- Continue rejecting targetless code.
- Keep repair attempts at one unless separately approved.
- Preserve raw rejected transcript and parse decisions.
- Do not auto-wrap backend code into files.

Tests needed:

- Free-floating code remains rejected.
- Valid path-bound file block is accepted only for `.html`, `.css`, `.js` inside disposable workspace.
- Backend-authored repair content is not counted as model-authored.
- Repaired file bytes match model-authored content hashes.

Evidence needed:

- A repair rejection receipt and a valid path-bound repair receipt from local-only runs.

Promotion gate unblocked: Level 3 repair proof; Level 5 verifier evidence quality.

## Patch 3: Planner Criteria To Final Verdict Trace

Problem: planner/task criteria, behavior contracts, probe results, repair results, and final verdict reason codes are not yet a single auditable chain for all rows.

Likely files:

- `source_proxy/decision/task_spec_intake.py`
- `source_proxy/decision/artifact_final_verdict.py`
- `source_proxy/decision/artifact_retest_result.py`
- `source_proxy/decision/verifier_lane.py`
- report/evidence scripts

Why this is not prompt tailoring: it is provenance and verdict accounting. It does not change generated app content or expected answers.

Anti-cheat constraints:

- Route GO, file creation, openable HTML, static DOM, and model self-report remain non-pass signals.
- Browser behavior FAIL cannot become PASS.
- Verifier cannot convert UNVERIFIED into PASS.

Tests needed:

- Final verdict includes planner criterion ID, probe ID, observed actual values, repair attempt count, and evidence refs.
- PASS requires behavior proof for required behavior.
- Failed browser probe produces failure reason codes and no stale unverified-only reason.

Evidence needed:

- Refreshed HTML/JSON report with row-level trace links.
- Strict link and JSON checks.

Promotion gate unblocked: Level 4 context/planner traceability and Level 5 critic packet readiness.

## Patch 4: Generic Interactive Reliability Feedback, Not Templates

Problem: Qwen-authored disposable UIs frequently open but lack visible state changes.

Likely files:

- `source_proxy/decision/artifact_behavior_contract.py`
- `source_proxy/decision/artifact_repair_contract.py`
- `source_proxy/decision/human_messy_homepage.py`
- local-only diagnostic scripts

Why this is not prompt tailoring: the fix must be a generic instruction/contract that says interactive requests require visible state mutation tied to the inferred behavior contract. It must not provide UI templates, prompt-specific snippets, or benchmark answer keys.

Anti-cheat constraints:

- No deterministic app template library.
- No exact prompt mapping to code.
- No generated artifact patching outside model-authored actions.
- No lowering the 8/10 threshold.

Tests needed:

- Generic interactive prompts require behavior contract.
- Static mockups remain allowed only when the prompt is truly non-interactive or the contract explicitly permits static proof.
- Existing anti-cheat/fallback tests still pass.

Evidence needed:

- Fresh local-only rerun after approval showing behavior improvement without scaffold/fallback/backend-authored flags.

Promotion gate unblocked: Level 3 daily-driver behavior reliability.

## Patch 5: Verifier Preview Packet And No-Glaze Harness

Problem: verifier lane exists but is not yet proven as an independent critic against planner criteria and browser evidence.

Likely files:

- `source_proxy/decision/verifier_lane.py`
- `source_proxy/decision/model_lanes.py`
- `source_proxy/decision/cartographer_routing.py`
- `source_proxy/tests/test_verifier_lane.py`
- `source_proxy/tests/test_model_lanes.py`

Why this is not prompt tailoring: it verifies evidence quality and failure classification, not generated app content.

Anti-cheat constraints:

- Verifier cannot edit, repair, or start sidecars.
- Verifier cannot override browser behavior.
- Verifier cannot call cloud/API.
- Verifier cannot see benchmark answers.

Tests needed:

- PASS is downgraded without browser behavior evidence.
- Failed browser behavior remains NEEDS_FIX/HANDOFF/FAIL.
- Missing planner criteria and missing receipt evidence are reported as missing evidence.

Evidence needed:

- Preview-only verifier packets over existing failed rows.
- False-positive audit before any live verifier approval.

Promotion gate unblocked: Level 5 verifier critic readiness and Level 6 routing ownership planning.
