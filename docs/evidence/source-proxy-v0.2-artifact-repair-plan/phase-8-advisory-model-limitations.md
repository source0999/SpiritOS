# Phase 8 Advisory Model Limitation Notes

Phase: Phase 8 - Advisory model limitation memory.

Status: Local evidence only. No Obsidian write-back, Codex memory-store write, automatic learning loop, or model policy hardcoding was performed.

## Purpose

Record advisory local-Qwen strengths and limitations observed from the approved Source Proxy diagnostic evidence and v0.2 phases. These notes are guidance for future routing, verification, repair, and handoff decisions. They are not a benchmark answer key and must not be treated as immutable product policy.

## Advisory Strengths

- Qwen can often produce small disposable HTML/CSS/JS artifacts from blunt create prompts.
- Qwen can follow Source Proxy file-action structure well enough for receipts, transcripts, diffs, and evidence packets to be preserved.
- Qwen is useful when work is low-risk, local, disposable, path-guarded, and paired with explicit behavior contracts.
- Qwen can produce true useful behavior in some cases; the timer proof must be preserved as a corrected PASS when start/count/stop/freeze behavior works.

## Advisory Limitations

- Plausible UI does not imply working behavior.
- Route `GO`, file creation, preview opening, static DOM presence, or model self-report cannot become product PASS.
- Qwen may produce app-like surfaces whose core interactions fail, such as calculator arithmetic, theme visual change, or stateful habit tracking.
- Qwen may confuse app/document intent when the prompt contains noun collisions such as `notes app`.
- Qwen may produce missing or unusable preview artifacts for interactive prompts such as music player, password checker, or drawing pad.
- Qwen repair attempts must be bounded, local-only, and restricted to disposable generated artifact workspaces.

## Advisory Routing Guidance

Use local Qwen when:

- The task is a small disposable artifact or bounded repair.
- Allowed artifact paths are explicit and inside the disposable workspace.
- A behavior contract exists before generation or repair.
- Failure evidence includes expected behavior, observed behavior, and reason codes.
- A post-repair verifier can keep behavior PASS/FAIL/UNVERIFIED honest.

Produce HANDOFF when:

- The task needs production source edits.
- The task needs provider/API/high-usage/Codex escalation.
- The local worker is unavailable or fails repeatedly.
- The artifact path is missing, unsafe, or outside the allowed disposable workspace.
- The repair result remains failed, unverified, or needs stronger approved routing.

## Anti-Overfitting Rule

The June 12 prompts are fixtures and examples. They should inform generic behavior categories:

- arithmetic correctness
- computed visual theme change
- stateful list or habit mutation
- editable notes behavior
- password feedback change
- pointer/canvas drawing state
- local demo card fields and optional local controls
- preview/artifact readiness

They must not become special-case answer patches, prompt-specific shortcuts, or bypasses around verification.

## Evidence Basis

- Original diagnostic: `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/`
- Revamped diagnostic: `docs/evidence/source-proxy-general-intelligence-diagnostic-revamped-20260612/`
- v0.1 truth and behavior fixtures: `docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/`
- v0.2 Phase 0-7 local evidence in this plan directory.

Known missing evidence remains missing:

- `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612-real-behavior-audit/`

## Conclusion

Qwen is a useful local worker for scoped disposable artifact work, but Source Proxy must surround it with intent resolution, behavior contracts, failure packets, bounded repair attempts, re-test aggregation, and explicit handoff. These notes are advisory only.
