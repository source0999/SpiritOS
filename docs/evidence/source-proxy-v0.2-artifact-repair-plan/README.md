# Source Proxy v0.2 Artifact Repair Intelligence Plan

This directory is a plan-only packet for Source Proxy v0.2 Artifact Repair Intelligence. No Source Proxy implementation has started here, no generated artifact has been repaired, and no provider/model calls were run for this planning task.

## What v0.2 is

v0.2 is the planned bridge from truth-telling diagnostics into a limited local repair loop around local Qwen-generated artifacts. The target flow is:

`user prompt -> intent resolver -> behavior contract -> initial generation -> artifact/preview check -> browser/product behavior check -> failure packet -> limited local repair attempt -> re-test -> final PASS / FAIL / HANDOFF`

## Why it exists

v0.1 made Source Proxy better at telling the truth. It preserved receipts, transcripts, scores, diffs, evidence packets, review pages, canonical labels, permission boundaries, and behavior fixtures. The inspected evidence shows that truth is necessary but not enough: Source Proxy can now identify wrong behavior, but it does not yet coach the local worker through a bounded repair attempt.

## What v0.1 proved

- Disposable artifact workspaces can be used without mutating the real app.
- Prompt transcripts, receipts, scores, diffs, and evidence packets can preserve the raw proof trail.
- Runtime GO, preview existence, and file creation are weaker signals than behavior proof.
- Canonical truth labels prevent false PASS results when behavior is failed, blocked, or unverified.
- Behavior checks caught false positives for calculator, dark theme, and habit tracker.
- The timer false negative was corrected by direct behavior proof.

## What v0.2 should fix

- Infer artifact intent before generation, especially for blunt app prompts.
- Create an explicit behavior contract before generation and verification.
- Turn behavior failures into precise failure packets.
- Allow a small, local-only repair loop in disposable generated artifact workspaces.
- Re-test after repair and emit a final canonical verdict.
- Produce a handoff packet when local repair fails, is unsafe, or is out of scope.

## What v0.2 will not do

v0.2 is not a calculator patch, hardcoded benchmark helper, full brain revamp, multi-lane benchmark plan, automatic Obsidian write-back, broad `/coding` UI rebuild, hidden worker launcher, or paid/API/Codex escalation path. Paid/API/Codex/high-usage escalation requires Britton approval.

## Evidence inspected

- `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/`
- `docs/evidence/source-proxy-general-intelligence-diagnostic-revamped-20260612/`
- `docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/`
- Nearby diagnostic summaries, manifests, behavior checks, artifact review summary, receipts, scores, transcripts, diffs, and evidence packets under those roots.

The requested `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612-real-behavior-audit/` directory was not found during this planning pass.

## Plan status

Plan verdict: GO for planning review only. Implementation started: No.
