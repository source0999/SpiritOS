# Source Proxy Level 4 First Hard Artifact Complexity Proof

Date: 2026-06-13

Status: complete.

## Preflight

- Level 3 Gate B accepted status: GO.
- Level 3 Gate B baseline: final clean similar 10 rerun reached 9/10 behavior PASS against an 8/10 threshold.
- Level 3 anti-cheat: clean.
- Level 3 anti-tailoring: clean in searched runtime/source scopes.
- Remaining Level 3 backlog item: `make a dusk dawn palette switch` still failed behavior with `theme_no_computed_state_change`; backlog only, not a Level 4 blocker.
- Current git status before Level 4 evidence files: `## master`.
- Existing dirty files present before Level 4 evidence files: no normal tracked/untracked entries reported by `git status --branch --short --untracked-files=normal`.
- Runtime source patching to pass Level 4: prohibited for this task and not part of this proof.
- Evidence folder: `docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/`.
- Exact Level 4 GO threshold: at least 8/10 Level 4 behavior PASS with clean anti-cheat, clean anti-tailoring, usable traces and mini context pack.

## Required Artifacts

This folder is the evidence root for the first Level 4 hard artifact proof. Required outputs are produced here, with per-prompt trace files under `per-prompt-traces/` and disposable run outputs under `level-4-runs/`.

## Final Result

- Verdict: NO-GO.
- Level 4 pass/fail: 5 PASS, 5 FAIL.
- Threshold: 8/10 Level 4 behavior PASS for GO.
- Probe capability result: existing Gate B probe was Level 3-shaped, so the pre-run evidence-only Level 4 wrapper was used for strict two-observation scoring.
- Route/intake result: 9/10 routed GO; `level4-clean-08` routed EXPECTED-BLOCKED with no preview.
- Multi-step behavior result: 5/10 passed the strict Level 4 wrapper.
- Repair result: 3 disposable model-authored repair attempts; failures remained after strict Level 4 probing.
- Anti-tailoring: No exact prompt tailoring found in searched runtime/source scopes.
- Anti-cheat: clean for cheat contamination.
