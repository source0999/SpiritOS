# Source Proxy Expectation Scoring And Advanced Diagnostics Summary

This task implemented a generic additive expectation scoring layer over Source Proxy Product artifact evidence. It did not tune generation prompts, add prompt-specific branches, add hidden templates, patch generated artifacts, activate sidecars, write Obsidian, or expand benchmarks.

## What Was Implemented

- `source_proxy/decision/expectation_scoring.py`: generic expectation score evaluator and reason-code vocabulary.
- `expectation_score` is now added to Product path `score.json` before browser evidence; it remains `WEAK_PASS` when behavior is still unverified.
- Replay scoring over the existing 10-run evidence folder.
- Fresh scored 10-run diagnostic batch using the exact same blunt prompts.
- Per-run `expectation-score.json` after browser/open behavior evidence is attached.

## Replay Existing Evidence

Replay counts: `{'PASS': 10}`

| Prompt | Product Verdict | Behavior | Usability | Intent |
|---|---|---:|---:|---:|
| make a timer app | PASS | 100 | 100 | 100 |
| make a calculator app | PASS | 100 | 100 | 100 |
| make dark theme switcher page | PASS | 100 | 100 | 100 |
| make a todo list app | PASS | 100 | 100 | 100 |
| make a weather card demo | PASS | 100 | 100 | 100 |
| make a music player mockup | PASS | 100 | 100 | 100 |
| make a habit tracker | PASS | 100 | 100 | 100 |
| make a notes app | PASS | 100 | 100 | 100 |
| make a password strength checker | PASS | 100 | 100 | 100 |
| make a simple drawing pad | PASS | 100 | 100 | 100 |

## Fresh Scored Batch

Fresh counts after browser evidence: `{'PASS': 10}`

Important distinction: initial live `score.json` expectation verdicts were `WEAK_PASS` because browser behavior was not attached yet. After open/console and behavior probes were attached, all 10 became PASS.

| Prompt | Initial Live Score | Browser Probe | Final Product Verdict |
|---|---|---|---|
| make a timer app | WEAK_PASS | PASS | PASS |
| make a calculator app | WEAK_PASS | PASS | PASS |
| make dark theme switcher page | WEAK_PASS | PASS | PASS |
| make a todo list app | WEAK_PASS | PASS | PASS |
| make a weather card demo | WEAK_PASS | PASS | PASS |
| make a music player mockup | WEAK_PASS | PASS | PASS |
| make a habit tracker | WEAK_PASS | PASS | PASS |
| make a notes app | WEAK_PASS | PASS | PASS |
| make a password strength checker | WEAK_PASS | PASS | PASS |
| make a simple drawing pad | WEAK_PASS | PASS | PASS |

## Real General Create-Artifact Competence Observed

- Source Proxy inferred blunt create/artifact/product intent for all 10 prompts without explicit targets or file names.
- Qwen remained the selected primary local coding/action lane.
- The model chose paths and authored file bytes; backend-created content was not detected.
- Artifacts opened in browser and passed the existing obvious-behavior probes, including calculator arithmetic.
- No web search, Obsidian, live Cartographer routing, live sidecars, or external provider/API route was used.

## Where Scoring Is Still Shallow

- Usability depth is still probe-level: a PASS proves the obvious interaction worked, not that the artifact is polished or complete.
- Intent fit is currently inferred from route/task/artifact/behavior evidence, not from a richer natural-language rubric.
- External resource reasonability is recorded generically, but richer media/current-info prompts need separate evidence.
- Accessibility, responsive layout, keyboard support, and design quality are not deeply scored yet.

## Failure Interpretation Guide

- Bridge issues: parsed actions missing, files attempted but not created, file bytes do not match model-authored content, or backend-authored content appears.
- Model output issues: generated artifact opens but obvious behavior fails, controls are absent, state does not change, or linked files are missing.
- Verifier/scorer issues: artifact behaves correctly but browser probe fails, score reason codes contradict raw evidence, or PASS appears without behavior evidence.
- Context/search routing issues: local artifact prompts trigger unnecessary web search, current-info prompts skip needed search, or context sources are hidden.

## What Should Be Tuned Next

- Expand expectation scoring dimensions for usability depth, accessibility, layout/runtime quality, and richer intent fit.
- Add structured checks for missing linked assets and external resource reasonability.
- Keep browser expected/actual evidence attached to final product verdicts.
- Build scorer reports that compare initial live score versus post-browser evidence score.

## What Should Not Be Patched Narrowly

- Do not add prompt-string-specific branches for these 10 prompts.
- Do not add benchmark templates or hidden solution snippets.
- Do not weaken browser probes or scorer gates to preserve clean PASS counts.
- Do not manually fix generated artifacts.
- Do not activate Hermes/Gemma/cloud routes to rescue local output without separate approval.

## Recommended Next Phase

Tune the expectation scorer and diagnostics over more evidence categories without changing generation behavior. A reasonable next phase is Level 2 hardening of scoring/reporting only, or verifier-lane preview testing if explicitly approved. Do not proceed to autonomy or benchmark expansion from this packet.
