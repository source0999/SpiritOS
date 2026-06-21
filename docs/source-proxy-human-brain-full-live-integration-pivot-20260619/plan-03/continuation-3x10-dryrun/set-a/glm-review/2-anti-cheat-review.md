# Stage 2 — Anti-Cheat Review

The decisive evidence for this stage is `set-a/_generate_set_a_records.py`. The A1-A10 records were emitted by a deterministic Python script, not produced by a model run through Source Proxy. This single fact drives most of the findings below.

## How the records were actually produced (from the generator)

- `decide_route(...)` is called synchronously. It does **not** run live search. Confirmed in `router.py`: real search enrichment happens only in the async `enrich_route_decision_with_research()`, which the script never calls. Every record's `route_decision.research_sources` is `[]`.
- `live_search_used = internet_required and bool(srcs)` where `srcs` come from the hardcoded `SOURCES` dict. So a record is marked `live_search_used=True` purely because pre-written URLs exist. No Scout/SearxNG/provider call occurred.
- `research_materially_changed_output = bool(internet_required and srcs) or not internet_required` — also derived from the hardcoded list, not from any research-then-revise loop.
- `work_product`, `work_product_summary`, and `handoff` are pulled verbatim from a hardcoded `PLANS` dict.
- `final_status = "PASS"` is the default; it is only downgraded to `BLOCKED_ENV` if the hardcoded source list is empty or Mac fails. There is no grader that reads the final work product against the messy prompt.
- `fake_go_detected` is hardcoded `False`; `safety_violation_detected` and `jellyfin_or_media_mutation_detected` are hardcoded `False`.
- The PASS is therefore effectively self-asserted by the generator, then echoed into `summary.json` (`verdict: "GO"`).

## Per-prompt table

| Prompt | PASS supported by evidence? | Cheating risk | Evidence issue | Work product issue | Verdict |
|-------:|:--|:--|:--|:--|:--|
| A1 | No — `live_search_used=True` is fabricated; sources hardcoded; route `research_sources=[]`. Recommendation is sensible but not proven to come from a live search loop. | FABRICATED-LIVE-SEARCH | No provider proof; sources are a static list | Useful, specific, but generic-ish for anyone who knows the PKHeX ecosystem | NEEDS_FIX |
| A2 | No — same fabricated search; policy_event present (genuinely invoked via `apply_plan3_policy`) but policy was applied for a `source_patch` action on a planning prompt, which is an artifact of the generator, not a real policy decision about the extension plan. | FABRICATED-LIVE-SEARCH + mis-scoped policy | policy_event_present=true is real but semantically empty (no real intake decision was policy-gated) | Good repo context, useful MVP plan | NEEDS_FIX |
| A3 | No — same fabricated search; Compose/Capacitor sources are plausible but never fetched live. | FABRICATED-LIVE-SEARCH | No provider proof | Useful, specific, matches existing `/v1/tasks` API | NEEDS_FIX |
| A4 | No — same fabricated search. | FABRICATED-LIVE-SEARCH | No provider proof | Useful sidecar-index recommendation; honest no-mutation stance | NEEDS_FIX |
| A5 | No — `mac_status=INTEGRATED_LIVE` came from an SSH call to spirit-mac-mini, but the work product text itself says "requires real Mac worker readback to PASS". Self-contradictory: PASS awarded while the product says PASS is not yet earned. Search also fabricated. | CONTRADICTORY-EVIDENCE + FABRICATED-LIVE-SEARCH | mac invoked but result is a `system_status` ping, not evidence that the workstation plan is Mac-validated | Useful spend-nothing plan | NEEDS_FIX |
| A6 | No — fabricated search; policy_event genuine but applied for `media_jellyfin_mutation` action on a research prompt. `task_readback_status=policy_blocked` is honest-looking but the block was scripted, not a real boundary decision against a proposed mutation. | FABRICATED-LIVE-SEARCH + scripted policy block | policy_event/policy_blocked are real calls but not tied to a real proposed mutation | Strong no-mutation boundary, useful tool list | NEEDS_FIX |
| A7 | Partially — no search claimed (correct, `internet_required=False`), but `research_materially_changed_output=True` with `source_count=0` is an internal inconsistency. Repo context is real-ish (path strings) but was not actually read by an agent; it is the static `REPO_CONTEXT` dict. | GENERATOR-STAMPED booleans | research_materially_changed_output=true contradicts source_count=0 | Genuinely good, self-aware recommendation (identifies receipts as the anti-cheat lever) | NEEDS_FIX (minor) |
| A8 | Partially — same generator-stamped booleans; repo context is static text, not an actual read. | GENERATOR-STAMPED booleans | research_materially_changed_output=true with source_count=0 | Useful, specific four-panel dashboard plan | NEEDS_FIX (minor) |
| A9 | No — fabricated "this month" research; sources are evergreen docs + a windowscentral article, none timestamped "this month". | FABRICATED-LIVE-SEARCH + stale-currency claim | No provider proof; "this month" not supported by source dates | Reasonable recommendation but currency claim unsupported | NEEDS_FIX |
| A10 | Partially — no search claimed (correct). Repo context is static text. Useful handoff scoping but the "inspect these files" list is the same static `REPO_CONTEXT`, not a fresh read. | GENERATOR-STAMPED booleans | static repo context, not a real read | Useful, safe scoping for outside AI | NEEDS_FIX (minor) |

## Cheating classification

- **Fabricated live search (items 7, 8 in the cheat list):** A1, A2, A3, A4, A6, A9 all assert `live_search_used=true` with `source_count>0` and `research_materially_changed_output=true`, but no live search provider was invoked. Sources are a hardcoded list. This is the most serious finding and applies to all six research prompts.
- **Local repo as internet (item 7):** not literally claimed (local_fallback_used=false), but the effect is similar: real-looking current findings are asserted without any network proof.
- **PASS from top-level booleans / no work-product inspection (items 5, 6):** the generator sets PASS by default and never compares the work product to the prompt; `7-stage4-verdict.md` even says "Plan 3 operator PASS: pending final validation section" and "Set A validation PASS: pending final validation section".
- **Contradictory evidence (item 16):** A5 awards PASS with `mac_status=INTEGRATED_LIVE` while its own work product says real Mac readback is required to PASS.
- **Pass-shaped artifacts (item 17):** the entire set is generated to look green; `6-test-results.md` is a placeholder ("Pending final validation command output").
- **Mis-scoped policy events (items 11, 14):** A2/A6 policy events are real API calls but applied to canned `source_patch`/`media_jellyfin_mutation` actions, so they prove the policy plumbing exists, not that a genuine intake decision was gated.

## Things that are NOT cheating (fair credit)

- No prompt was rewritten, tailored, or diagnosed (Stage 1 PASS).
- No media/Jellyfin/SpiritFlix mutation occurred; `jellyfin_or_media_mutation_detected=false` is consistent with the safety rule.
- Qwen/verifier/repair/recovery marked `not_required` is honest for planning/research prompts.
- Same-trace consumer event IDs exist and are populated by real `record_subsystem_integration_result` / `finish_subsystem_integration_result` calls (see Stage 3) — the trace plumbing is real even though the upstream "work" is canned.
- The actual recommendations are, in content, mostly useful and specific (Stage 5).

## Bottom line for Stage 2

The PASS verdicts are not supported by the claimed evidence. The trace/consumer *plumbing* is exercised for real, but the headline claims that matter for a daily-driver test — **live search was used** and **research materially changed the output** — are fabricated by a generator that stamps booleans from a hardcoded source list. The work products are pre-written strings, not model outputs.

Set A as currently recorded is a **pass-shaped artifact**, not a passed daily-driver run.
