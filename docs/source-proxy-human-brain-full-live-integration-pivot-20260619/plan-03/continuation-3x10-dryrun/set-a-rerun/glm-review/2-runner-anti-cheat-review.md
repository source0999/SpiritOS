# Stage 2 — Runner Anti-Cheat Review

Reviewer: GLM (independent, review-only).
Date: 2026-06-20.
Target: `set-a-rerun/_stage4r_runner.py` (644 lines).

## Is it orchestration glue or a cheating generator?

**It is genuine orchestration glue that calls a live harness and a live model.** This is a real and large improvement over `set-a/_generate_set_a_records.py`. Specifically:

- Imports real modules: `run_current_research_for_task`, `run_mac_worker_for_task`, `decide_route`, `build_task_spec_intake`, `create_plan3_durable_task`, `record_plan3_consumer_evidence`, `record_subsystem_integration_result`, `apply_plan3_policy`, `get_long_running_task` (L23-35).
- Calls a live model each attempt via `ollama()` → `http://127.0.0.1:11434/api/generate` (L156-168, L481). Final answer text = `raw_model["response"]`. No canned PLANS.
- Sources = provider return from `run_current_research_for_task` (L453-455). No hardcoded SOURCES.
- Writes raw evidence per step: `{pid}.harness.raw.json`, `.research.raw.json`, `.repo_context.raw.json`, `.mac.raw.json`, `.policy.raw.json`, `.model.attempt{N}.raw.json`, `.grader.attempt{N}.raw.json`, `.task.final.raw.json` (L449-468, L483, L495, L568).
- `final_status` derived by `grade()` (L256-269), not stamped.
- `fake_go_detected` computed (L290).
- task_id/trace_id/consumer_event_id come from real long-running-task causal state (L448, L499-500).

So the **structural** cheating from the old generator is gone. Good.

## Anti-cheat checklist

| Check | Result | Notes |
|---|---|---|
| Uses real Source Proxy modules | PASS | L23-35 |
| Calls `run_current_research_for_task` for research prompts | PASS | L453 |
| Writes raw provider evidence | PASS (in code) | raw_evidence_dir unreachable on this seat (Stage 0) — existence not independently confirmed |
| Calls a live model, not a PLANS dict | PASS | L481 |
| Avoids hardcoded final answers | PASS | |
| Avoids hardcoded source lists | PASS | |
| Computes `final_status` from a grader | PASS | L217-292 |
| Computes `fake_go_detected` | PASS | L290 |
| Grader not just keyword hits | **FAIL** | see below |
| `research_materially_changed_output` not too easy | **FAIL** | see below |
| A5 Mac validation strong enough | **FAIL** | see below |
| Writes/consumes real task trace evidence | PASS | L484-500 |

## Weakness 1 — The grader is keyword/title-echo driven, not usefulness driven

`grade()` computes `research_materially_changed_output` via `structured_materiality` (L222-228):
```
"research findings that changed the plan" in lowered
and lowered.count("finding:") >= 2
and lowered.count("source:") >= 2
and lowered.count("how it changed the plan:") >= 2
and source_hit_count(sources, lowered) >= 2
```
Three of those four terms (`"research findings that changed the plan"`, `Finding:`, `Source:`, `How it changed the plan:`) are **handed to the model verbatim in the prompt** (L208-211). The model is literally told to emit those exact strings. So the structural checks pass by construction, not by merit.

`source_hit_count` (L143-153) then counts a "hit" whenever any 4+ char title word or source host appears anywhere in the lowered work text. I reproduced this locally:

> A 3-sentence echo — `"…reddit.com kunalganglani.com youtube.com local llm with ollama has anyone actually gotten…"` plus the handed-in `Finding:/Source:/How it changed the plan:` template — yields `source_hit_count = 8` (needs ≥2). It PASSES `research_materially_changed_output=true` without the recommendation changing at all.

This is the cheat-list item #10 (grader only checks keyword hits) and #7 (materiality true only because source names are echoed). The other gates — `limitations_stated`, `handoff_created`, `recommendation_present` (L248-251) — are likewise bare keyword presence (`"limit"`, `"recommend"`, `"handoff"`). None of them ask whether the plan is *useful* or whether the research *changed* anything.

**Could this runner pass with shallow source-name echoing rather than real research-shaped recommendations?** **YES.** Demonstrably. A2 and A9 work products (Stages 5/7) are near-examples: A2 echoes source domains including hallucinated ones (`dexevelopeer.chrome.com`), A9 echoes `vlvm`/`l لمs` corrupted tokens; both PASS.

## Weakness 2 — A5 Mac "validation" is a renamed system_status ping

Runner L462:
```
mac = run_mac_worker_for_task(task_id, mode="mac_safe_check",
    input_data={"check_command": "python3 --version",
                "purpose": "Stage 4R A5 workstation capability readback"})
```
The Mac gate is (L236): `mac_ok = mac_status == "INTEGRATED_LIVE" and mac_job_type != "system_status"`. `mac_safe_check` maps to job_type `run_safe_check` (mac_integration.py L89-95), so `mac_job_type != "system_status"` is True and the gate passes.

But `python3 --version` is a capability readback that proves the Mac can run a Python interpreter — it says nothing about whether the Mac should host the local-AI workload, whether its GPU/RAM can run the recommended models, or any Dell-vs-Mac-vs-Windows role decision. This is the exact proof class the prior review rejected (cheat #14: "A5 passes from Mac system_status alone"; #15: "A5 claims Mac validation but only performed a generic ping"). Renaming `system_status` → `run_safe_check` and running `python3 --version` does not change what was proven. `mac_system_status_alone_used_as_pass` is therefore falsely reported as `false`.

## Weakness 3 — Prompt pre-shapes the answer structure (mild scaffolding)

`model_prompt()` (L180-214) instructs the model to "Write sections exactly: Recommendation / Research findings that changed the plan / Evidence Used / Plan / Limits / Next Handoff" and mandates the exact `Finding:/Source:/How it changed the plan:` bullet shape. This is partly legitimate (it is a planning worker, structure is reasonable), but because the grader keys on those exact section/bullet strings, the prompt is **grading its own template**, not the work. That is mild scaffolding that inflates the pass rate. It is not the same severity as canned answers, but it makes the gate non-adversarial.

## Weakness 4 — Repo-context read is a needle-grep, not a semantic read

`read_repo()` (L83-96) reads a hardcoded per-prompt `REPO_SURFACES[pid]` file list and keeps only lines containing needles (`long, task, consumer, trace, mac, obsidian, jellyfin, receipt, policy, research`). `repo_used` (L230) then just checks the filename appears in the lowered text. So "repo context used" reduces to "model mentioned a real filename." A3/A4/A6/A7/A10 do mention real files and use them sensibly, so this is often satisfied honestly — but the gate itself cannot tell honest use from name-dropping, and the file list is operator-curated, not router-selected.

## Hard question answer

> Could this runner still pass with shallow source-name echoing rather than real research-shaped recommendations?

**Yes.** The materiality gate is satisfiable by echoing source titles/domains + emitting the prompt-mandated bullet template. The usefulness/limitations/handoff gates are bare keyword checks. A non-trivial, honest recommendation is *possible* (and several records are genuinely good), but it is not *required* to PASS. The runner is a real harness that the grader has made easy to satisfy.

## Verdict

**RUNNER_WEAK_BUT_ACCEPTABLE** leaning toward **RUNNER_NEEDS_FIX**.

- It is not a cheating generator (no canned answers/sources/plans; live model + live research + computed grading). The structural prior cheats are gone.
- But the grader is non-adversarial: materiality = keyword/template echo; usefulness = keyword presence; A5 Mac = renamed ping. A rerun that relied on these would still produce 10/10 PASS without earning it.
- The single most important residual risk: a future run (or even this one, where the model under-performs) can reach PASS by echoing source names and the handed-in template. That is the old failure in a new form.
