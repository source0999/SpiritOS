# GLM Set A Verdict

Reviewer: GLM (independent, review-only).
Date: 2026-06-20.
Scope: Set A (A1-A10) anti-cheat + usefulness audit.

## Headline

**NEEDS_FIX.** Set A's claim of 10/10 PASS / GO is **not supported** by the evidence.

The ten A-records were produced by a deterministic generator script (`set-a/_generate_set_a_records.py`), not by a live model run through Source Proxy. The recommendations read well, the prompts are genuinely good messy asks, and the causal-trace plumbing (task_id / trace_id / consumer_event_id) is honestly exercised — but the two claims that make this a *daily-driver intelligence test* are fabricated:

1. **Live search was not used.** `live_search_used=true` on A1, A2, A3, A4, A6, A9 is derived from a hardcoded `SOURCES` list. No Scout/SearxNG/provider was invoked; every record's `route_decision.research_sources` is `[]`.
2. **Research did not materially change the output.** Work products and handoffs come from a hardcoded `PLANS` dict; PASS is the generator default and is never derived by reading the work product against the prompt.

## What is genuinely good (do not lose this)

- Prompt integrity: PASS — prompts are clean, messy, human, un-tailored, hidden expectations not leaked.
- Human messy prompt quality: PASS — a solid, hard, broad battery.
- Lane *selection*: correct — Qwen/verifier/repair/recovery honestly `not_required` for planning prompts; no required lane dodged.
- Safety: clean — no media/Jellyfin/SpiritFlix mutation; A6/A10 boundaries explicit and honored.
- Trace plumbing: real — consumer event IDs are produced by real Source Proxy functions and are same-trace (not hand-typed).
- Content quality: decent — usefulness avg 3.9; A6 (media cleanup) and A10 (outside-AI handoff) are genuinely strong; A7 is on-target (it names receipts as the anti-cheat lever).

## What invalidates PASS

- Fabricated `live_search_used` / `research_materially_changed_output` on all six research prompts (A1, A2, A3, A4, A6, A9). Cheat-list items 7 and 8.
- PASS awarded from generator defaults / top-level booleans, with no work-product-vs-prompt grading. Cheat-list items 5 and 6. `7-stage4-verdict.md` itself says operator/validation PASS are "pending final validation section", and `6-test-results.md` is a placeholder.
- A5 self-contradiction: `mac_status=INTEGRATED_LIVE` + PASS, while the work product says "requires real Mac worker readback to PASS". The "integration" is a read-only `system_status` SSH ping, not plan validation. Cheat-list item 16 (contradictory evidence).
- `fake_go_detected=false` is hardcoded and never computed — unreliable.
- `repo_context_used` is one shared static text block for A2-A10, not an in-run read.
- A2/A6 `policy_event_present=true` is real plumbing but fires on canned `source_patch`/`media_jellyfin_mutation` actions, so it proves the gate exists, not that a real intake decision was bounded.

## Acceptance gate check

| Criterion | Required | Actual | Met? |
|---|---|---|---|
| All 10 prompts reviewed | yes | 10 | yes |
| Prompts clean human messy | yes | yes (Stage 1/7) | yes |
| No cheating/handholding/scaffolding/fallback | yes | fabricated live search; generator-stamped PASS | **no** |
| Trace/consumer evidence present | yes | present & real plumbing | yes |
| Research quality adequate | yes | 0/6 with provider proof | **no** |
| Work product usefulness avg >= 4 | yes | 3.9 | **no** |
| No prompt usefulness < 3 | yes | min 3 (A5, A9) | yes |
| No media/Jellyfin mutation | yes | none | yes |
| No hidden expectations leaked | yes | none | yes |

Two hard gates fail (research quality; no-fabrication) and the usefulness average is marginally under 4. The acceptance gate is **not met**.

## Required fixes before Set B (and before re-claiming Set A PASS)

1. Run A1-A10 through the real Source Proxy path (the existing canonical workflow/task harness), one prompt at a time, with a live model — not a generator that stamps booleans.
2. For the six research prompts, actually invoke live search (`enrich_route_decision_with_research` / Scout / SearxNG) and capture provider response evidence to raw evidence (`/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a`). `live_search_used` must be true only when a provider returned results; set `BLOCKED_ENV` honestly if no provider is configured.
3. Make `research_materially_changed_output` derive from a real research-then-revise step (recommendation references a finding fetched in-run), not from `bool(srcs)`.
4. Compute `final_status` and `fake_go_detected` from a grader that reads the final work product against the messy prompt — not from generator defaults.
5. Resolve A5: either run a Mac worker job that actually validates a workstation decision and consume it, or mark A5 BLOCKED_ENV. A `system_status` ping must not satisfy a Mac-required plan.
6. Replace `6-test-results.md` placeholder and the "pending final validation section" lines in `7-stage4-verdict.md` with real validation output, or downgrade the verdict until they exist.
7. Populate `repo_context_used` from an actual in-run read per prompt, or stop asserting it as evidence.
8. Keep (do not regress): prompt integrity, no-mutation safety, lane selection logic, and the consumer-evidence plumbing.

## Recommendation

- Do **not** approve Stage 5 on the basis of the current Set A.
- Treat the current A1-A10 as a **draft scaffold / target answers**, not as passed records. They are useful as expected-output fixtures for a real rerun.
- Re-run Set A through the real harness with live search + a work-product grader, then re-grade. Until then, the honest summary verdict for Set A is **NEEDS_FIX** (not GO), with cheating detected in the form of fabricated live-search evidence and generator-stamped PASS.

## Safety confirmation

Review only. No source patches, no Source Proxy runtime mutation, no Set A reruns, no Set B/C, no Stage 5, no Plan 4, no staging, no commit, no push, no media/Jellyfin/SpiritFlix mutation. All writes confined to `set-a/glm-review/`.
