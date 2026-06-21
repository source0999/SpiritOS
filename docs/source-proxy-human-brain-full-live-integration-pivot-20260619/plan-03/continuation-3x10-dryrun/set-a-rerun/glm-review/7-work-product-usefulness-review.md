# Stage 7 — Work Product Usefulness Review

Reviewer: GLM (independent, review-only).
Date: 2026-06-20.

Rubric: 5 = immediately useful, specific, safe, actionable, evidence-shaped · 4 = useful with minor gaps · 3 = plausible but generic · 2 = weak/mostly template · 1 = not useful · 0 = missing.

Bar: average ≥ 4.0; no prompt < 3; A2 and A5 ≥ 4.

## Per-prompt scores

**A1 — Pokémon save editor plan — 4**
Names PKHeX (+ web variant) concretely, references batch editing, save-format handling (sav/dsv/dat/gci), and a build order. Specific and actionable; better than tutorial slop. Gaps: no Gen/format compatibility matrix, no homebrew/CFW extraction step (the sources hint at JKSM/checkpoint), URLs mangled. Useful for Britton to prototype from. 4.

**A2 — Browser extension → Source Proxy task — 3**
Right direction (Native Messaging + native host), names the receiver endpoint files. But: hallucinated/corrupted domains (`dexevelopeer.chrome.com/.mozilla.org`) in the materiality section; no manifest sketch, no `nativeMessaging` permission call-out in the plan, no MV3 service-worker lifecycle caveat, no message-size cap — all of which the in-run research actually contained. A coding agent could start but would have to re-derive the MV3 specifics. Borderline 3/4; the corrupted evidence and missing MV3 detail pull it to 3. 3.

**A3 — Android app to start tasks + receipts — 4**
Sound, repo-aware plan: ACTION_SEND intent, Retrofit to `/v1/tasks/long-running`, receipt-checking flow, names `long_running_tasks.py`/`route.ts`/`CodingCommandCenterShell.tsx`. Minor URL typo (`daveveloper.android.com`). Specific enough to execute. 4.

**A4 — Obsidian notes → AI context — 5**
Best record. Recommends Smart Connections first, ties it to real repo files and real env flags, gives a concrete 4-step build plan, honestly states the local-embedding tradeoff. Research visibly drives "build first." Minor env-flag typos. 5.

**A5 — Local AI workstation (Dell/Mac/Windows, cost) — 2**
Collapses "Dell Mac" into one machine; never gives Dell or Windows distinct roles; no cost/GPU guidance; ignores the homelab-GPU/Docker+AMD research that should drive a cost-aware split; routes production LLM traffic to `spirit-mac-mini` on the strength of a `python3 --version` ping (overclaim). Materiality bullets are decorative. Does not satisfy the actual user goal. 2.

**A6 — Media metadata cleanup, no mutation — 5**
Strong and honest: recommends TinyMediaManager, correctly reasons the no-mutation constraint rules out direct SpiritFlix integration, names the right repo files, gives an install/configure/cleanup order, flags backup-before-cleanup. Research-shaped and boundary-honest. 5.

**A7 — Next highest-leverage daily-driver step — 3**
Reasonable (targets `policy_blocked` states in `long_running.py`) but generic: "locate the code… investigate root cause… implement a fix… add tests." It is a plausible direction, not a specific actionable next step; it does not name the actual policy function or the specific recovery path. Better than nothing for an outside agent, but mostly template-shaped. 3.

**A8 — Small proxy-run dashboard — 3**
Generic dashboard sketch (status, task, execution details, errors) tied loosely to `long_running.py`/`durable_execution.py`/`CodingCommandCenterShell.tsx`. No concrete data model, no mention of the causal events / consumer evidence that a real proxy-run dashboard would surface. Plausible but template-y. 3.

**A9 — Current local LLM tools, "this month" — 2**
Direction (vLLM or LM Studio) is plausible and sources are 2026-dated, but the work product is **garbled**: corrupted URLs/tokens (`local_l لمs`, `l لم-inference`, fabricated `vlvm` host). Currency is only weakly stated ("for the current month", no month named). Comparison is thin. Not clean enough to hand to another agent without re-research. 2.

**A10 — Outside-AI next-step handoff — 3**
Reasonable (investigate `current_research.py`, integration with durable execution, adherence to canonical paths) and names real files/functions (`run_current_research_for_task`, `run_scout_research_diagnostics`, `run_searxng_research_diagnostics`, `research_packet_hash`). But it is an "investigate and report" handoff, not a concrete build step, and it explicitly defers all conclusions. Useful as orientation, generic as a next action. 3.

## Roll-up

| ID | Score |
|----|-------|
| A1 | 4 |
| A2 | 3 |
| A3 | 4 |
| A4 | 5 |
| A5 | 2 |
| A6 | 5 |
| A7 | 3 |
| A8 | 3 |
| A9 | 2 |
| A10 | 3 |

- Sum = 34 / 10 → **average = 3.4**
- Lowest score: **2** (A5, A9)
- Prompts below 3: **none at <3**, but two at exactly the floor (A5, A9 = 2) → **fails "no prompt below 3" if read strictly as "≥3"**; either way, two prompts are at/below the floor.
- A2 (3) and A5 (2): **both below the required 4** for the previously-failing prompts.

## Acceptance bar check

- average ≥ 4.0? **NO (3.4)**
- no prompt below 3? **NO** (A5=2, A9=2)
- A2 ≥ 4? **NO (3)**
- A5 ≥ 4? **NO (2)**

The usefulness bar is **not met** on every axis.

## Notes

- The genuinely strong records (A4, A6, A1, A3) show the live harness *can* produce evidence-shaped, repo-aware plans when the model cooperates and the topic is well-covered by search. These are real and should not be discarded.
- The weak records (A5, A9, A2) correlate exactly with the grader's blind spots: corrupted/garbled content, decorative materiality, and a renamed Mac ping all PASS the keyword gate. This is the Stage 2 weakness showing up in final output.
- Compared to the failed generated draft (prior avg 3.9): this rerun's average (3.4) is *lower*, primarily because A5 and A9 regressed into garbled/under-specified outputs while still passing the (now easier) gate. That is the opposite of what a tightened fix should produce.
