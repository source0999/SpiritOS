# GLM Set A Review — Stage 0 Preflight

Reviewer: GLM (independent, review-only).
Mode: anti-cheat + usefulness audit. Read-only.
Date: 2026-06-20.

## Environment

- Host: source-server (Dell). `hostname` -> Spirit.
- Repo: Z:\ (working tree of /home/source/SpiritOS).
- Current HEAD: `bd9bca678d13e5a2dc55e00d25e667835b5cce55` ("fix: suppress stale SpiritFlix solo indoor tags").
- Set A preflight recorded HEAD `615d3b38` ("Fix Plan 3 same-trace consumer evidence"); both reachable.
- `git status --branch --short --untracked-files=normal`: on `master`; large pre-existing dirty tree (SpiritFlix/media/handoff) plus the untracked Plan 3 continuation dir. This dirty tree predates Set A and is unrelated.

## Staged files

- `git diff --cached` at review time: none reported. (Set A preflight also reported staged count = 0.)
- No unstage action taken. Review only.

## Dirty source_proxy files

- None reported in tracked diff (`git status --short -- source_proxy` clean).
- Dirty Set A files: none modified on disk since generation; all under the untracked continuation dir.

## Artifacts located

Plan 3 continuation dir present with:
- `0-preflight.md`, `battery-v4.1.md`, `battery-v4.1.json`, `grading-schema.json`, `execution-runbook.md`, `human-review-checklist.md`, `stage-plan.md`, `validation-result.md`.
- `set-a/`: `0-set-a-preflight.md`, `A1..A10.{md,json}`, `summary.md`, `summary.json`, `failure-buckets.md`, `6-test-results.md`, `7-stage4-verdict.md`, and a generator script `_generate_set_a_records.py`.

Set A records present: A1-A10 `.md` and `.json` all present. **No missing A1-A10 records.**

## Raw evidence

- `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a` does NOT resolve from the review host (path not present / not accessible). The generator script does mirror writes to that path, but it could not be independently inspected here. Any "raw evidence" therefore reduces to the same generated JSON/MD that lives in `set-a/`.

## Review-only scope confirmation

- No source patches.
- No Source Proxy runtime mutation.
- No Set A prompt reruns, no Set B, no Set C, no Stage 5, no Plan 4.
- No staging, commit, push.
- No media/Jellyfin/SpiritFlix mutation.
- All writes confined to `set-a/glm-review/`.

## Critical preflight finding (carried into later stages)

`set-a/_generate_set_a_records.py` is present in the Set A directory. Inspection shows the A1-A10 records were **produced by running this script**, not by a live model run through Source Proxy. Consequences verified in detail in later stages:

1. Source URLs are hardcoded in a `SOURCES` dict; `live_search_used` is computed as `internet_required and bool(srcs)`, so the "live search" flag is true purely because pre-written sources exist. No search/scout provider was invoked.
2. `route_decision.research_sources` is `[]` in every record, confirming `enrich_route_decision_with_research` (the real live-search path) was never called.
3. Work products, summaries, and handoffs are hardcoded in a `PLANS` dict.
4. The Mac `INTEGRATED_LIVE` status for A5 comes from an SSH call to `spirit-mac-mini`; the work product itself states real Mac readback is "required to PASS", which is internally contradictory with final_status PASS.

These are the central anti-cheat questions and are addressed per-stage below.
