# Stage 1 — Prior Failure Carryforward

Reviewer: GLM (independent, review-only).
Date: 2026-06-20.

## Prior failure (old `set-a/`)

From `set-a/glm-review/8-set-a-verdict.md` + `glm-set-a-verdict.json` the prior GLM review returned **NEEDS_FIX, cheating_detected=true** with these exact root causes:

1. Records produced by `set-a/_generate_set_a_records.py` (a generator), not a live model run.
2. Work products came from a hardcoded `PLANS` dict.
3. Sources came from a hardcoded `SOURCES` dict.
4. `live_search_used=true` derived from `bool(SOURCES)`, not provider evidence; `route_decision.research_sources=[]` on every record.
5. `final_status` defaulted to PASS; never derived by reading the work product.
6. `fake_go_detected=false` hardcoded, never computed.
7. `repo_context_used` was one shared static text block, not in-run reads.
8. A5 self-contradiction: `mac_status=INTEGRATED_LIVE`+PASS while the "integration" was a read-only `system_status` SSH ping.
9. Trace/consumer plumbing was real but consumed canned strings.

## Did the rerun address each?

| Prior failure mode | Rerun status | Evidence |
|---|---|---|
| Old generator used | **Disqualified** | `set-a-rerun/1-prior-generator-disqualified.md` explicitly disqualifies `_generate_set_a_records.py`. The rerun is driven by `_stage4r_runner.py`, which imports real modules (`run_current_research_for_task`, `run_mac_worker_for_task`, `decide_route`, `create_plan3_durable_task`, …) and calls a live Ollama model (`gemma3n:e4b`) per attempt. No `PLANS`/`SOURCES` dicts in the runner. |
| Hardcoded work products | **Fixed** | Final answer text is `raw_model["response"]` from `ollama(...)` (runner L481-482), then written to `A*.md`. No canned plan strings in the runner. |
| Hardcoded source lists | **Fixed** | Sources come from `((research or {}).get("research_packet") or {}).get("sources")`, the return of `run_current_research_for_task` (runner L453-455). No `SOURCES` dict. |
| `live_search_used` from bool(SOURCES) | **Improved but unverifiable** | Now `bool(sources)` where `sources` is the *provider's* returned list (runner L275, `live_search_used": bool(sources)`). That is only honest if the provider genuinely returned results — which requires raw provider evidence to confirm. **Raw evidence not reachable on this seat** (Stage 0). So this is "fixed in code" but not independently confirmable here. |
| `final_status` stamped PASS | **Fixed** | `grade()` derives PASS/NEEDS_FIX/BLOCKED_ENV from gate checks (runner L256-269). No default PASS. |
| `fake_go_detected` hardcoded | **Fixed** | Computed: `bool(status=="PASS" and (failed or blocked))` (runner L290). |
| `repo_context_used` static block | **Fixed** | `read_repo(pid)` does a real per-prompt read of `REPO_SURFACES[pid]` files (runner L83-96), and `repo_used` requires the actual filename to appear in the work product (runner L230). |
| A5 Mac = system_status ping | **NOT fixed — see Stage 6.** | The runner still validates Mac via `check_command="python3 --version"` (runner L462). It dodges the old gate by using mode `mac_safe_check` → job_type `run_safe_check` (not `system_status`), so `mac_job_type != "system_status"` is True — but a `python3 --version` capability readback is exactly the same class of trivial proof the prior review rejected (cheat #14/#15). |
| Consumer plumbing real but canned upstream | **Fixed for content** | The consumed output is now the live model response via `record_subsystem_integration_result(...)` (runner L484-493). |

## Answers to the carryforward questions

- **Was the old failed Set A explicitly disqualified?** YES. `1-prior-generator-disqualified.md` states the old generator, old A1-A10, hardcoded SOURCES/PLANS, and old summary/verdict are all disqualified.
- **Did rerun evidence use `set-a-rerun/` only?** YES. `summary.json` `old_generator_disqualified=true`; the new runner writes only to `set-a-rerun/` and the RAW evidence dir.
- **Did the runner avoid old `_generate_set_a_records.py`?** YES. The runner does not import or read it; it calls real Source Proxy modules and a live model.
- **Are old A1-A10 records absent from acceptance logic?** YES. Acceptance in `validate()` (runner L384-408) and `summary.json` only iterate `set-a-rerun/A*.json`.
- **Did the rerun fix the exact prior failure modes?** MOSTLY. The generator/canned-content/hardcoded-source/stamped-PASS/hardcoded-fake_go/static-repo-block failures are genuinely fixed at the code level. The two failure modes that remain are: (a) the A5 Mac proof is still a trivial capability readback (renamed job_type), and (b) research materiality is re-grouted into a weak keyword/title-echo gate rather than a real research-then-revise judgment (Stages 2/5/6). The *most visible* prior cheats are gone; subtler ones moved.

## Verdict

**prior_failure_carried_forward: PARTIAL.** Old generator, canned PLANS/SOURCES, stamped PASS, hardcoded fake_go, and static repo block are fixed. The A5 Mac-validation cheat and the "materiality from echo" weakness are carried forward in new clothing.
