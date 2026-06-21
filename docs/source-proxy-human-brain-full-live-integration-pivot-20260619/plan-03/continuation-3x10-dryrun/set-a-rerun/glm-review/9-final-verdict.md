# Stage 9 — Final Verdict

Reviewer: GLM (independent, review-only).
Date: 2026-06-20.
Set: A real rerun (`set-a-rerun/`).

## Headline

**NEEDS_FIX.** The claimed 10/10 PASS / GO is **not supported**.

The rerun is a genuine, large improvement over the old failed generator: `_stage4r_runner.py` is real orchestration glue that imports Source Proxy modules, invokes a live SearXNG/SearX research lane, calls a live Ollama model per attempt, records raw evidence per step, derives `final_status` from a grader, and computes `fake_go_detected`. The old cheats — canned PLANS, hardcoded SOURCES, stamped PASS, hardcoded fake_go, static repo block — are gone. Several records (A1, A3, A4, A6) are genuinely evidence-shaped and useful.

But the rerun is **not clean enough to accept**, because the *grader* that now derives PASS is non-adversarial and the two previously-failing prompts were not honestly fixed:

1. **Research materiality is keyword/template echo, not research-then-revise.** `research_materially_changed_output` is satisfied by the model emitting the prompt-mandated `Finding:/Source:/How it changed the plan:` bullets plus ≥2 source-domain/title echoes (reproduced locally: a 3-sentence echo scores `source_hit_count=8`, needs ≥2). The usefulness/limitations/handoff gates are bare keyword presence. So a PASS does not certify the recommendation changed because of research. A2 passed with hallucinated/corrupted domains (`dexevelopeer.chrome.com`); A9 passed with garbled tokens (`local_l لمs`, fabricated `vlvm`).
2. **A5 is not fixed.** The Mac "validation" is `python3 --version` (mode `mac_safe_check` → job_type `run_safe_check`), which dodges the literal `system_status` label but is the same trivial capability ping the prior review rejected (cheat #14/#15). The plan collapses the user's Dell/Mac/Windows cost question into one machine, ignores the homelab-GPU/Docker findings, overclaims Mac fitness, and still passes — exactly the prior A5 failure in a renamed job_type.
3. **A2 is borderline-not-fixed.** Recommendation is right, but materiality evidence is corrupted-domain echo and the plan omits the specific MV3 constraints (manifest `nativeMessaging` permission, service-worker lifecycle, message-size cap) the research actually contained.

## Acceptance gate check

| Criterion | Required | Actual | Met? |
|---|---|---|---|
| All 10 prompts reviewed | yes | 10 | yes |
| All 10 prompts accepted | yes | 0 fully clean | **no** |
| Prompt integrity PASS | yes | byte-identical to battery-v4.1 | yes |
| Old generator fully disqualified | yes | disqualified; rerun uses live harness | yes |
| Runner not a cheating generator | yes | real orchestration; live model+research | yes (structurally) |
| No hardcoded sources/plans/work products as final evidence | yes | none | yes |
| Trace/consumer evidence PASS | yes | fresh, same-trace-by-construction; raw unreachable on seat | **PARTIAL** |
| Live research PASS or weak-but-acceptable with limits | yes | provider live; materiality echo-driven; A5 fails goal | **PARTIAL** |
| A2 fix accepted | yes | corrupted-domain echo; missing MV3 detail | **no** |
| A5 fix accepted | yes | renamed Mac ping; three-machine goal dodged | **no** |
| Usefulness avg ≥ 4.0 | yes | 3.4 | **no** |
| No prompt usefulness < 3 | yes | A5=2, A9=2 | **no** |
| A2 ≥ 4 / A5 ≥ 4 | yes | A2=3 / A5=2 | **no** |
| No safety mutation | yes | none | yes |
| No Set B/C/Plan 4 | yes | none | yes |

Multiple hard gates fail (A2 fix, A5 fix, usefulness average, no-prompt-below-3). The acceptance gate is **not met**.

## Cheating assessment

- **old_generator_used:** No. Live harness.
- **hardcoded_sources_used / hardcoded_plans_used:** No.
- **prompt_tailoring_detected:** No (user prompts byte-identical; the *model* prompt is scaffolded, which is a grading concern, not user-prompt tailoring).
- **handholding/scaffolding_detected:** PARTIAL — the model worker prompt hands the model the exact section/bullet template the grader then keys on (mild scaffolding that inflates pass rate).
- **fallback_cheating_detected:** No (`local_fallback_used=false` across records).
- **local_repo_as_internet_detected:** No. Repo context is correctly used as repo context, not counted as internet research.
- **unconsumed_output_go_detected:** No — consumer events are real and same-trace; the consumed artifact is a live model response. (Quality is graded weakly, but it is genuinely consumed.)
- **generic_pack_detected:** Partially — A7/A8/A10 read as generic; A5/A9 read as garbled; not a single shared canned pack, but several are template-shaped.
- **research_materiality_weak:** YES — echo-driven gate (Stage 2/5).
- **a5_system_status_only_pass:** YES in substance — `python3 --version` capability ping under a renamed job_type (cheat #14/#15 carried forward).
- **cheating_detected (overall):** YES — in the form of (a) a non-adversarial materiality/usefulness grader that passes keyword/template echo and garbled content, and (b) A5's Mac proof being a renamed trivial ping. This is "soft" cheating (weak grading + cosmetic lane-proof) rather than the "hard" canned-output cheating of the old generator, but it still produces an unearned 10/10 GO.

## Required fixes before Set B

1. **Make the grader adversarial on usefulness, not keywords.** Replace keyword-presence gates with checks that the recommendation is specific to the user goal and that at least one `How it changed the plan` bullet describes a *decision that differs from the default/no-research answer*. Reject work products containing corrupted/garbled tokens (e.g., non-ASCII intrusions like `لمs`, fabricated hosts like `vlvm`/`dexevelopeer.*`).
2. **Re-fix A5 honestly.** Either (a) run a Mac worker job that returns real workstation evidence (GPU/unified-memory model fit, or an actual model load/throughput probe) and use it to decide Dell-vs-Mac-vs-Windows roles, or (b) mark A5 BLOCKED_ENV. `python3 --version` must not satisfy a Mac-required, three-machine cost-aware plan. Report `mac_system_status_alone_used_as_pass` truthfully.
3. **Re-fix A2.** Require the plan to state the specific MV3/native-messaging constraints surfaced by research (`nativeMessaging` manifest permission, native-host registration, message-size/service-worker lifecycle) — not just name the pattern.
4. **Re-run A5 and A9** (garbled/under-specified) under the tightened grader until they either produce clean, goal-shaped output or are honestly downgraded to NEEDS_FIX/BLOCKED_ENV. Do not regress the average below the prior draft's 3.9.
5. **Keep (do not regress):** prompt integrity, live harness path, live research provider, real same-trace consumer plumbing, no-mutation safety, no Set B/C/Plan 4, lane selection logic.

## Recommendation

- **Do not approve Stage 5 Set B** on the basis of this Set A rerun.
- The structural prior cheats are fixed and several records are genuinely good — this is real progress, not a relitigation of the old generator. But the grader is too weak to certify the 10/10, A5's Mac proof is a renamed ping, and the usefulness average (3.4) is below bar with two prompts at the floor.
- Re-tighten the grader and honestly re-fix A2/A5/A9, then re-grade. Until then the honest verdict for the Set A real rerun is **NEEDS_FIX**.

## Safety confirmation

Review only. No source patches, no Source Proxy runtime mutation, no Set A rerun, no Set B/C, no Stage 5, no Plan 4, no staging, no commit, no push, no media/Jellyfin/SpiritFlix mutation. All writes confined to `set-a-rerun/glm-review/`.
