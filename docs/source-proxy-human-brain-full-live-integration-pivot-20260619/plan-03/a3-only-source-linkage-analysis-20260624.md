# A3-Only Source Linkage Analysis - 2026-06-24

## Scope

- Branch: `integration/cleanup-plan3-debug-20260623`
- Starting HEAD: `0296415db64e0fb4c51d3e865676afbf8a95b90c`
- Prompt in scope: A3 only
- Set B/C: not run
- Plan 4: not started

## Current A3 Failure

- Prompt: `figure out the best path for an android app that lets me start proxy tasks from my phone and check receipts`
- Receipt: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/A3.json`
- Trace: `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/A3.task.final.raw.json`
- Selected lane/model/provider: `ollama_default` / `gemma3n:e4b` / `ollama`
- Status: `NEEDS_FIX`
- Failed gate: `research_change_source_not_from_raw_sources`
- Debugger adequacy: adequate. The receipt names the selected lane/model/provider, failure classification, failed gate, receipt path, trace path, and bounded next action.

## Raw Research Sources

The latest A3 run collected six raw research sources:

- `Send simple data to other apps | App data and files - Android Developers` / `developer.android.com` / `https://developer.android.com/training/sharing/send`
- `Kotlin Multiplatform samples` / `kotlinlang.org`
- `Handle user interaction | Jetpack Compose | Android Developers` / `developer.android.com`
- `Intents in Android for Jetpack Compose Users | by Akshay Sarapure | Medium` / `medium.com`
- `The ULTIMATE Guide to Sharing Data Between Screens in Jetpack ...` / `youtube.com`
- `Take your messaging to the next level — basic, better, and best` / `developer.android.com`

## Leakage Path

Root cause label: `MODEL_SOURCE_LEAKED_INTO_PACKET`

The model output contains valid research-change blocks for Android intent sources, but it also places repo evidence inside the `Research-to-decision changes` section:

- Finding: `The project uses Intents for long-running task creation.`
- Source: `source_proxy/api/long_running_tasks.py`

That repo file is valid repo context, but it is not raw research provenance and must not satisfy research-change source refs. The parser is not crossing into the later repo section; the model leaked repo evidence into the research section. The model also respelled Android host text in some source lines, so accepted research source refs should be canonicalized back to the raw research registry rather than preserving model-owned host spellings.

## Proposed Smallest Honest Fix

- In the existing code-owned research-change repair pass, canonicalize any matched research `Source:` line to the raw source title, host, and URL.
- Drop research-change blocks whose source cannot be matched to the raw research source registry before grading.
- Keep the grader strict: if too few raw-source-backed research-change blocks remain, `research_materially_changed_output` must still fail.
- Keep repo/Mac evidence out of research provenance; repo evidence can still appear in repo/evidence sections, just not as research source proof.
- Do not add prompt-ID branches, fake source acceptance, API/frontier calls, Set B/C execution, or Plan 4 work.
