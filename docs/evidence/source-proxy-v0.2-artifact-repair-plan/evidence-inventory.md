# Evidence Inventory

## `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/`

Found: Yes.

Contains: Original June 12 Source Proxy general intelligence diagnostic with `diagnostic-summary.md` and per-run `receipt.json`, `score.json`, `transcript.txt`, `workspace.diff`, and `evidence-packet.json` files for 10 prompts.

Key findings: The batch used disposable workspaces and did not mutate real app files. It showed strong evidence for model-authored file creation and receipts. It labeled calculator, dark theme, todo, weather, and habit tracker as PASS by heuristic, but the summary itself warned that interactive usefulness and semantic app behavior needed stricter verification. Timer failed as missing ticking/control logic. Notes became markdown. Music player, password checker, and drawing pad produced no usable preview artifact.

Influence on v0.2: Preserve the raw evidence model, but do not let heuristic usability or preview existence become final product PASS. Add behavior contracts and failure packets before repair.

## `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612-real-behavior-audit/`

Found: No.

Contains: Missing during this planning pass.

Key findings: No proof can be claimed from this directory. Its absence should be recorded in closeout and treated as an evidence gap.

Influence on v0.2: v0.2 must rely on the available revamped behavior checks and v0.1 fixture contract instead of inventing audit results.

## `docs/evidence/source-proxy-general-intelligence-diagnostic-revamped-20260612/diagnostic-summary.md`

Found: Yes.

Contains: Revamped 11-prompt diagnostic summary with source_proxy_status, behavior_truth_label, file counts, HTML paths, and reason codes.

Key findings: Summary rows mark homepage, timer, calculator, dark theme, todo, and weather as PASS; music player, habit tracker, notes, password checker, and drawing pad as FAIL. Missing-artifact cases are explicit. The summary says browser behavior checks were not run inside the generation batch and static behavior probes are labeled separately.

Influence on v0.2: Final verdict cleanup must merge route/generation status with later behavior verification and prevent summary PASS from overriding browser FAIL.

## `docs/evidence/source-proxy-general-intelligence-diagnostic-revamped-20260612/manifest.json`

Found: Yes.

Contains: Prompt list, run slugs, source proxy statuses, behavior truth labels, reason codes, files, and HTML paths.

Key findings: All 11 runs have run directories. Missing artifacts are represented as `EXPECTED-BLOCKED` with `no_artifact_files`. Notes has only `notes_app.md`. Habit tracker has HTML/CSS/JS but fails with `habit_controls_or_state_change_missing`.

Influence on v0.2: The intent resolver and artifact readiness gates should distinguish no-artifact, markdown-only, static UI, and behavior-failed states.

## `docs/evidence/source-proxy-general-intelligence-diagnostic-revamped-20260612/behavior-check-results.json`

Found: Yes.

Contains: Browser/product behavior checks for homepage, timer, calculator, dark theme, and habit tracker.

Key findings: Homepage PASS by text inspection. Timer PASS by start/wait/stop/freeze proof. Calculator FAIL because display stayed `0` instead of `5`. Dark theme FAIL because computed colors did not change after toggle. Habit tracker FAIL because no inputs, buttons, checkboxes, or state-changing controls were present.

Influence on v0.2: This is the clearest evidence that final PASS must require behavior proof and that failure packets should include observed state, expected state, path, test name, and reason.

## `docs/evidence/source-proxy-general-intelligence-diagnostic-revamped-20260612/artifact-review-summary.json`

Found: Yes.

Contains: Review report metadata, old/new roots, prompt count, browser behavior check count, and summarized browser results.

Key findings: It records five browser behavior checks and points to `artifact-behavior-report.html`. It explicitly calls calculator, dark theme, and habit tracker FAIL even though generation status was GO.

Influence on v0.2: The final verdict aggregator must prefer behavior-check truth over weaker route/file/proxy status.

## `docs/evidence/source-proxy-general-intelligence-diagnostic-revamped-20260612/artifact-behavior-report.html`

Found: Yes.

Contains: Human review page for artifact behavior results.

Key findings: The file exists and should remain a review surface, but this planning task did not rely on it for extra claims beyond the JSON summaries.

Influence on v0.2: v0.2 should continue producing reviewable HTML surfaces while keeping machine-readable JSON canonical.

## Revamped per-run files under `runs/<slug>/`

Found: Yes for all 11 runs.

Contains: Each run has `receipt.json`, `score.json`, `transcript.txt`, `workspace.diff`, and `evidence-packet.json`.

Key findings: The raw model prompt/response and file outputs are preserved. This supports anti-cheat review and lets repair prompts cite observed failure evidence without mutating the original run.

Influence on v0.2: Repair attempts should create new attempt-specific receipts, diffs, transcripts, behavior results, and final verdict records.

## `docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/`

Found: Yes.

Contains: v0.1 planning/control-plane evidence across phases 0-10, including truth labels, memory contract, intake/context router, permission previews, worker selector, behavior verifier fixtures, safe execution previews, integrated dry-run loop, timer proof, and closeout.

Key findings: v0.1 is GO for an evidence-backed foundation only, not autonomous execution. It explicitly deferred automatic learning, Obsidian write-back, multi-lane execution, automatic worker starts, model limitation memory, broad UI rebuild, and autonomous execution.

Influence on v0.2: v0.2 should reuse v0.1 contracts and stay permission-gated. Repair is a new bounded capability, not permission to start autonomous execution.

## `phase-1/canonical-truth-contract.md`

Found: Yes.

Contains: Canonical labels and evidence strength rules.

Key findings: Product PASS requires verified behavior against acceptance criteria. Artifact existence, preview opens, static content, route liveness, and model self-report are not enough.

Influence on v0.2: Final verdict cleanup must be Phase 1 and must use canonical labels consistently.

## `phase-6/behavior-fixture-contract.md`

Found: Yes.

Contains: June 12 fixtures for calculator, dark theme, habit tracker, timer, notes, and missing-preview failures.

Key findings: Calculator, dark theme, and habit tracker are corrected false positives. Timer is a corrected false negative. Notes markdown-only and missing preview cases must remain failures for artifact readiness/behavior.

Influence on v0.2: These fixtures become regression proof inputs for repair-loop design and re-test integration.

## `phase-10/v0.1-readiness-report.md`

Found: Yes.

Contains: v0.1 readiness verdict, established contracts, protected flows, preserved fixtures, deferred work, and residual risks.

Key findings: v0.1 is not a GO for autonomous execution, worker starts, provider calls, Obsidian write-back, production Source Proxy refactors, or multi-lane benchmarks.

Influence on v0.2: The repair plan must begin with approval-gated phases and keep all work local, disposable, and reviewable.
