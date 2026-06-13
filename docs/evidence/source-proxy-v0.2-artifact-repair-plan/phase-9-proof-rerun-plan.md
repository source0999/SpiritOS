# Phase 9 Proof Diagnostic Rerun Plan

Phase: Phase 9 - v0.2 proof diagnostic rerun plan.

Status: Plan only. No diagnostic rerun was executed.

## Purpose

Define a repeatable, permission-safe proof rerun for Source Proxy v0.2 Artifact Repair Intelligence. The rerun should prove the v0.2 flow against the same 11 blunt prompts, with explicit behavior checks and zero known false positives.

## Frozen Prompt Set

The prompt set must remain identical to the revamped June 12 diagnostic:

1. `init a repo and make homepage for agent lab expermients`
2. `make a timer app`
3. `make a calculator app`
4. `make dark theme switcher page`
5. `make a todo list app`
6. `make a weather card demo`
7. `make a music player mockup`
8. `make a habit tracker`
9. `make a notes app`
10. `make a password strength checker`
11. `make a simple drawing pad`

Do not add, remove, reorder, reword, scaffold, or hint the prompts during the proof rerun.

## Planned Evidence Root

Recommended new disposable evidence root:

`docs/evidence/source-proxy-v0.2-proof-diagnostic-rerun-20260612/`

The rerun must not mutate the original diagnostic roots:

- `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/`
- `docs/evidence/source-proxy-general-intelligence-diagnostic-revamped-20260612/`

## Required Per-Run Evidence

Each run should write:

- `receipt.json`
- `score.json`
- `transcript.txt`
- `workspace.diff`
- `evidence-packet.json`
- `behavior-contract.json`
- `failure-packet.json` if behavior/artifact readiness fails
- `repair-attempts.json` if local repair is attempted
- `retest-result.json` after repair or after artifact readiness/behavior verification
- `handoff-packet.json` if local repair is unavailable, failed, unsafe, out of scope, or needs approval

Top-level evidence should include:

- `manifest.json`
- `diagnostic-summary.md`
- `behavior-check-results.json`
- `artifact-review-summary.json`
- optional `artifact-behavior-report.html`
- `rerun-findings.json`

## Expected Behavior Probes

| Prompt | Required probe |
| --- | --- |
| `init a repo and make homepage for agent lab expermients` | Open homepage and inspect visible body text for agent/lab/experiment intent. |
| `make a timer app` | Start timer, wait, stop, verify elapsed time increased and then froze. |
| `make a calculator app` | Enter or click `2 + 3 =`, expect display/result `5`. |
| `make dark theme switcher page` | Capture computed colors, toggle theme, verify computed background or text color changes. |
| `make a todo list app` | Add an item and verify it appears; complete/delete/change one item if available. |
| `make a weather card demo` | Verify plausible local demo fields for city/temp/condition; interact with local demo control if present. |
| `make a music player mockup` | Verify visible track/player controls; click play/pause or skip and observe state change. |
| `make a habit tracker` | Add/toggle/edit/remove or otherwise change habit state; static hard-coded habits are FAIL. |
| `make a notes app` | Type/create/edit/save visible note text in an app artifact; markdown-only output is FAIL. |
| `make a password strength checker` | Type weak and stronger passwords; verify feedback changes appropriately. |
| `make a simple drawing pad` | Dispatch pointer/mouse drag and verify canvas pixels or drawing state changes. |

## Rerun Command Template

This is a template only and must not be executed until Britton approves the rerun:

```powershell
# DO NOT RUN WITHOUT SEPARATE APPROVAL
$env:SOURCE_PROXY_V02_PROOF_ROOT = "docs/evidence/source-proxy-v0.2-proof-diagnostic-rerun-20260612"
python -m pytest source_proxy/tests/test_artifact_behavior_contract.py source_proxy/tests/test_artifact_repair_contract.py source_proxy/tests/test_artifact_repair_loop.py source_proxy/tests/test_artifact_retest_result.py source_proxy/tests/test_artifact_handoff_packet.py -q
# Approved rerun entrypoint must use the frozen 11 prompts, local-only route, disposable workspaces, and no provider/API escalation.
```

Before any actual proof rerun, identify the real local rerun entrypoint and dry-print the resolved output root. If the local route is unavailable, emit `NEEDS_FIX` or `HANDOFF` instead of escalating.

## Permission Rules

Allowed only after separate rerun approval:

- Create a new disposable evidence root.
- Run the approved local Source Proxy v0.2 proof rerun against the frozen 11 prompts.
- Run local behavior verification needed for the proof rerun.

Still forbidden without separate approval:

- Provider/API usage.
- Codex/high-usage escalation.
- Hidden worker starts.
- Full multi-lane benchmark execution.
- Obsidian write-back.
- Production source repair.
- Mutating original diagnostic artifacts.
- Git branch, commit, push, stash, reset, checkout, clean, or stage operations.

## Target Outcome

Target useful PASS: `7/11` or `8/11`.

Stretch useful PASS: `9/11` if local repair works well.

Required truth target: `0 known false positives`.

Final PASS requires post-repair or direct behavior PASS when behavior is required. Missing or unverified behavior remains `FAIL`, `UNVERIFIED`, `NEEDS_FIX`, `BLOCKED`, `PARTIAL`, or `HANDOFF`, not PASS.

## Dry-Check Result

Phase 9 did not run the rerun. It only defined the frozen prompt set, expected probes, planned evidence root, evidence schema, target score, and permission boundaries.
